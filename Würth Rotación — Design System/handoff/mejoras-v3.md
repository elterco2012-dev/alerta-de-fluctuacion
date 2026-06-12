# Mejoras v3 — patch para Claude Code

Pasale esta carpeta `handoff/` (ya actualizada) a Claude Code apuntado a tu repo y el
prompt del final. Son **7 mejoras** sobre el `dashboard.py` que ya implementaste.
Reemplazá primero estos dos archivos en el repo por los de esta carpeta:

- `assets/dashboard-v3.css`  ← versión nueva (agrega `.wz-statcard`, `.wz-breakdown`, `.wz-recom`)
- `src/snippets_v3.py`       ← versión nueva (formato es-AR, badges con forma, recomendación, desglose)

> Todo el "antes" es código real de tu `dashboard.py` actual. El "después" usa los
> helpers de `snippets_v3.py`. Nada inventa números.

---

## 1 · Una sola fuente de estilos (consolidar CSS)

**Problema.** Conviven dos sistemas: `dashboard-v3.css` (clases `wz-*`) **y** un bloque
`<style>` inline gigante con las clases viejas (`.vt .sc .bdg .pill .kpi-card …`). La
tabla, los score-circles y los badges siguen usando las viejas, así que el CSS v3 no es
la fuente de verdad.

**Cómo.** Mová los tokens y estilos compartidos a `dashboard-v3.css` y borrá del bloque
inline todo lo que ya viva ahí. Donde el HTML usa `.sc`/`.bdg`/`.pill`, pasá a los
helpers `wz_score_circle`/`wz_badge`/`pill` (que rinden `.wz-*`). Dejá en el inline solo
lo específico de Streamlit (ocultar sidebar/header, `.block-container`). Objetivo: si
cambiás un color en el `.css`, cambia en toda la app.

---

## 2 · Formato es-AR consistente (rápido, muy visible)

**Antes** (tarjetas de zona — usa punto decimal):
```python
perm_str = f"{perm:.1f}m"                       # "4.1m"  ✗
...
<div class="zpct">{g['cumplimiento_plan_promedio']:.0f}% plan</div>
```
**Después:**
```python
perm_str = fmt_meses(round(perm, 1)) if pd.notna(perm) else "—"   # "4,1 m"  ✓
...
<div class="zpct">{fmt_num(g['cumplimiento_plan_promedio'])}% plan</div>
```

**Antes** (tabla de onboarding — número crudo):
```python
<td><b>{r['pct_plan_3m']}%</b></td>
```
**Después:**
```python
<td><b>{fmt_num(r['pct_plan_3m'])}%</b></td>
```
Regla: **ningún número va crudo a la pantalla** — siempre por `fmt_num` / `fmt_pct` /
`fmt_meses` / `fmt_pesos`. (Ver `format-es-AR.txt`.)

---

## 3 · Accesibilidad: forma + color en los badges (#4)

**Antes** (`_bdg` con clases viejas, solo color):
```python
def _bdg(nivel, label=None):
    labels = {"critico":"Crítico","alto":"Alto","medio":"Medio","bajo":"Bajo"}
    tip = _ZONA_TOOLTIP.get(nivel, "")
    return f'<span class="bdg bdg-{nivel}" title="{tip}">{label or labels[nivel]}</span>'
```
**Después** (delega en `wz_badge`, que antepone la forma ▲◆■● y conserva tu tooltip):
```python
def _bdg(nivel, label=None):
    tip = _ZONA_TOOLTIP.get(nivel, "")
    return wz_badge(nivel, label, title=tip)     # ▲ Crítico / ◆ Alto / ■ Medio / ● Bajo
```
Así un supervisor daltónico distingue el nivel por **forma**, no solo por color.

---

## 4 · La columna "Acción sugerida" no debe meter ruido

**Problema.** Hoy `accion_tag(nivel)` muestra "Monitoreo mensual" / "Seguimiento normal"
en filas `medio`/`bajo`, compitiendo con los críticos.

**Cómo.** El `accion_tag` nuevo ya recede `medio`/`bajo` (bajo = "—", colores tenues vía
CSS) y solo deja "pop" a crítico/alto. No tenés que cambiar la llamada — solo reemplazá
`snippets_v3.py`. El ojo va directo a quién requiere acción.

---

## 5 · Default accionable + no esconder a los que importan

