/* Por supervisor — v2. Ranked by urgency, action-oriented cards, hero on the
   most at-risk zone, cleaner detail. Reuses primitives + v2common. */

function SupCardV2({ row, onOpen, rank }) {
  const nivel = zonaNivel(row.rb);
  const cc = { critico: "var(--red-accent)", alto: "var(--orange-accent)", medio: "var(--blue-accent)", bajo: "var(--green-accent)" }[nivel];
  const c = row.criticos, a = row.altos;
  const necesita = c + a;
  return (
    <div style={{
      background: "var(--surface)", borderRadius: 14, padding: "18px 20px",
      boxShadow: "var(--shadow-card)", borderTop: `4px solid ${cc}`,
      display: "flex", flexDirection: "column",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 16, color: "var(--ink-900)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{row.supervisor}</div>
          <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 2 }}>{row.grupo} · {row.activos} activos</div>
        </div>
        <div style={{ flexShrink: 0 }}><Badge nivel={nivel} label={zonaLabel(row.rb)} /></div>
      </div>

      {/* the action number is the hero of the card */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginTop: 16 }}>
        <span style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 34, lineHeight: 1, color: necesita ? "var(--red-accent)" : "var(--green-text)" }}>{necesita}</span>
        <span style={{ fontSize: 13, color: "var(--ink-500)" }}>requieren atención</span>
      </div>
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 6 }}>
        {c ? <span><b style={{ color: "var(--red-text)" }}>{c} crítico{c > 1 ? "s" : ""}</b></span> : null}
        {c && a ? " · " : null}
        {a ? <span style={{ color: "var(--orange-text)" }}>{a} alto{a > 1 ? "s" : ""}</span> : null}
        {!necesita ? <span style={{ color: "var(--green-text)" }}>Sin alertas activas</span> : null}
        <span> · perm. {row.permEgreso.toFixed(1).replace(".", ",")}m</span>
      </div>

      <button onClick={() => onOpen(row.supervisor)} style={{
        marginTop: 16, width: "100%", padding: "9px 0", borderRadius: 8, cursor: "pointer",
        border: "none", background: necesita ? "var(--ink-900)" : "#fff",
        color: necesita ? "#fff" : "var(--ink-600)",
        boxShadow: necesita ? "none" : "inset 0 0 0 1px var(--line-strong)",
        fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13,
      }}>Ver mis vendedores →</button>
    </div>
  );
}

