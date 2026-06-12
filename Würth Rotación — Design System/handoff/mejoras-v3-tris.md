# Mejoras v3-tris — última tanda de pulido

4 cosas sobre el `dashboard.py` actual. Son menores y, después de esto, el tablero
está terminado: más pulido entraría en rendimientos decrecientes. Todo el "antes" es
código real de tu archivo. Orden por impacto: **#1 y #4 primero**.

> Requiere `src/snippets_v3.py` con la versión de esta carpeta (el `wz_badge` debe
> aceptar `title=` y anteponer la forma ▲◆■●).

---

## 1 · La tabla se contradice con el banner (lo más visible)

El banner dice *"empezá por los 20 de mayor riesgo"*, pero la tabla muestra
`df.head(5)` y esconde el resto en un expander — **incluso filtrando por Crítico/Alto**.
Si hay 30 críticos, el supervisor ve 5. Para un "foco = 20", mostrá los accionables.

**Antes:**
```python
if busqueda_sc:
    ...
    df_show = df[mask]
    df_extra = pd.DataFrame()
elif sup_sel != "Todos los supervisores":
    df_show = df
    df_extra = pd.DataFrame()
else:
    df_show = df.head(5)
    df_extra = df.iloc[5:]
```
**Después** (mostrar todo cuando hay una intención de foco: filtro de riesgo, búsqueda
o supervisor; top-5 solo en la vista "Todos" sin filtrar):
```python
_foco_activo = filtro in ("Crítico", "Alto") or busqueda_sc or sup_sel != "Todos los supervisores"

if busqueda_sc:
    df_show, df_extra = df[mask], pd.DataFrame()
elif _foco_activo:
    df_show, df_extra = df, pd.DataFrame()      # no escondas a los accionables
else:
    df_show, df_extra = df.head(FOCO_SEMANA), df.iloc[FOCO_SEMANA:]   # "Todos": top 20
```
Y ajustá el caption del caso `else`:
```python
else:
    st.caption(f"Top {min(FOCO_SEMANA, len(df))} de {len(df)} vendedores por score. "
               f"Filtrá por nivel, supervisor o usá el buscador para ver el resto.")
```

---

## 2 · Accesibilidad: que el badge muestre la forma ▲◆■● (#4)

Tu `_bdg` arma el HTML a mano, así que el glifo de forma nunca aparece (el CSS sí lo
soporta). Delegá en `wz_badge`, que antepone la forma y conserva tu tooltip.

**Antes:**
```python
def _bdg(nivel, label=None):
    labels = {"critico": "Crítico", "alto": "Alto", "medio": "Medio", "bajo": "Bajo"}
    tip = _ZONA_TOOLTIP.get(nivel, "")
    return f'<span class="wz-badge {nivel}" title="{tip}">{label or labels[nivel]}</span>'
```
**Después:**
```python
def _bdg(nivel, label=None):
    tip = _ZONA_TOOLTIP.get(nivel, "")
    return wz_badge(nivel, label, title=tip)     # ▲ Crítico / ◆ Alto / ■ Medio / ● Bajo
```
> El `_score_circle` puede quedar como está (el círculo ya distingue por número).
> Esto aplica al badge de zona y al de riesgo en onboarding — heredan la forma gratis.

---

## 3 · Una sola tabla: onboarding `.ot` → `.wz-table`

La principal ya usa `.wz-table`; onboarding sigue con `.ot` (estilo viejo). Unificá
para tener una sola fuente de verdad.

**Cómo:**
1. En los **dos** bloques HTML de onboarding (el top-5 y el del expander), cambiá
   `<table class="ot">` por `<table class="wz-table">`.
2. Borrá del `<style>` inline el bloque `.ot { } .ot th { } .ot td { }`.
3. Queda con el header transparente en mayúsculas de la v3 — consistente con el resto.

---

## 4 · Estado de error en la carga (#5)

Hoy `cargar_datos()` se llama directo: si la base falla, el usuario ve un stack trace.

**Antes:**
```python
scores_df, grupos_df, sparks, ventanas_df, perm_egreso_prom, delta_map, _ts_datos = cargar_datos()
```
**Después:**
```python
try:
    scores_df, grupos_df, sparks, ventanas_df, perm_egreso_prom, delta_map, _ts_datos = cargar_datos()
except Exception:
    st.error("⚠️ No se pudo conectar a la base de datos. "
             "Los datos pueden estar desactualizados. Reintentá en unos minutos "
             "o avisá a sistemas si el problema persiste.")
    st.stop()
```
(Opcional, después del control de acceso, por si un director queda sin vendedores tras
el filtro por supervisor:)
```python
if len(scores_df) == 0:
    st.info("No hay vendedores asignados a tu vista todavía.")
    st.stop()
```

---

## PROMPT para Claude Code (copiá y pegá)

```
Última tanda de pulido sobre dashboard.py. Está en handoff/mejoras-v3-tris.md, con el
"antes" (código real de mi archivo) y el "después" de cada cambio. Son 4, menores.

Antes de tocar nada, confirmá que src/snippets_v3.py tenga la versión de handoff/
(wz_badge acepta title= y antepone la forma ▲◆■●). Si no, actualizalo.

Aplicá los 4 cambios en orden:
1. En el armado de df_show/df_extra: mostrá TODOS los vendedores cuando el filtro es
   Crítico/Alto, hay búsqueda, o hay supervisor seleccionado. Top-FOCO_SEMANA (20) solo
   en la vista "Todos" sin filtrar. Ajustá el caption acorde.
2. _bdg debe delegar en wz_badge para que aparezca la forma por nivel (accesibilidad).
3. Migrá las DOS tablas de onboarding de class="ot" a class="wz-table" y borrá el
   bloque .ot del <style> inline.
4. Envolvé cargar_datos() en try/except con st.error + st.stop() amable, y agregá el
   estado vacío opcional.

Reglas: no cambies el stack ni la paleta ni la tipografía; no toques src/score_engine.py.
Mostrame el diff de la pantalla Inicio y cómo queda. Después de esto el tablero queda
cerrado — no agregues nada que no esté en esta lista.
```

---

*Después de esta tanda, lo siguiente ya no es diseño sino producto y depende de datos
reales: la pantalla de Precisión del modelo (cuando tengas 1-2 meses de `score_historico`
acumulado) y la recomendación de acción por perfil. Medí esas con datos reales antes de
construirlas.*
