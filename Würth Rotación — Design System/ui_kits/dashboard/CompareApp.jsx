/* Comparison shell — pick a screen, flip current vs v2. Feature screens
   (digest / mobile / estados) are v2-only and hide the toggle. */

const SCREENS = [
  { id: "inicio", label: "🏠 Inicio" },
  { id: "supervisor", label: "👤 Por supervisor" },
  { id: "intervenciones", label: "📝 Intervenciones" },
  { id: "costo", label: "💰 Costo" },
  { id: "historial", label: "📈 Historial" },
  { id: "actividad", label: "📞 Actividad" },
  { id: "precision", label: "🎯 Precisión" },
];
const FEATURES = [
  { id: "digest", label: "✉️ Resumen semanal" },
  { id: "mobile", label: "📱 Móvil" },
  { id: "estados", label: "🧩 Estados" },
];
const FEATURE_IDS = FEATURES.map((f) => f.id);
// v2-only screens (no "actual" counterpart → hide the toggle)
const V2_ONLY = [...FEATURE_IDS, "precision"];
const NUEVA_NOTA = {
  digest: "Resumen semanal que se envía por mail a cada supervisor para empujar la acción (#6).",
  mobile: "Vista móvil para viajantes en la ruta (#7).",
  estados: "Estados de carga, error de conexión y vacío (#5).",
  precision: "Valida que el score realmente predice las fugas — matriz predicción vs. resultado (#1).",
};

const V2_NOTES = {
  inicio: "① KPI dominante de riesgo · ② más aire · ③ permanencia 18→5m como estrella · ④ banner + columna “acción sugerida” · ⑤ chart sin ruido · ⑥ estado vacío.",
  supervisor: "Supervisores ordenados por urgencia · el nº de “requieren acción” es el héroe de cada tarjeta · banner de la peor zona · detalle con acción sugerida.",
  intervenciones: "Arranca con la tasa de efectividad · gráfico “qué tipo mueve más el score” · formulario plegable · impacto en lenguaje claro.",
  costo: "Lidera con el dinero en juego si no se actúa · exposición por zona priorizada · stat de la zona más cara · tabla más limpia.",
  historial: "Curva de supervivencia del equipo · tabla de retención por cohorte (#3) · rotación mensual · trayectoria del score promedio · ranking de mayores escaladas (#2).",
  actividad: "Lidera con el cumplimiento del canal · separa Televentas/Viajantes · ranking por menor cumplimiento · conecta baja actividad con riesgo de fuga.",
};

function CompareApp() {
  const data = window.DASH_DATA;
  const [screen, setScreen] = React.useState("inicio");
  const [v, setV] = React.useState("v2");
  const [modal, setModal] = React.useState(null);
  const isFeature = V2_ONLY.includes(screen);

  const actual = {
    inicio: () => <InicioView data={data} onOpenVendedor={setModal} />,
    supervisor: () => <SupervisorView data={data} onOpenVendedor={setModal} />,
    intervenciones: () => <InterventionsView data={data} />,
    costo: () => <CostView data={data} />,
    historial: () => <HistorialActual data={data} />,
    actividad: () => <ActividadActual data={data} />,
  }[screen];
  const v2 = {
    inicio: () => <InicioV2 data={data} onOpenVendedor={setModal} />,
    supervisor: () => <SupervisorV2 data={data} onOpenVendedor={setModal} />,
    intervenciones: () => <InterventionsV2 data={data} />,
    costo: () => <CostV2 data={data} />,
    historial: () => <HistorialV2 data={data} onOpenVendedor={setModal} />,
    actividad: () => <ActividadV2 data={data} onOpenVendedor={setModal} />,
    digest: () => <DigestView data={data} onOpenVendedor={setModal} />,
    mobile: () => <MobileView data={data} />,
    estados: () => <EstadosView />,
    precision: () => <PrecisionView data={data} />,
  }[screen];

  const Tab = ({ id, title, sub }) => (
    <button onClick={() => setV(id)} style={{
      flex: 1, textAlign: "left", padding: "11px 18px", borderRadius: 10, cursor: "pointer",
      border: "1px solid", borderColor: v === id ? "var(--ink-900)" : "var(--line-strong)",
      background: v === id ? "var(--ink-900)" : "#fff",
    }}>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14, color: v === id ? "#fff" : "var(--ink-700)" }}>{title}</div>
      <div style={{ fontFamily: "var(--font-sans)", fontSize: 12, color: v === id ? "rgba(255,255,255,.7)" : "var(--ink-400)", marginTop: 2 }}>{sub}</div>
    </button>
  );

  const pill = (s, active, onClick) => (
    <button key={s.id} onClick={onClick} style={{
      padding: "8px 15px", borderRadius: 999, cursor: "pointer", border: "1px solid",
      borderColor: active ? "var(--blue-accent)" : "var(--line-strong)",
      background: active ? "var(--blue-bg)" : "#fff",
      color: active ? "var(--blue-text)" : "var(--ink-600)",
      fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: 13, whiteSpace: "nowrap",
    }}>{s.label}</button>
  );

  return (
    <div style={{ maxWidth: 1180, margin: "0 auto", padding: "28px 2.5rem 60px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>
        <div>
          <div style={{ marginBottom: 4, fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 22, color: "var(--ink-900)" }}>🔔 Würth Rotación — antes / después</div>
          <div style={{ marginBottom: 18, fontFamily: "var(--font-sans)", fontSize: 13, color: "var(--ink-400)" }}>Pantallas del producto con toggle actual/v2, y mejoras nuevas (precisión, resumen semanal, móvil, estados).</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 7, fontFamily: "var(--font-sans)", fontSize: 12, color: "var(--ink-400)", whiteSpace: "nowrap" }}>
          <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--green-bright)" }} />
          Actualizado: 1 jun 2026, 08:00
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap", alignItems: "center" }}>
        {SCREENS.map((s) => pill(s, screen === s.id, () => { setScreen(s.id); setModal(null); }))}
        <span style={{ width: 1, height: 22, background: "var(--line-strong)", margin: "0 4px" }} />
        {FEATURES.map((s) => pill(s, screen === s.id, () => { setScreen(s.id); setModal(null); }))}
      </div>

      {!isFeature && (
        <div style={{ display: "flex", gap: 12, marginBottom: 14 }}>
          <Tab id="actual" title="Versión actual" sub="Recreación fiel del dashboard de hoy" />
          <Tab id="v2" title="Propuesta v2 profesional" sub="Jerarquía · acción · charts limpios" />
        </div>
      )}

      {!isFeature && v === "v2" && (
        <div style={{ background: "var(--blue-bg)", borderRadius: 10, padding: "12px 16px", marginBottom: 24, fontFamily: "var(--font-sans)", fontSize: 12.5, color: "var(--blue-text)", lineHeight: 1.5 }}>
          <b>Qué cambió:</b> {V2_NOTES[screen]}
        </div>
      )}
      {isFeature && (
        <div style={{ background: "var(--green-bg)", borderRadius: 10, padding: "12px 16px", marginBottom: 24, fontFamily: "var(--font-sans)", fontSize: 12.5, color: "var(--green-text)", lineHeight: 1.5 }}>
          <b>Mejora nueva</b> — no existe en el producto actual. {NUEVA_NOTA[screen]}
        </div>
      )}

      <div style={{ background: "#f4f5f7", borderRadius: 14, padding: 28 }}>
        {isFeature ? v2() : (v === "actual" ? actual() : v2())}
      </div>

      <VendedorModal r={modal} onClose={() => setModal(null)} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<CompareApp />);
