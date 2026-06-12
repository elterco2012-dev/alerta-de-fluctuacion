/* Shared v2 building blocks used across the "propuesta profesional" screens.
   Applies the same language as InicioV2: hero stat, secondary strip, clean
   section header, empty states. Reuses primitives.jsx. */

// big dominant stat card with a colored top-border
function HeroStat({ label, value, unit, accent = "var(--red-accent)", valueColor, children }) {
  return (
    <div style={{
      flex: "0 0 320px", background: "var(--surface)", borderRadius: 14,
      padding: "22px 24px", boxShadow: "var(--shadow-card)",
      borderTop: `4px solid ${accent}`, display: "flex", flexDirection: "column",
    }}>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13, color: "var(--ink-600)", textTransform: "uppercase", letterSpacing: ".04em" }}>{label}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 8 }}>
        <span style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 56, lineHeight: 1, color: valueColor || "var(--ink-900)" }}>{value}</span>
        {unit && <span style={{ fontFamily: "var(--font-sans)", fontSize: 16, color: "var(--ink-400)" }}>{unit}</span>}
      </div>
      {children && <div style={{ marginTop: 16 }}>{children}</div>}
    </div>
  );
}

// secondary, de-emphasised stat (inside a strip)
function StatItem({ value, label }) {
  return (
    <div style={{ flex: 1, padding: "4px 2px" }}>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 26, color: "var(--ink-900)" }}>{value}</div>
      <div style={{ fontFamily: "var(--font-sans)", fontSize: 12, color: "var(--ink-400)", marginTop: 2 }}>{label}</div>
    </div>
  );
}
function StatStrip({ children }) {
  return (
    <div style={{ display: "flex", gap: 0, padding: "0 4px 18px", marginBottom: 36, borderBottom: "1px solid var(--line-faint)" }}>{children}</div>
  );
}

// section header with optional right-aligned note/callout
function V2Section({ title, right, style }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12, ...style }}>
      <span style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 16, color: "var(--ink-900)" }}>{title}</span>
      {right}
    </div>
  );
}

// callout banner (action of the day / context)
function V2Banner({ emoji, title, sub, cta, onCta, tone = "red" }) {
  const map = {
    red:    ["var(--red-bg)", "#f4cfcd", "var(--red-text)", "#8a3331", "var(--red-accent)"],
    orange: ["var(--orange-bg)", "#f3d9a8", "var(--orange-text)", "#7a4a00", "var(--orange-accent)"],
    blue:   ["var(--blue-bg)", "#bcdcf5", "var(--blue-text)", "#2f5e86", "var(--blue-accent)"],
    green:  ["var(--green-bg)", "#cfe6b8", "var(--green-text)", "#3f6326", "var(--green-accent)"],
  }[tone];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 20px", borderRadius: 12, background: map[0], border: `1px solid ${map[1]}`, marginBottom: 28 }}>
      <span style={{ fontSize: 22 }}>{emoji}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontFamily: "var(--font-sans)", fontWeight: 800, fontSize: 16, color: map[2] }}>{title}</div>
        {sub && <div style={{ fontFamily: "var(--font-sans)", fontSize: 13, color: map[3], marginTop: 2 }}>{sub}</div>}
      </div>
      {cta && <button onClick={onCta} style={{ padding: "9px 18px", borderRadius: 8, border: "none", cursor: "pointer", background: map[4], color: "#fff", fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 13, whiteSpace: "nowrap" }}>{cta}</button>}
    </div>
  );
}

// surface card (rounded 14, no left-border) — v2 default container
function V2Card({ children, style, pad = true }) {
  return (
    <div style={{ background: "var(--surface)", borderRadius: 14, boxShadow: "var(--shadow-card)", padding: pad ? "20px 24px" : 0, ...style }}>{children}</div>
  );
}

// empty state
function V2Empty({ emoji = "✓", title, sub }) {
  return (
    <V2Card style={{ padding: "48px 22px", textAlign: "center" }}>
      <div style={{ fontSize: 30, marginBottom: 8 }}>{emoji}</div>
      <div style={{ fontFamily: "var(--font-sans)", fontWeight: 700, fontSize: 14, color: "var(--green-text)" }}>{title}</div>
      {sub && <div style={{ fontFamily: "var(--font-sans)", fontSize: 13, color: "var(--ink-400)", marginTop: 4 }}>{sub}</div>}
    </V2Card>
  );
}

const ACCION_V2 = {
  critico: ["Reunión esta semana", "var(--red-text)", "var(--red-bg)"],
  alto:    ["Seguimiento activo",  "var(--orange-text)", "var(--orange-bg)"],
  medio:   ["Monitoreo mensual",   "var(--ink-600)", "var(--table-head-bg)"],
  bajo:    ["Seguimiento normal",  "var(--ink-400)", "transparent"],
};
function AccionTag({ nivel }) {
  const [acc, tx, bg] = ACCION_V2[nivel];
  return <span style={{ display: "inline-block", padding: "4px 10px", borderRadius: 7, background: bg, color: tx, fontSize: 12, fontWeight: 700, whiteSpace: "nowrap" }}>{acc}</span>;
}

// shared v2 table chrome
const v2th = { background: "transparent", padding: "0 14px 10px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--ink-400)", textTransform: "uppercase", letterSpacing: ".04em", borderBottom: "2px solid var(--line-strong)" };
const v2td = { padding: "14px", borderBottom: "1px solid var(--line-faint)", verticalAlign: "middle", fontSize: 13 };

