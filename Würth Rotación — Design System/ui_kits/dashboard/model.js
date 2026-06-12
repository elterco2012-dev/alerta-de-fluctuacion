/* model.js — derived scoring model + extra datasets for the v2 screens.
   Loads AFTER data.js. Adds helpers to window and extends DASH_DATA with
   cohort retention, monthly rotation, and activity data. All simulated. */
(function () {
  const D = window.DASH_DATA;

  // ---- #1 Score explainability: signal catalog with weights ----
  // Keys match the señal labels used in data.js.
  const SIGNAL_CATALOG = {
    "onboarding":    { peso: 2.0, desc: "En ventana crítica de inducción (primeros 6 meses)" },
    "días cero↑":    { peso: 2.0, desc: "Días sin registrar ventas en aumento" },
    "caída 3m":      { peso: 2.0, desc: "Cumplimiento de plan cayó 3 meses seguidos" },
    "plan<80%":      { peso: 1.5, desc: "Cumplimiento de plan por debajo del 80%" },
    "zona quemada":  { peso: 1.5, desc: "Asignado a zona con alta rotación histórica" },
    "mes 4-6":       { peso: 1.0, desc: "Mes 4 a 6: ventana de adaptación" },
    "inactivos↑":    { peso: 1.0, desc: "Clientes inactivos en su cartera en aumento" },
    "cobranza baja": { peso: 1.0, desc: "Cobranza por debajo del objetivo" },
    "clientes L:0":  { peso: 0.5, desc: "Sin altas de clientes nuevos en el período" },
    "ticket↓":       { peso: 0.5, desc: "Ticket promedio en descenso" },
  };

  // returns { base, factores:[{label,peso,desc}], suma } for a vendor
  function scoreBreakdown(r) {
    const base = 1.0;
    const factores = (r.senales || []).map(([label]) => ({
      label, peso: (SIGNAL_CATALOG[label] || { peso: 0.5 }).peso,
      desc: (SIGNAL_CATALOG[label] || { desc: "Señal de riesgo" }).desc,
    })).sort((a, b) => b.peso - a.peso);
    const suma = base + factores.reduce((s, f) => s + f.peso, 0);
    return { base, factores, suma: Math.min(10, Math.round(suma)) };
  }

  // ---- #2 Score trajectory: deterministic 6-month history ending near score ----
  function buildScoreHistory(r) {
    // worsening signals → score climbed recently; recovering → fell
    const worsening = (r.senales || []).some(([l]) => ["caída 3m", "onboarding", "días cero↑"].includes(l));
    const seed = r.id % 7;
    const cur = r.score;
    const hist = [];
    for (let i = 5; i >= 0; i--) {
      let v;
      if (worsening) v = cur - Math.round(i * (0.6 + seed * 0.06));
      else v = cur + Math.round(i * (0.25 + (seed % 3) * 0.08)) - (i > 3 ? 1 : 0);
      hist.push(Math.max(1, Math.min(10, v)));
    }
    hist[5] = cur;
    return hist;
  }
  function scoreDelta(r) {
    const h = r._hist || buildScoreHistory(r);
    return h[5] - h[4];
  }

  // attach hist + delta to every vendor (in place)
  D.V.forEach((r) => { r._hist = buildScoreHistory(r); r._delta = r._hist[5] - r._hist[4]; });

  // ---- #3 Onboarding cohort retention (% still active by month of tenure) ----
  D.COHORTS = [
    { cohorte: "Jul 25", ingresos: 8, ret: [100, 88, 75, 50, 38, 38] },
    { cohorte: "Ago 25", ingresos: 6, ret: [100, 83, 67, 50, 33] },
    { cohorte: "Sep 25", ingresos: 9, ret: [100, 89, 78, 56] },
    { cohorte: "Oct 25", ingresos: 5, ret: [100, 80, 60] },
    { cohorte: "Nov 25", ingresos: 7, ret: [100, 86] },
    { cohorte: "Dic 25", ingresos: 4, ret: [100] },
  ];
  // company-wide survival curve, months 0..7
  D.RETENCION = [100, 86, 71, 53, 41, 33, 28, 25];

  // ---- Historial: monthly rotation + avg risk score trend (last 6 months) ----
  D.ROTACION = [
    { mes: "Ago", bajas: 6, altas: 5, scoreProm: 4.1 },
    { mes: "Sep", bajas: 4, altas: 9, scoreProm: 4.4 },
    { mes: "Oct", bajas: 7, altas: 5, scoreProm: 4.9 },
    { mes: "Nov", bajas: 5, altas: 7, scoreProm: 5.2 },
    { mes: "Dic", bajas: 8, altas: 4, scoreProm: 5.6 },
    { mes: "Ene", bajas: 6, altas: 6, scoreProm: 5.4 },
  ];

  // ---- Actividad: Televentas (llamadas) + Viajantes (visitas) vs plan ----
  // derived from V so names line up
  function actividadDe(r) {
    const esTel = r.tipo === "Televentas";
    const planUnidad = esTel ? 60 : 22;           // llamadas/día or visitas/semana target
    const cumpl = Math.max(35, Math.min(112, Math.round(r.plan3m * (0.9 + (r.id % 5) * 0.03))));
    const real = Math.round(planUnidad * cumpl / 100);
    const contactos = esTel ? Math.round(real * (0.55 + (r.id % 4) * 0.05)) : Math.round(real * (0.8));
    return { tipo: r.tipo, plan: planUnidad, real, cumpl, contactos, clientesL: r.senales.some(([l]) => l === "clientes L:0") ? 0 : 1 + (r.id % 4) };
  }
  D.ACTIVIDAD = D.V.map((r) => ({ id: r.id, nombre: r.nombre, grupo: r.grupo, supervisor: r.supervisor, nivel: r.nivel, ...actividadDe(r) }));

  // ---- #1 Prediction vs. outcome: did last month's score predict who left? ----
  // Confusion matrix over the cohort scored 1 month ago (simulated but internally
  // consistent: high score → much higher base rate of leaving).
  // marcado = score >= 6 last month ("alertado"); se_fue = actually left this month.
  D.PREDICCION = {
    periodo: "Mayo 2025",
    // counts
    vp: 11,   // marcado alto Y se fue          (verdadero positivo)
    fn: 3,    // NO marcado pero se fue          (falso negativo — la fuga sorpresa)
    fp: 8,    // marcado alto pero retenido      (falso positivo — incluye los que salvamos)
    vn: 39,   // NO marcado y se quedó           (verdadero negativo)
    // of the FP, how many had an intervention (i.e. we likely saved them)
    fp_intervenidos: 6,
  };

  // ---- #2 Action effectiveness by PROFILE (mejora promedio de score) ----
  // perfil = combinación de antigüedad + zona; tells you what worked for similar reps.
  D.EFECTIVIDAD = {
    onboarding_quemada: [   // nuevos (<6m) en zona de alta rotación
      { tipo: "Reunión 1:1", avg: 1.8, n: 7 },
      { tipo: "Acompañamiento", avg: 1.3, n: 5 },
      { tipo: "Reasignación de zona", avg: 1.1, n: 3 },
      { tipo: "Capacitación", avg: 0.4, n: 4 },
    ],
    onboarding_normal: [    // nuevos en zona normal
      { tipo: "Acompañamiento", avg: 1.6, n: 6 },
      { tipo: "Reunión 1:1", avg: 1.2, n: 8 },
      { tipo: "Capacitación", avg: 0.9, n: 5 },
    ],
    senior_caida: [         // veteranos (>12m) con caída de plan
      { tipo: "Ajuste de cartera", avg: 1.5, n: 4 },
      { tipo: "Reunión 1:1", avg: 1.1, n: 9 },
      { tipo: "Capacitación", avg: 0.7, n: 6 },
    ],
    default: [
      { tipo: "Reunión 1:1", avg: 1.3, n: 12 },
      { tipo: "Acompañamiento", avg: 1.0, n: 8 },
      { tipo: "Capacitación", avg: 0.6, n: 7 },
    ],
  };
  function perfilDe(r) {
    if (r.meses <= 6) return r.rb > 0.45 ? "onboarding_quemada" : "onboarding_normal";
    if (r.meses > 12 && r.senales.some(([l]) => l === "caída 3m" || l === "plan<80%")) return "senior_caida";
    return "default";
  }
  function perfilLabel(p) {
    return {
      onboarding_quemada: "nuevos en zona de alta rotación",
      onboarding_normal: "nuevos en zona normal",
      senior_caida: "veteranos con caída de plan",
      default: "vendedores en riesgo",
    }[p];
  }
  // best action + the whole ranking for a vendor's profile
  function recomendarAccion(r) {
    const p = perfilDe(r);
    const ranking = D.EFECTIVIDAD[p] || D.EFECTIVIDAD.default;
    return { perfil: p, perfilLabel: perfilLabel(p), ranking, mejor: ranking[0] };
  }

  Object.assign(window, { SIGNAL_CATALOG, scoreBreakdown, buildScoreHistory, scoreDelta, perfilDe, perfilLabel, recomendarAccion });
})();
