/* Feature demos: #6 weekly digest · #7 mobile view · #5 loading/error/empty states. */

// ---------- #6 Resumen semanal (digest) ----------
function DigestView({ data, onOpenVendedor }) {
  const { V } = data;
  const reunion = V.filter((r) => r.nivel === "critico").sort((a, b) => b.score - a.score);
  const escalaron = V.filter((r) => r._delta > 0).sort((a, b) => b._delta - a._delta).slice(0, 4);
  const mejoraron = V.filter((r) => r._delta < 0).sort((a, b) => a._delta - b._delta).slice(0, 3);

  const Row = ({ r, right }) => (
    <div onClick={() => onOpenVendedor && onOpenVendedor(r)} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: "1px solid var(--line-faint)", cursor: "pointer" }}>
      <ScoreCircle score={r.score} nivel={r.nivel} size={32} />
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 700, fontSize: 13, color: "var(--ink-900)" }}>{r.nombre}</div>
        <div style={{ fontSize: 11, color: "var(--ink-400)" }}>{r.tipo} · {fmtAntiguedad(r.meses)} · {r.grupo}</div>
      </div>
      {right}
    </div>
  );

  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <V2Card style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "22px 26px", background: "var(--ink-900)", color: "#fff" }}>
          <div style={{ fontSize: 12, opacity: .7, letterSpacing: ".04em", textTransform: "uppercase" }}>🔔 Würth Argentina · Resumen semanal</div>
          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 22, marginTop: 6 }}>Tu equipo esta semana</div>
          <div style={{ fontSize: 13, opacity: .8, marginTop: 4 }}>Semana del 27 ene – 2 feb · enviado los lunes 8:00</div>
        </div>
        <div style={{ padding: "20px 26px" }}>
          <div style={{ display: "flex", gap: 12, marginBottom: 22 }}>
            <div style={{ flex: 1, padding: "12px 14px", borderRadius: 10, background: "var(--red-bg)" }}>
              <div style={{ fontWeight: 800, fontSize: 24, color: "var(--red-text)" }}>{reunion.length}</div>
              <div style={{ fontSize: 12, color: "var(--red-text)" }}>necesitan reunión</div>
            </div>
            <div style={{ flex: 1, padding: "12px 14px", borderRadius: 10, background: "var(--orange-bg)" }}>
              <div style={{ fontWeight: 800, fontSize: 24, color: "var(--orange-text)" }}>{escalaron.length}</div>
              <div style={{ fontSize: 12, color: "var(--orange-text)" }}>escalaron de score</div>
            </div>
            <div style={{ flex: 1, padding: "12px 14px", borderRadius: 10, background: "var(--green-bg)" }}>
              <div style={{ fontWeight: 800, fontSize: 24, color: "var(--green-text)" }}>{mejoraron.length}</div>
              <div style={{ fontSize: 12, color: "var(--green-text)" }}>mejoraron</div>
            </div>
          </div>

          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14, color: "var(--red-text)", marginBottom: 4 }}>🔴 Reuní a estos vendedores esta semana</div>
          {reunion.map((r) => <Row key={r.id} r={r} right={<AccionTag nivel={r.nivel} />} />)}

          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14, color: "var(--orange-text)", margin: "20px 0 4px" }}>▲ Empeoraron respecto a la semana pasada</div>
          {escalaron.map((r) => <Row key={r.id} r={r} right={<ScoreDelta delta={r._delta} />} />)}

          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14, color: "var(--green-text)", margin: "20px 0 4px" }}>▼ Buenas noticias — mejoraron</div>
          {mejoraron.map((r) => <Row key={r.id} r={r} right={<ScoreDelta delta={r._delta} />} />)}

          <button style={{ marginTop: 22, width: "100%", padding: "12px 0", borderRadius: 8, border: "none", cursor: "pointer", background: "var(--red-accent)", color: "#fff", fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14 }}>Abrir el dashboard completo →</button>
        </div>
      </V2Card>
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 12, textAlign: "center" }}>Se envía por mail a cada supervisor con solo sus vendedores. Empuja la acción sin depender de que entren al dashboard.</div>
    </div>
  );
}

