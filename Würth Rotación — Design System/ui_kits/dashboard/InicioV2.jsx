/* Inicio v2 — "propuesta profesional". Same data as InicioView, rebuilt to apply:
   1) jerarquía visual  2) densidad/respiración  3) permanencia como estrella
   4) acción no solo diagnóstico  5) charts limpios  6) estados vacíos.
   Reuses primitives.jsx (Card, ScoreCircle, Pills, Badge, Sparkline). */

// ---- Acción sugerida por nivel (diagnóstico → to-do) ----
const ACCION = {
  critico: ["Reunión esta semana", "var(--red-text)", "var(--red-bg)"],
  alto:    ["Seguimiento activo",  "var(--orange-text)", "var(--orange-bg)"],
  medio:   ["Monitoreo mensual",   "var(--ink-600)", "var(--table-head-bg)"],
  bajo:    ["Seguimiento normal",  "var(--ink-400)", "transparent"],
};

// ---- 1+4: banner de acción del día ----
function ActionBanner({ nCrit, nOnb }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 14, padding: "14px 20px",
      borderRadius: 12, background: "var(--red-bg)", border: "1px solid #f4cfcd",
      marginBottom: 28,
    }}>
      <span style={{ fontSize: 22 }}>🔴</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 16, color: "var(--red-text)" }}>
          {nCrit} vendedores necesitan reunión esta semana
        </div>
        <div style={{ fontFamily: "var(--font-sans)", fontSize: 13, color: "#8a3331", marginTop: 2 }}>
          {nOnb} de ellos están en su ventana crítica de onboarding (primeros 6 meses).
        </div>
      </div>
      <button style={{
        padding: "9px 18px", borderRadius: 8, border: "none", cursor: "pointer",
        background: "var(--red-accent)", color: "#fff",
        fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13, whiteSpace: "nowrap",
      }}>Ver lista de acción →</button>
    </div>
  );
}

// ---- 1: KPI hero dominante (riesgo elevado) ----
function HeroKpi({ nElevado, nCrit, nAlto, total }) {
  return (
    <div style={{
      flex: "0 0 320px", background: "var(--surface)", borderRadius: 14,
      padding: "22px 24px", boxShadow: "var(--shadow-card)",
      borderTop: "4px solid var(--red-accent)", display: "flex", flexDirection: "column",
    }}>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13, color: "var(--ink-600)", textTransform: "uppercase", letterSpacing: ".04em" }}>
        En riesgo elevado
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 8 }}>
        <span style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 64, lineHeight: 1, color: "var(--red-accent)" }}>{nElevado}</span>
        <span style={{ fontFamily: "var(--font-sans)", fontSize: 16, color: "var(--ink-400)" }}>de {total} activos</span>
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <span style={{ flex: 1, textAlign: "center", padding: "8px 0", borderRadius: 8, background: "var(--red-bg)" }}>
          <span style={{ display: "block", fontWeight: 800, fontSize: 20, color: "var(--red-text)" }}>{nCrit}</span>
          <span style={{ fontSize: 11, color: "var(--red-text)", fontWeight: 600 }}>Crítico</span>
        </span>
        <span style={{ flex: 1, textAlign: "center", padding: "8px 0", borderRadius: 8, background: "var(--orange-bg)" }}>
          <span style={{ display: "block", fontWeight: 800, fontSize: 20, color: "var(--orange-text)" }}>{nAlto}</span>
          <span style={{ fontSize: 11, color: "var(--orange-text)", fontWeight: 600 }}>Alto</span>
        </span>
      </div>
    </div>
  );
}

