# Würth Rotación — Design System

A design system harvested from **Würth Argentina's "Sistema de Alertas Tempranas de Rotación"** — an internal early-warning dashboard that detects sales reps (*vendedores*) at risk of quitting *before* they resign.

> **What this is:** a faithful recreation of the visual language of one real, shipping internal tool. It is a data-dense, utilitarian analytics dashboard — not a marketing brand. The "brand" here is the dashboard's own consistent design vocabulary: white cards on a light canvas, a four-tier color-coded risk system, left-accent-border KPI cards, compact data tables, and emoji-as-iconography.

---

## Sources

This system was reverse-engineered **entirely from source code** (there is no Figma file, no separate brand kit, and no image assets in the repo — every value below is lifted verbatim from the CSS-in-Python in the dashboard):

- **GitHub:** [`elterco2012-dev/alerta-de-fluctuacion`](https://github.com/elterco2012-dev/alerta-de-fluctuacion) — Streamlit app (`dashboard.py` + `pages/*.py`), business logic (`src/score_engine.py`), and the project's own `CLAUDE.md` (business context).

If you have access, explore that repository to build richer or more accurate designs — the `CLAUDE.md` inside it documents the business rules, the scoring weights, and the database schema in depth.

> **No corporate logo is recreated here.** The shipping app brands itself purely with the text "Würth Argentina" plus a 🔔 emoji — there is no logo file in the codebase, and the official Würth logomark is not reproduced. Use the text wordmark treatment shown in the UI kit.

---

## The product in one paragraph

Würth Argentina's average sales-rep tenure fell from **18 months a decade ago to ~5 months today**. This dashboard exists to catch the warning signs of a departure early. A rules-based engine scores every active vendedor **1–10** on nine weighted signals (falling plan attainment, zero-sale days, shrinking active client book, "burned" high-rotation zones, the critical onboarding window, etc.). Reps, zones (*grupos*) and supervisors are all surfaced through the same color-coded risk lens. The audience is internal: **RRHH (HR), supervisors, and management** — each with their own view.

The product has **five surfaces**, all in one Streamlit app:
1. **Inicio** — the main board: KPIs, the ranked vendedor table, high-rotation zones, critical-window chart, onboarding tracker.
2. **Por supervisor** — supervisor cards → drill into "my reps."
3. **Intervenciones** — log an action taken on a rep and measure its impact on score.
4. **Historial** — historical trends & rotation analysis.
5. **Costo de Rotación** — estimated peso cost of each potential departure.
6. **Actividad** — Televentas call / Viajante visit activity vs. plan.

---

## CONTENT FUNDAMENTALS

**Language:** Argentine Spanish (Rioplatense). Copy uses the Argentine imperative — *"Documentá", "Pasá el mouse", "Usá el buscador", "Ajustar"* — never the Spanish *"documenta/pulsa"*. Translate any new copy into this register.

**Voice:** Operational, plain, and explanatory. This is a tool for busy supervisors and HR, so it tells you *what to do*, not just what happened. Risk levels map to verbs: **Crítico → "acción inmediata / reunión esta semana"**, **Alto → "seguimiento activo"**, **Medio → "monitoreo mensual"**, **Bajo → "seguimiento normal"**.

**Tone:** Calm, non-alarmist, evidence-led. Every threshold is justified inline. Heavy use of explanatory `title=` tooltips and `st.caption()` micro-copy beneath tables — the design assumes the user will hover to learn *why* a signal fired. Example caption: *"El impacto se mide comparando el score al momento de intervenir con el score actual."*

**Casing:** Sentence case everywhere — section headers, labels, buttons (*"💾 Guardar intervención"*, *"Ver mis vendedores →"*). ALL-CAPS is reserved for emphasis on a single token (*"COSTO TOTAL"*, a risk level rendered `.upper()`).

**Person:** Addresses the user directly as *vos/you* in instructional copy ("tu zona", "mis vendedores"); describes the rep in third person.

**Numbers & units:** Pesos formatted with dot thousands-separators (`$1.400.000`). Percentages as whole numbers + `%`. Tenure spelled out (*"5 meses", "1 año y 2 meses"*). Months of a rep's career are written `M1`, `M4-6`. The `·` (middot) is the universal separator in meta lines: *"Viajante · 3 meses · zona quemada"*.

**Domain vocabulary (keep these exact):** *vendedor* (rep), *viajante* (field rep), *televentas* (inside sales), *grupo / zona* (territory), *cartera* (client book), *score*, *señales* (signals), *cumplimiento de plan / % Plan*, *onboarding / inducción*, *ventana crítica*, *zona quemada* (high-rotation territory), *rotación / fluctuación* (churn), *cobranza* (collections).

**Emoji:** Yes — used deliberately and consistently as section/nav icons (see ICONOGRAPHY). Never decorative-only; each emoji is a wayfinding label.

---

## VISUAL FOUNDATIONS

**Overall feel.** A clean, white, information-dense operations dashboard. No hero imagery, no gradients, no dark mode. Content sits in flat white cards floating on a near-white canvas with generous `2.5rem` page padding. The eye is guided entirely by **color-coded risk**, **weight contrast** (800 vs 400), and **whitespace** — not by borders or decoration.

**Color.** One organizing principle: **risk level = color.**
- 🔴 **Crítico** `#E24B4A` · 🟠 **Alto** `#EF9F27` · 🔵 **Medio/Info** `#4A90D9` · 🟢 **Bajo** `#639922`.
- `#E24B4A` doubles as the **Würth brand red** and the primary accent.
- Each tier is a triad: a saturated **accent** (borders, rings, bars), a pale **bg** tint, and a deep **text** shade. (e.g. red = `#E24B4A` / `#FDECEA` / `#B71C1C`.)
- Blue `#4A90D9` is also the *only* link color.
- A single non-risk categorical color exists: **purple** `#F3E8FF`/`#6B21A8` for intervention-type badges.
- Ink is a 9-step gray ladder from `#1a1a2e` (headings) down to `#ccc` (placeholders). There is no pure black text.

**Typography.** **Source Sans 3** (Streamlit's default UI font) throughout. The system has no serif and no display face — hierarchy comes from **weight (800 → 700 → 400) and size**, not from family changes. KPI values and titles are `800`; labels, names and section headers `700`; table headers and badges `600`; body `400`. Sizes step 30 → 22 → 20 → 15 → 13 → 12 → 11px. Desktop-only, sized in px (no rem scaling).

**Backgrounds.** Flat. White cards, white/near-white page. **No** images, **no** gradients, **no** textures, **no** patterns. The only "fills" are the pale risk-tint backgrounds inside pills, badges and score circles, and conditional-format cell tints in dense data tables.

**Cards.** The atomic container: `background:#fff`, `border-radius:12px` (10px for the tighter vendor-card), `box-shadow:0 1px 4px rgba(0,0,0,0.08)`, `padding:~20px`. **The signature move is a 4px colored left-border** whose color encodes risk (`border-left:4px solid #E24B4A`). KPI cards, vendor cards and supervisor cards all use it. Cards have **no** full border — only the shadow + optional left accent. *(Note: the generic "rounded card + colored left-border only" is normally an AI-slop tell — here it is genuinely the product's real, load-bearing pattern, so use it confidently.)*

**Borders & dividers.** Hairlines only. Table rows separated by `1px #f2f2f2`; section/nav dividers `1px #eee`; table headers underlined `2px #e9ecef`. No heavy outlines anywhere.

**Shadows.** Exactly one elevation: a whisper-soft `0 1px 4px rgba(0,0,0,0.08)` (or `0 1px 3px /.07` on smaller cards). No layered, colored, or large shadows. No inner shadows. The system is nearly flat.

**Corner radii.** `12px` cards · `10px` small cards & pills · `4px` badges · `50%` score circles. Bars get a `2px` top radius.

**Component shapes.**
- **Score circle** — a 36px round chip with a 2px colored ring, pale tint fill, and an 800-weight number (the rep's 1–10 score).
- **Pill** — fully-rounded (`radius 10px`) signal tag, pale bg + deep text, ~11px/600. Used in clusters.
- **Badge** — squared (`radius 4px`) risk label, same color logic.
- **Sparkline** — a row of 9px-wide flex-end bars, each colored green/orange/red by its value (≥90 / ≥70 / <70). The product's only inline data-viz primitive.

**Tables.** The workhorse. Light `#f8f9fa` header, `600/12px/#666` uppercase-ish header text, `13px` body, `1px #f2f2f2` row separators, and a subtle `#fafafa` row-hover. Two-line cells are common: a bold name on top, a faint `11px` meta line (*"Viajante · 3 meses"*) below.

**Charts.** Plotly, on a **white** plot + paper background, no chart-junk: gridlines `#f0f0f0`, no zero-line, labels outside the bars, `11–12px` font. Bars are colored by the same risk palette (red/orange/neutral-gray/green). Horizontal bars for ranked exposure, vertical for the critical-window histogram.

**Layout rules.** Fixed sticky-feel top bar: product name (800/20px) on the left, a row of blue emoji-prefixed nav links on the right, separated by a `1px #eee` divider. Below it: a KPI row (flex, equal columns, `14px` gap), then section blocks. Multi-column splits use ratios like `[1, 1.6]`. Filters (radio pills / select / search) sit directly above the data they filter. Generous `2.5rem` page gutters; full-width content (`max-width:100%`).

**Transparency & blur.** None. No glassmorphism, no backdrop blur, no overlays. Everything is opaque.

**Animation & motion.** Essentially none — this is Streamlit's default behavior. The only interactive feedback is the table **row-hover** tint (`#fafafa`) and standard link/button states. No transitions, fades, bounces, or easing curves are defined. If you add motion when extending the system, keep it minimal and functional (a 120–150ms ease on hover at most).

**Hover / press states.** Table rows tint to `#fafafa` on hover. Links are blue with no underline. Buttons are Streamlit defaults (primary button = filled). Keep added hover states subtle: a slight tint or a one-step-darker accent, never a scale-up or glow.

**Imagery vibe.** N/A — the product is imagery-free by design. If a future surface needs imagery, keep it warm-neutral and businesslike to match the restrained palette; do not introduce stocky gradients or illustration.

---

## ICONOGRAPHY

**The icon system is emoji + Unicode glyphs. There is no icon font, no SVG sprite, and no PNG icons in the codebase.** This is a deliberate, consistent choice — emoji act as wayfinding labels, never as decoration.

**Navigation / section emoji (stable mapping — reuse these exactly):**

| Emoji | Meaning | Where |
|---|---|---|
| 🔔 | the product (alerts) | page icon / favicon |
| 🏠 | Inicio | nav |
| 👤 | Por supervisor | nav |
| 📝 | Intervenciones | nav |
| 📈 | Historial | nav |
| 💰 | Costo de rotación | nav |
| 📞 | Actividad (Televentas) | nav |
| 🚗 | Viajantes | activity |
| 📋 | ranked vendedor table | section |
| 📍 | high-rotation zones | section |
| ⏱️ | critical windows | section |
| 👥 | onboarding | section |
| 📊 / 🧾 | charts / detail tables | section |
| ➕ 💾 | add / save (forms) | buttons |
| 🔍 | search inputs | placeholders |
| ⚠️ | structural-risk warning | inline |

**Unicode glyphs used as micro-icons:** `↑` `↓` (trend direction), `→` (CTA arrows, *"Ver mis vendedores →"*), `←` (back), `·` (middot separator), `ⓘ` (info affordance on table headers), `✓` (success), `—` / `=` (no-data / no-change), and colored square/circle glyphs `🔴 🟠 🟢 ⬜` used in chart legends.

**Guidance for extending:** keep using this emoji set for nav/section labels — do **not** introduce a stroke-icon library (Lucide/Heroicons) into the dashboard itself, as it would clash with the established voice. If you build a *new* surface where line icons genuinely fit (e.g. a marketing page), document the substitution and prefer a neutral set; but the core product is emoji-native. **Never hand-draw SVG icons to fake this** — type the actual emoji/Unicode character.

> *Substitution flag:* this design system links **Source Sans 3** from Google Fonts as the genuine Streamlit default. No font files ship in the repo, so if Würth has a licensed/hinted copy, drop the `.woff2` files into `fonts/` and update `colors_and_type.css`.

---

## Index — what's in this folder

| Path | What it is |
|---|---|
| `README.md` | this file — context, content & visual foundations, iconography |
| `colors_and_type.css` | all design tokens (color scale + semantic, type scale + roles, shape/elevation) |
| `SKILL.md` | Agent-Skill manifest so this system can be used in Claude Code |
| `preview/` | small HTML specimen cards that populate the Design System tab |
| `ui_kits/dashboard/` | high-fidelity, interactive recreation of the dashboard (see its own README) |
| `assets/` | brand/asset notes (the product ships no image assets — emoji-native) |

**UI kits**
- `ui_kits/dashboard/` — the internal rotation-alerts dashboard. Modular JSX components (top nav, KPI cards, vendedor table, score circle, signal pills, sparkline, zone list, onboarding table, intervention form, cost cards) assembled into an interactive `index.html` click-through across Inicio → Por supervisor → Intervenciones → Costo.

*(No slide template was provided in the source, so this system ships no `slides/`.)*
