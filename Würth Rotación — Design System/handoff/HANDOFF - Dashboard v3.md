# HANDOFF — Dashboard v3 (Würth Rotación)

Paquete para implementar la **propuesta v2/v3** en el dashboard real
(`elterco2012-dev/alerta-de-fluctuacion`, Streamlit + Python). Pasale esta carpeta
entera a Claude Code apuntado a tu repo y dale el prompt del final.

---

## Qué hay en esta carpeta

| Archivo | Para qué |
|---|---|
| `HANDOFF - Dashboard v3.md` | este documento — qué cambiar y cómo, + el prompt |
| `dashboard-v3.css` | estilos listos para inyectar con `st.markdown` (clases `wz-*`) |
| `snippets-v3.py` | helpers de Python/Streamlit: formato, badges, KPI hero, matriz de confusión, recomendación de acción |
| `queries-v3.sql` | las 3 consultas reales (precisión, cohortes, efectividad) contra el esquema de `wurth.db` |
| `mejoras-v3.md` | **patch de 7 mejoras** sobre el `dashboard.py` ya implementado (antes/después + prompt) |
| `format-es-AR.txt` | reglas de formato de números y tono (es-AR / voseo) |
| `icons.txt` | mapeo estable emoji → significado |

> Todo está pensado para **Streamlit con CSS-in-Python**, que es como ya está hecho
> tu dashboard. No cambia el stack: inyectás un `<style>`, y renderizás componentes
> como strings HTML con `st.markdown(..., unsafe_allow_html=True)`.

---

## El principio rector

La v2/v3 convierte el dashboard de **"¿cómo están los números?"** a **"¿qué hago hoy?"**.
Cada pantalla abre con una acción, no con una grilla de KPIs iguales. Mantené el
lenguaje visual actual (blanco, tarjetas, riesgo = color, Source Sans 3) — solo
cambian jerarquía, orientación a la acción y un par de pantallas nuevas.

## Los 12 cambios (en orden de impacto)

**Layout / jerarquía**
1. **KPI hero dominante** — en vez de 5 KPIs del mismo tamaño, uno grande manda
   (el de riesgo elevado). El resto baja a una tira secundaria. → `hero_kpi()`, `.wz-stat`
2. **Banner de acción del día** arriba de cada pantalla: *"4 vendedores necesitan
   reunión esta semana"*. → `banner()`
3. **Columna "Acción sugerida"** en la tabla de vendedores (Crítico→reunión, etc.). → `accion_tag()`
4. **Más aire**: padding de filas, separación entre secciones, agrupación.
5. **Charts sin ruido**: sacar gridlines fuertes, labels afuera de las barras,
   y poner el dato clave como texto (*"% se va antes del mes 7"*).
6. **Estados reales**: vacío ("sin vendedores en riesgo 🎉"), carga (skeletons),
   error de conexión.

**Inteligencia del producto**
7. **#1 Explicabilidad del score** — desglose ponderado "por qué este 9"
   (caída 3m +2.0, onboarding +2.0…). → `score_breakdown_rows()`
8. **#2 Trayectoria del score** — Δ vs mes anterior (▲ rojo / ▼ verde) en cada fila,
   y mini-historial de 6 meses en el detalle. → `score_delta()`
9. **#3 Cohortes** en Historial: curva de supervivencia del equipo + tabla de
   retención por cohorte de ingreso.
10. **#1 Precisión del modelo** (pantalla nueva 🎯): matriz predicción vs. resultado
    real — ¿el score predijo las fugas? → `matriz_confusion_html()`
11. **#2 Recomendación de acción** en el detalle del vendedor: qué intervención
    funcionó para perfiles similares. → `recomendar_accion()`

**Oficio**
12. **#4 Accesibilidad** (forma ▲◆■● + color en badges), **#3 formato unificado**
    (`fmt_*`), **densidad** ajustable en tablas, y **timestamp de frescura** en el header.

> Las pantallas nuevas que NO tienen datos todavía (Precisión, cohortes, efectividad
> por perfil) usan números de ejemplo en `snippets-v3.py`. **Conectalas a datos reales**:
> los comentarios en el código dicen exactamente qué query hace falta.

---

## Cómo aplicarlo (paso a paso)

1. Copiá `dashboard-v3.css` y `snippets-v3.py` al repo (p. ej. en `assets/` y `src/`).
2. Al inicio de `dashboard.py`, inyectá el CSS una vez:
   ```python
   st.markdown(f"<style>{open('assets/dashboard-v3.css').read()}</style>",
               unsafe_allow_html=True)
   from src.snippets_v3 import *   # o importá lo que uses
   ```
