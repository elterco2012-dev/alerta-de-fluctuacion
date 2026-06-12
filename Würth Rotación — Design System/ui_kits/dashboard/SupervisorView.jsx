/* Por supervisor — landing grid of supervisor cards → drill into "my reps". */

function SupCard({ row, onOpen }) {
  const nivel = zonaNivel(row.rb);
  const cc = { critico: "var(--red-accent)", alto: "var(--orange-accent)", medio: "var(--blue-accent)", bajo: "var(--green-accent)" }[nivel];
  const c = row.criticos, a = row.altos;
  let alerta;
  if (c > 0) alerta = <span><span style={{ color: "var(--red-accent)", fontWeight: 700 }}>{c} crítico{c > 1 ? "s" : ""}</span>{a ? <span> · <span style={{ color: "var(--orange-text)" }}>{a} alto{a > 1 ? "s" : ""}</span></span> : null}</span>;
  else if (a) alerta = <span style={{ color: "var(--orange-text)" }}>{a} alto{a > 1 ? "s" : ""}</span>;
  else alerta = <span style={{ color: "var(--green-text)" }}>Sin alertas activas</span>;

  return (
    <div style={{
      background: "var(--surface)", borderRadius: "var(--radius-card)", padding: "18px 20px",
      boxShadow: "var(--shadow-card)", borderLeft: `4px solid ${cc}`,
    }}>
      <div style={{ font: "var(--w-black) 15px var(--font-sans)", color: "var(--ink-900)" }}>{row.supervisor}</div>
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 2 }}>{row.grupo}</div>
      <div style={{ display: "flex", gap: 20, marginTop: 12 }}>
        <div><div style={{ fontSize: 20, fontWeight: 800 }}>{row.activos}</div><div style={{ fontSize: 11, color: "var(--ink-250)" }}>activos</div></div>
        <div><div style={{ fontSize: 20, fontWeight: 800 }}>{row.permEgreso.toFixed(1).replace(".", ",")}m</div><div style={{ fontSize: 11, color: "var(--ink-250)" }}>perm. prom.</div></div>
        <div style={{ marginLeft: "auto", alignSelf: "center" }}><Badge nivel={nivel} /></div>
      </div>
      <div style={{ fontSize: 12, marginTop: 10 }}>{alerta}</div>
      <button onClick={() => onOpen(row.supervisor)} style={{
        marginTop: 14, width: "100%", padding: "8px 0", borderRadius: 8, cursor: "pointer",
        border: "1px solid var(--line-strong)", background: "#fff",
        font: "var(--w-semibold) 13px var(--font-sans)", color: "var(--ink-700)",
      }}>Ver mis vendedores →</button>
    </div>
  );
}

function SupervisorView({ data, onOpenVendedor }) {
  const { V, Z } = data;
  const [sel, setSel] = React.useState(null);

  const resumen = Z.map((z) => {
    const reps = V.filter((r) => r.supervisor === z.supervisor);
    return {
      supervisor: z.supervisor, grupo: z.grupo, rb: z.rb, permEgreso: z.permEgreso,
      activos: reps.length,
      criticos: reps.filter((r) => r.nivel === "critico").length,
      altos: reps.filter((r) => r.nivel === "alto").length,
      scoreMax: Math.max(0, ...reps.map((r) => r.score)),
    };
  }).sort((a, b) => b.scoreMax - a.scoreMax);

  if (!sel) {
    return (
      <div>
        <div style={{ font: "var(--w-black) 22px var(--font-sans)", color: "var(--ink-900)", marginBottom: 4 }}>👤 Por supervisor</div>
        <div style={{ fontSize: 14, color: "var(--ink-400)", marginBottom: 22 }}>Cada supervisor ve solo sus vendedores. Clic en una tarjeta para entrar.</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
          {resumen.map((row) => <SupCard key={row.supervisor} row={row} onOpen={setSel} />)}
        </div>
      </div>
    );
  }

  // detail
  const reps = V.filter((r) => r.supervisor === sel).sort((a, b) => b.score - a.score);
  const z = Z.find((x) => x.supervisor === sel);
  const nivelZona = zonaNivel(z.rb);
  const nCrit = reps.filter((r) => r.nivel === "critico").length;
  const nAlto = reps.filter((r) => r.nivel === "alto").length;
  const nOnb = reps.filter((r) => r.meses <= 3).length;

  return (
    <div>
      <button onClick={() => setSel(null)} style={{
        marginBottom: 16, padding: "6px 14px", borderRadius: 8, cursor: "pointer",
        border: "1px solid var(--line-strong)", background: "#fff",
        font: "var(--w-semibold) 13px var(--font-sans)", color: "var(--ink-600)",
      }}>← Todas las zonas</button>
      <div style={{ font: "var(--w-black) 22px var(--font-sans)", color: "var(--ink-900)" }}>👤 {sel}</div>
      <div style={{ fontSize: 14, color: "var(--ink-400)", marginTop: 4, marginBottom: 18 }}>
        Zona: <b style={{ color: "var(--ink-900)" }}>{z.grupo}</b> &nbsp;·&nbsp; <Badge nivel={nivelZona} label={zonaLabel(z.rb)} />
      </div>

      {z.rb > 0.60 && (
        <div style={{
          background: "var(--orange-bg)", border: "1px solid #f3d9a8", borderRadius: 8,
          padding: "12px 16px", marginBottom: 20, fontSize: 13, color: "#7a4a00",
        }}>⚠️ <b>{z.grupo}</b> es una zona con alta rotación histórica. Los vendedores nuevos aquí tienen mayor probabilidad de irse antes de los 6 meses.</div>
      )}

      <div style={{ display: "flex", gap: 14, marginBottom: 24 }}>
        <KpiCard value={reps.length} label="Vendedores activos" sub="En tu zona" />
        <KpiCard value={nCrit + nAlto} valueColor="var(--red-accent)" accent="red" label="Requieren atención" sub={`${nCrit} crítico${nCrit !== 1 ? "s" : ""} · ${nAlto} alto${nAlto !== 1 ? "s" : ""}`} />
        <KpiCard value={`${z.permEgreso.toFixed(1).replace(".", ",")}m`} accent="orange" label="Permanencia prom. zona" sub="Duración al egreso" />
        <KpiCard value={nOnb} valueColor="var(--blue-accent)" accent="blue" label="En onboarding" sub="Primeros 3 meses" />
      </div>

      <SectionHeader>📋 Mis vendedores por score de riesgo</SectionHeader>
      <VendedorTable rows={reps} onOpen={onOpenVendedor} />
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 8 }}>{reps.length} vendedores en {z.grupo}</div>
    </div>
  );
}

Object.assign(window, { SupervisorView });
