---
name: wurth-rotacion-design
description: Use this skill to generate well-branded interfaces and assets for Würth Argentina's "Sistema de Alertas Tempranas de Rotación" (sales-rep churn early-warning dashboard), either for production or throwaway prototypes/mocks. Contains essential design guidelines, colors, type, the emoji icon system, design tokens, and a high-fidelity UI kit of dashboard components for prototyping.
user-invocable: true
---

Read the `README.md` file within this skill, and explore the other available files
(`colors_and_type.css` for tokens, `preview/` for specimen cards, `ui_kits/dashboard/`
for the interactive component recreation).

If creating visual artifacts (slides, mocks, throwaway prototypes, etc.), copy assets
out and create static HTML files for the user to view — link `colors_and_type.css`
and reuse the JSX components in `ui_kits/dashboard/` (TopNav, KpiCard, ScoreCircle,
Pill/Pills, Badge, Sparkline, the vendedor table). If working on production code, you
can copy the tokens and read the rules here to become an expert in designing with this
product's visual language.

Key things to honor (full detail in README.md):
- **Risk = color.** The whole system is organized around four tiers: Crítico (red
  `#E24B4A`), Alto (orange `#EF9F27`), Medio/Info (blue `#4A90D9`), Bajo (green
  `#639922`). Each is an accent/bg/text triad.
- **Source Sans 3**, hierarchy by weight (800/700/400) not family. White cards, flat
  near-zero elevation, signature 4px risk-colored left-border on cards.
- **Iconography is emoji + Unicode glyphs** — never hand-draw SVG icons; type the
  actual emoji (see the stable nav/section mapping in the README).
- **Copy is Argentine Spanish** (Rioplatense imperative: *documentá, usá, pasá*),
  operational and explanatory, with risk levels mapping to actions.

If the user invokes this skill without any other guidance, ask them what they want to
build or design, ask a few clarifying questions, and act as an expert designer who
outputs HTML artifacts *or* production code, depending on the need.

Source of truth: https://github.com/elterco2012-dev/alerta-de-fluctuacion