3. Pantalla por pantalla, reemplazá el bloque de KPIs por `hero_kpi()` + tira de
   `.wz-stat`, agregá el `banner()` arriba, y sumá la columna de acción a la tabla.
4. Mapeá los nombres de columnas de los snippets a tu esquema real
   (`score`, `nivel`, `senales`, `riesgo_base`, `meses`…).
5. Para Precisión, cohortes y efectividad: enchufá las queries reales (ver comentarios).
6. Revisá `format-es-AR.txt` e `icons.txt` y pasá todo el copy/números por esas reglas.

**No rehagas el stack ni cambies la paleta.** Es una capa de presentación sobre la
lógica que ya tenés (`src/score_engine.py` sigue igual).

---

## Datos reales — leé esto (revisé tu esquema)

Repasé `wurth.db` (tablas `vendedores`, `ventas_mensual`, `grupos`, `intervenciones`).
Las 3 consultas listas están en **`queries-v3.sql`**. Resumen de qué tan enchufable
es cada una:

- **✅ Cohortes (#3)** — directo. Sale solo de `fecha_ingreso` / `fecha_egreso`. Query lista.
- **✅ Efectividad por perfil (#2)** — directo. La tabla `intervenciones` ya guarda
  `score_inicial`; el `score_actual` se calcula en vivo en Python (como ya hace
  `intervenciones.calcular_impacto`). Query + el join en Python están en el `.sql`.
- **⚠️ Precisión del modelo (#1)** — **tiene un bloqueante:** el score **no se guarda**
  (CLAUDE.md dice "el score NO es una foto mensual", se calcula al vuelo). No hay
  histórico contra el cual validar. Dos salidas, ambas en `queries-v3.sql`:
  - **Camino A (recomendado):** crear una tabla `score_snapshot` y empezar a volcar
    una foto del score cada cierre de mes. Simple, pero necesitás esperar 1-2 meses
    para tener con qué comparar.
  - **Camino B (backfill):** como `ventas_mensual` sí tiene el histórico, se puede
    **recalcular** el score "como era" en meses pasados corriendo `score_engine` con
    un corte de período. Te da la matriz **ya**, sin esperar.

  Mi recomendación: hacé **las dos** — prendé el snapshot mensual ya (barato, no te
  va a doler nunca más) y, si querés el dato hoy, pedile a Claude el backfill.

---

## PROMPT para Claude Code (copiá y pegá)

```
Tengo el dashboard Streamlit de alertas de rotación de Würth (este repo). Quiero
aplicarle un rediseño "v3" que ya está especificado en la carpeta handoff/.

Antes de tocar nada, leé:
- handoff/HANDOFF - Dashboard v3.md   (qué cambiar y cómo)
- handoff/dashboard-v3.css            (estilos, clases wz-*)
- handoff/snippets-v3.py              (helpers de componentes)
- handoff/queries-v3.sql              (las 3 consultas reales a wurth.db)
- handoff/format-es-AR.txt            (reglas de formato y tono es-AR)
- handoff/icons.txt                   (iconos)

Después explorá el código actual (dashboard.py, pages/*.py, src/score_engine.py,
src/intervenciones.py) para entender el esquema de datos y de dónde sale cada número.

Reglas:
- NO cambies el stack (sigue Streamlit + CSS-in-Python) ni la paleta ni la tipografía.
- Es una capa de presentación: src/score_engine.py y el cálculo del score NO se tocan.
- Aplicá el formato de números y el tono de voseo de format-es-AR.txt en TODO el copy.
- Para los datos nuevos, usá queries-v3.sql contra wurth.db (NO inventes números):
  cohortes y efectividad son directos; para Precisión del modelo, primero
  proponeme implementar la tabla score_snapshot (camino A) y/o el backfill recalculando
  desde ventas_mensual (camino B), y avisame cuál preferís antes de codear esa pantalla.
- Respetá la regla del repo: SOLO LECTURA sobre Informix/SQL Server/MySQL; lo único
  que se escribe es wurth.db.

Empezá por la pantalla Inicio: inyectá el CSS, reemplazá la fila de KPIs por un KPI
hero dominante + tira secundaria, agregá el banner de acción del día y la columna
"Acción sugerida" en la tabla de vendedores. Mostrame el diff de esa pantalla y cómo
queda antes de seguir.

Trabajá pantalla por pantalla, pidiéndome confirmación entre cada una.
```

---

### Referencia visual
La recreación interactiva de toda la v3 (las 6 pantallas con toggle antes/después +
Precisión, resumen semanal, móvil y estados) está en
`../ui_kits/dashboard/compare.html`. Abrila para ver el objetivo de cada cambio.
