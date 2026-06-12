/* Inicio — the main board. KPI row, filter, vendedor table, zones + critical
   window chart, onboarding tracker. */

function FilterRadio({ value, onChange, options }) {
  return (
    <div style={{ display: "flex", gap: 8, marginBottom: 14, flexWrap: "wrap" }}>
      {options.map((o) => (
        <button key={o} onClick={() => onChange(o)} style={{
          font: "var(--w-semibold) 13px var(--font-sans)", padding: "5px 14px",
          borderRadius: 8, cursor: "pointer", border: "1px solid",
          borderColor: value === o ? "var(--blue-accent)" : "var(--line-strong)",
          background: value === o ? "var(--blue-bg)" : "#fff",
          color: value === o ? "var(--blue-text)" : "var(--ink-600)",
        }}>{o}</button>
      ))}
    </div>
  );
}

function SearchInput({ value, onChange, placeholder }) {
  return (
    <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      style={{
        width: "100%", padding: "9px 12px", borderRadius: 8, border: "1px solid var(--line-strong)",
        font: "var(--w-regular) 13px var(--font-sans)", color: "var(--ink-900)",
        background: "#fff", outline: "none", boxSizing: "border-box",
      }} />
  );
}

function VendedorRow({ r, onOpen }) {
  const zN = zonaNivel(r.rb), zL = zonaLabel(r.rb);
  return (
    <tr onClick={() => onOpen && onOpen(r)} style={{ cursor: onOpen ? "pointer" : "default" }} className="vrow">
      <td style={cellStyle}>
        <div style={{ fontWeight: 700, color: "var(--ink-900)", fontSize: 13 }}>
          {r.nombre} <span style={{ color: "var(--ink-400)", fontWeight: 400, fontSize: 11 }}>({r.id})</span>
        </div>
        <div style={{ color: "var(--ink-250)", fontSize: 11, marginTop: 2 }}>{r.tipo} · {fmtAntiguedad(r.meses)}</div>
      </td>
      <td style={cellStyle}><Pills senales={r.senales} /></td>
      <td style={cellStyle}><b>{r.plan3m}%</b></td>
      <td style={cellStyle}><Sparkline vals={r.spark} /></td>
      <td style={cellStyle}>
        <div style={{ fontWeight: 600, fontSize: 13 }}>{r.grupo}</div>
        <div style={{ marginTop: 3 }}><Badge nivel={zN} label={zL} /></div>
      </td>
      <td style={cellStyle}><ScoreCircle score={r.score} nivel={r.nivel} /></td>
    </tr>
  );
}

const cellStyle = { padding: "11px 12px", borderBottom: "1px solid var(--line-faint)", verticalAlign: "middle", fontSize: 13 };
const thStyle = { background: "var(--table-head-bg)", padding: "10px 12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "var(--ink-500)", borderBottom: "2px solid var(--line-strong)" };

function VendedorTable({ rows, onOpen }) {
  return (
    <Card pad={false} style={{ overflow: "hidden" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr>
          {["Vendedor", "Señales detectadas", "% Plan 3m", "Tendencia ⓘ", "Zona ⓘ", "Score ⓘ"].map((h) =>
            <th key={h} style={thStyle}>{h}</th>)}
        </tr></thead>
        <tbody>{rows.map((r) => <VendedorRow key={r.id} r={r} onOpen={onOpen} />)}</tbody>
      </table>
    </Card>
  );
}

function CriticalWindowChart({ data }) {
  const max = Math.max(...data.map((d) => d.n));
  const colorMes = (m) => m <= 3 ? "var(--red-accent)" : m <= 6 ? "var(--orange-accent)" : m <= 12 ? "var(--chart-neutral)" : "var(--green-soft)";
  return (
    <Card>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height: 200, paddingTop: 10 }}>
        {data.map((d) => (
          <div key={d.m} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4, height: "100%", justifyContent: "flex-end" }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-500)" }}>{d.n}</div>
            <div style={{ width: "100%", maxWidth: 26, height: `${(d.n / max) * 150}px`, background: colorMes(d.m), borderRadius: "2px 2px 0 0" }} />
            <div style={{ fontSize: 10, color: "var(--ink-400)" }}>M{d.m}</div>
          </div>
        ))}
      </div>
      <div style={{ fontSize: 11, color: "var(--ink-400)", marginTop: 10, lineHeight: 1.5 }}>
        🔴 Mes 1-3 (inducción) · 🟠 Mes 4-6 (adaptación) · ⬜ Mes 7-12. Más de la mitad de las renuncias ocurren antes del mes 7.
      </div>
    </Card>
  );
}

