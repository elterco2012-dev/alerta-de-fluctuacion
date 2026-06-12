/* Intervenciones — register an action on an at-risk rep, see impact history. */

function Field({ label, children }) {
  return (
    <label style={{ display: "block", marginBottom: 14 }}>
      <div style={{ font: "var(--w-bold) 13px var(--font-sans)", color: "var(--ink-700)", marginBottom: 5 }}>{label}</div>
      {children}
    </label>
  );
}
const inputStyle = {
  width: "100%", padding: "9px 11px", borderRadius: 8, border: "1px solid var(--line-strong)",
  font: "var(--w-regular) 13px var(--font-sans)", color: "var(--ink-900)", background: "#fff",
  outline: "none", boxSizing: "border-box",
};

function ImpactCell({ imp, estado }) {
  if (estado === "Baja") return <span style={{ color: "var(--ink-400)", fontSize: 13 }}>— Baja</span>;
  if (imp == null) return <span style={{ color: "var(--ink-400)", fontSize: 13 }}>—</span>;
  if (imp > 0.4) return <span style={{ color: "var(--green-text)", fontWeight: 700, fontSize: 14 }}>↓ {imp.toFixed(1)} mejora</span>;
  if (imp < -0.4) return <span style={{ color: "var(--red-text)", fontWeight: 700, fontSize: 14 }}>↑ {Math.abs(imp).toFixed(1)} empeora</span>;
  return <span style={{ color: "var(--ink-400)", fontSize: 13 }}>= sin cambio</span>;
}

