/* Costo de Rotación — estimated peso cost of each potential departure. */

const SAL_INDUCCION = 1400000, SAL_PRODUCTIVO = 1800000, SAL_TELEVENTAS = 1215298;
const MESES_NUEVO = 1.5, MESES_RAMPA = 2, PCT_COB = 0.08, PCT_RAMPA = 0.12;
const PLAN_VIAJANTE = 17000000, PLAN_TELEVENTAS = 6000000;

function costoRotacion(r) {
  const sal = r.tipo === "Televentas" ? SAL_TELEVENTAS : (r.meses <= 6 ? SAL_INDUCCION : SAL_PRODUCTIVO);
  const plan = r.tipo === "Televentas" ? PLAN_TELEVENTAS : PLAN_VIAJANTE;
  const directo = sal * 2 + SAL_INDUCCION * Math.round(MESES_NUEVO + MESES_RAMPA);
  const indirecto = plan * MESES_NUEVO * PCT_COB + plan * MESES_RAMPA * PCT_RAMPA;
  return { sal, reemplazo: SAL_INDUCCION * Math.round(MESES_NUEVO + MESES_RAMPA), perdida: indirecto, total: directo + indirecto };
}

function CostView({ data }) {
  const { V, Z } = data;
  const [niveles, setNiveles] = React.useState(["critico", "alto"]);

  const enriched = V.map((r) => ({ ...r, c: costoRotacion(r) }));
  const toggle = (n) => setNiveles((p) => p.includes(n) ? p.filter((x) => x !== n) : [...p, n]);
  const fil = enriched.filter((r) => niveles.includes(r.nivel));

  const costoCrit = enriched.filter((r) => r.nivel === "critico").reduce((s, r) => s + r.c.total, 0);
  const costoTodos = enriched.filter((r) => ["critico", "alto"].includes(r.nivel)).reduce((s, r) => s + r.c.total, 0);
  const nElevado = enriched.filter((r) => ["critico", "alto"].includes(r.nivel));
  const costoProm = nElevado.length ? costoTodos / nElevado.length : 0;
  const nCrit = enriched.filter((r) => r.nivel === "critico").length;

  // exposure by zone
  const byZone = Z.map((z) => {
    const reps = enriched.filter((r) => r.grupo === z.grupo && ["critico", "alto"].includes(r.nivel));
    return { grupo: z.grupo, total: reps.reduce((s, r) => s + r.c.total, 0), scoreMax: Math.max(0, ...reps.map((r) => r.score)) };
  }).filter((z) => z.total > 0).sort((a, b) => a.total - b.total);
  const maxZone = Math.max(...byZone.map((z) => z.total), 1);

  return (
    <div>
      <div style={{ font: "var(--w-black) 22px var(--font-sans)", color: "var(--ink-900)", marginBottom: 18 }}>💰 Costo de Rotación</div>

      <div style={{ display: "flex", gap: 14, marginBottom: 28 }}>
        <KpiCard value={fmtPesos(costoCrit)} accent="red" label="Exposición nivel crítico" sub={`${nCrit} vendedores en riesgo inmediato`} />
        <KpiCard value={fmtPesos(costoTodos)} accent="orange" label="Exposición total (crítico + alto)" sub={`${nElevado.length} en riesgo elevado`} />
        <KpiCard value={fmtPesos(costoProm)} accent="blue" label="Costo promedio por baja" sub="Directo + pérdida de cartera" />
        <KpiCard value={fmtPesos(fil.reduce((s, r) => s + r.c.total, 0))} accent="green" label="Vendedores en vista" sub={`${fil.length} con los filtros actuales`} />
      </div>

      <SectionHeader>📊 Exposición por zona</SectionHeader>
      <Card style={{ marginBottom: 28 }}>
        {byZone.map((z) => (
          <div key={z.grupo} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
            <div style={{ width: 70, fontSize: 13, fontWeight: 600, color: "var(--ink-700)", textAlign: "right" }}>{z.grupo}</div>
            <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ height: 22, borderRadius: 4, width: `${(z.total / maxZone) * 100}%`, minWidth: 4, background: z.scoreMax >= 8 ? "var(--red-accent)" : "var(--orange-accent)" }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-700)", whiteSpace: "nowrap" }}>{fmtPesos(z.total)}</span>
            </div>
          </div>
        ))}
      </Card>

      <SectionHeader>🧾 Detalle por vendedor</SectionHeader>
      <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
        <span style={{ fontSize: 12, color: "var(--ink-400)", marginRight: 4 }}>Nivel:</span>
        {["critico", "alto", "medio", "bajo"].map((n) => (
          <button key={n} onClick={() => toggle(n)} style={{
            font: "var(--w-semibold) 12px var(--font-sans)", padding: "4px 11px", borderRadius: 7, cursor: "pointer",
            border: "1px solid", borderColor: niveles.includes(n) ? "var(--blue-accent)" : "var(--line-strong)",
            background: niveles.includes(n) ? "var(--blue-bg)" : "#fff",
            color: niveles.includes(n) ? "var(--blue-text)" : "var(--ink-400)",
          }}>{NIVEL_LABEL[n]}</button>
        ))}
      </div>
      <Card pad={false} style={{ overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr>
            {["Vendedor", "Tipo", "Zona", "Antigüedad", "Score", "Salario/mes", "Reemplazo", "Pérd. cartera", "Costo total"].map((h) => <th key={h} style={thStyle}>{h}</th>)}
          </tr></thead>
          <tbody>
            {fil.sort((a, b) => b.c.total - a.c.total).map((r) => (
              <tr key={r.id} className="vrow">
                <td style={cellStyle}><b>{r.nombre}</b> <span style={{ color: "var(--ink-400)", fontSize: 11 }}>({r.id})</span></td>
                <td style={cellStyle}>{r.tipo}</td>
                <td style={cellStyle}>{r.grupo}</td>
                <td style={cellStyle}>{fmtAntiguedad(r.meses)}</td>
                <td style={cellStyle}><Badge nivel={r.nivel} label={String(r.score)} /></td>
                <td style={cellStyle}>{fmtPesos(r.c.sal)}</td>
                <td style={cellStyle}>{fmtPesos(r.c.reemplazo)}</td>
                <td style={cellStyle}>{fmtPesos(r.c.perdida)}</td>
                <td style={{ ...cellStyle, fontWeight: 800, color: "var(--ink-900)" }}>{fmtPesos(r.c.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 8 }}>Salarios según estructura Würth Argentina 2025 · modelo de cobertura televentas. Datos simulados.</div>
    </div>
  );
}

function VendedorModal({ r, onClose }) {
  if (!r) return null;
  const zN = zonaNivel(r.rb);
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(26,26,46,0.32)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: 460, maxWidth: "90vw", background: "#fff", borderRadius: 12, boxShadow: "0 12px 40px rgba(0,0,0,0.2)", overflow: "hidden" }}>
        <div style={{ padding: "20px 22px", borderBottom: "1px solid var(--line)", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ font: "var(--w-black) 18px var(--font-sans)", color: "var(--ink-900)" }}>{r.nombre} <span style={{ color: "var(--ink-400)", fontWeight: 400, fontSize: 13 }}>({r.id})</span></div>
            <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 3 }}>{r.tipo} · {fmtAntiguedad(r.meses)} · {r.grupo} ({r.supervisor})</div>
          </div>
          <ScoreCircle score={r.score} nivel={r.nivel} size={44} />
        </div>
        <div style={{ padding: "18px 22px" }}>
          <div style={{ display: "flex", gap: 24, marginBottom: 18 }}>
            <div><div style={{ fontSize: 11, color: "var(--ink-400)", marginBottom: 4 }}>% Plan 3m</div><div style={{ fontWeight: 800, fontSize: 22 }}>{r.plan3m}%</div></div>
            <div><div style={{ fontSize: 11, color: "var(--ink-400)", marginBottom: 4 }}>Tendencia plan</div><Sparkline vals={r.spark} /></div>
            <div><div style={{ fontSize: 11, color: "var(--ink-400)", marginBottom: 4 }}>Zona</div><Badge nivel={zN} label={zonaLabel(r.rb)} /></div>
          </div>

          {/* #2 score trajectory */}
          {r._hist && (
            <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 14px", borderRadius: 8, background: "var(--table-head-bg)", marginBottom: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: "var(--ink-400)", marginBottom: 2 }}>Trayectoria del score · últimos 6 meses</div>
                <div style={{ fontSize: 12, color: "var(--ink-600)" }}>
                  {r._delta > 0 ? <span style={{ color: "var(--red-text)", fontWeight: 700 }}>▲ subió {r._delta} este mes — empeorando</span>
                    : r._delta < 0 ? <span style={{ color: "var(--green-text)", fontWeight: 700 }}>▼ bajó {Math.abs(r._delta)} este mes — mejorando</span>
                    : <span>sin cambio respecto al mes anterior</span>}
                </div>
              </div>
              <ScoreHistory hist={r._hist} w={110} h={34} />
            </div>
          )}

          {/* #1 score explainability */}
          {window.ScoreBreakdown && <div style={{ marginBottom: 16 }}><ScoreBreakdown vendedor={r} /></div>}

          <div style={{ fontSize: 11, color: "var(--ink-400)", marginBottom: 6 }}>Señales detectadas</div>
          <div style={{ minHeight: 26 }}><Pills senales={r.senales} /></div>

          {/* #2 action recommendation based on what worked for similar profiles */}
          {window.recomendarAccion && ["critico", "alto"].includes(r.nivel) && (() => {
            const rec = window.recomendarAccion(r);
            return (
              <div style={{ marginTop: 18, padding: "14px 16px", borderRadius: 10, background: r.nivel === "critico" ? "var(--red-bg)" : "var(--orange-bg)" }}>
                <div style={{ fontSize: 11, color: r.nivel === "critico" ? "var(--red-text)" : "var(--orange-text)", textTransform: "uppercase", letterSpacing: ".04em", marginBottom: 6, fontWeight: 700 }}>
                  Acción recomendada
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
                  <span style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 17, color: "var(--ink-900)" }}>{rec.mejor.tipo}</span>
                  <span style={{ fontSize: 13, color: "var(--green-text)", fontWeight: 700 }}>↓ {fmtNum(rec.mejor.avg, 1)} de score en promedio</span>
                </div>
                <div style={{ fontSize: 12, color: "var(--ink-600)", marginTop: 6, lineHeight: 1.5 }}>
                  Es lo que mejor funcionó para <b>{rec.perfilLabel}</b> ({rec.mejor.n} casos). {r.nivel === "critico" ? "Agendá la reunión esta semana." : "Programá el seguimiento."}
                </div>
                <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
                  {rec.ranking.slice(1).map((a) => (
                    <span key={a.tipo} style={{ fontSize: 11, color: "var(--ink-500)", background: "rgba(255,255,255,.6)", padding: "3px 8px", borderRadius: 6 }}>
                      {a.tipo} · ↓{fmtNum(a.avg, 1)}
                    </span>
                  ))}
                </div>
              </div>
            );
          })()}
          {(!window.recomendarAccion || !["critico", "alto"].includes(r.nivel)) && (
            <div style={{ marginTop: 18, padding: "12px 14px", borderRadius: 8, background: "var(--table-head-bg)", fontSize: 12, color: "var(--ink-600)", lineHeight: 1.5 }}>
              Acción sugerida: {r.nivel === "medio" ? "monitoreo mensual." : "seguimiento normal."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { CostView, VendedorModal, costoRotacion });
