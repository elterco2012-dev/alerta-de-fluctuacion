/* Historial — faithful "actual" recreation + v2 redesign.
   v2 adds: company retention/survival curve, cohort table (#3), monthly rotation
   trend, average-risk-score trajectory, and a "biggest escalations" leaderboard (#2). */

// ---------- small SVG line chart ----------
function LineChart({ series, w = 560, h = 150, max = 100, min = 0, labels, fmt = (v) => v, pad = 28 }) {
  const iw = w - pad * 2, ih = h - 24;
  const n = series[0].data.length;
  const xy = (v, i) => [pad + (n === 1 ? iw / 2 : (i / (n - 1)) * iw), 8 + ih - ((v - min) / (max - min)) * ih];
  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} style={{ display: "block" }}>
      {[0, 0.5, 1].map((g) => {
        const y = 8 + ih - g * ih;
        return <line key={g} x1={pad} y1={y} x2={w - pad} y2={y} stroke="var(--line-faint)" strokeWidth="1" />;
      })}
      {series.map((s) => {
        const pts = s.data.map((v, i) => xy(v, i));
        return (
          <g key={s.name}>
            <polyline points={pts.map((p) => p.join(",")).join(" ")} fill="none" stroke={s.color} strokeWidth={s.width || 2.5} strokeLinejoin="round" strokeLinecap="round" strokeDasharray={s.dash || "0"} />
            {pts.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r="3" fill={s.color} />)}
            {s.showVals && pts.map((p, i) => <text key={"t" + i} x={p[0]} y={p[1] - 8} textAnchor="middle" fontSize="10" fontWeight="700" fill="var(--ink-500)" fontFamily="var(--font-sans)">{fmt(s.data[i])}</text>)}
          </g>
        );
      })}
      {labels && labels.map((l, i) => (
        <text key={l + i} x={xy(min, i)[0]} y={h - 4} textAnchor="middle" fontSize="10" fill="var(--ink-400)" fontFamily="var(--font-sans)">{l}</text>
      ))}
    </svg>
  );
}