// ---- 3: permanencia como estrella, con la caída 18 → 5 ----
function PermanenciaCard() {
  const serie = [
    { y: "2016", m: 18 }, { y: "2019", m: 13 }, { y: "2022", m: 8 }, { y: "2025", m: 5.2 },
  ];
  const max = 18;
  return (
    <div style={{
      flex: 1, background: "var(--surface)", borderRadius: 14, padding: "22px 24px",
      boxShadow: "var(--shadow-card)", borderTop: "4px solid var(--orange-accent)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13, color: "var(--ink-600)", textTransform: "uppercase", letterSpacing: ".04em" }}>
            Permanencia al egreso
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginTop: 8 }}>
            <span style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 44, lineHeight: 1, color: "var(--ink-900)" }}>5,2</span>
            <span style={{ fontFamily: "var(--font-sans)", fontSize: 18, color: "var(--ink-400)" }}>meses</span>
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontWeight: 800, fontSize: 22, color: "var(--red-accent)" }}>−71%</div>
          <div style={{ fontSize: 11, color: "var(--ink-400)", maxWidth: 130, lineHeight: 1.35, marginTop: 2 }}>vs. 18 meses hace una década</div>
        </div>
      </div>
      {/* mini-tendencia de la caída */}
      <div style={{ display: "flex", alignItems: "flex-end", gap: 14, height: 70, marginTop: 18 }}>
        {serie.map((d, i) => (
          <div key={d.y} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 5, height: "100%", justifyContent: "flex-end" }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: i === serie.length - 1 ? "var(--red-accent)" : "var(--ink-400)" }}>{String(d.m).replace(".", ",")}m</span>
            <div style={{ width: "70%", maxWidth: 30, height: `${(d.m / max) * 48}px`, borderRadius: "3px 3px 0 0", background: i === serie.length - 1 ? "var(--red-accent)" : "var(--chart-neutral)" }} />
            <span style={{ fontSize: 10, color: "var(--ink-300)" }}>{d.y}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---- 1: stats secundarias, de-enfatizadas ----
function SecondaryStat({ value, label }) {
  return (
    <div style={{ flex: 1, padding: "4px 2px" }}>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 26, color: "var(--ink-900)" }}>{value}</div>
      <div style={{ fontFamily: "var(--font-sans)", fontSize: 12, color: "var(--ink-400)", marginTop: 2 }}>{label}</div>
    </div>
  );
}

// ---- 5: chart limpio (ventana crítica) ----
function CleanWindowChart({ data }) {
  const max = Math.max(...data.map((d) => d.n));
  const color = (m) => m <= 3 ? "var(--red-accent)" : m <= 6 ? "var(--orange-accent)" : "var(--chart-neutral)";
  const totalEarly = data.filter((d) => d.m <= 6).reduce((s, d) => s + d.n, 0);
  const totalAll = data.reduce((s, d) => s + d.n, 0);
  return (
    <div style={{ background: "var(--surface)", borderRadius: 14, padding: "20px 24px", boxShadow: "var(--shadow-card)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 18 }}>
        <span style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 15, color: "var(--ink-900)" }}>⏱️ Ventanas críticas de permanencia</span>
        <span style={{ fontFamily: "var(--font-sans)", fontSize: 13, color: "var(--red-text)", fontWeight: 700 }}>
          {Math.round((totalEarly / totalAll) * 100)}% se va antes del mes 7
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 7, height: 150 }}>
        {data.map((d) => (
          <div key={d.m} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 5, height: "100%", justifyContent: "flex-end" }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: "var(--ink-400)" }}>{d.n}</span>
            <div style={{ width: "100%", maxWidth: 24, height: `${(d.n / max) * 110}px`, borderRadius: "3px 3px 0 0", background: color(d.m) }} />
            <span style={{ fontSize: 10, color: "var(--ink-300)" }}>M{d.m}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---- 4: tabla con columna de acción ----