function ZonesPanel({ zones }) {
  const sorted = [...zones].sort((a, b) => b.rb - a.rb);
  return (
    <Card pad={false} style={{ padding: "4px 20px" }}>
      {sorted.map((g, i) => {
        const nivel = zonaNivel(g.rb);
        return (
          <div key={g.grupo} style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            padding: "13px 0", borderBottom: i < sorted.length - 1 ? "1px solid var(--line-faint)" : "none",
          }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: "var(--ink-900)" }}>{g.grupo} · {g.supervisor}</div>
              <div style={{ fontSize: 11, color: "var(--ink-250)", marginTop: 2 }}>
                {g.historicos} vendedores históricos · duración prom. al egreso: {g.permEgreso.toFixed(1).replace(".", ",")}m
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
              <div style={{ fontWeight: 700, fontSize: 13 }}>{g.planProm}% plan</div>
              <Badge nivel={nivel} />
            </div>
          </div>
        );
      })}
    </Card>
  );
}

function InicioView({ data, onOpenVendedor }) {
  const { V, Z, VENTANAS } = data;
  const [filtro, setFiltro] = React.useState("Todos");
  const [busq, setBusq] = React.useState("");

  let df = [...V].sort((a, b) => b.score - a.score);
  if (filtro === "Crítico") df = df.filter((r) => r.nivel === "critico");
  else if (filtro === "Alto") df = df.filter((r) => r.nivel === "alto");
  else if (filtro === "Viajantes") df = df.filter((r) => r.tipo === "Viajante");
  else if (filtro === "Televentas") df = df.filter((r) => r.tipo === "Televentas");
  if (busq) df = df.filter((r) => r.nombre.toLowerCase().includes(busq.toLowerCase()) || String(r.id).includes(busq));

  const total = V.length;
  const enRiesgo = V.filter((r) => ["critico", "alto"].includes(r.nivel)).length;
  const permProm = (V.reduce((s, r) => s + r.meses, 0) / V.length);
  const obCritico = V.filter((r) => r.meses <= 6 && ["critico", "alto"].includes(r.nivel)).length;
  const onb = [...V].filter((r) => r.meses <= 6).sort((a, b) => b.score - a.score);

  return (
    <div>
      <div style={{ display: "flex", gap: 14, marginBottom: 28 }}>
        <KpiCard value={total} label="Vendedores activos" sub="Actualizando mensualmente" />
        <KpiCard value={enRiesgo} valueColor="var(--red-accent)" accent="red" label="En riesgo elevado" sub="Score ≥ 6 (alto o crítico)" />
        <KpiCard value={"5,2 m"} accent="orange" label="Permanencia al egreso" sub="Solo últimos 12 meses" />
        <KpiCard value={obCritico} valueColor="var(--blue-accent)" accent="blue" label="Onboarding en riesgo" sub="Score ≥ 6 en sus primeros 6 meses" />
        <KpiCard value={4} label="Supervisores activos" sub="3.5 vendedores/supervisor" />
      </div>

      <SectionHeader>📋 Vendedores por score de riesgo de fuga</SectionHeader>
      <FilterRadio value={filtro} onChange={setFiltro} options={["Todos", "Crítico", "Alto", "Viajantes", "Televentas"]} />
      <div style={{ maxWidth: 360, marginBottom: 12 }}>
        <SearchInput value={busq} onChange={setBusq} placeholder="🔍 Buscar por nombre o número de vendedor..." />
      </div>
      <VendedorTable rows={df} onOpen={onOpenVendedor} />
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 8 }}>{df.length} vendedores · clic en una fila para ver el detalle.</div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr", gap: 28, marginTop: 32, alignItems: "start" }}>
        <div>
          <SectionHeader>📍 Zonas con mayor rotación histórica</SectionHeader>
          <ZonesPanel zones={Z} />
        </div>
        <div>
          <SectionHeader>⏱️ Ventanas críticas de permanencia</SectionHeader>
          <CriticalWindowChart data={VENTANAS} />
        </div>
      </div>

      <div style={{ marginTop: 32 }}>
        <SectionHeader note={`${onb.length} vendedores en sus primeros 6 meses`}>👥 Onboarding activo — meses 1 a 6</SectionHeader>
        <Card pad={false} style={{ overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead><tr>
              {["Vendedor", "Tipo", "Mes en empresa", "Zona asignada", "% Plan 3m", "Riesgo"].map((h) => <th key={h} style={thStyle}>{h}</th>)}
            </tr></thead>
            <tbody>
              {onb.map((r) => {
                const zN = zonaNivel(r.rb), zL = zonaLabel(r.rb);
                const warn = (zN === "critico" || zN === "alto") ? " ⚠️" : "";
                return (
                  <tr key={r.id} className="vrow">
                    <td style={cellStyle}><b>{r.nombre}</b> <span style={{ color: "var(--ink-400)", fontSize: 11 }}>({r.id})</span></td>
                    <td style={cellStyle}>{r.tipo}</td>
                    <td style={cellStyle}>{fmtAntiguedad(r.meses)}</td>
                    <td style={cellStyle}>{r.grupo} <Badge nivel={zN} label={zL + warn} /></td>
                    <td style={cellStyle}><b>{r.plan3m}%</b></td>
                    <td style={cellStyle}><Badge nivel={r.nivel} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
}

Object.assign(window, { InicioView, VendedorTable, thStyle, cellStyle });
