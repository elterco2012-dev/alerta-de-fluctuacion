/* Mock data for the Würth Rotación dashboard UI kit.
   Shapes mirror src/score_engine.py output (scores_df) + grupos + sparklines.
   Numbers are invented; nothing here is real Würth data. */
(function () {
  // sparkline = last 3 months % Plan (oldest → newest)
  const V = [
    { id: 1119, nombre: "Pérez, Martín",     tipo: "Viajante",   grupo: "Centro",   supervisor: "Rodríguez, A.", meses: 3,  score: 9, nivel: "critico", plan3m: 62, spark: [74, 66, 62], rb: 0.68,
      senales: [["caída 3m","red"],["onboarding","red"],["plan<80%","orange"],["zona quemada","orange"]] },
    { id: 6453, nombre: "Gómez, Laura",       tipo: "Televentas", grupo: "Norte",    supervisor: "Díaz, M.",      meses: 2,  score: 8, nivel: "critico", plan3m: 58, spark: [70, 61, 58], rb: 0.41,
      senales: [["onboarding","red"],["días cero↑","red"],["plan<80%","orange"]] },
    { id: 5855, nombre: "Sosa, Diego",        tipo: "Viajante",   grupo: "Centro",   supervisor: "Rodríguez, A.", meses: 5,  score: 8, nivel: "critico", plan3m: 64, spark: [80, 72, 64], rb: 0.68,
      senales: [["caída 3m","red"],["mes 4-6","orange"],["zona quemada","orange"],["inactivos↑","orange"]] },
    { id: 2207, nombre: "Ibáñez, Carla",      tipo: "Televentas", grupo: "Oeste",    supervisor: "Vega, P.",      meses: 14, score: 7, nivel: "alto",    plan3m: 71, spark: [78, 74, 71], rb: 0.52,
      senales: [["plan<80%","orange"],["cobranza baja","orange"],["clientes L:0","yellow"]] },
    { id: 4419, nombre: "López, Hernán",      tipo: "Viajante",   grupo: "Sur",      supervisor: "Fernández, J.", meses: 4,  score: 7, nivel: "alto",    plan3m: 73, spark: [69, 71, 73], rb: 0.28,
      senales: [["mes 4-6","orange"],["clientes L:0","yellow"]] },
    { id: 7781, nombre: "Méndez, Sofía",      tipo: "Televentas", grupo: "Norte",    supervisor: "Díaz, M.",      meses: 9,  score: 6, nivel: "alto",    plan3m: 77, spark: [72, 75, 77], rb: 0.41,
      senales: [["plan<80%","orange"],["ticket↓","yellow"]] },
    { id: 3392, nombre: "Castro, Julián",     tipo: "Viajante",   grupo: "Centro",   supervisor: "Rodríguez, A.", meses: 22, score: 5, nivel: "medio",   plan3m: 84, spark: [82, 83, 84], rb: 0.68,
      senales: [["zona quemada","orange"]] },
    { id: 1280, nombre: "Romero, Valeria",    tipo: "Televentas", grupo: "Oeste",    supervisor: "Vega, P.",      meses: 7,  score: 5, nivel: "medio",   plan3m: 86, spark: [80, 84, 86], rb: 0.52,
      senales: [["cobranza baja","orange"]] },
    { id: 9014, nombre: "Acosta, Pablo",      tipo: "Viajante",   grupo: "Sur",      supervisor: "Fernández, J.", meses: 31, score: 4, nivel: "medio",   plan3m: 89, spark: [85, 87, 89], rb: 0.28,
      senales: [["clientes L:0","yellow"]] },
    { id: 6627, nombre: "Núñez, Florencia",   tipo: "Televentas", grupo: "Norte",    supervisor: "Díaz, M.",      meses: 18, score: 3, nivel: "bajo",    plan3m: 94, spark: [91, 93, 94], rb: 0.41, senales: [] },
    { id: 3105, nombre: "Vera, Maximiliano",  tipo: "Viajante",   grupo: "Sur",      supervisor: "Fernández, J.", meses: 41, score: 2, nivel: "bajo",    plan3m: 98, spark: [96, 97, 98], rb: 0.28, senales: [] },
    { id: 8890, nombre: "Ríos, Camila",       tipo: "Televentas", grupo: "Oeste",    supervisor: "Vega, P.",      meses: 26, score: 2, nivel: "bajo",    plan3m: 101, spark: [99, 100, 101], rb: 0.52, senales: [] },
    { id: 1407, nombre: "Torres, Nicolás",    tipo: "Viajante",   grupo: "Centro",   supervisor: "Rodríguez, A.", meses: 1,  score: 9, nivel: "critico", plan3m: 55, spark: [0, 60, 55], rb: 0.68,
      senales: [["onboarding","red"],["días cero↑","red"],["zona quemada","orange"]] },
    { id: 5520, nombre: "Silva, Agustina",    tipo: "Televentas", grupo: "Norte",    supervisor: "Díaz, M.",      meses: 6,  score: 6, nivel: "alto",    plan3m: 76, spark: [82, 79, 76], rb: 0.41,
      senales: [["caída 3m","red"],["mes 4-6","orange"]] },
  ];

  // grupos / zones — riesgo_base drives zona level
  const Z = [
    { grupo: "Centro", supervisor: "Rodríguez, A.", historicos: 38, permEgreso: 4.1, planProm: 64, rb: 0.68, activos: 4 },
    { grupo: "Oeste",  supervisor: "Vega, P.",      historicos: 24, permEgreso: 5.8, planProm: 79, rb: 0.52, activos: 3 },
    { grupo: "Norte",  supervisor: "Díaz, M.",      historicos: 21, permEgreso: 6.8, planProm: 81, rb: 0.41, activos: 4 },
    { grupo: "Sur",    supervisor: "Fernández, J.", historicos: 14, permEgreso: 12.4, planProm: 96, rb: 0.28, activos: 3 },
  ];

  // critical-window histogram: month of career → resignations
  const VENTANAS = [
    { m: 1, n: 9 }, { m: 2, n: 14 }, { m: 3, n: 17 }, { m: 4, n: 11 }, { m: 5, n: 8 },
    { m: 6, n: 7 }, { m: 7, n: 4 }, { m: 8, n: 3 }, { m: 9, n: 3 }, { m: 10, n: 2 },
    { m: 11, n: 2 }, { m: 12, n: 3 }, { m: 14, n: 1 }, { m: 16, n: 1 },
  ];

  // intervention history
  const INTERV = [
    { fecha: "2025-01-22", id: 1119, tipoV: "Viajante",   grupo: "Centro", tipo: "Reunión 1:1",       sup: "Rodríguez, A.", si: 9, sa: 7, nivelI: "critico", nivelA: "alto",   estado: "activo", obs: "Acordó plan de visitas semanal. Se lo notó receptivo." },
    { fecha: "2025-01-20", id: 6453, tipoV: "Televentas", grupo: "Norte",  tipo: "Acompañamiento",    sup: "Díaz, M.",      si: 8, sa: 8, nivelI: "critico", nivelA: "critico", estado: "activo", obs: "Sin cambios todavía. Reprogramar seguimiento." },
    { fecha: "2025-01-15", id: 2207, tipoV: "Televentas", grupo: "Oeste",  tipo: "Capacitación",      sup: "Vega, P.",      si: 7, sa: 5, nivelI: "alto",    nivelA: "medio",  estado: "activo", obs: "Capacitación en gestión de cartera. Mejoró cobranza." },
    { fecha: "2025-01-10", id: 5855, tipoV: "Viajante",   grupo: "Centro", tipo: "Ajuste de cartera", sup: "Rodríguez, A.", si: 8, sa: null, nivelI: "critico", nivelA: null, estado: "Baja", obs: "Renunció antes del seguimiento. Zona crítica." },
  ];

  const TIPOS_INTERV = ["Reunión 1:1", "Acompañamiento", "Capacitación", "Ajuste de cartera", "Reasignación de zona"];

  // ── Historial: cohortes por año de ingreso (mediana de permanencia de los que se fueron) ──
  const COHORTES = [
    { anio: 2016, mediana: 17, bajas: 22 }, { anio: 2017, mediana: 15, bajas: 26 },
    { anio: 2018, mediana: 14, bajas: 31 }, { anio: 2019, mediana: 12, bajas: 35 },
    { anio: 2020, mediana: 9,  bajas: 28 }, { anio: 2021, mediana: 8,  bajas: 41 },
    { anio: 2022, mediana: 7,  bajas: 44 }, { anio: 2023, mediana: 6,  bajas: 52 },
    { anio: 2024, mediana: 5,  bajas: 58 }, { anio: 2025, mediana: 5,  bajas: 49 },
  ];
  // bajas reales por año de egreso + tasa de rotación
  const ROTACION = [
    { anio: 2019, bajas: 30, tasa: 38 }, { anio: 2020, bajas: 34, tasa: 44 },
    { anio: 2021, bajas: 47, tasa: 55 }, { anio: 2022, bajas: 51, tasa: 58 },
    { anio: 2023, bajas: 56, tasa: 61 }, { anio: 2024, bajas: 62, tasa: 64 },
    { anio: 2025, bajas: 59, tasa: 63 },
  ];
  // zonas históricas: % que se fue en <6 meses
  const ZONAS_HIST = [
    { grupo: "Centro",           supervisor: "Rodríguez, A.", activos: 4, total: 38, bajasRapidas: 23, pctRapida: 61, permMediana: 4 },
    { grupo: "Televentas Auto",  supervisor: "Vega, P.",      activos: 3, total: 24, bajasRapidas: 13, pctRapida: 54, permMediana: 5 },
    { grupo: "Norte",            supervisor: "Díaz, M.",      activos: 4, total: 21, bajasRapidas: 9,  pctRapida: 43, permMediana: 7 },
    { grupo: "Televentas Metal", supervisor: "Vega, P.",      activos: 2, total: 18, bajasRapidas: 7,  pctRapida: 39, permMediana: 6 },
    { grupo: "Oeste",            supervisor: "Vega, P.",      activos: 3, total: 16, bajasRapidas: 5,  pctRapida: 31, permMediana: 9 },
    { grupo: "Sur",              supervisor: "Fernández, J.", activos: 3, total: 14, bajasRapidas: 3,  pctRapida: 21, permMediana: 12 },
  ];

  // ── Actividad: cumplimiento de plan, por período ──
  const PERIODOS = ["2025-01", "2024-12", "2024-11"];
  // resumen por tipo (período actual 2025-01)
  const ACTIVIDAD = {
    "2025-01": {
      televentas: { vendedores: 6, targetDia: 80, planDia: 72, ejecPlanDia: 41, espontaneasDia: 9, totalDia: 50, cumpl: 69 },
      viajantes:  { vendedores: 8, targetDia: 15, planDia: 13, ejecPlanDia: 7,  espontaneasDia: 2, totalDia: 9,  cumpl: 69 },
    },
    "2024-12": {
      televentas: { vendedores: 6, targetDia: 80, planDia: 70, ejecPlanDia: 38, espontaneasDia: 8, totalDia: 46, cumpl: 66 },
      viajantes:  { vendedores: 8, targetDia: 15, planDia: 13, ejecPlanDia: 6,  espontaneasDia: 2, totalDia: 8,  cumpl: 62 },
    },
    "2024-11": {
      televentas: { vendedores: 5, targetDia: 80, planDia: 68, ejecPlanDia: 35, espontaneasDia: 7, totalDia: 42, cumpl: 62 },
      viajantes:  { vendedores: 7, targetDia: 15, planDia: 12, ejecPlanDia: 6,  espontaneasDia: 1, totalDia: 7,  cumpl: 58 },
    },
  };
  // tendencia mensual (cumplimiento %)
  const ACT_TREND = {
    televentas: [{ p: "2024-11", c: 62 }, { p: "2024-12", c: 66 }, { p: "2025-01", c: 69 }],
    viajantes:  [{ p: "2024-11", c: 58 }, { p: "2024-12", c: 62 }, { p: "2025-01", c: 69 }],
  };
  // ranking por vendedor (período actual)
  const ACT_RANKING = {
    televentas: [
      { nombre: "Gómez, Laura",     id: 6453, grupo: "Televentas Auto",  plan: 80, delPlan: 14, esp: 4, total: 18, cumpl: 23 },
      { nombre: "Méndez, Sofía",    id: 7781, grupo: "Televentas Metal", plan: 72, delPlan: 28, esp: 6, total: 34, cumpl: 47 },
      { nombre: "Romero, Valeria",  id: 1280, grupo: "Televentas Auto",  plan: 70, delPlan: 36, esp: 8, total: 44, cumpl: 63 },
      { nombre: "Silva, Agustina",  id: 5520, grupo: "Televentas Metal", plan: 74, delPlan: 42, esp: 9, total: 51, cumpl: 69 },
      { nombre: "Ríos, Camila",     id: 8890, grupo: "Televentas Auto",  plan: 68, delPlan: 51, esp: 11, total: 62, cumpl: 91 },
      { nombre: "Núñez, Florencia", id: 6627, grupo: "Televentas Metal", plan: 70, delPlan: 55, esp: 12, total: 67, cumpl: 96 },
    ],
    viajantes: [
      { nombre: "Torres, Nicolás",   id: 1407, grupo: "Centro", plan: 15, delPlan: 2,  esp: 1, total: 3,  cumpl: 20 },
      { nombre: "Pérez, Martín",     id: 1119, grupo: "Centro", plan: 14, delPlan: 5,  esp: 1, total: 6,  cumpl: 43 },
      { nombre: "Sosa, Diego",       id: 5855, grupo: "Centro", plan: 13, delPlan: 7,  esp: 2, total: 9,  cumpl: 69 },
      { nombre: "López, Hernán",     id: 4419, grupo: "Sur",    plan: 13, delPlan: 8,  esp: 2, total: 10, cumpl: 77 },
      { nombre: "Castro, Julián",    id: 3392, grupo: "Centro", plan: 12, delPlan: 9,  esp: 2, total: 11, cumpl: 92 },
      { nombre: "Acosta, Pablo",     id: 9014, grupo: "Sur",    plan: 12, delPlan: 10, esp: 2, total: 12, cumpl: 100 },
      { nombre: "Vera, Maximiliano", id: 3105, grupo: "Sur",    plan: 11, delPlan: 10, esp: 3, total: 13, cumpl: 118 },
    ],
  };

  window.DASH_DATA = { V, Z, VENTANAS, INTERV, TIPOS_INTERV, COHORTES, ROTACION, ZONAS_HIST, PERIODOS, ACTIVIDAD, ACT_TREND, ACT_RANKING };
})();