function SupervisorV2({ data, onOpenVendedor }) {
  const { V, Z } = data;
  const [sel, setSel] = React.useState(null);

  const resumen = Z.map((z) => {
    const reps = V.filter((r) => r.supervisor === z.supervisor);
    return {
      supervisor: z.supervisor, grupo: z.grupo, rb: z.rb, permEgreso: z.permEgreso,
      activos: reps.length,
      criticos: reps.filter((r) => r.nivel === "critico").length,
      altos: reps.filter((r) => r.nivel === "alto").length,
    };
  }).sort((a, b) => (b.criticos * 10 + b.altos) - (a.criticos * 10 + a.altos));

  if (!sel) {
    const totalAccion = resumen.reduce((s, r) => s + r.criticos + r.altos, 0);
    const peor = resumen[0];
    return (
      <div>
        <V2Banner emoji="👤" tone="orange"
          title={`${peor.grupo} (${peor.supervisor}) es la zona que más atención necesita`}
          sub={`${totalAccion} vendedores en riesgo elevado repartidos entre 4 supervisores.`}
          cta="Ver zona crítica →" />
        <StatStrip>
          <StatItem value={resumen.length} label="Supervisores activos" />
          <StatItem value={V.length} label="Vendedores totales" />
          <StatItem value={totalAccion} label="En riesgo elevado" />
          <StatItem value="3,5" label="Vendedores / supervisor" />
        </StatStrip>
        <V2Section title="📋 Supervisores por urgencia" right={<span style={{ fontSize: 12, color: "var(--ink-400)" }}>Ordenados por vendedores en riesgo</span>} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
          {resumen.map((row, i) => <SupCardV2 key={row.supervisor} row={row} onOpen={setSel} rank={i} />)}
        </div>
      </div>
    );
  }

  const reps = V.filter((r) => r.supervisor === sel).sort((a, b) => b.score - a.score);
  const z = Z.find((x) => x.supervisor === sel);
  const nivelZona = zonaNivel(z.rb);
  const nCrit = reps.filter((r) => r.nivel === "critico").length;
  const nAlto = reps.filter((r) => r.nivel === "alto").length;
  const accion = reps.filter((r) => ["critico", "alto"].includes(r.nivel));
  const nOnb = reps.filter((r) => r.meses <= 6).length;

  return (
    <div>
      <button onClick={() => setSel(null)} style={{ marginBottom: 16, padding: "6px 14px", borderRadius: 8, cursor: "pointer", border: "1px solid var(--line-strong)", background: "#fff", fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: 13, color: "var(--ink-600)" }}>← Todas las zonas</button>

      {z.rb > 0.45 && (
        <V2Banner emoji="⚠️" tone={z.rb > 0.60 ? "red" : "orange"}
          title={`${z.grupo} es una zona de alta rotación histórica`}
          sub="Los vendedores nuevos aquí tienen mayor probabilidad de irse antes de los 6 meses. Priorizá el onboarding." />
      )}

      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <HeroStat label={`${sel} — requieren acción`} value={nCrit + nAlto} unit={`de ${reps.length}`} accent="var(--red-accent)" valueColor="var(--red-accent)">
          <div style={{ display: "flex", gap: 8 }}>
            <span style={{ flex: 1, textAlign: "center", padding: "8px 0", borderRadius: 8, background: "var(--red-bg)" }}><span style={{ display: "block", fontWeight: 800, fontSize: 20, color: "var(--red-text)" }}>{nCrit}</span><span style={{ fontSize: 11, color: "var(--red-text)", fontWeight: 600 }}>Crítico</span></span>
            <span style={{ flex: 1, textAlign: "center", padding: "8px 0", borderRadius: 8, background: "var(--orange-bg)" }}><span style={{ display: "block", fontWeight: 800, fontSize: 20, color: "var(--orange-text)" }}>{nAlto}</span><span style={{ fontSize: 11, color: "var(--orange-text)", fontWeight: 600 }}>Alto</span></span>
          </div>
        </HeroStat>
        <V2Card style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", gap: 18 }}>
          <div style={{ display: "flex", gap: 28 }}>
            <div><div style={{ fontSize: 11, color: "var(--ink-400)", textTransform: "uppercase", letterSpacing: ".04em" }}>Zona</div><div style={{ marginTop: 6 }}><Badge nivel={nivelZona} label={`${z.grupo} · ${zonaLabel(z.rb)}`} /></div></div>
            <div><div style={{ fontSize: 11, color: "var(--ink-400)", textTransform: "uppercase", letterSpacing: ".04em" }}>Permanencia prom.</div><div style={{ fontWeight: 800, fontSize: 24, marginTop: 4 }}>{z.permEgreso.toFixed(1).replace(".", ",")}m</div></div>
            <div><div style={{ fontSize: 11, color: "var(--ink-400)", textTransform: "uppercase", letterSpacing: ".04em" }}>En onboarding</div><div style={{ fontWeight: 800, fontSize: 24, marginTop: 4, color: "var(--blue-accent)" }}>{nOnb}</div></div>
          </div>
          <div style={{ fontSize: 12, color: "var(--ink-400)", lineHeight: 1.5 }}>Empezá por los {accion.length} vendedores marcados abajo — los críticos necesitan una reunión esta semana.</div>
        </V2Card>
      </div>
      <div style={{ height: 20 }} />

      <V2Section title="📋 Mis vendedores por prioridad" />
      {reps.length === 0
        ? <V2Empty title="Sin vendedores asignados" sub="Esta zona no tiene vendedores activos." />
        : <V2VendedorTable rows={reps} onOpen={onOpenVendedor} />}
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 10 }}>{reps.length} vendedores en {z.grupo}</div>
    </div>
  );
}

// reusable v2 table with acción column (shared by Supervisor + Inicio v2)
function V2VendedorTable({ rows, onOpen }) {
  const density = useDensity();
  const td = tdFor(density);
  return (
    <V2Card pad={false} style={{ overflow: "hidden", padding: "8px 8px 0" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr>
          <th style={v2th}>Vendedor</th><th style={v2th}>Señales</th><th style={v2th}>% Plan 3m</th>
          <th style={v2th}>Tendencia</th><th style={v2th}>Score · Δ mes</th><th style={v2th}>Acción sugerida</th>
        </tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="vrow" onClick={() => onOpen && onOpen(r)} style={{ cursor: "pointer" }}>
              <td style={td}>
                <div style={{ fontWeight: 700, color: "var(--ink-900)", fontSize: 13 }}>{r.nombre} <span style={{ color: "var(--ink-400)", fontWeight: 400, fontSize: 11 }}>({r.id})</span></div>
                <div style={{ color: "var(--ink-250)", fontSize: 11, marginTop: 2 }}>{r.tipo} · {fmtAntiguedad(r.meses)} · {r.grupo}</div>
              </td>
              <td style={td}><Pills senales={r.senales} /></td>
              <td style={td}><b>{r.plan3m}%</b></td>
              <td style={td}><Sparkline vals={r.spark} /></td>
              <td style={td}><div style={{ display: "flex", alignItems: "center", gap: 8 }}><ScoreCircle score={r.score} nivel={r.nivel} /><ScoreDelta delta={r._delta} /></div></td>
              <td style={td}><AccionTag nivel={r.nivel} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </V2Card>
  );
}

Object.assign(window, { SupervisorV2, V2VendedorTable });