// ---------- v2 ----------
function HistorialV2({ data, onOpenVendedor }) {
  const { V, RETENCION, ROTACION, COHORTS } = data;
  const mesLabels = ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7"];

  const totalBajas = ROTACION.reduce((s, m) => s + m.bajas, 0);
  const retM6 = RETENCION[6];
  const escaladas = [...V].filter((r) => r._delta > 0).sort((a, b) => b._delta - a._delta).slice(0, 5);

  // cohort color by retention at last known month
  const cohortCell = (v) => v == null ? "transparent" : v >= 70 ? "var(--green-pos-bg)" : v >= 50 ? "var(--cell-warn-bg)" : "var(--cell-bad-bg)";
  const cohortTx = (v) => v == null ? "var(--ink-200)" : v >= 70 ? "var(--green-pos-tx)" : v >= 50 ? "var(--cell-warn-tx)" : "var(--cell-bad-tx)";

  return (
    <div>
      <V2Banner emoji="📈" tone="red"
        title={`Solo ${retM6}% del equipo sigue activo al mes 6`}
        sub={`En los últimos 6 meses hubo ${totalBajas} bajas. La curva de supervivencia se desploma entre el mes 3 y el 5 — ahí está la fuga.`}
        cta="Ver cohortes →" />

      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <HeroStat label="Permanencia al egreso" value="5,2" unit="meses" accent="var(--orange-accent)">
          <div style={{ fontSize: 12, color: "var(--ink-500)" }}><b style={{ color: "var(--red-accent)" }}>−71%</b> vs. 18 meses hace una década</div>
        </HeroStat>
        <V2Card style={{ flex: 1 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
            <span style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14, color: "var(--ink-900)" }}>Curva de supervivencia del equipo</span>
            <span style={{ fontSize: 12, color: "var(--ink-400)" }}>% activos por mes de antigüedad</span>
          </div>
          <LineChart w={560} h={150} max={100} min={0}
            series={[{ name: "ret", color: "var(--red-accent)", data: RETENCION, showVals: true }]}
            labels={mesLabels} fmt={(v) => v + "%"} />
        </V2Card>
      </div>
      <StatStrip>
        <StatItem value={totalBajas} label="Bajas últimos 6 meses" />
        <StatItem value={`${retM6}%`} label="Retención al mes 6" />
        <StatItem value={`${RETENCION[3]}%`} label="Retención al mes 3" />
        <StatItem value={escaladas.length} label="Vendedores escalando este mes" />
      </StatStrip>

      <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 24, marginBottom: 32, alignItems: "start" }}>
        <div>
          <V2Section title="🔄 Rotación mensual — bajas vs. altas" />
          <V2Card>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 16, height: 150 }}>
              {ROTACION.map((m) => {
                const mx = Math.max(...ROTACION.flatMap((x) => [x.bajas, x.altas]));
                return (
                  <div key={m.mes} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6, height: "100%", justifyContent: "flex-end" }}>
                    <div style={{ display: "flex", gap: 3, alignItems: "flex-end", height: 110 }}>
                      <div style={{ width: 12, height: `${(m.altas / mx) * 100}%`, background: "var(--green-soft)", borderRadius: "2px 2px 0 0" }} title={`${m.altas} altas`} />
                      <div style={{ width: 12, height: `${(m.bajas / mx) * 100}%`, background: "var(--red-accent)", borderRadius: "2px 2px 0 0" }} title={`${m.bajas} bajas`} />
                    </div>
                    <span style={{ fontSize: 10, color: "var(--ink-400)" }}>{m.mes}</span>
                  </div>
                );
              })}
            </div>
            <div style={{ display: "flex", gap: 16, marginTop: 12, fontSize: 11, color: "var(--ink-500)" }}>
              <span><span style={{ display: "inline-block", width: 9, height: 9, background: "var(--red-accent)", borderRadius: 2, marginRight: 5 }} />Bajas</span>
              <span><span style={{ display: "inline-block", width: 9, height: 9, background: "var(--green-soft)", borderRadius: 2, marginRight: 5 }} />Altas</span>
            </div>
          </V2Card>
        </div>
        <div>
          <V2Section title="📊 Score de riesgo promedio" />
          <V2Card>
            <LineChart w={360} h={150} max={7} min={3}
              series={[{ name: "score", color: "var(--red-accent)", data: ROTACION.map((m) => m.scoreProm), showVals: true }]}
              labels={ROTACION.map((m) => m.mes)} fmt={(v) => v.toFixed(1)} />
            <div style={{ fontSize: 11, color: "var(--ink-400)", marginTop: 8 }}>El riesgo promedio del equipo viene en aumento — más vendedores entran en zona de alerta.</div>
          </V2Card>
        </div>
      </div>

      {/* #3 cohort retention table */}
      <V2Section title="👥 Retención por cohorte de ingreso" right={<span style={{ fontSize: 12, color: "var(--ink-400)" }}>% que sigue activo cada mes</span>} />
      <V2Card pad={false} style={{ overflow: "hidden", padding: "8px 8px 8px" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr>
            <th style={v2th}>Cohorte</th><th style={{ ...v2th, textAlign: "center" }}>Ingresos</th>
            {["M0", "M1", "M2", "M3", "M4", "M5"].map((m) => <th key={m} style={{ ...v2th, textAlign: "center" }}>{m}</th>)}
          </tr></thead>
          <tbody>
            {COHORTS.map((c) => (
              <tr key={c.cohorte}>
                <td style={{ ...v2td, fontWeight: 700 }}>{c.cohorte}</td>
                <td style={{ ...v2td, textAlign: "center", color: "var(--ink-500)" }}>{c.ingresos}</td>
                {[0, 1, 2, 3, 4, 5].map((mi) => {
                  const v = c.ret[mi];
                  return <td key={mi} style={{ ...v2td, textAlign: "center", padding: 6 }}>
                    {v == null ? <span style={{ color: "var(--ink-150)" }}>·</span>
                      : <span style={{ display: "inline-block", minWidth: 40, padding: "5px 0", borderRadius: 6, background: cohortCell(v), color: cohortTx(v), fontWeight: 700, fontSize: 12 }}>{v}%</span>}
                  </td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </V2Card>
      <div style={{ fontSize: 12, color: "var(--ink-400)", margin: "8px 0 32px" }}>Cada cohorte pierde ~25-40% para el mes 3. Las cohortes en zonas quemadas (Centro) caen más rápido.</div>

      {/* #2 escalation leaderboard */}
      <V2Section title="⚠️ Mayores escaladas de score este mes" right={<span style={{ fontSize: 12, color: "var(--ink-400)" }}>Quiénes empeoraron más rápido</span>} />
      {escaladas.length === 0
        ? <V2Empty title="Nadie escaló este mes" sub="Ningún vendedor subió su score respecto al mes anterior." />
        : (
          <V2Card pad={false} style={{ overflow: "hidden", padding: "8px 8px 0" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr><th style={v2th}>Vendedor</th><th style={v2th}>Score actual</th><th style={v2th}>Δ mes</th><th style={v2th}>Trayectoria 6m</th><th style={v2th}>Zona</th></tr></thead>
              <tbody>
                {escaladas.map((r) => (
                  <tr key={r.id} className="vrow" onClick={() => onOpenVendedor && onOpenVendedor(r)} style={{ cursor: "pointer" }}>
                    <td style={v2td}><b>{r.nombre}</b> <span style={{ color: "var(--ink-400)", fontSize: 11 }}>({r.id})</span><div style={{ color: "var(--ink-250)", fontSize: 11 }}>{r.tipo} · {fmtAntiguedad(r.meses)}</div></td>
                    <td style={v2td}><ScoreCircle score={r.score} nivel={r.nivel} /></td>
                    <td style={v2td}><ScoreDelta delta={r._delta} /></td>
                    <td style={v2td}><ScoreHistory hist={r._hist} w={100} h={30} /></td>
                    <td style={v2td}><Badge nivel={zonaNivel(r.rb)} label={r.grupo} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </V2Card>
        )}
    </div>
  );
}

// ---------- faithful "actual" ----------
function HistorialActual({ data }) {
  const { ROTACION, RETENCION } = data;
  const mx = Math.max(...ROTACION.flatMap((x) => [x.bajas, x.altas]));
  return (
    <div>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 22, color: "var(--ink-900)", marginBottom: 18 }}>📈 Historial de rotación</div>
      <div style={{ display: "flex", gap: 14, marginBottom: 24 }}>
        <KpiCard value={ROTACION.reduce((s, m) => s + m.bajas, 0)} label="Bajas (6 meses)" />
        <KpiCard value={"5,2 m"} label="Permanencia prom." />
        <KpiCard value={`${RETENCION[6]}%`} label="Retención al mes 6" />
      </div>
      <SectionHeader>Rotación mensual</SectionHeader>
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 16, height: 180 }}>
          {ROTACION.map((m) => (
            <div key={m.mes} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6, height: "100%", justifyContent: "flex-end" }}>
              <div style={{ display: "flex", gap: 4, alignItems: "flex-end", height: 140 }}>
                <div style={{ width: 14, height: `${(m.altas / mx) * 100}%`, background: "#8DB56B" }} />
                <div style={{ width: 14, height: `${(m.bajas / mx) * 100}%`, background: "#E24B4A" }} />
              </div>
              <span style={{ fontSize: 11, color: "var(--ink-500)" }}>{m.mes}</span>
            </div>
          ))}
        </div>
        <div style={{ fontSize: 12, color: "var(--ink-500)", marginTop: 12 }}>🔴 Bajas · 🟢 Altas</div>
      </Card>
      <SectionHeader>Permanencia al egreso por mes</SectionHeader>
      <Card>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 12, height: 120 }}>
          {RETENCION.map((v, i) => (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 5, height: "100%", justifyContent: "flex-end" }}>
              <span style={{ fontSize: 10, color: "var(--ink-500)" }}>{v}%</span>
              <div style={{ width: "70%", height: `${v}%`, background: "#4A90D9", borderRadius: "2px 2px 0 0" }} />
              <span style={{ fontSize: 10, color: "var(--ink-400)" }}>M{i}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

Object.assign(window, { HistorialV2, HistorialActual, LineChart });
