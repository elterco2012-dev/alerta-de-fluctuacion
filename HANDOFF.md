# HANDOFF — Würth Argentina: Sistema de Alertas de Rotación
**Fecha:** 12 de junio de 2026  
**Rama de trabajo:** `claude/sales-turnover-alerts-l8pO6`  
**Estado:** sesión cerrada por migración de cuenta — todo commiteado y pusheado.

---

## Qué es esto

Sistema de detección temprana de riesgo de fuga de vendedores para Würth Argentina.
Dashboard Streamlit + motor de scoring basado en reglas ponderadas.
Lee de SQLite local (`data/wurth.db`) que se sincroniza diariamente desde tres fuentes:
Informix (ERP), MySQL Reactor (CRM), SQL Server SUN (cobranza).

**No hay datos simulados.** Todo es producción real. `data/wurth.db` no se commitea (.gitignore).

---

## Estado al cierre de sesión

### Completado en esta sesión

| # | Qué | Archivo(s) |
|---|---|---|
| 1 | Clasificación Televentas corregida: solo `zone='TVTAS'`, eliminado fallback `vart=2` | `scripts/inicializar_db.py` |
| 2 | VERTR_EXCLUIDOS (1500/7777/9499) purgados explícitamente post-insert en SQLite | `scripts/inicializar_db.py` |
| 3 | `diagnostico_vart.py` creado: cruza f040 con SQLite, exporta CSV con discrepancias | `scripts/diagnostico_vart.py` |
| 4 | `badge()` ahora acepta `title=` (era requerido por `_bdg()` en dashboard) | `src/snippets_v3.py` |
| 5 | `accion_tag("bajo")` muestra `—` en vez de "Seguimiento normal" (menos ruido) | `src/snippets_v3.py` |
| 6 | `_bdg()` delega en `wz_badge()` → badges ahora muestran forma ▲◆■● | `dashboard.py` |
| 7 | Tabla onboarding migrada de `.ot` a `.wz-table`; CSS `.ot` eliminado | `dashboard.py` |
| 8 | Columnas Score + Δ mes fusionadas en una (tabla de 8 → 7 columnas) | `dashboard.py` |
| 9 | Vista default top 5 (no top 20); muestra todo cuando hay filtro activo | `dashboard.py` |
| 10 | `try/except` en `cargar_datos()` con `st.error` amable + estado vacío | `dashboard.py` |
| 11 | CLAUDE.md actualizado con estructura completa, decisiones y problemas conocidos | `CLAUDE.md` |

### Pendiente (en orden de prioridad)

1. **Correr `inicializar_db.bat` + `diagnostico_vart.py` en producción** para aplicar
   la clasificación nueva y confirmar 0 discrepancias. El diagnóstico anterior mostraba
   1 discrepancia (Kalpokas 1500) que ya tiene fix commiteado — solo falta correr el bat.
   Secuencia: `git pull` → `del scripts\diagnostico_vart.py` si existe local → `inicializar_db.bat` → `sincronizar_todo.bat` → `diagnostico_vart.py`.

2. **Precisión del modelo** — `pages/Precision.py` existe pero muestra datos de ejemplo.
   Bloqueado hasta tener tabla `score_snapshot`. Dos caminos (ver `scripts/queries-v3.sql`):
   - **Camino A** (recomendado): activar guardado mensual del score → esperar 1-2 meses.
   - **Camino B** (backfill): recalcular scores históricos desde `ventas_mensual` con
     `scripts/backfill_scores.py` para tener la matriz ya.

