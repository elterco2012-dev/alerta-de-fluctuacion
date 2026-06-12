/* Würth Rotación UI kit — shared primitives + helpers.
   Faithful ports of the dashboard's CSS-in-Python components. */

const NIVEL_LABEL = { critico: "Crítico", alto: "Alto", medio: "Medio", bajo: "Bajo" };

function fmtAntiguedad(m) {
  if (m < 12) return `${m} mes${m !== 1 ? "es" : ""}`;
  const a = Math.floor(m / 12), r = m % 12;
  let s = `${a} año${a !== 1 ? "s" : ""}`;
  if (r) s += ` y ${r} mes${r !== 1 ? "es" : ""}`;
  return s;
}
function fmtPesos(n) {
  return "$" + Math.round(n).toLocaleString("es-AR").replace(/,/g, ".");
}
// ---- #3 unified number formatting (one rule set, used everywhere) ----
// pesos abreviados para titulares: $1,4 M / $980 mil
function fmtPesosCorto(n) {
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(1).replace(".", ",") + " M";
  if (n >= 1e3) return "$" + Math.round(n / 1e3) + " mil";
  return "$" + Math.round(n);
}
function fmtPct(n, dec = 0) {
  return n.toFixed(dec).replace(".", ",") + "%";
}
function fmtNum(n, dec = 0) {
  return n.toFixed(dec).replace(".", ",");
}
function fmtMeses(n) {
  return fmtNum(n, 1) + " m";
}
// signed delta with the product's tendency glyph (▲ worse, ▼ better when invert)
function fmtDelta(n, { invert = false, dec = 1 } = {}) {
  if (!n) return "=";
  const up = n > 0;
  const glyph = up ? "▲" : "▼";
  return glyph + " " + fmtNum(Math.abs(n), dec);
}
function zonaNivel(rb) {
  if (rb > 0.60) return "critico";
  if (rb > 0.45) return "alto";
  if (rb > 0.30) return "medio";
  return "bajo";
}
function zonaLabel(rb) {
  return { critico: "rot alta", alto: "rot alta", medio: "rot media", bajo: "rot baja" }[zonaNivel(rb)];
}

// ---- Card ----
function Card({ children, style, pad = true }) {
  return (
    <div style={{
      background: "var(--surface)", borderRadius: "var(--radius-card)",
      padding: pad ? "var(--pad-card)" : 0, boxShadow: "var(--shadow-card)", ...style,
    }}>{children}</div>
  );
}

// ---- Section header ----
function SectionHeader({ children, note }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "8px 0 14px" }}>
      <span style={{ font: "var(--w-bold) var(--t-section) var(--font-sans)", color: "var(--ink-900)" }}>{children}</span>
      {note && <span style={{ font: "var(--w-regular) var(--t-sub) var(--font-sans)", color: "var(--ink-400)" }}>{note}</span>}
    </div>
  );
}

// ---- Score circle ----
function ScoreCircle({ score, nivel, size = 36 }) {
  const c = {
    critico: ["var(--red-bg)", "var(--red-text)", "var(--red-accent)"],
    alto:    ["var(--orange-bg)", "var(--orange-text)", "var(--orange-accent)"],
    medio:   ["var(--blue-bg)", "var(--blue-text)", "var(--blue-accent)"],
    bajo:    ["var(--green-bg)", "var(--green-text)", "var(--green-accent)"],
  }[nivel] || ["#f0f0f0", "#999", "#ccc"];
  return (
    <div title={NIVEL_LABEL[nivel]} style={{
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      width: size, height: size, borderRadius: "50%", fontWeight: 800,
      fontSize: size * 0.42, fontFamily: "var(--font-sans)",
      background: c[0], color: c[1], border: `2px solid ${c[2]}`,
    }}>{score}</div>
  );
}

// ---- Pill (signal tag) ----
function Pill({ label, color }) {
  const c = {
    red:    ["var(--red-bg)", "var(--red-text)"],
    orange: ["var(--orange-bg)", "var(--orange-text)"],
    yellow: ["var(--yellow-bg)", "var(--yellow-text)"],
  }[color] || ["var(--yellow-bg)", "var(--yellow-text)"];
  return (
    <span style={{
      display: "inline-block", padding: "2px 8px", borderRadius: "var(--radius-pill)",
      fontSize: 11, fontWeight: 600, margin: "1px 2px", whiteSpace: "nowrap",
      fontFamily: "var(--font-sans)", background: c[0], color: c[1],
    }}>{label}</span>
  );
}
function Pills({ senales }) {
  if (!senales || !senales.length)
    return <span style={{ color: "var(--ink-150)", fontSize: 12 }}>Sin alertas</span>;
  return <span>{senales.map((s, i) => <Pill key={i} label={s[0]} color={s[1]} />)}</span>;
}

