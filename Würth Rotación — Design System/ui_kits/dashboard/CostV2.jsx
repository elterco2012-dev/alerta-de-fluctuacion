/* Costo de Rotación — v2. Leads with the single number that matters
   (total exposure in pesos), makes the "what's at stake if we do nothing"
   tangible, ranks where to act, cleaner table. Reuses costoRotacion(). */

function CostV2({ data }) {
  const { V, Z } = data;
  const [niveles, setNiveles] = React.useState(["critico", "alto"]);

  const enriched = V.map((r) => ({ ...r, c: window.costoRotacion(r) }));
  const toggle = (n) => setNiveles((p) => p.includes(n) ? p.filter((x) => x !== n) : [...p, n]);
  const fil = enriched.filter((r) => niveles.includes(r.nivel));

  const critArr = enriched.filter((r) => r.nivel === "critico");
  const elevArr = enriched.filter((r) => ["critico", "alto"].includes(r.nivel));
  const costoCrit = critArr.reduce((s, r) => s + r.c.total, 0);
  const costoTodos = elevArr.reduce((s, r) => s + r.c.total, 0);
  const costoProm = elevArr.length ? costoTodos / elevArr.length : 0;

  const byZone = Z.map((z) => {
    const reps = enriched.filter((r) => r.grupo === z.grupo && ["critico", "alto"].includes(r.nivel));
    return { grupo: z.grupo, total: reps.reduce((s, r) => s + r.c.total, 0), n: reps.length, scoreMax: Math.max(0, ...reps.map((r) => r.score)) };
  }).filter((z) => z.total > 0).sort((a, b) => b.total - a.total);
  const maxZone = Math.max(...byZone.map((z) => z.total), 1);

  return (
    <div>
      <V2Banner emoji="💰" tone="red"
        title={`${fmtPesos(costoTodos)} en juego si no se actúa`}
        sub={`Exposición de los ${elevArr.length} vendedores en riesgo elevado. Cada baja cuesta en promedio ${fmtPesos(costoProm)} entre reemplazo y pérdida de cartera.`}
        cta="Ver dónde priorizar →" />

      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <HeroStat label="Exposición nivel crítico" value={fmtPesos(costoCrit)} accent="var(--red-accent)" valueColor="var(--red-accent)">
          <div style={{ fontSize: 12, color: "var(--ink-500)" }}>{critArr.length} vendedores en riesgo inmediato de baja</div>
        </HeroStat>
        <V2Card style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14, color: "var(--ink-900)", marginBottom: 14 }}>📊 Dónde está la exposición</div>
          {byZone.map((z) => (
            <div key={z.grupo} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <span style={{ width: 64, fontSize: 12, fontWeight: 600, color: "var(--ink-700)", textAlign: "right" }}>{z.grupo}</span>
              <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ height: 20, borderRadius: 4, width: `${(z.total / maxZone) * 100}%`, minWidth: 4, background: z.scoreMax >= 8 ? "var(--red-accent)" : "var(--orange-accent)" }} />
                <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-700)", whiteSpace: "nowrap" }}>{fmtPesos(z.total)} <span style={{ color: "var(--ink-400)", fontWeight: 400 }}>· {z.n}</span></span>
              </div>
            </div>
          ))}
        </V2Card>
      </div>
      <StatStrip>
        <StatItem value={fmtPesos(costoTodos)} label="Exposición total (crítico + alto)" />
        <StatItem value={fmtPesos(costoProm)} label="Costo promedio por baja" />
        <StatItem value={elevArr.length} label="Vendedores en riesgo" />
        <StatItem value={byZone[0] ? byZone[0].grupo : "—"} label="Zona de mayor exposición" />
      </StatStrip>

      <V2Section title="🧾 Detalle por vendedor"
        right={
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "var(--ink-400)" }}>Nivel:</span>
            {["critico", "alto", "medio", "bajo"].map((n) => (
              <button key={n} onClick={() => toggle(n)} style={{ fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: 12, padding: "4px 11px", borderRadius: 7, cursor: "pointer", border: "1px solid", borderColor: niveles.includes(n) ? "var(--blue-accent)" : "var(--line-strong)", background: niveles.includes(n) ? "var(--blue-bg)" : "#fff", color: niveles.includes(n) ? "var(--blue-text)" : "var(--ink-400)" }}>{NIVEL_LABEL[n]}</button>
            ))}
          </div>
        } />
      {fil.length === 0
        ? <V2Empty emoji="🔍" title="Ningún vendedor en los niveles elegidos" sub="Activá al menos un nivel arriba para ver el detalle." />
        : (
          <V2Card pad={false} style={{ overflow: "hidden", padding: "8px 8px 0" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr>{["Vendedor", "Tipo", "Zona", "Antigüedad", "Score", "Reemplazo", "Pérd. cartera", "Costo total"].map((h) => <th key={h} style={v2th}>{h}</th>)}</tr></thead>
              <tbody>
                {fil.sort((a, b) => b.c.total - a.c.total).map((r) => (
                  <tr key={r.id} className="vrow">
                    <td style={v2td}><b>{r.nombre}</b> <span style={{ color: "var(--ink-400)", fontSize: 11 }}>({r.id})</span></td>
                    <td style={v2td}>{r.tipo}</td>
                    <td style={v2td}>{r.grupo}</td>
                    <td style={v2td}>{fmtAntiguedad(r.meses)}</td>
                    <td style={v2td}><Badge nivel={r.nivel} label={String(r.score)} /></td>
                    <td style={v2td}>{fmtPesos(r.c.reemplazo)}</td>
                    <td style={v2td}>{fmtPesos(r.c.perdida)}</td>
                    <td style={{ ...v2td, fontWeight: 800, color: "var(--ink-900)" }}>{fmtPesos(r.c.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </V2Card>
        )}
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 10 }}>Salarios según estructura Würth Argentina 2025 · datos simulados.</div>
    </div>
  );
}

Object.assign(window, { CostV2 });