**Antes:**
```python
filtro = st.radio("", ["Todos","Crítico","Alto","Viajantes","Televentas"],
                  horizontal=True, label_visibility="collapsed")
...
df_show = df.head(5)
df_extra = df.iloc[5:]
```
**Después** (arranca en "Requieren acción"; ese filtro muestra TODOS, no top-5):
```python
filtro = st.radio("",
    ["Requieren acción","Todos","Crítico","Alto","Viajantes","Televentas"],
    horizontal=True, index=0, label_visibility="collapsed")

if filtro == "Requieren acción":
    df = df[df.nivel_riesgo.isin(["critico","alto"])]
# ... resto de filtros igual ...

# No escondas a los accionables detrás del expander:
if filtro in ("Requieren acción","Crítico","Alto") or busqueda_sc or sup_sel != "Todos los supervisores":
    df_show, df_extra = df, pd.DataFrame()
else:
    df_show, df_extra = df.head(5), df.iloc[5:]
```

---

## 6 · Frescura del dato (#5) + manejo de error

**Frescura** — en el header, a la derecha del título:
```python
from datetime import datetime
ahora = datetime.now().strftime("%d %b %Y, %H:%M")
# dentro del flex del header, como segundo hijo:
{fresh(ahora)}        # rinde:  ● Actualizado: 02 jun 2026, 08:00
```
**Error** — envolvé la carga:
```python
try:
    scores_df, grupos_df, sparks, ventanas_df, perm_egreso_prom = cargar_datos()
except Exception as e:
    st.error("⚠️ No se pudo conectar a la base de datos. "
             "Los datos pueden estar desactualizados. Reintentá en unos minutos.")
    st.stop()
```
(Opcional, estado vacío: si `len(scores_df)==0`, mostrá un mensaje amable en vez de tablas.)

---

## 7 · Sumar lo "inteligente": desglose del score (#1) y recomendación (#2)

Streamlit no hace modales, pero un selector + detalle funciona perfecto. Debajo de la
tabla principal:
```python
st.markdown('<div class="sec-header">🔍 Ver detalle de un vendedor</div>', unsafe_allow_html=True)
opts = {f"{r['nombre']} ({int(r['id_vendedor'])})": r for _, r in df.iterrows()}
sel = st.selectbox("", ["—"] + list(opts), label_visibility="collapsed")
if sel != "—":
    r = opts[sel]
    labels = [SEÑAL_TAGS.get(s, (s,))[0] for s in r["señales_activas"]]   # etiquetas cortas
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Por qué este score**", unsafe_allow_html=True)
        st.markdown(score_breakdown_html(labels), unsafe_allow_html=True)
    with c2:
        if r["nivel_riesgo"] in ("critico","alto"):
            st.markdown(recomendacion_html(
                r["meses_activo"], r["grupo_riesgo_base"], labels, r["nivel_riesgo"]
            ), unsafe_allow_html=True)
```
- `score_breakdown_html` → barras ponderadas "base +1, caída 3m +2, …" (ajustá `SIGNAL_PESO` a tu `score_engine.py`).
- `recomendacion_html` → "Reunión 1:1 · ↓1,8 de score · lo que mejor funcionó para nuevos en zona quemada". **Conectá `EFECTIVIDAD` a datos reales** con el bloque #3 de `queries-v3.sql`.

> El Δ de trayectoria (▲/▼ por fila, `score_delta`) sigue pendiente del `score_snapshot`
> mensual — ver `queries-v3.sql` (#1). Cuando lo tengas, agregá la columna "Score · Δ".

---

## PROMPT para Claude Code (copiá y pegá)

```
Implementá las mejoras v3 sobre el dashboard.py de este repo. Está todo en handoff/.

1) Reemplazá assets/dashboard-v3.css y src/snippets_v3.py por los de handoff/ (son
   versiones nuevas, superset de las actuales — revisá que los imports sigan vivos).
2) Aplicá, en orden, los 7 cambios de handoff/mejoras-v3.md. Cada uno trae el "antes"
   (código real de mi dashboard.py) y el "después".
3) Mostrame el diff de la pantalla Inicio y cómo queda antes de tocar las demás
   (Por supervisor, Intervenciones, Costo, Historial, Actividad) replicando el mismo
   patrón donde aplique.

Reglas:
- No cambies el stack (Streamlit + CSS-in-Python) ni la paleta ni la tipografía.
- No toques src/score_engine.py: el cálculo del score queda igual.
- Pasá TODOS los números por los helpers fmt_* (ver handoff/format-es-AR.txt) y los
  badges por wz_badge (forma + color). Nada de números crudos ni "%.1f" con punto.
- Para datos nuevos usá handoff/queries-v3.sql (cohortes y efectividad son directos);
  la matriz de Precisión depende de crear score_snapshot — proponémelo antes de codearla.
- Respetá la regla del repo: SOLO LECTURA sobre las bases de producción; solo se
  escribe wurth.db.

Trabajá pantalla por pantalla, pidiéndome confirmación entre cada una.
```
