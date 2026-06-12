/* App shell — top nav + screen router + vendedor detail modal. */

function Placeholder({ emoji, title, blurb }) {
  return (
    <div>
      <div style={{ font: "var(--w-black) 22px var(--font-sans)", color: "var(--ink-900)", marginBottom: 4 }}>{emoji} {title}</div>
      <div style={{ fontSize: 14, color: "var(--ink-400)", marginBottom: 22 }}>{blurb}</div>
      <Card style={{ padding: "40px 22px", textAlign: "center", color: "var(--ink-400)" }}>
        <div style={{ fontSize: 34, marginBottom: 10 }}>{emoji}</div>
        <div style={{ fontSize: 14, fontWeight: 600, color: "var(--ink-600)" }}>Pantalla presente en el producto real</div>
        <div style={{ fontSize: 13, marginTop: 6, maxWidth: 460, marginLeft: "auto", marginRight: "auto", lineHeight: 1.5 }}>
          Este UI kit recrea Inicio, Por supervisor, Intervenciones y Costo de rotación.
          <b> {title}</b> existe en la app pero no se reconstruyó aquí — usá los mismos componentes (tabla, KPIs, badges, charts) para armarla.
        </div>
      </Card>
    </div>
  );
}

function App() {
  const data = window.DASH_DATA;
  const [screen, setScreen] = React.useState("inicio");
  const [modal, setModal] = React.useState(null);

  let view;
  if (screen === "inicio") view = <InicioView data={data} onOpenVendedor={setModal} />;
  else if (screen === "supervisor") view = <SupervisorView data={data} onOpenVendedor={setModal} />;
  else if (screen === "intervenciones") view = <InterventionsView data={data} />;
  else if (screen === "costo") view = <CostView data={data} />;
  else if (screen === "historial") view = <HistorialView data={data} />;
  else if (screen === "actividad") view = <ActividadView data={data} />;

  return (
    <div style={{ padding: "2.5rem", maxWidth: 1280, margin: "0 auto" }}>
      <TopNav current={screen} onNav={(k) => { setScreen(k); setModal(null); }} />
      {view}
      <div style={{ marginTop: 36, paddingTop: 16, borderTop: "1px solid var(--line)", fontSize: 12, color: "var(--ink-300)" }}>
        Würth Argentina · Sistema de alertas de rotación · Datos simulados · Recreación UI kit
      </div>
      <VendedorModal r={modal} onClose={() => setModal(null)} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