function V2Table({ rows, onOpen, empty }) {
  const density = useDensity();
  const th = { background: "transparent", padding: "0 14px 10px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--ink-400)", textTransform: "uppercase", letterSpacing: ".04em", borderBottom: "2px solid var(--line-strong)" };
  const td = tdFor(density);
  if (!rows.length) {
    return (
      <div style={{ background: "var(--surface)", borderRadius: 14, boxShadow: "var(--shadow-card)", padding: "48px 22px", textAlign: "center" }}>
        <div style={{ fontSize: 30, marginBottom: 8 }}>✓</div>
        <div style={{ fontWeight: 700, fontSize: 14, color: "var(--green-text)" }}>{empty || "Sin vendedores en esta vista"}</div>
        <div style={{ fontSize: 13, color: "var(--ink-400)", marginTop: 4 }}>Probá con otro filtro o limpiá la búsqueda.</div>
      </div>
    );
  }
  return (
    <div style={{ background: "var(--surface)", borderRadius: 14, boxShadow: "var(--shadow-card)", overflow: "hidden", padding: "8px 8px 0" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr>
          <th style={th}>Vendedor</th><th style={th}>Señales</th><th style={th}>% Plan 3m</th>
          <th style={th}>Tendencia</th><th style={th}>Score · Δ mes</th><th style={th}>Acción sugerida</th>
        </tr></thead>
        <tbody>
          {rows.map((r) => {
            const [acc, accTx, accBg] = ACCION[r.nivel];
            return (
              <tr key={r.id} className="vrow" onClick={() => onOpen && onOpen(r)} style={{ cursor: "pointer" }}>
                <td style={td}>
                  <div style={{ fontWeight: 700, color: "var(--ink-900)", fontSize: 13 }}>{r.nombre} <span style={{ color: "var(--ink-400)", fontWeight: 400, fontSize: 11 }}>({r.id})</span></div>
                  <div style={{ color: "var(--ink-250)", fontSize: 11, marginTop: 2 }}>{r.tipo} · {fmtAntiguedad(r.meses)} · {r.grupo}</div>
                </td>
                <td style={td}><Pills senales={r.senales} /></td>
                <td style={td}><b>{r.plan3m}%</b></td>
                <td style={td}><Sparkline vals={r.spark} /></td>
                <td style={td}><div style={{ display: "flex", alignItems: "center", gap: 8 }}><ScoreCircle score={r.score} nivel={r.nivel} /><ScoreDelta delta={r._delta} /></div></td>
                <td style={td}>
                  <span style={{ display: "inline-block", padding: "4px 10px", borderRadius: 7, background: accBg, color: accTx, fontSize: 12, fontWeight: 700, whiteSpace: "nowrap" }}>{acc}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function InicioV2({ data, onOpenVendedor }) {
  const { V, VENTANAS } = data;
  const [filtro, setFiltro] = React.useState("Requieren acción");
  const [busq, setBusq] = React.useState("");

  const total = V.length;
  const crit = V.filter((r) => r.nivel === "critico");
  const alto = V.filter((r) => r.nivel === "alto");
  const nElevado = crit.length + alto.length;
  const nOnbCrit = V.filter((r) => r.meses <= 6 && r.nivel === "critico").length;

  let df = [...V].sort((a, b) => b.score - a.score);
  if (filtro === "Requieren acción") df = df.filter((r) => ["critico", "alto"].includes(r.nivel));
  else if (filtro === "Crítico") df = df.filter((r) => r.nivel === "critico");
  else if (filtro === "Onboarding") df = df.filter((r) => r.meses <= 6);
  if (busq) df = df.filter((r) => r.nombre.toLowerCase().includes(busq.toLowerCase()) || String(r.id).includes(busq));

  const pill = (o) => (
    <button key={o} onClick={() => setFiltro(o)} style={{
      fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: 13, padding: "6px 15px", borderRadius: 8, cursor: "pointer",
      border: "1px solid", borderColor: filtro === o ? "var(--blue-accent)" : "var(--line-strong)",
      background: filtro === o ? "var(--blue-bg)" : "#fff", color: filtro === o ? "var(--blue-text)" : "var(--ink-600)",
    }}>{o}</button>
  );

  return (
    <div>
      <ActionBanner nCrit={crit.length} nOnb={nOnbCrit} />

      {/* fila KPI con jerarquía: hero + estrella, luego stats menores */}
      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <HeroKpi nElevado={nElevado} nCrit={crit.length} nAlto={alto.length} total={total} />
        <PermanenciaCard />
      </div>
      <div style={{ display: "flex", gap: 0, padding: "0 4px", marginBottom: 36, borderBottom: "1px solid var(--line-faint)", paddingBottom: 18 }}>
        <SecondaryStat value={total} label="Vendedores activos" />
        <SecondaryStat value={nOnbCrit} label="Onboarding en riesgo" />
        <SecondaryStat value="4" label="Supervisores activos" />
        <SecondaryStat value="3,5" label="Vendedores / supervisor" />
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
        <span style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 16, color: "var(--ink-900)" }}>📋 Vendedores por prioridad</span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {["Requieren acción", "Crítico", "Onboarding", "Todos"].map(pill)}
          <input value={busq} onChange={(e) => setBusq(e.target.value)} placeholder="🔍 Buscar…"
            style={{ padding: "7px 12px", borderRadius: 8, border: "1px solid var(--line-strong)", fontFamily: "var(--font-sans)", fontSize: 13, width: 150, outline: "none" }} />
          <DensityToggle />
        </div>
      </div>
      <V2Table rows={df} onOpen={onOpenVendedor} empty="No hay vendedores que requieran acción 🎉" />
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 10 }}>{df.length} vendedores · ordenados por score · clic para ver el detalle.</div>

      <div style={{ marginTop: 40 }}>
        <CleanWindowChart data={VENTANAS} />
      </div>
    </div>
  );
}

Object.assign(window, { InicioV2 });