// ---- #2 score trajectory: Δ vs previous month (higher score = worse = red) ----
function ScoreDelta({ delta }) {
  if (!delta) return <span style={{ fontSize: 12, color: "var(--ink-300)" }}>=</span>;
  const worse = delta > 0;
  return (
    <span style={{ fontSize: 12, fontWeight: 700, color: worse ? "var(--red-text)" : "var(--green-text)", whiteSpace: "nowrap" }}>
      {worse ? "▲" : "▼"} {Math.abs(delta)}
    </span>
  );
}

// mini line of the 6-month score history (1..10, higher = worse)
function ScoreHistory({ hist, w = 90, h = 30 }) {
  if (!hist || hist.length < 2) return <span>—</span>;
  const max = 10, min = 1, n = hist.length;
  const pts = hist.map((v, i) => {
    const x = (i / (n - 1)) * w;
    const y = h - ((v - min) / (max - min)) * h;
    return [x, y];
  });
  const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  const last = hist[n - 1], prev = hist[n - 2];
  const col = last > prev ? "var(--red-accent)" : last < prev ? "var(--green-accent)" : "var(--ink-300)";
  return (
    <svg width={w} height={h} style={{ display: "block", overflow: "visible" }}>
      <polyline points={pts.map((p) => p.join(",")).join(" ")} fill="none" stroke={col} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={pts[n - 1][0]} cy={pts[n - 1][1]} r="3" fill={col} />
    </svg>
  );
}

// ---- #1 score explainability: weighted factor breakdown ----
function ScoreBreakdown({ vendedor }) {
  const { base, factores } = window.scoreBreakdown(vendedor);
  const maxPeso = 2.0;
  return (
    <div>
      <div style={{ fontSize: 11, color: "var(--ink-400)", textTransform: "uppercase", letterSpacing: ".04em", marginBottom: 10 }}>
        Por qué este score
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 9 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ width: 150, fontSize: 12, color: "var(--ink-500)" }}>Base (todos arrancan en 1)</span>
          <div style={{ flex: 1, height: 14, background: "var(--line-faint)", borderRadius: 4, overflow: "hidden" }}>
            <div style={{ width: `${(base / maxPeso) * 100}%`, height: "100%", background: "var(--ink-200)" }} />
          </div>
          <span style={{ width: 34, textAlign: "right", fontSize: 12, fontWeight: 700, color: "var(--ink-500)" }}>+{base.toFixed(0)}</span>
        </div>
        {factores.map((f) => (
          <div key={f.label} style={{ display: "flex", alignItems: "center", gap: 10 }} title={f.desc}>
            <span style={{ width: 150, fontSize: 12, color: "var(--ink-700)", fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{f.label}</span>
            <div style={{ flex: 1, height: 14, background: "var(--line-faint)", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ width: `${(f.peso / maxPeso) * 100}%`, height: "100%", background: f.peso >= 2 ? "var(--red-accent)" : f.peso >= 1.5 ? "var(--orange-accent)" : "var(--yellow-text)" }} />
            </div>
            <span style={{ width: 34, textAlign: "right", fontSize: 12, fontWeight: 700, color: "var(--ink-700)" }}>+{f.peso.toFixed(1)}</span>
          </div>
        ))}
        {!factores.length && <div style={{ fontSize: 12, color: "var(--ink-400)" }}>Sin señales de riesgo activas — score bajo.</div>}
      </div>
      <div style={{ marginTop: 10, fontSize: 11, color: "var(--ink-300)", lineHeight: 1.5 }}>
        Pasá el mouse sobre cada factor para ver su definición. Pesos del modelo de scoring.
      </div>
    </div>
  );
}

// ---- #5 loading skeleton ----
function Skeleton({ w = "100%", h = 14, r = 6, style }) {
  return <div className="sk" style={{ width: w, height: h, borderRadius: r, ...style }} />;
}

// ---- #4 adjustable density (shared across separately-transpiled files) ----
function setDensity(d) { window.__density = d; window.dispatchEvent(new Event("densitychange")); }
function useDensity() {
  const [d, setD] = React.useState(window.__density || "comodo");
  React.useEffect(() => {
    const h = () => setD(window.__density || "comodo");
    window.addEventListener("densitychange", h);
    return () => window.removeEventListener("densitychange", h);
  }, []);
  return d;
}
// returns the td style for the current density
function tdFor(density) {
  return density === "compacto"
    ? { padding: "7px 14px", borderBottom: "1px solid var(--line-faint)", verticalAlign: "middle", fontSize: 12.5 }
    : { padding: "14px", borderBottom: "1px solid var(--line-faint)", verticalAlign: "middle", fontSize: 13 };
}
function DensityToggle() {
  const d = useDensity();
  return (
    <div style={{ display: "inline-flex", border: "1px solid var(--line-strong)", borderRadius: 8, overflow: "hidden" }}>
      {[["comodo", "Cómodo"], ["compacto", "Compacto"]].map(([k, l]) => (
        <button key={k} onClick={() => setDensity(k)} style={{
          padding: "5px 12px", border: "none", cursor: "pointer",
          background: d === k ? "var(--ink-900)" : "#fff", color: d === k ? "#fff" : "var(--ink-600)",
          fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: 12,
        }}>{l}</button>
      ))}
    </div>
  );
}

Object.assign(window, { HeroStat, StatItem, StatStrip, V2Section, V2Banner, V2Card, V2Empty, AccionTag, ACCION_V2, v2th, v2td, ScoreDelta, ScoreHistory, ScoreBreakdown, Skeleton, setDensity, useDensity, tdFor, DensityToggle });
