# Dashboard UI Kit — Würth Rotación

A high-fidelity, interactive recreation of Würth Argentina's internal
**Sistema de Alertas Tempranas de Rotación** dashboard. Built with React +
Babel (in-browser), styled entirely with the design tokens in
`../../colors_and_type.css`. Cosmetic recreation — the data is mock and the
scoring is faked; this exists to give designers pixel-faithful, reusable
components.

## Run it
Open `index.html`. No build step — React/Babel load from CDN and the `.jsx`
files are transformed in the browser.

## Interactive click-through
- **Inicio** — KPI row · filter pills + search · ranked vendedor table → **click any row** to open a vendedor detail modal · high-rotation zones · critical-window histogram · onboarding tracker.
- **Por supervisor** — grid of supervisor cards → **"Ver mis vendedores →"** drills into that supervisor's reps (with a high-rotation-zone warning banner).
- **Intervenciones** — impact KPIs · a working **registration form** (pick a rep, type, supervisor, notes → "💾 Guardar" prepends a new highlighted row) · impact history table.
- **Costo de rotación** — exposure KPIs · per-zone exposure bars · filterable detail table with peso costs.
- **Historial** — permanence-by-cohort line (with 18m benchmark + trend), bajas/rotation-rate by year, and critical-zone bars (% who left in <6 months).
- **Actividad** — plan compliance for Televentas (calls) and Viajantes (visits): period selector, summary table, monthly trend, and per-rep ranking with conditional-format cells.

## `compare.html` — antes / después + mejoras v2
A second entry point that flips the **same data** between the faithful recreation of
today's dashboard and a **v2 "propuesta profesional"** for all six screens
(Inicio · Por supervisor · Intervenciones · Costo · Historial · Actividad), plus three
**new capabilities** the current product lacks (v2-only, toggle hidden):

| Feature screen | What it shows | File |
|---|---|---|
| ✉️ Resumen semanal | weekly digest emailed to each supervisor (#6) | `FeatureViews.jsx` |
| 📱 Móvil | one-column view for viajantes in the field, in an iPhone frame (#7) | `FeatureViews.jsx` + `ios-frame.jsx` |
| 🧩 Estados | loading skeletons, connection-error, and empty states (#5) | `FeatureViews.jsx` |

The v2 direction applies six layout refinements (dominant hero KPI · breathing room ·
permanencia 18→5m as the star · action-orientation via banners + an "acción sugerida"
column · de-noised charts · real empty states) **plus** these cross-cutting upgrades:

- **#1 Score explainability** — the vendedor modal shows a weighted "Por qué este score" breakdown (`ScoreBreakdown`, from `model.js`'s `SIGNAL_CATALOG`).
- **#2 Score trajectory** — a Δ-vs-last-month indicator (`ScoreDelta`) in every v2 table, a 6-month mini-line (`ScoreHistory`), and a "mayores escaladas" leaderboard in Historial.
- **#3 Cohort retention** — Historial's survival curve + per-cohort retention table.
- **#4 Accessibility** — risk `Badge`s carry a distinct **shape** per level (▲◆■●), so meaning survives without color.

New files: `model.js`, `v2common.jsx`, `*V2.jsx` per screen, `HistorialViews.jsx`,
`ActividadViews.jsx`, `FeatureViews.jsx`, `PrecisionView.jsx`, `ios-frame.jsx`.

### Round 3 — professionalization pass
- **🎯 Precisión del modelo** (`PrecisionView.jsx`) — a confusion matrix (predicción vs. resultado real) with recall/precision in plain language: *does the score actually predict who leaves?* The screen that validates the whole product.
- **Action recommendation** — the vendor modal now recommends a specific intervention based on what historically worked for similar profiles (`recomendarAccion` + `EFECTIVIDAD` in `model.js`), with a ranked fallback list.
- **Unified number formatting** — one rule set (`fmtPct`, `fmtNum`, `fmtMeses`, `fmtPesosCorto`, `fmtDelta`) so commas, thousands separators and tendency glyphs are consistent everywhere.
- **Adjustable density** — a Cómodo/Compacto toggle on the main tables (`useDensity`/`setDensity`/`DensityToggle`), so a supervisor with 3 reps and HR with 47 each get a fitting view.
- **Data-freshness timestamp** — a discreet "Actualizado: …" with a live dot in the header.

## Files
| File | Contents |
|---|---|
| `index.html` | entry point — loads React, tokens, and all component scripts |
| `data.js` | mock dataset (`window.DASH_DATA`): vendedores, grupos, ventanas, intervenciones |
| `primitives.jsx` | shared building blocks + helpers — see below |
| `InicioView.jsx` | main board: KPI row, filter, `VendedorTable`, `ZonesPanel`, `CriticalWindowChart`, onboarding table |
| `SupervisorView.jsx` | supervisor landing cards + per-supervisor detail |
| `InterventionsView.jsx` | impact KPIs, registration form, impact history + `ImpactCell` |
| `CostView.jsx` | cost KPIs, exposure bars, detail table, `VendedorModal`, `costoRotacion()` |
| `App.jsx` | top-nav router + modal host |

## Component inventory (in `primitives.jsx`)
- `<TopNav current onNav>` — product wordmark + emoji nav links
- `<KpiCard value label sub accent valueColor>` — the left-accent-border KPI tile (`accent`: red/orange/blue/green)
- `<ScoreCircle score nivel size>` — the signature round 1–10 risk chip
- `<Pill label color>` / `<Pills senales>` — rounded signal tags (red/orange/yellow)
- `<Badge nivel|kind label>` — squared risk/category badge (kind `"tipo"` = purple)
- `<Sparkline vals>` — 3-bar % Plan trend, per-bar color by value
- `<Card>` / `<SectionHeader note>` — surface + section title
- Helpers: `fmtAntiguedad`, `fmtPesos`, `zonaNivel`, `zonaLabel`, `NIVEL_LABEL`

All components export to `window` (each file ends with `Object.assign(window, {…})`)
so the separately-transpiled Babel scripts can share scope.

## Notes & fidelity
- The real app is **Streamlit** (Python, CSS-in-`st.markdown`). This kit reproduces
  its *visuals and flows*, not its implementation. Charts are pure CSS/flex here
  (the original uses Plotly) but match the palette and layout.
- Colors, radii, shadows, type and spacing are pulled from the shared token file —
  edit `../../colors_and_type.css` to retheme everything at once.
- Source of truth: [`elterco2012-dev/alerta-de-fluctuacion`](https://github.com/elterco2012-dev/alerta-de-fluctuacion).