// ---------- #7 Mobile (viajantes en la ruta) ----------
function MobileView({ data }) {
  const { V } = data;
  const reps = [...V].filter((r) => r.supervisor === "Rodríguez, A.").sort((a, b) => b.score - a.score);
  const fallback = !window.IOSDevice;

  const list = (
    <div style={{ background: "#f4f5f7", minHeight: "100%" }}>
      <div style={{ padding: "8px 16px 12px" }}>
        <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 24, color: "var(--ink-900)" }}>Mis vendedores</div>
        <div style={{ fontSize: 13, color: "var(--ink-400)", marginTop: 2 }}>Centro · Rodríguez, A.</div>
      </div>
      <div style={{ display: "flex", gap: 8, padding: "0 16px 12px" }}>
        <div style={{ flex: 1, background: "#fff", borderRadius: 10, padding: "10px 12px", boxShadow: "var(--shadow-card)" }}>
          <div style={{ fontWeight: 800, fontSize: 20, color: "var(--red-accent)" }}>{reps.filter((r) => r.nivel === "critico").length}</div>
          <div style={{ fontSize: 11, color: "var(--ink-400)" }}>críticos</div>
        </div>
        <div style={{ flex: 1, background: "#fff", borderRadius: 10, padding: "10px 12px", boxShadow: "var(--shadow-card)" }}>
          <div style={{ fontWeight: 800, fontSize: 20, color: "var(--ink-900)" }}>{reps.length}</div>
          <div style={{ fontSize: 11, color: "var(--ink-400)" }}>activos</div>
        </div>
      </div>
      <div style={{ padding: "0 16px 24px", display: "flex", flexDirection: "column", gap: 10 }}>
        {reps.map((r) => {
          const cc = { critico: "var(--red-accent)", alto: "var(--orange-accent)", medio: "var(--blue-accent)", bajo: "var(--green-accent)" }[r.nivel];
          return (
            <div key={r.id} style={{ background: "#fff", borderRadius: 12, padding: "14px 16px", boxShadow: "var(--shadow-card)", borderLeft: `4px solid ${cc}` }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <ScoreCircle score={r.score} nivel={r.nivel} size={40} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 15, color: "var(--ink-900)" }}>{r.nombre}</div>
                  <div style={{ fontSize: 12, color: "var(--ink-400)" }}>{r.tipo} · {fmtAntiguedad(r.meses)}</div>
                </div>
                <ScoreDelta delta={r._delta} />
              </div>
              <div style={{ marginTop: 10 }}><AccionTag nivel={r.nivel} /></div>
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <div style={{ display: "flex", gap: 36, alignItems: "center", justifyContent: "center", flexWrap: "wrap", padding: "12px 0" }}>
      {fallback
        ? <div style={{ width: 320, height: 640, overflow: "auto", border: "10px solid #111", borderRadius: 40 }}>{list}</div>
        : <IOSDevice title="">{list}</IOSDevice>}
      <div style={{ maxWidth: 320 }}>
        <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 20, color: "var(--ink-900)", marginBottom: 10 }}>📱 Para viajantes en la ruta</div>
        <div style={{ fontSize: 14, color: "var(--ink-600)", lineHeight: 1.6 }}>
          Los supervisores de campo no están frente a una computadora. Esta vista compacta deja revisar
          <b> "mis vendedores"</b> desde el teléfono: misma jerarquía de riesgo, score con tendencia (▲/▼) y la
          acción sugerida a mano, antes de entrar a ver a un cliente.
        </div>
        <div style={{ marginTop: 16, padding: "12px 14px", borderRadius: 10, background: "var(--blue-bg)", fontSize: 13, color: "var(--blue-text)", lineHeight: 1.5 }}>
          Reusa exactamente los mismos componentes que el dashboard de escritorio — solo cambia el layout a una columna.
        </div>
      </div>
    </div>
  );
}

