# Mejoras v3-bis — segundo pase de pulido

5 mejoras sobre el `dashboard.py` que ya tenés andando (con `score_historico`, roles,
Δ mes real). Todo el "antes" es código real de tu archivo actual. Son pulido, no
arreglos — ninguna es grave. Prioridad: **#1 y #2 primero** (rápidas y muy visibles).

> Requiere los helpers de `snippets-v3.py` (ya los importás). Si tu `wz_badge` no acepta
> `title=`/`shape=`, actualizá `src/snippets_v3.py` con la versión de esta carpeta.

---

## 1 · Formato es-AR consistente (lo más visible)

La tabla principal ya usa `fmt_num`, pero quedaron dos lugares con número crudo.

**Antes** — tarjetas de zona (`_zona_cards_html`):
```python
perm_str = f"{perm:.1f}m" if pd.notna(perm) else "—"
...
<div class="zpct">{g['cumplimiento_plan_promedio']:.0f}% plan</div>
```
**Después:**
```python
perm_str = fmt_meses(round(perm, 1)) if pd.notna(perm) else "—"   # "4,1 m"
...
<div class="zpct">{fmt_num(g['cumplimiento_plan_promedio'])}% plan</div>
```

**Antes** — tabla de onboarding (`_onb_rows_html`):
```python
<td><b>{r['pct_plan_3m']}%</b></td>
```
**Después:**
```python
<td><b>{fmt_num(r['pct_plan_3m'])}%</b></td>
```

> Regla: ningún número va crudo a pantalla. Buscá en todo el archivo `:.0f}`, `:.1f}`
> y `']}%` y pasalos por `fmt_num` / `fmt_pct` / `fmt_meses` / `fmt_pesos`.

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
> El badge de "Riesgo" en la tabla de onboarding usa `_bdg(nivel)` → hereda la forma
> gratis. (El `_bdg(z_n, z_l + warn)` de zona también; el ⚠️ queda después de la forma,
> está bien.)

---

## 3 · Una sola tabla (consolidar `.ot` → `.wz-table`)

La tabla principal usa `.wz-table`; onboarding sigue con `.ot` (estilo viejo). Unificá
para tener una sola fuente de verdad de estilos de tabla.

**Cómo:**
1. En los dos bloques HTML de onboarding, cambiá `class="ot"` por `class="wz-table"`.
2. Borrá el bloque `.ot { } .ot th { } .ot td { }` del `<style>` inline.
3. Si querés mantener el header gris de onboarding (la `.wz-table` tiene header
   transparente con mayúsculas), está perfecto que herede el estilo v3 — queda
   consistente con el resto.

---

## 4 · Bajar de 8 a 7 columnas: fusionar Δ mes + Score

Con muchas pills, la tabla de 8 columnas se aprieta (por eso el `overflow-x:auto`).
El score y su variación se leen mejor juntos ("9 ▲2" de un golpe).

**Antes** — `_tabla_rows` (dos celdas separadas) + `_tabla_html` (dos `<th>`):
```python
      <td>{accion_tag(nivel)}</td>
      <td>{score_delta(delta)}</td>
      <td>{_score_circle(r['score'], nivel)}</td>
    </tr>"""
```
```python
  <th>Acción sugerida</th>
  <th title="Variación vs el mes anterior...">Δ mes ⓘ</th>
  <th title="Crítico 8-10...">Score ⓘ</th>
```
**Después** — una sola celda score+Δ:
```python
      <td>{accion_tag(nivel)}</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px;">
          {_score_circle(r['score'], nivel)}{score_delta(delta)}
        </div>
      </td>
    </tr>"""
```
```python
  <th>Acción sugerida</th>
  <th title="Score 1-10 (Crítico 8-10 · Alto 6-7 · Medio 4-5 · Bajo 1-3) y su variación vs el mes anterior (▲ subió = empeoró, ▼ bajó = mejoró; vacío si no hay historial)">Score · Δ mes ⓘ</th>
```

---

## 5 · Estado de error en la carga de datos (#5)

Ya tenés el timestamp de frescura; falta el manejo de fallo de conexión. Hoy un error
de base muestra un stack trace de Python al usuario.

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

if len(scores_df) == 0:
    st.success("✅ No hay vendedores para mostrar con los datos actuales.")
    st.stop()
```

---

## PROMPT para Claude Code (copiá y pegá)

```
Aplicá un segundo pase de pulido sobre el dashboard.py de este repo. Está en
handoff/mejoras-v3-bis.md, con el "antes" (código real de mi archivo) y el "después"
de cada cambio.

Antes de tocar nada, confirmá que src/snippets_v3.py tenga la versión de handoff/
(wz_badge debe aceptar title= y anteponer la forma ▲◆■●). Si no, actualizalo.

Aplicá los 5 cambios en orden:
1. Pasá TODOS los números crudos por los helpers fmt_* (zona: perm y % plan;
   onboarding: % plan). Buscá en todo el archivo ':.0f}', ':.1f}' y "']}%".
2. _bdg debe delegar en wz_badge para que aparezca la forma por nivel (accesibilidad).
3. Migrá la tabla de onboarding de class="ot" a class="wz-table" y borrá el bloque .ot
   del <style> inline.
4. Fusioná las columnas "Δ mes" y "Score" de la tabla principal en una sola
   ("Score · Δ mes"), con el círculo y el delta lado a lado.
5. Envolvé cargar_datos() en try/except con un st.error + st.stop() amable, y agregá
   un estado vacío si no hay vendedores.

Reglas: no cambies el stack ni la paleta ni la tipografía; no toques src/score_engine.py.
Mostrame el diff de la pantalla Inicio y cómo queda antes de dar por cerrado.
```