function InterventionsView({ data }) {
  const { V, INTERV, TIPOS_INTERV } = data;
  const enRiesgo = V.filter((r) => ["critico", "alto"].includes(r.nivel)).sort((a, b) => b.score - a.score);
  const sups = [...new Set(V.map((r) => r.supervisor))].sort();

  const [rows, setRows] = React.useState(INTERV);
  const [vid, setVid] = React.useState(enRiesgo[0].id);
  const [tipo, setTipo] = React.useState(TIPOS_INTERV[0]);
  const [sup, setSup] = React.useState(enRiesgo[0].supervisor);
  const [obs, setObs] = React.useState("");
  const [flash, setFlash] = React.useState(null);

  const submit = (e) => {
    e.preventDefault();
    const v = V.find((r) => r.id === Number(vid));
    setRows([{ fecha: "2025-01-24", id: v.id, tipoV: v.tipo, grupo: v.grupo, tipo, sup, si: v.score, sa: v.score, nivelI: v.nivel, nivelA: v.nivel, estado: "activo", obs: obs || "—", _new: true }, ...rows]);
    setObs(""); setFlash(`✓ Intervención registrada para ID ${v.id} — ${tipo}`);
    setTimeout(() => setFlash(null), 3200);
  };

  const withImp = rows.map((r) => ({ ...r, imp: r.sa == null ? null : r.si - r.sa }));
  const total = rows.length;
  const mejoraron = withImp.filter((r) => (r.imp || 0) > 0.4).length;
  const empeoraron = withImp.filter((r) => (r.imp || 0) < -0.4 && r.estado !== "Baja").length;
  const bajas = rows.filter((r) => r.estado === "Baja").length;

  return (
    <div>
      <div style={{ font: "var(--w-black) 22px var(--font-sans)", color: "var(--ink-900)" }}>📝 Registro de intervenciones</div>
      <div style={{ fontSize: 14, color: "var(--ink-400)", marginTop: 4, marginBottom: 22 }}>Documentá qué acción se tomó sobre cada vendedor en riesgo y medí el impacto real.</div>

      <div style={{ display: "flex", gap: 14, marginBottom: 24 }}>
        <KpiCard value={total} label="Intervenciones registradas" />
        <KpiCard value={mejoraron} valueColor="var(--green-text)" accent="green" label="Con mejora de score" sub="Score bajó ≥ 0.5 después" />
        <KpiCard value={empeoraron} valueColor="var(--red-accent)" accent="red" label="Sin mejora" sub="Score igual o subió" />
        <KpiCard value={bajas} valueColor="var(--ink-400)" accent="blue" label="Vendedor dio de baja" sub="A pesar de la intervención" />
      </div>

      <SectionHeader>➕ Registrar nueva intervención</SectionHeader>
      <Card style={{ marginBottom: 28 }}>
        <form onSubmit={submit}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
            <div>
              <Field label="Vendedor en riesgo">
                <select value={vid} onChange={(e) => { setVid(e.target.value); const v = V.find((r) => r.id === Number(e.target.value)); if (v) setSup(v.supervisor); }} style={inputStyle}>
                  {enRiesgo.map((r) => <option key={r.id} value={r.id}>ID {r.id} — {r.grupo} — Score {r.score} ({r.nivel.toUpperCase()})</option>)}
                </select>
              </Field>
              <Field label="Tipo de intervención">
                <select value={tipo} onChange={(e) => setTipo(e.target.value)} style={inputStyle}>
                  {TIPOS_INTERV.map((t) => <option key={t}>{t}</option>)}
                </select>
              </Field>
              <Field label="Fecha"><input type="text" defaultValue="2025-01-24" style={inputStyle} /></Field>
            </div>
            <div>
              <Field label="Supervisor que intervino">
                <select value={sup} onChange={(e) => setSup(e.target.value)} style={inputStyle}>
                  {sups.map((s) => <option key={s}>{s}</option>)}
                </select>
              </Field>
              <Field label="Observaciones">
                <textarea value={obs} onChange={(e) => setObs(e.target.value)} placeholder="¿Qué se habló? ¿Qué se acordó? ¿Cómo reaccionó el vendedor?"
                  style={{ ...inputStyle, height: 92, resize: "vertical", fontFamily: "var(--font-sans)" }} />
              </Field>
            </div>
          </div>
          <button type="submit" style={{
            width: "100%", marginTop: 4, padding: "11px 0", borderRadius: 8, cursor: "pointer",
            border: "none", background: "var(--red-accent)", color: "#fff",
            font: "var(--w-bold) 14px var(--font-sans)",
          }}>💾 Guardar intervención</button>
          {flash && <div style={{ marginTop: 12, padding: "10px 14px", borderRadius: 8, background: "var(--green-bg)", color: "var(--green-text)", fontSize: 13, fontWeight: 600 }}>{flash}</div>}
        </form>
      </Card>

      <SectionHeader>📊 Historial de intervenciones e impacto</SectionHeader>
      <Card pad={false} style={{ overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr>
            {["Fecha", "Vendedor", "Tipo", "Supervisor", "Score inicial", "Score actual", "Impacto", "Observaciones"].map((h) => <th key={h} style={thStyle}>{h}</th>)}
          </tr></thead>
          <tbody>
            {withImp.map((r, i) => (
              <tr key={i} className="vrow" style={{ background: r._new ? "var(--green-bg)" : "transparent" }}>
                <td style={{ ...cellStyle, color: "var(--ink-250)", fontSize: 12 }}>{r.fecha}</td>
                <td style={cellStyle}><div style={{ fontWeight: 700 }}>ID {r.id}</div><div style={{ color: "var(--ink-250)", fontSize: 11 }}>{r.tipoV} · {r.grupo}</div></td>
                <td style={cellStyle}><Badge kind="tipo" label={r.tipo} /></td>
                <td style={cellStyle}>{r.sup}</td>
                <td style={{ ...cellStyle, textAlign: "center" }}><ScoreCircle score={r.si} nivel={r.nivelI} size={32} /></td>
                <td style={{ ...cellStyle, textAlign: "center" }}>{r.sa != null ? <ScoreCircle score={r.sa} nivel={r.nivelA} size={32} /> : <Badge kind="bajo" label="Baja" />}</td>
                <td style={cellStyle}><ImpactCell imp={r.imp} estado={r.estado} /></td>
                <td style={{ ...cellStyle, color: "var(--ink-400)", fontSize: 12, maxWidth: 220 }}>{r.obs}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 8 }}>Impacto = score inicial − score actual. Positivo = riesgo bajó = intervención efectiva.</div>
    </div>
  );
}

Object.assign(window, { InterventionsView });