// ---------- #5 Loading / error / empty states ----------
function SkeletonRow() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 0", borderBottom: "1px solid var(--line-faint)" }}>
      <Skeleton w={36} h={36} r={18} />
      <div style={{ flex: 1 }}><Skeleton w="55%" h={12} /><div style={{ height: 6 }} /><Skeleton w="35%" h={10} /></div>
      <Skeleton w={60} h={20} r={10} />
      <Skeleton w={36} h={36} r={18} />
    </div>
  );
}

function EstadosView() {
  const [state, setState] = React.useState("loading");
  return (
    <div>
      <V2Section title="🧩 Estados de la interfaz" right={
        <div style={{ display: "flex", gap: 8 }}>
          {[["loading", "Cargando"], ["error", "Error"], ["empty", "Vacío"]].map(([k, l]) => (
            <button key={k} onClick={() => setState(k)} style={{ padding: "6px 14px", borderRadius: 8, cursor: "pointer", border: "1px solid", borderColor: state === k ? "var(--blue-accent)" : "var(--line-strong)", background: state === k ? "var(--blue-bg)" : "#fff", color: state === k ? "var(--blue-text)" : "var(--ink-600)", fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: 13 }}>{l}</button>
          ))}
        </div>
      } />
      <V2Card style={{ minHeight: 320 }}>
        {state === "loading" && (
          <div>
            <div style={{ display: "flex", gap: 14, marginBottom: 24 }}>
              {[0, 1, 2, 3].map((i) => <div key={i} style={{ flex: 1 }}><Skeleton w="40%" h={28} /><div style={{ height: 8 }} /><Skeleton w="80%" h={12} /></div>)}
            </div>
            {[0, 1, 2, 3, 4].map((i) => <SkeletonRow key={i} />)}
            <div style={{ fontSize: 12, color: "var(--ink-300)", marginTop: 14, textAlign: "center" }}>Cargando datos del mes… los skeletons evitan el "salto" de layout.</div>
          </div>
        )}
        {state === "error" && (
          <div style={{ textAlign: "center", padding: "48px 22px" }}>
            <div style={{ fontSize: 34, marginBottom: 10 }}>⚠️</div>
            <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 16, color: "var(--ink-900)" }}>No se pudo conectar a la base de datos</div>
            <div style={{ fontSize: 13, color: "var(--ink-500)", marginTop: 6, maxWidth: 420, marginLeft: "auto", marginRight: "auto", lineHeight: 1.5 }}>
              Los datos mostrados pueden estar desactualizados. Reintentá en unos minutos o avisá a sistemas si persiste.
            </div>
            <button onClick={() => setState("loading")} style={{ marginTop: 18, padding: "10px 22px", borderRadius: 8, border: "none", cursor: "pointer", background: "var(--ink-900)", color: "#fff", fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13 }}>↻ Reintentar</button>
          </div>
        )}
        {state === "empty" && (
          <div style={{ textAlign: "center", padding: "48px 22px" }}>
            <div style={{ fontSize: 34, marginBottom: 10 }}>✓</div>
            <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 16, color: "var(--green-text)" }}>No hay vendedores en riesgo 🎉</div>
            <div style={{ fontSize: 13, color: "var(--ink-500)", marginTop: 6, maxWidth: 420, marginLeft: "auto", marginRight: "auto", lineHeight: 1.5 }}>
              Ningún vendedor superó el umbral de alerta este mes. Buen trabajo del equipo de supervisión.
            </div>
          </div>
        )}
      </V2Card>
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 10 }}>Tres estados que el dashboard real necesita y hoy no tiene: carga, error de conexión y vacío.</div>
    </div>
  );
}

Object.assign(window, { DigestView, MobileView, EstadosView });
