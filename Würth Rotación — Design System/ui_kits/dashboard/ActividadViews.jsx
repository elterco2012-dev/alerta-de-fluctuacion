/* Actividad comercial — Televentas (llamadas) + Viajantes (visitas) vs plan.
   actual = faithful conditional-format table; v2 = leads with cumplimiento,
   splits the two channels, ranks reps, ties low activity back to risk. */

function cumplColor(v) {
  if (v >= 90) return ["var(--green-pos-bg)", "var(--green-pos-tx)"];
  if (v >= 70) return ["var(--cell-warn-bg)", "var(--cell-warn-tx)"];
  return ["var(--cell-bad-bg)", "var(--cell-bad-tx)"];
}

function ActividadV2({ data, onOpenVendedor }) {
  const A = data.ACTIVIDAD;
  const tel = A.filter((a) => a.tipo === "Televentas");
  const via = A.filter((a) => a.tipo === "Viajante");
  const [canal, setCanal] = React.useState("Televentas");
  const rows = (canal === "Televentas" ? tel : via).slice().sort((a, b) => a.cumpl - b.cumpl);

  const avg = (arr) => Math.round(arr.reduce((s, a) => s + a.cumpl, 0) / arr.length);
  const bajoPlan = A.filter((a) => a.cumpl < 70);
  const unidad = canal === "Televentas" ? "llamadas/día" : "visitas/semana";
  const verbo = canal === "Televentas" ? "llamó" : "visitó";

  return (
    <div>
      <V2Banner emoji={bajoPlan.length ? "⚠️" : "📞"} tone={bajoPlan.length > 2 ? "orange" : "blue"}
        title={`${bajoPlan.length} vendedores están por debajo del 70% del plan de actividad`}
        sub="La baja actividad suele anticipar la caída de plan. Revisalos antes de que el score escale." />

      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <HeroStat label={`Cumplimiento ${canal}`} value={`${avg(canal === "Televentas" ? tel : via)}%`}
          accent={avg(canal === "Televentas" ? tel : via) >= 80 ? "var(--green-accent)" : "var(--orange-accent)"}
          valueColor={avg(canal === "Televentas" ? tel : via) >= 80 ? "var(--green-text)" : "var(--orange-text)"}>
          <div style={{ fontSize: 12, color: "var(--ink-500)" }}>Promedio del canal vs. plan de {unidad}</div>
        </HeroStat>
        <V2Card style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", gap: 16 }}>
          <div style={{ display: "flex", gap: 10 }}>
            {[["Televentas", "📞", tel], ["Viajante", "🚗", via]].map(([k, ico, arr]) => (
              <button key={k} onClick={() => setCanal(k)} style={{
                flex: 1, textAlign: "left", padding: "14px 16px", borderRadius: 10, cursor: "pointer",
                border: "1px solid", borderColor: canal === k ? "var(--blue-accent)" : "var(--line-strong)",
                background: canal === k ? "var(--blue-bg)" : "#fff",
              }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "var(--ink-700)" }}>{ico} {k === "Viajante" ? "Viajantes" : k}</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginTop: 4 }}>
                  <span style={{ fontWeight: 800, fontSize: 26, color: avg(arr) >= 80 ? "var(--green-text)" : "var(--orange-text)" }}>{avg(arr)}%</span>
                  <span style={{ fontSize: 11, color: "var(--ink-400)" }}>{arr.length} reps</span>
                </div>
              </button>
            ))}
          </div>
          <div style={{ fontSize: 12, color: "var(--ink-400)", lineHeight: 1.5 }}>Elegí un canal para ver el ranking de actividad. Los de menor cumplimiento aparecen primero.</div>
        </V2Card>
      </div>
      <StatStrip>
        <StatItem value={A.length} label="Vendedores con actividad" />
        <StatItem value={`${avg(A)}%`} label="Cumplimiento general" />
        <StatItem value={bajoPlan.length} label="Por debajo del 70%" />
        <StatItem value={A.filter((a) => a.clientesL === 0).length} label="Sin altas de clientes" />
      </StatStrip>

      <V2Section title={`${canal === "Televentas" ? "📞" : "🚗"} Ranking de actividad — ${canal === "Viajante" ? "Viajantes" : canal}`} right={<span style={{ fontSize: 12, color: "var(--ink-400)" }}>Ordenado por menor cumplimiento</span>} />
      <V2Card pad={false} style={{ overflow: "hidden", padding: "8px 8px 0" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr>
            <th style={v2th}>Vendedor</th><th style={v2th}>Plan</th><th style={v2th}>Real</th>
            <th style={v2th}>Cumplimiento</th><th style={v2th}>Contactos efectivos</th><th style={v2th}>Riesgo</th>
          </tr></thead>
          <tbody>
            {rows.map((a) => {
              const [bg, tx] = cumplColor(a.cumpl);
              return (
                <tr key={a.id} className="vrow">
                  <td style={v2td}><b>{a.nombre}</b> <span style={{ color: "var(--ink-400)", fontSize: 11 }}>({a.id})</span><div style={{ color: "var(--ink-250)", fontSize: 11 }}>{a.grupo}</div></td>
                  <td style={v2td}>{a.plan} <span style={{ color: "var(--ink-400)", fontSize: 11 }}>{unidad.split("/")[1] ? "/" + unidad.split("/")[1] : ""}</span></td>
                  <td style={v2td}><b>{a.real}</b></td>
                  <td style={v2td}><span style={{ display: "inline-block", minWidth: 52, textAlign: "center", padding: "4px 0", borderRadius: 6, background: bg, color: tx, fontWeight: 700, fontSize: 12 }}>{a.cumpl}%</span></td>
                  <td style={v2td}>{a.contactos}</td>
                  <td style={v2td}><Badge nivel={a.nivel} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </V2Card>
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 10 }}>{verbo.charAt(0).toUpperCase() + verbo.slice(1)}: real vs. plan de {unidad}. Datos simulados.</div>
    </div>
  );
}

function ActividadActual({ data }) {
  const A = data.ACTIVIDAD.slice().sort((a, b) => a.cumpl - b.cumpl);
  return (
    <div>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 22, color: "var(--ink-900)", marginBottom: 4 }}>📞 Actividad comercial</div>
      <div style={{ fontSize: 14, color: "var(--ink-400)", marginBottom: 22 }}>Televentas (llamadas) y Viajantes (visitas): target vs. ejecutado.</div>
      <Card pad={false} style={{ overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr>
            {["Vendedor", "Tipo", "Zona", "Plan", "Real", "Cumplimiento", "Contactos"].map((h) =>
              <th key={h} style={{ background: "var(--table-head-bg)", padding: "10px 12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "var(--ink-500)", borderBottom: "2px solid var(--line-strong)" }}>{h}</th>)}
          </tr></thead>
          <tbody>
            {A.map((a) => {
              const [bg, tx] = cumplColor(a.cumpl);
              return (
                <tr key={a.id}>
                  <td style={{ padding: "11px 12px", borderBottom: "1px solid var(--line-faint)", fontSize: 13, fontWeight: 700 }}>{a.nombre}</td>
                  <td style={{ padding: "11px 12px", borderBottom: "1px solid var(--line-faint)", fontSize: 13 }}>{a.tipo}</td>
                  <td style={{ padding: "11px 12px", borderBottom: "1px solid var(--line-faint)", fontSize: 13 }}>{a.grupo}</td>
                  <td style={{ padding: "11px 12px", borderBottom: "1px solid var(--line-faint)", fontSize: 13 }}>{a.plan}</td>
                  <td style={{ padding: "11px 12px", borderBottom: "1px solid var(--line-faint)", fontSize: 13 }}>{a.real}</td>
                  <td style={{ padding: "8px 12px", borderBottom: "1px solid var(--line-faint)", fontSize: 13 }}><span style={{ display: "inline-block", padding: "3px 10px", borderRadius: 4, background: bg, color: tx, fontWeight: 600 }}>{a.cumpl}%</span></td>
                  <td style={{ padding: "11px 12px", borderBottom: "1px solid var(--line-faint)", fontSize: 13 }}>{a.contactos}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

Object.assign(window, { ActividadV2, ActividadActual });
