/* Intervenciones — v2. Leads with effectiveness (does intervening work?),
   foregrounds which types move the score, keeps the form but tightens it. */

function ImpactCellV2({ imp, estado }) {
  if (estado === "Baja") return <span style={{ color: "var(--ink-400)", fontSize: 13 }}>— dio de baja</span>;
  if (imp == null) return <span style={{ color: "var(--ink-400)", fontSize: 13 }}>— sin medir</span>;
  if (imp > 0.4) return <span style={{ color: "var(--green-text)", fontWeight: 700, fontSize: 14 }}>↓ {imp.toFixed(1)} mejoró</span>;
  if (imp < -0.4) return <span style={{ color: "var(--red-text)", fontWeight: 700, fontSize: 14 }}>↑ {Math.abs(imp).toFixed(1)} empeoró</span>;
  return <span style={{ color: "var(--ink-400)", fontSize: 13 }}>= sin cambio</span>;
}

function InterventionsV2({ data }) {
  const { V, INTERV, TIPOS_INTERV } = data;
  const enRiesgo = V.filter((r) => ["critico", "alto"].includes(r.nivel)).sort((a, b) => b.score - a.score);
  const sups = [...new Set(V.map((r) => r.supervisor))].sort();

  const [rows, setRows] = React.useState(INTERV);
  const [vid, setVid] = React.useState(enRiesgo[0].id);
  const [tipo, setTipo] = React.useState(TIPOS_INTERV[0]);
  const [sup, setSup] = React.useState(enRiesgo[0].supervisor);
  const [obs, setObs] = React.useState("");
  const [flash, setFlash] = React.useState(null);
  const [openForm, setOpenForm] = React.useState(false);

  const submit = (e) => {
    e.preventDefault();
    const v = V.find((r) => r.id === Number(vid));
    setRows([{ fecha: "2025-01-24", id: v.id, tipoV: v.tipo, grupo: v.grupo, tipo, sup, si: v.score, sa: v.score, nivelI: v.nivel, nivelA: v.nivel, estado: "activo", obs: obs || "—", _new: true }, ...rows]);
    setObs(""); setFlash(`✓ Intervención registrada para ID ${v.id} — ${tipo}`);
    setTimeout(() => setFlash(null), 3200); setOpenForm(false);
  };

  const withImp = rows.map((r) => ({ ...r, imp: r.sa == null ? null : r.si - r.sa }));
  const total = rows.length;
  const medidas = withImp.filter((r) => r.imp != null && r.estado !== "Baja");
  const mejoraron = medidas.filter((r) => r.imp > 0.4).length;
  const tasa = medidas.length ? Math.round((mejoraron / medidas.length) * 100) : 0;
  const bajas = rows.filter((r) => r.estado === "Baja").length;

  // efectividad por tipo
  const porTipo = {};
  withImp.forEach((r) => {
    if (r.imp == null || r.estado === "Baja") return;
    (porTipo[r.tipo] ||= []).push(r.imp);
  });
  const efTipo = Object.entries(porTipo).map(([t, arr]) => ({ t, avg: arr.reduce((s, x) => s + x, 0) / arr.length, n: arr.length }))
    .sort((a, b) => b.avg - a.avg);
  const maxAbs = Math.max(0.1, ...efTipo.map((e) => Math.abs(e.avg)));

  const inputStyle = { width: "100%", padding: "9px 11px", borderRadius: 8, border: "1px solid var(--line-strong)", fontFamily: "var(--font-sans)", fontSize: 13, color: "var(--ink-900)", background: "#fff", outline: "none", boxSizing: "border-box" };
  const Field = ({ label, children }) => <label style={{ display: "block", marginBottom: 14 }}><div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13, color: "var(--ink-700)", marginBottom: 5 }}>{label}</div>{children}</label>;

  return (
    <div>
      <V2Banner emoji="📝" tone="blue"
        title="Intervenir funciona — el score baja en la mayoría de los casos"
        sub={`${mejoraron} de ${medidas.length} intervenciones medidas mejoraron el riesgo del vendedor.`}
        cta={openForm ? "Cerrar formulario" : "➕ Registrar intervención"}
        onCta={() => setOpenForm((o) => !o)} />

      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <HeroStat label="Tasa de efectividad" value={`${tasa}%`} accent="var(--green-accent)" valueColor="var(--green-text)">
          <div style={{ fontSize: 12, color: "var(--ink-500)" }}>{mejoraron} de {medidas.length} intervenciones bajaron el score ≥ 0,5</div>
        </HeroStat>
        <V2Card style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14, color: "var(--ink-900)", marginBottom: 14 }}>¿Qué tipo de intervención mueve más el score?</div>
          {efTipo.map((e) => (
            <div key={e.t} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
              <span style={{ width: 150, fontSize: 12, color: "var(--ink-600)", textAlign: "right", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{e.t}</span>
              <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ height: 18, borderRadius: 4, width: `${(Math.abs(e.avg) / maxAbs) * 100}%`, minWidth: 4, background: e.avg > 0 ? "var(--green-accent)" : "var(--red-accent)" }} />
                <span style={{ fontSize: 12, fontWeight: 700, color: e.avg > 0 ? "var(--green-text)" : "var(--red-text)", whiteSpace: "nowrap" }}>{e.avg > 0 ? "↓" : "↑"} {Math.abs(e.avg).toFixed(1)}</span>
              </div>
            </div>
          ))}
        </V2Card>
      </div>
      <StatStrip>
        <StatItem value={total} label="Intervenciones registradas" />
        <StatItem value={mejoraron} label="Con mejora de score" />
        <StatItem value={medidas.length - mejoraron} label="Sin mejora aún" />
        <StatItem value={bajas} label="Vendedor dio de baja" />
      </StatStrip>

      {flash && <div style={{ marginBottom: 18, padding: "11px 16px", borderRadius: 8, background: "var(--green-bg)", color: "var(--green-text)", fontSize: 13, fontWeight: 600 }}>{flash}</div>}

      {openForm && (
        <V2Card style={{ marginBottom: 28 }}>
          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 15, color: "var(--ink-900)", marginBottom: 16 }}>➕ Registrar nueva intervención</div>
          <form onSubmit={submit}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
              <div>
                <Field label="Vendedor en riesgo"><select value={vid} onChange={(e) => { setVid(e.target.value); const v = V.find((r) => r.id === Number(e.target.value)); if (v) setSup(v.supervisor); }} style={inputStyle}>{enRiesgo.map((r) => <option key={r.id} value={r.id}>ID {r.id} — {r.grupo} — Score {r.score} ({r.nivel.toUpperCase()})</option>)}</select></Field>
                <Field label="Tipo de intervención"><select value={tipo} onChange={(e) => setTipo(e.target.value)} style={inputStyle}>{TIPOS_INTERV.map((t) => <option key={t}>{t}</option>)}</select></Field>
              </div>
              <div>
                <Field label="Supervisor que intervino"><select value={sup} onChange={(e) => setSup(e.target.value)} style={inputStyle}>{sups.map((s) => <option key={s}>{s}</option>)}</select></Field>
                <Field label="Observaciones"><textarea value={obs} onChange={(e) => setObs(e.target.value)} placeholder="¿Qué se habló? ¿Qué se acordó?" style={{ ...inputStyle, height: 64, resize: "vertical" }} /></Field>
              </div>
            </div>
            <button type="submit" style={{ width: "100%", marginTop: 4, padding: "11px 0", borderRadius: 8, cursor: "pointer", border: "none", background: "var(--red-accent)", color: "#fff", fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14 }}>💾 Guardar intervención</button>
          </form>
        </V2Card>
      )}

      <V2Section title="📊 Historial de intervenciones e impacto" right={<span style={{ fontSize: 12, color: "var(--ink-400)" }}>Impacto = score inicial − actual</span>} />
      <V2Card pad={false} style={{ overflow: "hidden", padding: "8px 8px 0" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr>{["Fecha", "Vendedor", "Tipo", "Supervisor", "Inicial", "Actual", "Impacto", "Observaciones"].map((h) => <th key={h} style={v2th}>{h}</th>)}</tr></thead>
          <tbody>
            {withImp.map((r, i) => (
              <tr key={i} className="vrow" style={{ background: r._new ? "var(--green-bg)" : "transparent" }}>
                <td style={{ ...v2td, color: "var(--ink-250)", fontSize: 12 }}>{r.fecha}</td>
                <td style={v2td}><div style={{ fontWeight: 700 }}>ID {r.id}</div><div style={{ color: "var(--ink-250)", fontSize: 11 }}>{r.tipoV} · {r.grupo}</div></td>
                <td style={v2td}><Badge kind="tipo" label={r.tipo} /></td>
                <td style={v2td}>{r.sup}</td>
                <td style={{ ...v2td, textAlign: "center" }}><ScoreCircle score={r.si} nivel={r.nivelI} size={32} /></td>
                <td style={{ ...v2td, textAlign: "center" }}>{r.sa != null ? <ScoreCircle score={r.sa} nivel={r.nivelA} size={32} /> : <Badge kind="bajo" label="Baja" />}</td>
                <td style={v2td}><ImpactCellV2 imp={r.imp} estado={r.estado} /></td>
                <td style={{ ...v2td, color: "var(--ink-400)", fontSize: 12, maxWidth: 220 }}>{r.obs}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </V2Card>
    </div>
  );
}

Object.assign(window, { InterventionsV2 });