// ---- Accessibility: distinct SHAPE per risk level so meaning survives w/o color ----
const NIVEL_SHAPE = { critico: "▲", alto: "◆", medio: "■", bajo: "●" };

// ---- Badge ----
// `shape` (default true for risk levels) prepends the level glyph so color-blind
// users distinguish levels by form, not hue alone.
function Badge({ nivel, label, kind, shape }) {
  const map = {
    critico: ["var(--red-bg)", "var(--red-text)"],
    alto:    ["var(--orange-bg)", "var(--orange-text)"],
    medio:   ["var(--blue-bg)", "var(--blue-text)"],
    bajo:    ["var(--green-bg)", "var(--green-text)"],
    tipo:    ["var(--purple-bg)", "var(--purple-text)"],
  };
  const key = kind || nivel;
  const c = map[key] || map.medio;
  const showShape = shape !== false && NIVEL_SHAPE[key];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4, padding: "2px 8px", borderRadius: "var(--radius-badge)",
      fontSize: 11, fontWeight: 600, fontFamily: "var(--font-sans)", whiteSpace: "nowrap",
      background: c[0], color: c[1],
    }}>
      {showShape && <span aria-hidden="true" style={{ fontSize: 8, lineHeight: 1 }}>{NIVEL_SHAPE[key]}</span>}
      {label || NIVEL_LABEL[nivel]}
    </span>
  );
}

// ---- Sparkline ----
function Sparkline({ vals }) {
  if (!vals || !vals.length) return <span>—</span>;
  const cap = Math.max(...vals, 100);
  return (
    <div style={{ display: "inline-flex", alignItems: "flex-end", gap: 3, height: 24 }}>
      {vals.map((v, i) => {
        const h = Math.max(3, Math.round((v / cap) * 22));
        const c = v >= 90 ? "var(--green-accent)" : v >= 70 ? "var(--orange-accent)" : "var(--red-accent)";
        return <div key={i} style={{ width: 9, borderRadius: "2px 2px 0 0", height: h, background: c }} />;
      })}
    </div>
  );
}

// ---- KPI card ----
function KpiCard({ value, label, sub, accent, valueColor }) {
  const border = {
    red: "var(--red-accent)", orange: "var(--orange-accent)",
    blue: "var(--blue-accent)", green: "var(--green-accent)",
  }[accent] || "var(--border-idle)";
  return (
    <div style={{
      flex: 1, minWidth: 0, background: "var(--surface)", borderRadius: "var(--radius-card)",
      padding: "var(--pad-card-y) var(--pad-card-x)", boxShadow: "var(--shadow-card)",
      borderLeft: `var(--accent-border) solid ${border}`,
      display: "flex", flexDirection: "column",
    }}>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 30, lineHeight: 1.1, color: valueColor || "var(--ink-900)" }}>{value}</div>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 12, lineHeight: 1.35, color: "var(--ink-700)", marginTop: 6 }}>{label}</div>
      {sub && <div style={{ fontFamily: "var(--font-sans)", fontWeight: 400, fontSize: 11, lineHeight: 1.35, color: "var(--ink-300)", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

// ---- Top nav ----
function TopNav({ current, onNav }) {
  const items = [
    ["inicio", "🏠 Inicio"], ["supervisor", "👤 Por supervisor"],
    ["intervenciones", "📝 Intervenciones"], ["historial", "📈 Historial"],
    ["costo", "💰 Costo de rotación"], ["actividad", "📞 Actividad"],
  ];
  return (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      marginBottom: 20, paddingBottom: 14, borderBottom: "1px solid var(--line)",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
        <span style={{ fontSize: 20 }}>🔔</span>
        <span style={{ font: "var(--w-black) var(--t-header) var(--font-sans)", color: "var(--ink-900)" }}>
          Würth Argentina — Alertas de Rotación
        </span>
      </div>
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {items.map(([k, label]) => (
          <a key={k} onClick={() => onNav(k)} style={{
            font: "var(--w-regular) var(--t-table) var(--font-sans)", cursor: "pointer",
            whiteSpace: "nowrap", textDecoration: "none",
            color: current === k ? "var(--ink-900)" : "var(--blue-accent)",
            fontWeight: current === k ? 700 : 400,
          }}>{label}</a>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, {
  fmtAntiguedad, fmtPesos, fmtPesosCorto, fmtPct, fmtNum, fmtMeses, fmtDelta, zonaNivel, zonaLabel, NIVEL_LABEL, NIVEL_SHAPE,
  Card, SectionHeader, ScoreCircle, Pill, Pills, Badge, Sparkline, KpiCard, TopNav,
});
