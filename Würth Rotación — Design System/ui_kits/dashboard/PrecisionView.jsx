/* Precisión del modelo (#1) — does the risk score actually predict who leaves?
   Confusion matrix over last month's cohort + recall/precision, framed in plain
   language. This is the screen that validates the whole product. */

function PrecisionView({ data }) {
  const P = data.PREDICCION;
  const { vp, fn, fp, vn, fp_intervenidos, periodo } = P;
  const totalFugas = vp + fn;
  const totalMarcados = vp + fp;
  const recall = Math.round((vp / totalFugas) * 100);            // % de fugas que anticipamos
  const precision = Math.round((vp / totalMarcados) * 100);      // % de marcados que se fueron
  const fpReales = fp - fp_intervenidos;                          // falsos positivos no explicados por intervención
  const total = vp + fn + fp + vn;
  const accuracy = Math.round(((vp + vn) / total) * 100);

  const Cell = ({ n, label, tone, big }) => {
    const map = {
      good: ["var(--green-bg)", "var(--green-text)", "#cfe6b8"],
      bad: ["var(--red-bg)", "var(--red-text)", "#f4cfcd"],
      warn: ["var(--orange-bg)", "var(--orange-text)", "#f3d9a8"],
      neutral: ["var(--table-head-bg)", "var(--ink-600)", "var(--line-strong)"],
    }[tone];
    return (
      <div style={{ background: map[0], border: `1px solid ${map[2]}`, borderRadius: 10, padding: "16px 18px" }}>
        <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: big ? 34 : 30, color: map[1], lineHeight: 1 }}>{n}</div>
        <div style={{ fontFamily: "var(--font-sans)", fontSize: 12.5, color: map[1], marginTop: 6, lineHeight: 1.4 }}>{label}</div>
      </div>
    );
  };

  return (
    <div>
      <V2Banner emoji="🎯" tone={recall >= 75 ? "green" : "orange"}
        title={`El modelo anticipó ${recall}% de las fugas del mes`}
        sub={`De ${totalFugas} vendedores que se fueron en ${periodo}, ${vp} estaban marcados en riesgo el mes anterior. Esto valida que el score sirve para actuar a tiempo.`}
        cta="Ver detalle →" />

      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <HeroStat label="Sensibilidad (recall)" value={fmtPct(recall)} accent="var(--green-accent)" valueColor="var(--green-text)">
          <div style={{ fontSize: 12, color: "var(--ink-500)" }}>{vp} de {totalFugas} fugas fueron anticipadas por el score</div>
        </HeroStat>
        <V2Card style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
          <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14, color: "var(--ink-900)", marginBottom: 14 }}>Precisión de las alertas</div>
          <div style={{ display: "flex", gap: 24 }}>
            <div><div style={{ fontWeight: 800, fontSize: 30, color: "var(--ink-900)" }}>{fmtPct(precision)}</div><div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 2, maxWidth: 150, lineHeight: 1.4 }}>de los marcados realmente se fue</div></div>
            <div><div style={{ fontWeight: 800, fontSize: 30, color: "var(--green-text)" }}>{fp_intervenidos}</div><div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 2, maxWidth: 160, lineHeight: 1.4 }}>marcados que retuvimos tras intervenir (no son errores)</div></div>
            <div><div style={{ fontWeight: 800, fontSize: 30, color: "var(--ink-900)" }}>{fmtPct(accuracy)}</div><div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 2, maxWidth: 140, lineHeight: 1.4 }}>precisión global del modelo</div></div>
          </div>
        </V2Card>
      </div>

      <V2Section title="📊 Predicción vs. resultado real" right={<span style={{ fontSize: 12, color: "var(--ink-400)" }}>Cohorte de {periodo} · {total} vendedores activos</span>} />
      <V2Card style={{ marginBottom: 10 }}>
        <div style={{ display: "grid", gridTemplateColumns: "120px 1fr 1fr", gap: 12, alignItems: "stretch" }}>
          <div />
          <div style={{ textAlign: "center", fontSize: 12, fontWeight: 700, color: "var(--ink-500)", paddingBottom: 4 }}>Se fue ✓</div>
          <div style={{ textAlign: "center", fontSize: 12, fontWeight: 700, color: "var(--ink-500)", paddingBottom: 4 }}>Se quedó</div>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", fontSize: 12, fontWeight: 700, color: "var(--ink-500)", textAlign: "right", paddingRight: 4 }}>Marcado en riesgo ▲</div>
          <Cell n={vp} tone="good" big label="Acertado — lo vimos venir y pudimos actuar" />
          <Cell n={fp} tone="warn" label={`Marcado pero retenido — ${fp_intervenidos} salvados por intervención, ${fpReales} falsa alarma`} />

          <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", fontSize: 12, fontWeight: 700, color: "var(--ink-500)", textAlign: "right", paddingRight: 4 }}>No marcado</div>
          <Cell n={fn} tone="bad" big label="Fuga sorpresa — el modelo NO la anticipó. Acá hay que mejorar." />
          <Cell n={vn} tone="neutral" label="Correcto — sin alerta y se quedó" />
        </div>
      </V2Card>
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginBottom: 32, lineHeight: 1.5 }}>
        Leé las filas como “qué dijo el modelo” y las columnas como “qué pasó de verdad”. La celda roja (fugas no anticipadas) es la que querés llevar a cero — son las {fn} personas que se fueron sin que saltara la alerta.
      </div>

      <V2Section title="🔍 ¿Dónde falló el modelo?" />
      <V2Card>
        <div style={{ display: "flex", gap: 28, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 240 }}>
            <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13, color: "var(--red-text)", marginBottom: 6 }}>▲ {fn} fugas sorpresa</div>
            <div style={{ fontSize: 13, color: "var(--ink-600)", lineHeight: 1.6 }}>Vendedores que se fueron sin alerta previa. Patrón común: renuncias rápidas en el mes 1-2, antes de que el score acumule señales. <b>Sugerencia:</b> dar más peso a la inactividad temprana.</div>
          </div>
          <div style={{ flex: 1, minWidth: 240 }}>
            <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13, color: "var(--green-text)", marginBottom: 6 }}>✓ {fp_intervenidos} retenciones</div>
            <div style={{ fontSize: 13, color: "var(--ink-600)", lineHeight: 1.6 }}>Marcados como riesgo que <b>no</b> se fueron — y la mayoría tuvo una intervención. No son errores del modelo: son los casos donde actuar funcionó. El sistema se paga solo acá.</div>
          </div>
        </div>
      </V2Card>
      <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 10 }}>Datos simulados de validación. En producción se calcula comparando el snapshot de score del mes anterior con las bajas efectivas del mes.</div>
    </div>
  );
}

Object.assign(window, { PrecisionView });