3. **Recomendación de acción** — `recomendar_accion()` en `snippets_v3.py` está
   implementada pero devuelve `None` si no hay datos reales de efectividad.
   Conectarla cuando haya suficientes intervenciones medidas (ver query #3 en `queries-v3.sql`).

4. **Cohortes de retención** en `pages/Historial.py` — la query está lista en
   `queries-v3.sql` (#2). Solo requiere conectarla a la página.

5. **Re-correr `scripts/validar_pesos.py`** periódicamente para auditar que el modelo
   siga separando. Separación actual (REF=8): ~10.3. Conviene re-correr cada vez que
   haya suficientes egresados nuevos en el historial.

### No hacer todavía

- Reemplazar `data/wurth.db` con ML — esperar 6+ meses de datos reales.
- Cambiar la lógica de scoring sin actualizar `CLAUDE.md`.
- Commitear `data/wurth.db` ni `data/estado_alertas.json`.
- Cualquier INSERT/UPDATE/DELETE sobre Informix (MSPA), SQL Server (SUNDB) o MySQL (Reactor).

---

## Decisiones técnicas críticas tomadas (y por qué)

### Clasificación Televentas
- **Antes:** `vart=2` clasificaba como Televentas. Resultaba en falsos positivos (viajantes
  de campo con `vart=2` por error de carga en el ERP).
- **Ahora:** solo `f040.zone = 'TVTAS'` clasifica como Televentas. Hay exactamente 3 grupos
  TVTAS (971, 972, 973), ~56 vendedores. Resto (incluidos grupos 200-209) son Viajantes.
- **Verificar:** después de cada `inicializar_db.bat` correr `scripts/diagnostico_vart.py`.

### Navegación (login persistente)
- La identidad del usuario viaja en `?usuario=NombreUsuario` en todos los links.
- `nav_links()` en `snippets_v3.py` propaga `?usuario=` automáticamente.
- El iframe de `st.components.v1.html()` no permite `window.parent.location.replace()`
  (SecurityError de sandbox). Solución: inyectar un `<script>` en
  `window.parent.document.head` que corre en contexto sin sandbox.
- Auto-login via `localStorage` para no mostrar el selector en cada recarga.

### Score (no cambiar sin leer CLAUDE.md)
- `RIESGO_REFERENCIA = 8.0` → score 1-10.
- 9 señales activas, 6 deshabilitadas (problemas de cobertura de datos en egresados).
- Acción por **ranking** (mayor score primero), NO por umbral fijo.
- La clave `descripcion=` de cada señal es su ID en todo el sistema — NO cambiar el
  string aunque cambie el umbral numérico.

### UI
- `badge(nivel, label, shape=True, title="")` — el parámetro `title=` es obligatorio
  en `_bdg()`. Si se regenera el helper, incluirlo.
- Tabla principal: 7 columnas (`Score · Δ mes` fusionados).
- Vista default: top 5; muestra todo cuando hay filtro activo (Crítico/Alto/supervisor/búsqueda).

---

## Errores conocidos al cierre

| Error | Causa | Solución |
|---|---|---|
| `badge() got unexpected kwarg 'title'` | `badge()` no tenía el param `title=` | **Resuelto** — commiteado en `24be1e9` |
| Kalpokas (1500) aparece en diagnóstico | Registro viejo en SQLite de run anterior | **Resuelto** — fix en `2ebc9c4`; requiere correr `inicializar_db.bat` |
| `git pull` falla con "untracked files" | `diagnostico_vart.py` existía local sin trackear | `del scripts\diagnostico_vart.py && git pull` |
| Login no navega al hacer click en "Ingresar" | Sandbox de iframe Streamlit bloquea navegación | **Resuelto** — parent DOM script injection en `acceso.py` |
| Selector de perfil aparece en cada página | Links sin `?usuario=` | **Resuelto** — `nav_links()` propaga el param automáticamente |

---

## Comandos importantes

```bat
REM — Inicializar / re-poblar la base (solo cuando cambia estructura de vendedores)
inicializar_db.bat

REM — Sincronizar datos desde las tres fuentes (correr diario)
sincronizar_todo.bat

REM — Verificar clasificación Televentas/Viajante
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\diagnostico_vart.py

REM — Levantar el dashboard
streamlit run dashboard.py
REM o bien:
iniciar_dashboard.bat

REM — Automatización completa (sync + alertas) — lo que corre el Programador de Windows
sync_y_alertas.bat

REM — Probar canal de email
scripts\test_email.bat
```

```bash
# Git — bajar cambios y resolver conflicto habitual
del scripts\diagnostico_vart.py   # si existe local sin trackear
git pull
```

---

## Estructura de archivos clave

```
dashboard.py          ← pantalla Inicio (gerencia/director)
src/
  score_engine.py     ← motor de scoring — NO tocar sin actualizar CLAUDE.md
  snippets_v3.py      ← todos los helpers HTML/formato/navegación
  acceso.py           ← control de acceso por rol + login
assets/
  dashboard-v3.css    ← estilos únicos (clases wz-*)
scripts/
  inicializar_db.py   ← crea/repobla wurth.db (Python 32-bit, ODBC)
  diagnostico_vart.py ← verifica clasificación TV/VJ (correr post-inicializar)
  backfill_scores.py  ← recalcula score_historico (correr tras cambios en el motor)
  validar_pesos.py    ← audita el modelo: lift por señal + barrido REF
data/
  wurth.db            ← SQLite local (NO commitear)
  estado_alertas.json ← estado de alertas (NO commitear)
```

---

## Entorno de Python (dos versiones en la misma máquina Windows)

| Uso | Versión | Ruta aproximada |
|---|---|---|
| Scripts de sync e inicialización (ODBC/Informix) | **32-bit** 3.12 | `C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\` |
| Dashboard Streamlit + alertas (Outlook COM) | **64-bit** | `python` en PATH |

`sync_y_alertas.bat` maneja el split automáticamente.

---

*Leer `CLAUDE.md` completo antes de tocar cualquier archivo del proyecto.*
