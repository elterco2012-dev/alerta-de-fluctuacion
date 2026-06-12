# DESIGN-SYSTEM-FLUCTUACION.md

> **Würth Rotación — Design System · Especificación portable y autosuficiente**
>
> Documento único y exhaustivo para **migrar este design system a otra cuenta** y
> reconstruirlo desde cero. Es la **única fuente de verdad** post-migración: contiene
> todos los tokens (JSON + CSS), el inventario completo de componentes con su código,
> las guías de uso, y un prompt de reconstrucción listo para pegar.
>
> **Producto de origen:** dashboard interno de **Würth Argentina — "Sistema de Alertas
> Tempranas de Rotación"** (detecta vendedores con riesgo de fuga *antes* de que
> renuncien). Stack original: Streamlit + CSS-in-Python. Recreación de referencia: React.
> Repo fuente: `https://github.com/elterco2012-dev/alerta-de-fluctuacion`.
>
> **Idea rectora del sistema:** *riesgo = color*. Todo (vendedor, zona, KPI, badge) lleva
> un nivel de riesgo, y el nivel **es** el color. Cuatro niveles, memorizalos:
> 🔴 Crítico · 🟠 Alto · 🔵 Medio/Info · 🟢 Bajo.

---

## Índice

1. [Tokens de diseño (JSON + CSS)](#1-tokens-de-diseño)
2. [Inventario de componentes](#2-inventario-de-componentes)
3. [Guías de uso y convenciones](#3-guías-de-uso-y-convenciones)
4. [Instrucciones de reconstrucción (prompt)](#4-instrucciones-de-reconstrucción)

---

# 1. TOKENS DE DISEÑO

Hay **dos convenciones de nombres de variables CSS** en el sistema, ambas válidas y con
los **mismos valores hex**:
- **Set A — escala completa** (`colors_and_type.css`): nombres con sufijo de uso
  (`--red-accent`, `--ink-900`, `--t-kpi`, `--radius-card`…). Es la fuente de verdad.
- **Set B — runtime v3** (`dashboard-v3.css`): subconjunto compacto que usan los
  componentes `.wz-*`. Usa `--font` (en vez de `--font-sans`), `--radius`/`--radius-sm`,
  y agrega los tokens de *celda semáforo* (`--cell-*`).

La migración debe incluir **ambos sets** (o unificarlos; ver nota al final de §1).

## 1.1 Colores — JSON

```json
{
  "color": {
    "risk": {
      "critico": { "accent": "#E24B4A", "bg": "#FDECEA", "text": "#B71C1C",
        "note": "rojo · 'actuar esta semana' · también es el rojo de marca Würth" },
      "alto":    { "accent": "#EF9F27", "bg": "#FFF3E0", "text": "#E65100",
        "note": "naranja · 'seguimiento activo'" },
      "medio":   { "accent": "#4A90D9", "bg": "#E3F2FD", "text": "#1565C0",
        "note": "azul · 'monitoreo mensual' · TAMBIÉN es el único color de links" },
      "bajo":    { "accent": "#639922", "bg": "#F1F8E9", "text": "#2E7D32",
        "note": "verde · 'seguimiento normal'" }
    },
    "support": {
      "green-bright": "#27AE60", "green-soft": "#8DB56B",
      "green-pos-bg": "#D4EDDA", "green-pos-tx": "#155724",
      "yellow-bg": "#FFFDE7", "yellow-text": "#F57F17",
      "purple-bg": "#F3E8FF", "purple-text": "#6B21A8"
    },
    "cell": {
      "good-bg": "#D4EDDA", "good-tx": "#155724",
      "warn-bg": "#FFF3CD", "warn-tx": "#856404",
      "bad-bg":  "#FFE0E0", "bad-tx":  "#C0392B"
    },
    "ink": {
      "900": "#1a1a2e", "700": "#333333", "600": "#555555", "500": "#666666",
      "400": "#888888", "300": "#999999", "250": "#aaaaaa", "200": "#bbbbbb", "150": "#cccccc"
    },
    "surface": {
      "surface": "#ffffff", "page-bg": "#ffffff", "table-head-bg": "#f8f9fa",
      "row-hover": "#fafafa"
    },
    "line": {
      "line-strong": "#e9ecef", "line": "#eeeeee", "line-faint": "#f2f2f2",
      "border-idle": "#e0e0e0", "chart-neutral": "#B4B2A9"
    },
    "banner-border": {
      "red": "#f4cfcd", "orange": "#f3d9a8", "blue": "#bcdcf5", "green": "#cfe6b8"
    }
  }
}
```

### Mapa semántico de color (qué hace cada uno)
| Token | Hex | Uso |
|---|---|---|
| `--red-accent` | `#E24B4A` | borde-izq de card, anillo del score circle, barras; **rojo de marca** |
| `--red-bg` / `--red-text` | `#FDECEA` / `#B71C1C` | fondo/texto de pill·badge·circle crítico |
| `--orange-accent/-bg/-text` | `#EF9F27` / `#FFF3E0` / `#E65100` | nivel Alto |
| `--blue-accent/-bg/-text` | `#4A90D9` / `#E3F2FD` / `#1565C0` | nivel Medio/Info + **links** |
| `--green-accent/-bg/-text` | `#639922` / `#F1F8E9` / `#2E7D32` | nivel Bajo / OK |
| `--green-bright` | `#27AE60` | punto "dato fresco", barras positivas |
| `--green-soft` | `#8DB56B` | barras "altas" en charts de rotación |
| `--yellow-bg/-text` | `#FFFDE7` / `#F57F17` | pill de menor severidad (`clientes L:0`, `ticket↓`) |
| `--purple-bg/-text` | `#F3E8FF` / `#6B21A8` | **único** badge categórico no-riesgo (tipo de intervención) |
| `--cell-*` | ver JSON | tinte semáforo de celdas en tablas de Actividad |
| `--ink-900 … --ink-150` | `#1a1a2e → #ccc` | escalera de tinta (sin negro puro) |
| `--surface` | `#ffffff` | toda card |
| `--table-head-bg` | `#f8f9fa` | header de tabla (estilo viejo) |
| `--row-hover` | `#fafafa` | hover de fila |
| `--line-strong/-/-faint` | `#e9ecef/#eee/#f2f2f2` | 2px underline / divisor / separador de fila |
| `--border-idle` | `#e0e0e0` | borde-izq de KPI sin riesgo |
| `--chart-neutral` | `#B4B2A9` | barras estables (mes 7-12), de-enfatizadas |

## 1.2 Tipografía — JSON

```json
{
  "font": {
    "family": {
      "sans": "'Source Sans 3', 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      "mono": "'SF Mono', 'Roboto Mono', ui-monospace, Menlo, Consolas, monospace"
    },
    "source": "Google Fonts — family=Source+Sans+3:ital,wght@0,400;0,600;0,700;0,800;1,400&family=Roboto+Mono:wght@400;500",
    "weight": { "regular": 400, "semibold": 600, "bold": 700, "black": 800 },
    "size": {
      "kpi": "30px", "kpi-sm": "26px", "title": "22px", "header": "20px",
      "section": "15px", "body": "14px", "table": "13px", "label": "12px",
      "sub": "11px", "hint": "10px"
    },
    "role": {
      "page-title": { "size": "22px", "weight": 800, "line-height": 1.15, "color": "#1a1a2e" },
      "header":     { "size": "20px", "weight": 800, "line-height": 1.2,  "color": "#1a1a2e" },
      "section":    { "size": "15px", "weight": 700, "line-height": 1.3,  "color": "#1a1a2e" },
      "kpi-value":  { "size": "30px", "weight": 800, "line-height": 1.1,  "color": "#1a1a2e" },
      "kpi-label":  { "size": "12px", "weight": 700, "color": "#333333" },
      "kpi-sub":    { "size": "11px", "weight": 400, "color": "#999999" },
      "body":       { "size": "14px", "weight": 400, "line-height": 1.5,  "color": "#333333" },
      "th":         { "size": "12px", "weight": 600, "color": "#666666" },
      "meta":       { "size": "11px", "weight": 400, "color": "#aaaaaa" },
      "hero-value": { "size": "56px", "weight": 800, "line-height": 1, "note": "KPI hero v3" }
    }
  }
}
```

**Regla tipográfica clave:** una sola familia (Source Sans 3). **La jerarquía la hace el
peso (800→700→400) y el tamaño, NUNCA un cambio de familia.** No hay serif ni display.
Desktop-only: tamaños en px, sin escalado rem. La mono (`Roboto Mono`) solo aparece en
etiquetas hex/código de los specimens del design system, no en el producto.

## 1.3 Espaciado, radios, sombras, breakpoints — JSON

```json
{
  "radius": { "card": "12px", "card-sm": "10px", "pill": "10px", "badge": "4px",
    "circle": "50%", "v3-card": "14px", "v3-sm": "10px" },
  "border": { "accent-left": "4px", "note": "borde-izquierdo de color = firma del sistema" },
  "shadow": {
    "card":    "0 1px 4px rgba(0,0,0,0.08)",
    "card-sm": "0 1px 3px rgba(0,0,0,0.07)",
    "note": "una sola elevación, casi plano. Sin sombras internas/coloreadas/grandes."
  },
  "spacing": {
    "pad-card": "20px", "pad-card-y": "18px", "pad-card-x": "22px",
    "pad-page": "2.5rem", "gap-kpi": "14px",
    "scale-observed-px": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 32, 40]
  },
  "breakpoints": {
    "note": "Producto desktop-only; no hay media queries en el core. La vista MÓVIL del UI kit usa un ancho fijo de 320px (frame de iPhone).",
    "mobile-frame": "320px", "deck/artboard-ref": "1280px"
  }
}
```

## 1.4 Tokens como CSS (pegá tal cual)

```css
/* ── Carga de fuentes ── */
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,400;0,600;0,700;0,800;1,400&family=Roboto+Mono:wght@400;500&display=swap');

:root {
  /* COLOR · riesgo (accent / bg / text) */
  --red-accent:#E24B4A;    --red-bg:#FDECEA;    --red-text:#B71C1C;
  --orange-accent:#EF9F27; --orange-bg:#FFF3E0; --orange-text:#E65100;
  --blue-accent:#4A90D9;   --blue-bg:#E3F2FD;   --blue-text:#1565C0;
  --green-accent:#639922;  --green-bg:#F1F8E9;  --green-text:#2E7D32;

  /* COLOR · soporte */
  --green-bright:#27AE60;  --green-soft:#8DB56B;
  --green-pos-bg:#D4EDDA;  --green-pos-tx:#155724;
  --yellow-bg:#FFFDE7;     --yellow-text:#F57F17;
  --purple-bg:#F3E8FF;     --purple-text:#6B21A8;

  /* COLOR · celdas semáforo */
  --cell-good-bg:#D4EDDA;  --cell-good-tx:#155724;
  --cell-warn-bg:#FFF3CD;  --cell-warn-tx:#856404;
  --cell-bad-bg:#FFE0E0;   --cell-bad-tx:#C0392B;

  /* COLOR · tinta (sin negro puro) */
  --ink-900:#1a1a2e; --ink-700:#333333; --ink-600:#555555; --ink-500:#666666;
  --ink-400:#888888; --ink-300:#999999; --ink-250:#aaaaaa; --ink-200:#bbbbbb; --ink-150:#cccccc;

  /* COLOR · superficies y líneas */
  --surface:#ffffff; --page-bg:#ffffff; --table-head-bg:#f8f9fa; --row-hover:#fafafa;
  --line-strong:#e9ecef; --line:#eeeeee; --line-faint:#f2f2f2;
  --border-idle:#e0e0e0; --chart-neutral:#B4B2A9;

  /* TIPOGRAFÍA */
  --font-sans:'Source Sans 3','Source Sans Pro',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  --font-mono:'SF Mono','Roboto Mono',ui-monospace,Menlo,Consolas,monospace;
  --font:var(--font-sans); /* alias usado por componentes .wz-* */
  --w-regular:400; --w-semibold:600; --w-bold:700; --w-black:800;
  --t-kpi:30px; --t-kpi-sm:26px; --t-title:22px; --t-header:20px; --t-section:15px;
  --t-body:14px; --t-table:13px; --t-label:12px; --t-sub:11px; --t-hint:10px;

  /* FORMA · radios */
  --radius-card:12px; --radius-card-sm:10px; --radius-pill:10px; --radius-badge:4px; --radius-circle:50%;
  --radius:14px; --radius-sm:10px; /* alias v3 */

  /* FORMA · borde de acento (firma del sistema) */
  --accent-border:4px;

  /* ELEVACIÓN */
  --shadow-card:0 1px 4px rgba(0,0,0,0.08);
  --shadow-card-sm:0 1px 3px rgba(0,0,0,0.07);

  /* ESPACIADO */
  --pad-card:20px; --pad-card-y:18px; --pad-card-x:22px; --pad-page:2.5rem; --gap-kpi:14px;
}

/* ── Roles de tipografía (clases utilitarias) ── */
.ds-page-title { font: var(--w-black) var(--t-title)/1.15 var(--font-sans); color: var(--ink-900); }
.ds-header     { font: var(--w-black) var(--t-header)/1.2 var(--font-sans); color: var(--ink-900); }
.ds-section    { font: var(--w-bold) var(--t-section)/1.3 var(--font-sans); color: var(--ink-900);
                 display: flex; align-items: center; gap: 6px; }
.ds-kpi-value  { font: var(--w-black) var(--t-kpi)/1.1 var(--font-sans); color: var(--ink-900); }
.ds-kpi-label  { font: var(--w-bold) var(--t-label) var(--font-sans); color: var(--ink-700); }
.ds-kpi-sub    { font: var(--w-regular) var(--t-sub) var(--font-sans); color: var(--ink-300); }
.ds-body       { font: var(--w-regular) var(--t-body)/1.5 var(--font-sans); color: var(--ink-700); }
.ds-th         { font: var(--w-semibold) var(--t-label) var(--font-sans); color: var(--ink-500); }
.ds-meta       { font: var(--w-regular) var(--t-sub) var(--font-sans); color: var(--ink-250); }
```

> **Nota de unificación:** Set A (`--font-sans`, `--radius-card`) y Set B (`--font`,
> `--radius`) coexisten porque el sistema creció en dos capas. El bloque de arriba ya
> define **ambos** + alias, así que es seguro de migrar sin tocar componentes. Si querés
> consolidar, conservá Set A como canónico y dejá los alias `--font`/`--radius`/`--radius-sm`.

---

# 2. INVENTARIO DE COMPONENTES

El sistema tiene **dos expresiones del mismo lenguaje visual**, ambas incluidas y
exhaustivas:

- **2.A — Primitivos React** (recreación/UI-kit y prototipos HTML): componentes JSX que
  leen los tokens vía `var(--…)`.
- **2.B — Componentes `.wz-*`** (handoff a Streamlit/HTML): clases CSS + helpers Python
  que rinden el **mismo** diseño en el producto real.

Para cada componente: propósito, variantes, estados y **código completo**.

## 2.A Primitivos React (`primitives.jsx`)

Todos exportan a `window` al final (para compartir scope entre scripts Babel). Helpers de
formato incluidos al final de §2.A.

### 2.A.1 `Card`
**Propósito:** contenedor atómico. Fondo blanco, radio 12, sombra suave. **Variantes:**
`pad` (true → padding 20px; false → 0, para tablas full-bleed). **Estados:** ninguno (estático).

```jsx
function Card({ children, style, pad = true }) {
  return (
    <div style={{
      background: "var(--surface)", borderRadius: "var(--radius-card)",
      padding: pad ? "var(--pad-card)" : 0, boxShadow: "var(--shadow-card)", ...style,
    }}>{children}</div>
  );
}
```

### 2.A.2 `SectionHeader`
**Propósito:** título de sección con emoji + nota opcional a la derecha. **Variantes:**
con/sin `note`.

```jsx
function SectionHeader({ children, note }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "8px 0 14px" }}>
      <span style={{ font: "var(--w-bold) var(--t-section) var(--font-sans)", color: "var(--ink-900)" }}>{children}</span>
      {note && <span style={{ font: "var(--w-regular) var(--t-sub) var(--font-sans)", color: "var(--ink-400)" }}>{note}</span>}
    </div>
  );
}
```

### 2.A.3 `ScoreCircle` — *componente firma*
**Propósito:** chip redondo con anillo de 2px + número 1–10 en peso 800. **Variantes:**
`nivel` (critico/alto/medio/bajo) → terna de color; `size` (default 36; en el modal 44; en
tablas 32). **Estado fallback:** nivel desconocido → gris.

```jsx
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
```

### 2.A.4 `Pill` / `Pills`
**Propósito:** tag de señal redondeado. **Variantes de color:** `red` / `orange` /
`yellow` (severidad). `Pills` envuelve una lista y muestra el **estado vacío** "Sin alertas".

```jsx
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
```

### 2.A.5 `Badge` — *con accesibilidad por forma*
**Propósito:** etiqueta cuadrada de nivel. **Variantes:** `nivel` (riesgo) o `kind="tipo"`
(categórico morado). **Accesibilidad (#4):** antepone glifo de **forma** por nivel
(▲ critico · ◆ alto · ■ medio · ● bajo) para no depender solo del color; se puede apagar
con `shape={false}`.

```jsx
const NIVEL_SHAPE = { critico: "▲", alto: "◆", medio: "■", bajo: "●" };

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
```

### 2.A.6 `Sparkline`
**Propósito:** mini-barras (% Plan últimos 3 meses). **Color por valor:** ≥90 verde ·
≥70 naranja · <70 rojo. **Estado vacío:** "—".

```jsx
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
```

### 2.A.7 `KpiCard` — *borde-izq de color = firma*
**Propósito:** tarjeta KPI con **borde izquierdo de 4px** color-codificado por riesgo.
**Variantes:** `accent` (red/orange/blue/green; default `--border-idle` gris si no hay
riesgo); `valueColor` opcional.

```jsx
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
```

### 2.A.8 `TopNav`
**Propósito:** barra superior fija: wordmark (800/20) izq + links de nav con emoji (azules)
der, sobre un divisor hairline. **Estado activo:** link actual en `--ink-900` peso 700; el
resto en `--blue-accent` peso 400.

```jsx
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
```

### 2.A.9 Helpers de formato + lógica de nivel (es-AR)
**Propósito:** una sola fuente de verdad para números y para el mapeo riesgo→etiqueta.

```jsx
const NIVEL_LABEL = { critico: "Crítico", alto: "Alto", medio: "Medio", bajo: "Bajo" };

function fmtAntiguedad(m) {
  if (m < 12) return `${m} mes${m !== 1 ? "es" : ""}`;
  const a = Math.floor(m / 12), r = m % 12;
  let s = `${a} año${a !== 1 ? "s" : ""}`;
  if (r) s += ` y ${r} mes${r !== 1 ? "es" : ""}`;
  return s;
}
function fmtPesos(n)      { return "$" + Math.round(n).toLocaleString("es-AR").replace(/,/g, "."); }
function fmtPesosCorto(n) { if (n>=1e6) return "$"+(n/1e6).toFixed(1).replace(".",",")+" M";
                            if (n>=1e3) return "$"+Math.round(n/1e3)+" mil"; return "$"+Math.round(n); }
function fmtPct(n, dec=0) { return n.toFixed(dec).replace(".", ",") + "%"; }
function fmtNum(n, dec=0) { return n.toFixed(dec).replace(".", ","); }
function fmtMeses(n)      { return fmtNum(n, 1) + " m"; }
function fmtDelta(n, { dec = 1 } = {}) { // ▲ peor / ▼ mejor (score: subir = peor)
  if (!n) return "="; return (n > 0 ? "▲" : "▼") + " " + fmtNum(Math.abs(n), dec);
}
// zona: riesgo_base (0..1) → nivel + etiqueta corta
function zonaNivel(rb) { return rb>0.60?"critico":rb>0.45?"alto":rb>0.30?"medio":"bajo"; }
function zonaLabel(rb) { return {critico:"rot alta",alto:"rot alta",medio:"rot media",bajo:"rot baja"}[zonaNivel(rb)]; }
```

**Umbrales de nivel por score (1–10):** `score>=8` critico · `>=6` alto · `>=4` medio ·
resto bajo. **Umbrales de zona por `riesgo_base` (0–1):** `>0.60` critico · `>0.45` alto ·
`>0.30` medio · resto bajo.

---

## 2.B Componentes `.wz-*` (handoff Streamlit/HTML)

CSS completo + el helper Python que lo rinde (de `snippets-v3.py`). Mismo diseño que 2.A.

### 2.B.1 `.wz-banner` — banner de acción del día
**Propósito:** llamada a la acción arriba de cada pantalla ("4 vendedores necesitan
reunión esta semana"). **Variantes (tono):** `red` / `orange` / `blue` / `green`.

```css
.wz-banner{display:flex;align-items:center;gap:14px;padding:14px 20px;
  border-radius:12px;margin:6px 0 24px;font-family:var(--font);}
.wz-banner .em{font-size:22px;}
.wz-banner .ttl{font-weight:800;font-size:16px;}
.wz-banner .sub{font-size:13px;margin-top:2px;opacity:.85;}
.wz-banner.red{background:var(--red-bg);border:1px solid #f4cfcd;color:var(--red-text);}
.wz-banner.orange{background:var(--orange-bg);border:1px solid #f3d9a8;color:var(--orange-text);}
.wz-banner.blue{background:var(--blue-bg);border:1px solid #bcdcf5;color:var(--blue-text);}
.wz-banner.green{background:var(--green-bg);border:1px solid #cfe6b8;color:var(--green-text);}
```
```python
def banner(emoji, titulo, sub="", tono="red"):
    return (f'<div class="wz-banner {tono}"><span class="em">{emoji}</span>'
            f'<div><div class="ttl">{titulo}</div><div class="sub">{sub}</div></div></div>')
```

### 2.B.2 `.wz-hero` + `.wz-statcard` — jerarquía de KPIs (#1)
**Propósito:** UN KPI dominante (borde **superior** 4px, valor 56px) + tira de stats
secundarias de-enfatizadas. **Variante:** `.val.red` para el número en rojo.

```css
.wz-hero{background:var(--surface);border-radius:var(--radius);padding:22px 24px;
  box-shadow:var(--shadow-card);border-top:4px solid var(--red-accent);font-family:var(--font);}
.wz-hero .lbl{font-weight:700;font-size:13px;color:var(--ink-600);text-transform:uppercase;letter-spacing:.04em;}
.wz-hero .val{font-weight:800;font-size:56px;line-height:1;color:var(--ink-900);margin-top:8px;}
.wz-hero .val.red{color:var(--red-accent);}
.wz-hero .sub{font-size:12px;color:var(--ink-500);margin-top:8px;}

.wz-stat .val{font-weight:800;font-size:26px;color:var(--ink-900);}
.wz-stat .lbl{font-size:12px;color:var(--ink-400);margin-top:2px;}
.wz-statcard{background:var(--surface);border-radius:12px;padding:16px 18px;
  box-shadow:var(--shadow-card);font-family:var(--font);height:100%;}
.wz-statcard .val{font-weight:800;font-size:26px;color:var(--ink-900);line-height:1.1;}
.wz-statcard .lbl{font-size:12px;color:var(--ink-400);margin-top:4px;line-height:1.35;}
```
```python
def hero_kpi(label, valor, sub="", red=False):
    cls = "val red" if red else "val"
    return (f'<div class="wz-hero"><div class="lbl">{label}</div>'
            f'<div class="{cls}">{valor}</div><div class="sub">{sub}</div></div>')
def stat_kpi(label, valor):
    return f'<div class="wz-statcard"><div class="val">{valor}</div><div class="lbl">{label}</div></div>'
```

### 2.B.3 `.wz-score` — score circle (Streamlit)
**Variantes:** `critico/alto/medio/bajo`.
```css
.wz-score{display:inline-flex;align-items:center;justify-content:center;
  width:36px;height:36px;border-radius:50%;font-weight:800;font-size:15px;font-family:var(--font);}
.wz-score.critico{background:var(--red-bg);color:var(--red-text);border:2px solid var(--red-accent);}
.wz-score.alto{background:var(--orange-bg);color:var(--orange-text);border:2px solid var(--orange-accent);}
.wz-score.medio{background:var(--blue-bg);color:var(--blue-text);border:2px solid var(--blue-accent);}
.wz-score.bajo{background:var(--green-bg);color:var(--green-text);border:2px solid var(--green-accent);}
```
```python
def score_circle(score, nivel=None, title=""):
    nivel = nivel or nivel_de(score)
    t = f' title="{title}"' if title else ""
    return f'<span class="wz-score {nivel}"{t}>{int(score)}</span>'
```

### 2.B.4 `.wz-badge` — badge con forma (#4)
**Variantes:** `critico/alto/medio/bajo/tipo`. La forma ▲◆■● va en `.shp`.
```css
.wz-badge{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;
  border-radius:var(--radius-badge);font-size:11px;font-weight:600;font-family:var(--font);white-space:nowrap;}
.wz-badge .shp{font-size:8px;line-height:1;}
.wz-badge.critico{background:var(--red-bg);color:var(--red-text);}
.wz-badge.alto{background:var(--orange-bg);color:var(--orange-text);}
.wz-badge.medio{background:var(--blue-bg);color:var(--blue-text);}
.wz-badge.bajo{background:var(--green-bg);color:var(--green-text);}
.wz-badge.tipo{background:var(--purple-bg);color:var(--purple-text);}
```
```python
NIVEL_LABEL = {"critico":"Crítico","alto":"Alto","medio":"Medio","bajo":"Bajo"}
NIVEL_SHAPE = {"critico":"▲","alto":"◆","medio":"■","bajo":"●"}
def badge(nivel, label=None, shape=True, title="", kind=None):
    key = kind or nivel
    shp = f'<span class="shp">{NIVEL_SHAPE.get(key,"")}</span>' if shape and key in NIVEL_SHAPE else ""
    t = f' title="{title}"' if title else ""
    return f'<span class="wz-badge {key}"{t}>{shp}{label or NIVEL_LABEL.get(nivel, nivel)}</span>'
```

### 2.B.5 `.wz-pill` — pill de señal
**Variantes:** `red/orange/yellow`.
```css
.wz-pill{display:inline-block;padding:2px 8px;border-radius:var(--radius-sm);
  font-size:11px;font-weight:600;margin:1px 2px;font-family:var(--font);white-space:nowrap;}
.wz-pill.red{background:var(--red-bg);color:var(--red-text);}
.wz-pill.orange{background:var(--orange-bg);color:var(--orange-text);}
.wz-pill.yellow{background:#FFFDE7;color:#F57F17;}
```
```python
def pill(label, color="orange", title=""):
    t = f' title="{title}"' if title else ""
    return f'<span class="wz-pill {color}"{t}>{label}</span>'
```

### 2.B.6 `.wz-accion` — tag de acción sugerida (#4)
**Propósito:** verbo de acción por nivel. **Regla anti-ruido:** crítico/alto resaltan;
medio recede (gris); **bajo se reduce a "—"**.
```css
.wz-accion{display:inline-block;padding:4px 10px;border-radius:7px;
  font-size:12px;font-weight:700;font-family:var(--font);white-space:nowrap;}
.wz-accion.critico{background:var(--red-bg);color:var(--red-text);}
.wz-accion.alto{background:var(--orange-bg);color:var(--orange-text);}
.wz-accion.medio{background:var(--table-head-bg);color:var(--ink-600);}
.wz-accion.bajo{color:var(--ink-400);}
```
```python
ACCION_TXT = {"critico":"Reunión esta semana","alto":"Seguimiento activo",
              "medio":"Monitoreo mensual","bajo":"Seguimiento normal"}
def accion_tag(nivel):
    if nivel == "bajo":
        return '<span class="wz-accion bajo">—</span>'
    return f'<span class="wz-accion {nivel}">{ACCION_TXT[nivel]}</span>'
```

### 2.B.7 `.wz-delta` — trayectoria del score (#2)
**Propósito:** Δ vs mes anterior. **Semántica de color (importante):** subir score = **peor**
→ `worse` rojo (▲); bajar = mejor → `better` verde (▼); sin histórico → `flat` "·".
```css
.wz-delta{font-size:12px;font-weight:700;white-space:nowrap;}
.wz-delta.worse{color:var(--red-text);}
.wz-delta.better{color:var(--green-text);}
.wz-delta.flat{color:var(--ink-300);}
```
```python
def score_delta(delta):
    if delta is None: return '<span class="wz-delta flat" title="Sin histórico todavía">·</span>'
    if not delta:     return '<span class="wz-delta flat">=</span>'
    cls, g = ("worse","▲") if delta > 0 else ("better","▼")
    return f'<span class="wz-delta {cls}">{g} {abs(delta)}</span>'
```

### 2.B.8 `.wz-breakdown` — desglose ponderado del score (#1 explicabilidad)
**Propósito:** "por qué este score" en barras (base +1 + cada señal por su peso). **Color de
barra por peso:** ≥2 rojo · ≥1.5 naranja · resto amarillo/gris.
```css
.wz-breakdown{font-family:var(--font);}
.wz-breakdown .row{display:flex;align-items:center;gap:10px;margin-bottom:8px;}
.wz-breakdown .lbl{width:180px;font-size:12px;font-weight:600;color:var(--ink-700);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.wz-breakdown .bar{flex:1;height:14px;background:var(--line-faint);border-radius:4px;overflow:hidden;}
.wz-breakdown .bar>span{display:block;height:100%;border-radius:4px;}
.wz-breakdown .num{width:36px;text-align:right;font-size:12px;font-weight:700;color:var(--ink-700);}
```
```python
SIGNAL_PESO = {"inducción":2.0,"días cero↑":2.0,"caída 3m":2.0,"ausencias↑":2.0,
  "plan<80%":1.5,"zona quemada":1.5,"cobranza baja":1.0,"mes 4-6":1.0,"inactivos↑":1.0,
  "balanza neg.":1.0,"sin acomp.":1.0,"< 70% llamadas":1.0,"< 70% visitas":1.0,
  "clientes L:0":0.5,"ticket↓":0.5}
def score_breakdown_html(senales_labels):
    filas = [("Base (todos arrancan en 1)", 1.0)]
    filas += sorted(((s, SIGNAL_PESO.get(s, 0.5)) for s in senales_labels), key=lambda x: -x[1])
    out = '<div class="wz-breakdown">'
    for label, peso in filas:
        color = ("var(--red-accent)" if peso>=2 else "var(--orange-accent)" if peso>=1.5
                 else "var(--ink-200)" if label.startswith("Base") else "#F57F17")
        w = int(peso/2.0*100)
        out += (f'<div class="row"><span class="lbl">{label}</span>'
                f'<span class="bar"><span style="width:{w}%;background:{color}"></span></span>'
                f'<span class="num">+{fmt_num(peso,1)}</span></div>')
    return out + '</div>'
```

### 2.B.9 `.wz-recom` — recomendación de acción (#2)
**Propósito:** sugiere la intervención que mejor funcionó para perfiles similares. **Variantes
(tono):** `red` (crítico) / `orange` (alto). Solo se muestra en crítico/alto.
```css
.wz-recom{border-radius:10px;padding:14px 16px;font-family:var(--font);}
.wz-recom.red{background:var(--red-bg);}
.wz-recom.orange{background:var(--orange-bg);}
.wz-recom .cap{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--ink-600);margin-bottom:6px;}
.wz-recom .main{font-size:17px;font-weight:800;color:var(--ink-900);}
.wz-recom .main .imp{font-size:13px;font-weight:700;color:var(--green-text);margin-left:8px;}
.wz-recom .sub{font-size:12px;color:var(--ink-600);margin-top:6px;line-height:1.5;}
.wz-recom .alts{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;}
.wz-recom .alt{font-size:11px;color:var(--ink-500);background:rgba(255,255,255,.6);padding:3px 8px;border-radius:6px;}
```

### 2.B.10 `.wz-fresh` — frescura del dato (#5)
**Propósito:** "Actualizado: …" con punto verde, arriba a la derecha del header.
```css
.wz-fresh{display:inline-flex;align-items:center;gap:7px;font-size:12px;color:var(--ink-400);font-family:var(--font);}
.wz-fresh .dot{width:7px;height:7px;border-radius:50%;background:#27AE60;}
```
```python
def fresh(ts_str):
    return f'<span class="wz-fresh"><span class="dot"></span>Actualizado: {ts_str}</span>'
```

### 2.B.11 `.wz-cm` — celda de matriz de confusión (#1 precisión)
**Propósito:** cuadrante de la matriz predicción-vs-resultado. **Variantes:** `good` (acierto)
/ `bad` (fuga sorpresa) / `warn` (marcado pero retenido) / `neutral` (correcto sin alerta).
```css
.wz-cm{padding:16px 18px;border-radius:10px;font-family:var(--font);}
.wz-cm .n{font-weight:800;font-size:30px;line-height:1;}
.wz-cm .d{font-size:12.5px;margin-top:6px;line-height:1.4;}
.wz-cm.good{background:var(--green-bg);border:1px solid #cfe6b8;color:var(--green-text);}
.wz-cm.bad{background:var(--red-bg);border:1px solid #f4cfcd;color:var(--red-text);}
.wz-cm.warn{background:var(--orange-bg);border:1px solid #f3d9a8;color:var(--orange-text);}
.wz-cm.neutral{background:var(--table-head-bg);border:1px solid var(--line-strong);color:var(--ink-600);}
```

### 2.B.12 `.wz-card` — card genérica v3
```css
.wz-card{background:var(--surface);border-radius:var(--radius);
  box-shadow:var(--shadow-card);padding:20px 24px;font-family:var(--font);}
```

### 2.B.13 `.wz-table` — tabla (workhorse)
**Propósito:** tabla densa. **Variante:** `.compacto` (densidad ajustable #4 — padding 7px,
fuente 12.5). **Estado hover:** fila tinta a `--row-hover`. Header transparente en
mayúsculas con `letter-spacing`.
```css
.wz-table{width:100%;border-collapse:collapse;font-family:var(--font);}
.wz-table th{padding:0 14px 10px;text-align:left;font-size:11px;font-weight:700;
  color:var(--ink-400);text-transform:uppercase;letter-spacing:.04em;
  border-bottom:2px solid var(--line-strong);}
.wz-table td{padding:14px;border-bottom:1px solid var(--line-faint);
  vertical-align:middle;font-size:13px;color:var(--ink-700);}
.wz-table.compacto td{padding:7px 14px;font-size:12.5px;}
.wz-table tr:hover td{background:var(--row-hover);}
```

### 2.B.14 Formato es-AR (Python) — fuente de verdad de números
```python
def fmt_num(n, dec=0):
    s = f"{n:,.{dec}f}"                       # '1,234.5' (en-US)
    return s.replace(",", "·").replace(".", ",").replace("·", ".")  # → '1.234,5'
def fmt_pct(n, dec=0):  return f"{fmt_num(n, dec)}%"
def fmt_pesos(n):       return "$" + fmt_num(round(n), 0)
def fmt_pesos_corto(n):
    if n>=1_000_000: return "$"+fmt_num(n/1_000_000,1)+" M"
    if n>=1_000:     return "$"+fmt_num(round(n/1_000),0)+" mil"
    return fmt_pesos(n)
def fmt_meses(n):       return fmt_num(n,1)+" m"
def fmt_delta(n, dec=1):
    if not n: return "="
    return ("▲ " if n>0 else "▼ ")+fmt_num(abs(n),dec)
def nivel_de(score):
    return "critico" if score>=8 else "alto" if score>=6 else "medio" if score>=4 else "bajo"
```

---

# 3. GUÍAS DE USO Y CONVENCIONES

## 3.1 Cuándo usar cada componente
| Necesito… | Usá | Notas |
|---|---|---|
| Mostrar el riesgo de un vendedor (1–10) | **ScoreCircle / `.wz-score`** | siempre con su `nivel`; tamaño 36 default, 32 en tablas, 44 en detalle |
| Etiquetar un nivel de riesgo de zona/fila | **Badge / `.wz-badge`** | cuadrado; **siempre con forma ▲◆■●** salvo que el espacio sea mínimo |
| Listar señales detectadas | **Pills / `.wz-pill`** | color = severidad (red>orange>yellow); vacío = "Sin alertas" |
| Un número grande de cabecera | **KpiCard** (multi-igual) o **`.wz-hero`** (uno dominante) | v3 prefiere UN hero + tira secundaria, no 5 KPIs iguales |
| Decir qué hacer hoy | **`.wz-banner`** + **`.wz-accion`** | banner arriba; tag de acción en cada fila |
| Mostrar tendencia de plan | **Sparkline** | 3 barras, color por valor |
| Mostrar si el riesgo sube/baja | **`.wz-delta`** | ▲ rojo = peor, ▼ verde = mejor |
| Explicar por qué un score | **`.wz-breakdown`** | barras ponderadas por señal |
| Recomendar una intervención | **`.wz-recom`** | solo crítico/alto |
| Validar el modelo | **`.wz-cm`** (matriz) | good/bad/warn/neutral |
| Cualquier contenedor | **Card / `.wz-card`** | blanco, radio 12–14, sombra suave |
| Tabla de datos | **`.wz-table`** | `.compacto` para densidad |

## 3.2 Tono visual del sistema
- **Riesgo = color.** Es la regla #1. Nunca uses los colores de riesgo para decorar; cada
  uso comunica un nivel. El azul es además el **único** color de links.
- **Plano y limpio.** Una sola elevación (`0 1px 4px rgba(0,0,0,.08)`). **Sin** gradientes,
  **sin** texturas/patrones, **sin** glassmorphism/blur, **sin** sombras internas o de color,
  **sin** dark mode. Fondo blanco/casi-blanco con gutters de `2.5rem`.
- **Jerarquía por peso, no por familia.** Una sola tipografía (Source Sans 3); 800 manda,
  700 sub-manda, 400 cuerpo. La mono solo en specimens.
- **Firma visual:** el **borde de 4px de color** (izquierdo en KpiCard, superior en `.wz-hero`)
  codificado por riesgo. Cards **sin** borde completo, solo sombra + (opcional) acento.
- **Hairlines:** filas `1px #f2f2f2`, divisores `1px #eee`, underline de header `2px #e9ecef`.
- **Radios:** 12 card · 10 card-sm/pill · 4 badge · 50% circle · (v3: 14 card).
- **Movimiento:** casi nulo (Streamlit). Único feedback: hover de fila a `#fafafa`. Si agregás
  motion, máximo 120–150ms ease en hover; nada de bounce/loops decorativos.
- **Imágenes:** el producto es **sin imágenes** por diseño. No hay logo file: la marca es el
  **wordmark de texto** "Würth Argentina" (800/20) + 🔔. No reproducir el logo corporativo.

## 3.3 Iconografía
- **Sistema = emoji + glifos Unicode tipeados**, nunca SVG a mano ni icon-font. Son etiquetas
  de orientación, no decoración. **No** introducir Lucide/Heroicons en el dashboard.
- **Mapa estable** (reusar EXACTO): 🔔 producto · 🏠 Inicio · 👤 Por supervisor · 📝 Intervenciones ·
  📈 Historial · 💰 Costo · 📞 Actividad · 🚗 Viajantes · 🎯 Precisión · 📋 tabla · 📍 zonas ·
  ⏱️ ventanas críticas · 👥 onboarding/cohortes · 📊 charts · 🧾 detalle · ✉️ resumen semanal ·
  📱 móvil · 🧩 estados · ➕ agregar · 💾 guardar · 🔍 buscar · ⚠️ advertencia · 🔄 rotación.
- **Glifos micro:** `↑↓` tendencia en prosa · `▲▼` delta de score (▲ peor=rojo, ▼ mejor=verde) ·
  `→ ←` CTA/volver · `·` middot separador de meta · `ⓘ` info en headers · `✓` ok · `=` sin cambio ·
  `▲◆■●` forma por nivel (#4 accesibilidad) · `🔴🟠🔵🟢⬜` swatches en leyendas.

## 3.4 Contenido y copy (es-AR / Rioplatense)
- **Voseo imperativo:** *Documentá · Pasá el mouse · Usá el buscador · Ajustá* (nunca el
  *documenta/pulsa/usa* de España). Al usuario lo tratás de vos; al vendedor en tercera persona.
- **Sentence case** en todo (títulos, labels, botones). MAYÚSCULAS solo para un token de
  énfasis suelto o un nivel `.upper()`.
- **Nivel → verbo de acción:** Crítico→"reunión esta semana" · Alto→"seguimiento activo" ·
  Medio→"monitoreo mensual" · Bajo→"seguimiento normal".
- **Números (regla única):** miles con punto, decimal con coma → `1.400.000` · `5,2`. Pesos
  largos `$1.400.000`, cortos `$1,4 M`/`$980 mil`. Porcentaje entero + `%` pegado: `78%`.
  Antigüedad en texto (*3 meses · 1 año y 2 meses*); en chips `5,2 m`, `M1`, `M4-6`. **Ningún
  número va crudo a pantalla:** siempre por `fmt_num/fmt_pct/fmt_meses/fmt_pesos`.
- **Separador de meta:** middot con espacios → `Viajante · 3 meses · zona quemada`.
- **Tono:** calmo, sin alarmismo, explicativo. Cada umbral se justifica inline (tooltip/caption).
- **Vocabulario de dominio (mantener exacto):** vendedor · viajante · televentas · grupo/zona ·
  cartera · score · señales · cumplimiento de plan / % Plan · onboarding/inducción ·
  ventana crítica · zona quemada · rotación/fluctuación · cobranza.

## 3.5 Reglas de layout
- Barra superior fija: wordmark izq + nav emoji-azul der, sobre divisor `1px #eee`.
- Fila de KPIs (flex, columnas iguales, gap 14) **o** hero+tira (v3). Luego bloques de sección.
- Splits multi-columna con ratios tipo `[1, 1.6]`. Filtros (radios/select/search) **arriba** de
  los datos que filtran. Gutters de `2.5rem`, contenido full-width.
- **Default accionable:** las vistas arrancan en "Requieren acción" (crítico+alto) y **no
  esconden** a los accionables detrás de un "ver más".
- **Accesibilidad:** todo nivel se comunica por **forma + color**, nunca solo color.
- **Estados obligatorios:** vacío (mensaje amable "Sin … 🎉"), carga (skeleton shimmer),
  error de conexión (mensaje + reintento), antes de dar una pantalla por terminada.

## 3.6 Convención de exportación (React/Babel)
Los primitivos viven en scripts Babel separados y comparten scope vía `window`. Cada archivo
termina con `Object.assign(window, { … })`. Nunca declarar un `const styles = {…}` global sin
prefijo (colisiona entre archivos): usá inline o nombres específicos.

---

# 4. INSTRUCCIONES DE RECONSTRUCCIÓN

## 4.1 Estructura de archivos a recrear
```
/  (raíz del nuevo proyecto de design system)
├─ DESIGN-SYSTEM-FLUCTUACION.md   ← este documento (fuente única)
├─ colors_and_type.css            ← §1.4 (tokens Set A + roles .ds-*)
├─ styles.css                     ← @import colors_and_type.css (stylesheet global)
├─ README.md                      ← contexto del producto + índice (resumir de §3)
├─ SKILL.md                       ← manifest de skill (ver 4.3)
├─ assets/                        ← sin imágenes; wordmark de texto + 🔔
├─ ui_kits/dashboard/
│  ├─ primitives.jsx              ← §2.A completo
│  ├─ index.html                  ← carga React 18.3.1 + Babel + tokens + primitives
│  └─ (vistas Inicio/Supervisor/… que componen los primitivos)
└─ handoff/
   ├─ dashboard-v3.css            ← §1.4 (Set B) + §2.B (todas las .wz-*)
   ├─ snippets-v3.py              ← §2.B helpers Python + §3.4 formato
   ├─ format-es-AR.txt            ← §3.4
   └─ icons.txt                   ← §3.3
```

## 4.2 Orden de reconstrucción
1. Crear `colors_and_type.css` con **todo** el bloque CSS de §1.4 (incluye alias `--font`,
   `--radius`, `--radius-sm` para que los `.wz-*` funcionen sin cambios).
2. Crear `styles.css` que haga `@import "colors_and_type.css";` (stylesheet global del DS).
3. Crear `handoff/dashboard-v3.css` pegando §2.B (todas las clases `.wz-*`).
4. Crear `ui_kits/dashboard/primitives.jsx` pegando §2.A (incluye el `Object.assign(window…)`).
5. Crear `handoff/snippets-v3.py` con los helpers Python de §2.B + formato de §3.4.
6. Generar cards de specimen (preview/) y registrarlas si la plataforma destino las soporta.
7. Validar: una página HTML que cargue tokens + primitives y renderice cada componente en sus
   variantes/estados. Verificar que **riesgo=color**, peso 800 en KPIs, borde 4px, hairlines.

## 4.3 PROMPT listo para pegar en otra instancia de Claude Design

```
Reconstruí, desde cero y de forma fiel, el design system "Würth Rotación" usando como
ÚNICA fuente de verdad el documento DESIGN-SYSTEM-FLUCTUACION.md que te adjunto. No
inventes nada que no esté en el documento; si algo no está, dejalo explícito en vez de
improvisar.

Contexto: es el lenguaje visual de un dashboard interno de Würth Argentina que detecta
vendedores con riesgo de rotación. Idea rectora: RIESGO = COLOR, cuatro niveles
(Crítico rojo / Alto naranja / Medio azul / Bajo verde). Estética: plana, blanca, densa,
sin gradientes ni imágenes; jerarquía por peso tipográfico (Source Sans 3, 800/700/400);
firma = borde de 4px de color en las cards; iconografía = emoji + glifos Unicode.

Hacé, en este orden:
1. colors_and_type.css con TODOS los tokens del documento (§1.4), incluyendo los alias
   --font / --radius / --radius-sm y los roles .ds-*.
2. styles.css global que importe colors_and_type.css.
3. handoff/dashboard-v3.css con TODAS las clases .wz-* del §2.B, verbatim.
4. ui_kits/dashboard/primitives.jsx con TODOS los primitivos React del §2.A
   (Card, SectionHeader, ScoreCircle, Pill/Pills, Badge con forma ▲◆■●, Sparkline,
   KpiCard, TopNav) + helpers de formato es-AR, terminando con Object.assign(window,…).
5. handoff/snippets-v3.py con los helpers Python del §2.B y el formato es-AR del §3.4.
6. Una página HTML de showcase que cargue React 18.3.1 (UMD pinneado), Babel, los tokens
   y primitives.jsx, y muestre cada componente en TODAS sus variantes y estados
   (hover de fila, vacío "Sin alertas", badge con/ sin forma, score circle por nivel y
   por tamaño 32/36/44, KPI con cada accent, banner en los 4 tonos, delta peor/mejor/flat,
   accion_tag que recede en bajo, matriz de confusión good/bad/warn/neutral, tabla normal
   y .compacto).

Respetá SIN EXCEPCIÓN las convenciones del §3: riesgo=color, número nunca crudo (formato
es-AR con coma decimal y punto de miles), copy en voseo argentino sentence-case, nivel→verbo
de acción, accesibilidad por forma+color, y los estados obligatorios (vacío/carga/error).
No agregues dark mode, gradientes, blur, ni una segunda familia tipográfica. No reproduzcas
un logo corporativo: la marca es el wordmark de texto "Würth Argentina" + 🔔.

Cuando termines, mostrame la página de showcase y confirmá contra el documento que no falta
ningún componente ni token.
```

---

## Apéndice · Checklist de fidelidad post-migración
- [ ] Los 4 niveles renderizan su terna exacta (accent/bg/text) y el azul es el único link.
- [ ] KPIs en peso 800; títulos 800/22; secciones 700/15; cuerpo 400/14.
- [ ] Borde de acento de 4px presente (izq en KpiCard, sup en .wz-hero).
- [ ] Una sola sombra `0 1px 4px rgba(0,0,0,.08)`; sin gradientes/blur/dark mode.
- [ ] Badges con forma ▲◆■● + color; score circle con anillo de 2px.
- [ ] Números en formato es-AR (`1.400.000`, `5,2 m`, `78%`, `$1,4 M`).
- [ ] Copy en voseo, sentence-case; nivel→verbo de acción correcto.
- [ ] Estados vacío/carga/error presentes; default "Requieren acción".
- [ ] Iconografía emoji del mapa estable; sin SVG a mano ni icon-font.
- [ ] Marca = wordmark de texto + 🔔; sin logo corporativo reproducido.
```
```

*Fin del documento — fuente única de verdad para la migración.*
