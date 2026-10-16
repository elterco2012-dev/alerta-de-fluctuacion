# Auditoría integral — Sistema de alerta temprana de rotación de vendedores

**Würth Argentina · octubre 2026**
**Base auditada:** rama `claude/optimistic-cerf-a2g7yw`, partiendo de `35b4db2` (merge del PR #81).

## Alcance y método

- **Qué se revisó.** Se leyó el repositorio completo: motor, ingesta, páginas, alertas, scripts y documentación. Además se escribieron tests con datos **sintéticos**.
- **Qué no se tocó.** No hubo conexión a Informix, Reactor ni SUN. No se usó `data/wurth.db`, que no está en el repo. No se envió ningún correo.
- **Cómo se trataron los hallazgos.** Los de los revisores paralelos (seguridad, ingesta, UX) se **verificaron contra el código** antes de incluirlos. Lo que no pudo verificarse figura como "a confirmar".
- **Sin métricas nuevas sobre datos reales.** Ninguna cifra de desempeño del modelo de este informe sale de datos reales nuevos. Los números históricos (separación 10,3, detección ~15 %, etc.) vienen de CLAUDE.md y se discuten críticamente.
- **Herramientas para medir.** Para obtener las cifras reales se dejaron dos herramientas de solo lectura: `scripts/chequeo_integridad.py` y `scripts/evaluar_ranking.py`.

---

## A. Diagnóstico ejecutivo

El sistema está bien encaminado en lo conceptual:

- usa reglas explicables;
- prioriza por ranking y no por un umbral;
- trata el dato faltante con cuidado en varias señales;
- documenta las decisiones con honestidad poco común.

**Hoy no se puede afirmar que el ranking anticipe las bajas mejor que mirar solo la antigüedad.** Hay cuatro razones:

1. **El score que ve el supervisor no es el que se validó.**
   - En vivo, el motor toma "las 3 filas más recientes" de cada tabla. Incluye el mes en curso, que está incompleto.
   - Por cómo está escrita la ingesta, también puede incluir filas de **meses futuros**. Pasa seguro en `balanza_clientes`, y posiblemente en el plan y en los datos de Reactor.
   - El backfill, en cambio, corta en meses cerrados.
2. **La validación histórica es optimista por construcción.**
   - El "riesgo de grupo" usa bajas posteriores al período evaluado, incluida la del propio vendedor.
   - La referencia de calibración (REF) se eligió mirando la misma mitad de egresados que después se reporta como "out-of-sample".
   - Egresados y activos se comparan en ventanas de tiempo distintas.
3. **La etiqueta mezcla renuncias con despidos.** `motivo_egreso` nunca se carga. Una señal de "plan bajo" que "predice" despidos por bajo rendimiento es circular, y además empuja a leer el ranking como una lista de candidatos a desvincular.
4. **La población de mayor riesgo puede no estar en el sistema.** El sync diario no da de alta a los vendedores nuevos: solo `inicializar_db.py` los inserta, y se corre a mano.

En seguridad y privacidad hay un problema urgente que **no es de código**: el repositorio es **público** y su historia contiene capturas de producción con datos personales de empleados. Además, la aplicación no tiene autenticación: la identidad viaja en un parámetro de la URL.

Se implementó un conjunto de mejoras seguras y reversibles que no cambian ningún resultado de scoring (ver F). Las de mayor valor:

- una suite de 98 tests;
- un evaluador point-in-time del ranking;
- un chequeo de integridad;
- la corrección de una fuga de confidencialidad en Intervenciones;
- la eliminación de datos de ejemplo que se escribían en la base real;
- textos al supervisor con los umbrales vigentes.

Los cambios de scoring, autenticación, ingesta y configuración quedan **propuestos y a la espera de aprobación** (sección E).

### Mapa del flujo real

```
Informix (MSPA) ──sincronizar_informix.py──► ventas_mensual, balanza_clientes,
   (f040, sbas, vplan, kund)                  vendedores (solo UPDATE), grupos.riesgo_base
Reactor (MySQL) ──sincronizar_reactor.py───► actividad_mensual, ausencias_mensual,
                                              acompanamiento_mensual
SUN (SQL Server)──sincronizar_sundb.py─────► ventas_mensual.cobranza_* (UPDATE)
f040 ───────────inicializar_db.py (manual)─► vendedores (INSERT/UPSERT), grupos
                         │
                         ▼
            data/wurth.db (SQLite, única base escrita)
                         │
   score_engine.calcular_scores()  ── modo vivo: dashboard, páginas, enviar_alertas
                         │          └ modo corte (hasta_mes): backfill / snapshot
                         ▼
   score_historico ◄── backfill_scores.py (18 meses) y snapshot_mensual.py (diario,
                       recalcula el mes anterior; no es una foto congelada)
                         │
   validar_pesos.py / Precision / Aprendizaje / evaluar_ranking.py (nuevo)
                         │
   enviar_alertas.py ── Outlook COM ── estado_alertas.json (re-alerta a 7 días)
   pages/Intervenciones.py ── tabla intervenciones (SQLite)
```

---

## B. Diez hallazgos principales

### 1. [P0] Datos personales de empleados expuestos públicamente

- **Evidencia:**
  - GitHub informa `visibility: public` para `elterco2012-dev/alerta-de-fluctuacion`.
  - `Würth Rotación — Design System/uploads/` contiene capturas del dashboard de producción. Una fue verificada directamente y el revisor reporta otras cuatro. Muestran nombre completo, legajo, score, nivel y señales individuales, como ausencias.
  - El commit `18ca0e5` incluyó `data/wurth.db`, después retirado en `b22ed98` pero todavía presente en la historia. Según el revisor parece una base semilla con nombres reales de supervisores; hay que confirmarlo.
  - `src/intervenciones.py` tenía observaciones inventadas ("problemas personales…") atribuidas a supervisores reales con nombre y apellido. Se eliminaron del árbol, pero siguen en la historia.
- **Impacto:** exposición de datos personales y de evaluaciones de desempeño de empleados (Ley 25.326). Es un riesgo reputacional y legal, independiente de la calidad del modelo.
- **Solución (requiere acción del dueño del repositorio):**
  1. Pasar el repo a privado.
  2. Borrar `uploads/`.
  3. Purgar la historia (`git filter-repo` sobre `uploads/`, `data/wurth.db` y los datos de ejemplo) y forzar el push.
  4. Revisar si hay forks.
  5. Informar a RRHH/Legales.

### 2. [P0] La identidad no está autenticada

- **Evidencia:** `src/acceso.py:314` toma el usuario de `st.query_params["usuario"]`. "Gerencia" da acceso total (`acceso.py:168-170`) y figura en el selector para cualquiera. `iniciar_dashboard.bat` levanta Streamlit sin `--server.address` y sin `.streamlit/config.toml`, así que escucha en todas las interfaces y muestra los tracebacks completos.
- **Impacto:** cualquiera con acceso a la red y la URL ve toda la empresa. Además, reenviar un link reenvía el rol.
- **Solución propuesta (proporcional, requiere aprobación):** links personales firmados `?usuario=X&t=HMAC(secreto, X)`.
  - Los genera Sistemas con un script; el secreto vive en `.env`.
  - `resolver()` valida con `hmac.compare_digest`.
  - "Gerencia" sale del selector público.
  - Se suma `config.toml` con `client.showErrorDetails = "type"` y `browser.gatherUsageStats = false`, y una regla de firewall que limite el puerto 8501 a la subred corporativa.
  - A mediano plazo, autenticación Windows con IIS como proxy inverso, si IT la soporta.

### 3. [P0] El score en vivo usa meses incompletos y posiblemente futuros

- **Evidencia:**
  - En modo vivo las consultas no tienen tope de fecha (`src/score_engine.py:246-300`). Para cada tabla se toman las 3 filas más recientes con `head(3)` (`:318-327`).
  - El mes en curso entra a `ventas_mensual` con ventas parciales contra el plan completo. El test `test_modo_vivo_incluye_mes_en_curso_parcial` lo demuestra: con 70 %, 70 % y 10 % (mes recién empezado) se enciende "plan bajo"; con los meses cerrados, no.
  - `sincronizar_informix.py:296` registra cada cliente "perdido" **12 meses después de su última compra**, sin tope superior. Eso crea filas en `balanza_clientes` en meses que todavía no ocurrieron.
  - `vplan` (`:315`) y las consultas de Reactor se filtran solo con `>= inicio`.
- **Impacto, en modo vivo:**
  - La balanza de los "últimos 2 meses" puede ser la de dos meses futuros: un número negativo igual a la cantidad de clientes que compraron hace poco. Así la señal marca a quien **tiene** cartera activa, o sea que queda invertida.
  - El ticket nunca dispara, porque las filas futuras tienen ticket 0.
  - El plan baja artificialmente a comienzo de mes.
  - El Δ mes compara ese score contra un score de meses cerrados.
  - Alertas y dashboard operan con un modelo distinto del validado.
  - Posiblemente las medianas usadas para recalibrar umbrales en 2026 (balanza −49) se midieron sobre datos contaminados. **A confirmar** con `chequeo_integridad.py`, punto 1.
- **Solución propuesta (cambia scores, requiere aprobación):**
  - En modo vivo, filtrar `anio*100+mes <= último mes cerrado`, igual que el backfill.
  - En los sync, descartar las claves posteriores al mes actual.
  - Medir antes y después con `evaluar_ranking.py`.

### 4. [P0] La validación histórica sobreestima la capacidad predictiva

- **Evidencia:**
  - `grupos.riesgo_base` se recalcula con **todas** las bajas, incluidas las posteriores al corte y la del propio vendedor (`sincronizar_informix.py:643-672`). El backfill usa ese valor de hoy para cualquier mes pasado; está documentado en el test `test_backfill_usa_riesgo_base_actual_sin_corte_temporal`.
  - `validar_pesos.py:293` elige el mejor REF maximizando la separación sobre `egr_recientes` (`:197`), que es la misma mitad que se presenta como "OUT-OF-SAMPLE". La poda de señales también se decidió con el Δsep calculado sobre esa mitad.
  - Los egresados se miden en los 3 meses previos a su egreso (`:161`) y los activos en sus 3 meses más recientes (`:184`). Son períodos distintos, con cobertura de datos distinta.
  - `snapshot_mensual.py` corre todos los días y recalcula el mes anterior con `INSERT OR REPLACE` (`:82`). No existe una foto de lo que el supervisor vio en su momento.
  - Nunca se midió el ranking (precisión@K), que es la base de la regla operativa "empezá por los de mayor score".
- **Impacto:** la separación histórica (~10,3 con REF=8) y el lift 2,1 de "grupo quemado", que es la hipótesis central, no son evidencia limpia.
- **Solución implementada:** `scripts/evaluar_ranking.py`, que evalúa como si se estuviera parado en cada fin de mes. Incluye:
  - precisión@K, recall@K, lift contra el azar y AUC a 30, 60 y 90 días;
  - top-k por zona;
  - consistencia entre mitades, estabilidad del top y anticipación;
  - comparación contra criterios simples;
  - la variante `modelo_grupo_pit`, que recalcula el riesgo de grupo solo con bajas anteriores al corte y sin contar al propio vendedor.

### 5. [P0] La etiqueta "baja" mezcla renuncias y despidos

- **Evidencia:** `inicializar_db.py:223` inserta `motivo_egreso = None` siempre. `Precision.py:121` dice filtrar "renuncia/abandono", pero no lo hace (no hay dato). Todas las métricas (Precisión, Aprendizaje, validar_pesos) usan cualquier egreso.
- **Impacto:**
  - Si una parte de las bajas son despidos por bajo rendimiento, "plan < 55 %" las "predice" porque las causa una decisión de la empresa. Eso infla la señal y es circular.
  - Además orienta el uso del ranking hacia "a quién se va a desvincular", lo opuesto a su propósito de acompañamiento.
- **Solución propuesta:** obtener el motivo de egreso de RRHH o del ERP (solo lectura) y evaluar por separado las renuncias voluntarias. Mientras tanto, cada informe de precisión lo advierte. Ya lo hacen `evaluar_ranking.py` y `chequeo_integridad.py`.

### 6. [P0] Los vendedores nuevos no entran solos al sistema

- **Evidencia:**
  - El único INSERT en `vendedores` está en `inicializar_db.py:378`.
  - `sincronizar_informix.py:108` arma la lista de IDs a sincronizar **desde SQLite** y solo hace UPDATE de fechas (`:634`).
  - `sync_y_alertas.bat` no corre la inicialización.
  - Además, el motor descarta a quien no tiene filas de ventas (`score_engine.py:320`).
- **Impacto:** quienes están en los meses 1-3, el grupo de mayor riesgo y el que justifica el proyecto, quedan fuera del score hasta que alguien corra `inicializar_db.bat` a mano. Lo mismo pasa con los cambios de grupo y de supervisor.
- **Solución propuesta (ingesta, requiere aprobación):** correr el upsert de vendedores de `inicializar_db` como paso 0 del sync diario (es idempotente). Se verifica con el punto "ingreso en los últimos 60 días" de `chequeo_integridad.py`.

### 7. [P1] Fallas silenciosas que pisan datos buenos

- **Evidencia:**
  - Si falla la lectura de `vplan`, el sync imprime un AVISO y sigue (`sincronizar_informix.py:331`). Después el upsert pone `plan = 0` en 18 meses de filas, lo que apaga la señal de plan para todos.
  - `sync_y_alertas.bat` no chequea el `errorlevel` del snapshot ni de las alertas, y sigue de largo si fallan Reactor o SUN.
  - El snapshot corre con el Python de **32 bits** (`sync_y_alertas.bat:27`), que muy probablemente no tiene pandas (no hay wheels win32 de pandas 2.x para Python 3.12). Es decir, el snapshot automático probablemente nunca se guarda. **A confirmar** en la salida de la tarea.
  - El motor traga con `except Exception` la falta de tablas opcionales.
  - No hay backups de `wurth.db`, que contiene datos no reconstruibles (intervenciones), ni WAL, ni registro de corridas de sync. El indicador "Actualizado" del dashboard muestra la hora de carga del caché, no la de la última sincronización.
- **Impacto:** alertas y scores con datos viejos o en cero, sin que nadie se entere.
- **Solución propuesta:**
  - Que el sync aborte con código distinto de 0 si una fuente obligatoria falla o vuelve vacía.
  - `errorlevel` y log en los .bat.
  - Snapshot con Python de 64 bits.
  - `con.backup()` rotativo antes de sincronizar.
  - Tabla `sync_log`.

### 8. [P1] Buena parte del score es antigüedad, y algunas señales tienen sesgos de cobertura

- **Evidencia:** de las 9 señales activas, 4 dependen solo de la antigüedad o solo se evalúan en ciertos meses:
  - ventana 1-3 (1,5) y ventana 4-6 (1,0);
  - ausencias, solo en meses 1-3 (2,0);
  - acompañamiento, solo en meses 1-6 (1,0).

  Un ingresante en un grupo quemado suma 3,0 puntos (score 4,4) sin ningún dato de desempeño. Además:
  - `ausencias_mensual` solo tiene filas para meses **con** ausencias (`sincronizar_reactor.py:693`) y el motor promedia esas filas. Con 3 días en un solo mes, de tres, se enciende "> 2 días/mes". Está en el test `test_ausencias_promedia_solo_meses_con_ausencias`.
  - "Supervisor no acompañó" no dispara si no hay filas de acompañamiento, que es justamente el peor caso.
  - `meses_activo = días/30` redondeado: con menos de 15 días vale 0, y la ventana 1-3 no se enciende.
- **Impacto:** el orden puede ser casi solo "más nuevo primero". Si es así, lo honesto es decirlo y simplificar. `evaluar_ranking.py` lo mide directamente contra `antiguedad_tramos` y `tramos+plan`. Los vendedores nuevos quedan penalizados por contexto, no por conducta, y la UI no lo distingue.
- **Solución propuesta:**
  - En la UI, separar las señales de **contexto** (antigüedad, grupo) de las de **desempeño**.
  - Promediar ausencias sobre los meses de la ventana, no sobre las filas. Cambia scores, requiere aprobación.
  - Mostrar "historial insuficiente" en vez de promediar un solo mes.
  - Para los meses 1-3, comparar contra la cohorte con la misma antigüedad.

### 9. [P1] Intervenciones: datos falsos, fuga de confidencialidad y efectividad sin control

- **Evidencia (antes de los cambios):**
  - En la versión anterior, `pages/Intervenciones.py:110` llamaba a `cargar_demo()` **antes** del control de acceso. Con la tabla vacía, cualquier visita escribía 7 intervenciones inventadas en la base real.
  - El historial, los KPIs y las observaciones usaban `obtener_todas()` sin filtrar, así que un supervisor leía las notas de toda la empresa. El test con AppTest lo reprodujo.
  - El texto libre se mostraba como HTML sin escapar.
  - La fecha por defecto era el 2025-01-24.
  - El "impacto" es el score inicial menos el actual, sin grupo de comparación. Excluye a quienes se fueron, y el score baja solo al salir de la ventana 1-3 o 4-6.
  - "Acción recomendada" salía con n = 2.
  - El autor de la intervención se elige libremente y no se registra quién la cargó.
- **Estado:** corregido, salvo el registro del autor (ver F). Medir efectividad en serio requiere comparar contra no intervenidos de score y antigüedad similares a +60/+90 días, contando la baja como fracaso.

### 10. [P1] Explicabilidad y lenguaje que inducen conclusiones incorrectas

- **Evidencia (antes de los cambios):**
  - Los textos al supervisor decían "plan < 80 %" (el umbral real es 55), "zona quemada > 60 %" (real: 40 %) y "pérdida neta > 3 clientes" (real: 60).
  - Describían señales deshabilitadas como si contaran.
  - Hablaban de "señal de fuga inminente — acción inmediata" y de "mayor probabilidad de irse", con un score que no es una probabilidad.
  - Aprendizaje calculaba sugerencias con pesos viejos (2,5 y 1,5 en señales que hoy pesan 0).
  - Siguen pendientes: "Reunión esta semana" para todo crítico (contradice la acción por ranking), tres cortes distintos de "zona quemada" (0,30/0,45/0,60 en los badges contra 0,40 en el motor) y la falta de advertencias de muestra chica en Historial y Costo.
- **Estado:** textos y pesos corregidos (ver F). El resto queda en la matriz.

---

## C. Confiabilidad predictiva

**Qué se puede afirmar hoy:**

- Las bajas se concentran en los primeros meses. Es un hecho descriptivo robusto que justifica priorizar a los ingresantes.
- Las señales deshabilitadas tenían problemas reales de cobertura en los egresados. Ese diagnóstico, documentado en CLAUDE.md, es correcto.

**Qué NO está demostrado:**

- Que el **ranking** del modelo identifique a los que se van mejor que ordenar por antigüedad, o por antigüedad más plan.
- Que "grupo quemado" anticipe bajas futuras y no solo describa las pasadas. El lift 2,1 está contaminado por la fuga temporal y por la autoinclusión. Muchos grupos tienen pocos vendedores, y una sola baja mueve mucho el `riesgo_base`.
- Que las cifras históricas de detección y falsa alarma sean out-of-sample: la REF se eligió sobre el holdout.
- Que el score sea una probabilidad. No hay calibración y no debe presentarse como tal.

**Cómo demostrarlo (con los datos reales, sin tocar producción):**

1. Correr `scripts\chequeo_integridad.bat`. Si marca filas futuras o del mes en curso, el punto 3 de B es real en producción.
2. Correr `scripts\evaluar_ranking.bat` (si la base no está al día, pasar `--fecha-datos`). Para cada horizonte se puede responder:
   - **¿Aporta el modelo?** `lift@20` y AUC de `modelo_grupo_pit` deben superar con holgura a `antiguedad_tramos` y a `tramos+plan` en **ambas** mitades temporales. Si no, el modelo actual equivale a "priorizar ingresantes" y conviene simplificarlo y decirlo.
   - **¿Cuánto venía de la fuga?** Diferencia entre `modelo` y `modelo_grupo_pit`.
   - **¿Sirve "grupo quemado"?** Fila `grupo_pit` contra `azar`.
   - **¿Es estable?** Jaccard del top 20 entre meses y la anticipación mediana en días.
3. Leer las cifras con su tamaño de muestra. Con ~190 activos y pocas bajas por mes, la precisión@20 de un mes aislado es muy ruidosa. Solo vale el agregado de 12 meses o más, y la consistencia entre mitades.

**Antigüedad:** no hay que penalizar a quien no tiene 3 meses de historial. La propuesta (pendiente):

- mostrar las señales de contexto aparte de las de desempeño;
- para los meses 1-3, comparar el % de plan contra la mediana de los vendedores con el mismo `mes_numero`;
- con un solo mes de datos, mostrar "historial insuficiente" en lugar de un promedio.

---

## D. Riesgos técnicos y de seguridad (por gravedad)

| # | Riesgo | Prioridad | Estado |
|---|---|---|---|
| D1 | Repo público con datos personales en historia | P0 | Capturas quitadas del árbol (`8e0418d`); **falta repo privado + purga del historial** (dueño) |
| D2 | Sin autenticación (`?usuario=`) | P0 | **Pospuesto por decisión**: por ahora un único link (Gerencia) para gerencia, RRHH y los 3 directores; links personales cuando se sume a los supervisores |
| D3 | Score vivo con meses parciales/futuros | P0 | **Corregido** (`4c705d0`) |
| D4 | Altas nuevas no sincronizadas | P0 | **Corregido** (`31d7ad3`) |
| D5 | Fallo de vplan pisa el plan con ceros; bats sin `errorlevel` | P1 | **Corregido** (`21344ac`) |
| D6 | Notas de intervenciones visibles entre zonas | P1 | **Corregido** |
| D7 | Datos de ejemplo escritos en la base real | P1 | **Corregido** (falta limpiar filas existentes: ver chequeo) |
| D8 | `get_connection()` puede apuntar a Informix y las intervenciones escribían por ahí | P1 | **Corregido** para escrituras; la rama Informix del motor sigue (solo lectura) |
| D9 | Sin backups/WAL de `wurth.db` | P1 | Propuesto |
| D10 | Tracebacks visibles, telemetría de Streamlit activa | P2 | **Corregido** (`4ce795f`) |
| D11 | HTML de nombres del ERP sin escapar en otras páginas | P2 | Pendiente (las observaciones ya se escapan) |
| D12 | Conexiones ODBC sin `readonly=True` ni usuario de solo lectura | P2 | Propuesto (los scripts solo hacen SELECT, verificado) |
| D13 | Consultas a producción sin timeout de consulta, ventana completa de 18 meses todos los días | P2 | Propuesto |
| D14 | Estado de alertas no atómico; sin dry-run | P2 | **Corregido** |
| D15 | Esquema de `ausencias`/`acompanamiento` divergente entre init y sync | P1 | **Corregido** |

Regla de solo lectura: todos los cursores ODBC de `sincronizar_*`, `inicializar_db`, `explorar_*` y `diagnostico_*` ejecutan únicamente SELECT/SHOW/DESCRIBE. Todas las escrituras van a SQLite. No hay contraseñas en el árbol ni en la historia.

---

## E. Matriz de mejoras (ordenada por valor y urgencia)

Columna **Estado**: ✅ hecho · 🔒 requiere aprobación · ⏳ pendiente.

| ID | Problema | Prio | Esfuerzo | Archivos | Solución | Criterio verificable de éxito | Estado |
|---|---|---|---|---|---|---|---|
| M1 | Datos personales públicos | P0 | Bajo (decisión) | repo, `uploads/` | Privado + `git filter-repo` + borrar `uploads/` | Repo privado; `git log --all -- '*uploads*'` vacío | Parcial: `uploads/` quitado ✅ · privado + purga 🔒 dueño |
| M2 | Score vivo con meses parciales o futuros | P0 | Bajo | `score_engine.py`, `sincronizar_*.py` | Tope = último mes cerrado; sync sin claves futuras | `chequeo_integridad` sin filas futuras; el test de modo vivo cambia de forma deliberada; `evaluar_ranking` antes y después | ✅ `4c705d0` |
| M3 | Altas nuevas | P0 | Medio | `sincronizar_informix.py`, `sync_y_alertas.bat` | Upsert de vendedores en el sync diario | "Ingresos últimos 60 días" > 0; ingresantes con score | ✅ `31d7ad3` |
| M4 | Autenticación | P0 | Medio | `acceso.py`, script generador, `.env` | Link firmado HMAC; "Gerencia" fuera del selector | `?usuario=Gerencia` sin token da acceso denegado (test) | Pospuesto (un solo link por ahora) |
| M5 | Validación optimista | P0 | — | `scripts/evaluar_ranking.py` | Evaluación point-in-time contra criterios simples | Correr sobre la base real y decidir con la regla de C | ✅ (falta correrlo) |
| M6 | Fuga de `riesgo_base` en el motor | P1 | Medio | `score_engine.py`, backfill | `riesgo_base` point-in-time por corte, con n mínimo | `modelo` = `modelo_grupo_pit` en `evaluar_ranking` | 🔒 (decidir tras M5) |
| M7 | Etiqueta con despidos | P1 | Medio | `inicializar_db.py` (SELECT a la fuente del motivo) | Cargar `motivo_egreso`; evaluar renuncias aparte | `motivo_egreso` > 90 % cargado en el chequeo | ⏳ (definir fuente con RRHH) |
| M8 | Fallas silenciosas de la ingesta | P1 | Bajo | `sincronizar_informix.py`, `.bat` | Fail-fast si vplan/kund fallan; `errorlevel` y log; snapshot en 64 bits | Un fallo simulado de vplan termina con exit 1 y no actualiza plan | ✅ `21344ac` |
| M9 | Ausencias promediadas sobre filas | P1 | Bajo | `score_engine.py` | Promediar sobre los meses de la ventana | El test `test_ausencias_promedia_…` se invierte; Δ en `evaluar_ranking` | ✅ `f3ba7c2` (re-correr backfill) |
| M10 | Backups/WAL/sync_log | P1 | Bajo | scripts de sync | `con.backup()` rotativo, WAL, tabla `sync_log`; frescura real en la UI | Existe un backup diario; "Actualizado" = último sync OK | ⏳ |
| M11 | Flujo del supervisor | P1 | Medio | `Supervisor.py`, `Vendedor.py`, `intervenciones.py` | Columnas "en top desde" y "última intervención"; registrar desde el detalle; seguimiento con fecha | Un supervisor registra y ve el seguimiento sin cambiar de página | ⏳ |
| M12 | Autor de la intervención | P2 | Bajo | `intervenciones.py`, página | Columna `registrado_por` = usuario | Test: el autor queda grabado | ⏳ |
| M13 | "Reunión esta semana" para todo crítico | P2 | Bajo | `snippets_v3.accion_tag` | Acción por posición en el ranking (top N de la zona) | La etiqueta aparece solo en el top N | ⏳ |
| M14 | Cortes de "zona quemada" inconsistentes | P2 | Bajo | `dashboard.py`, `Supervisor.py`, `Vendedor.py` | Un solo umbral (0,40) más n mínimo | Badge y señal coinciden | ⏳ |
| M15 | `config.toml` (errores, telemetría) | P2 | Bajo | `.streamlit/config.toml` | `showErrorDetails="type"`, `gatherUsageStats=false` | Una excepción no muestra el traceback en el navegador | ✅ `4ce795f` |
| M16 | Rendimiento | P2 | Medio | `score_engine.py`, páginas | `groupby` en vez de filtrar dentro de `iterrows`; caché compartido de scores | Tiempo de `calcular_scores` medido antes y después | ⏳ |
| M17 | Scripts obsoletos | P3 | Bajo | `check_212.py`, `fix_vendedor_1407.*`, `diagnostico_grupo*`, `diagnostico_dias_venta_cero.py` (roto) | Mover a `scripts/archivo/` o borrar | Inventario de scripts operativos en el README | ⏳ |
| M18 | Rutas fijas `C:\Users\aarmoa\…` en los .bat | P3 | Bajo | `*.bat` | Variable `PY64`/`PY32` en un `config.bat` | Los .bat corren en otra PC cambiando un solo archivo | ⏳ |

---

## F. Mejoras implementadas

| Commit | Qué | Por qué | Archivos |
|---|---|---|---|
| `3a44c5a` | Suite de caracterización del motor (49 tests): señales, umbrales, dato faltante, normalización, niveles, población, y los 3 comportamientos señalados (fuga de `riesgo_base`, mes en curso, ausencias) | Proteger el comportamiento actual antes de tocar nada | `tests/conftest.py`, `tests/test_score_engine.py`, `requirements-dev.txt` |
| `9a4908d` | `evaluar_ranking.py`: evaluación point-in-time del ranking | La validación existente no mide el ranking y es optimista | `scripts/evaluar_ranking.py`, tests |
| `ed02bf7` | Se elimina `cargar_demo()`; las intervenciones escriben solo en SQLite; filtro de alcance que falla cerrado; HTML escapado; fecha por defecto = hoy; textos de impacto honestos; recomendación con n ≥ 10 y rotulada "no demostrado"; estado de alertas atómico y recuperable; `enviar_alertas.py --dry-run`; con COM ya no se exige `SMTP_PWD`; esquema de ausencias y acompañamiento alineado; `.gitignore` para salidas con datos personales | Integridad, confidencialidad, regla de solo lectura, pruebas sin envíos reales | `pages/Intervenciones.py`, `pages/Vendedor.py`, `src/intervenciones.py`, `src/alertas.py`, `scripts/enviar_alertas.py`, `scripts/inicializar_db.py`, `scripts/sincronizar_reactor.py`, `.gitignore` |
| `6b15b85` | `SEÑALES`/`PESOS` a nivel módulo (fuente única); Aprendizaje usa los pesos reales; test de sincronía con `validar_pesos` y `snippets_v3`; textos al usuario con los umbrales vigentes y sin lenguaje de probabilidad; fix del `KeyError` de Actividad; smoke de todas las páginas | Explicabilidad correcta; evitar copias desincronizadas | `src/score_engine.py`, `dashboard.py`, `pages/*`, `src/snippets_v3.py`, `src/alertas.py`, tests |
| `54960ce` | `chequeo_integridad.py` (solo conteos, solo lectura) y los .bat de los dos scripts nuevos | Medir en la base real los problemas de datos | `scripts/chequeo_integridad.*`, `scripts/evaluar_ranking.bat` |
| `01a9fab` | Documentación: README, CLAUDE.md, este informe | Corregir contradicciones | `README.md`, `CLAUDE.md`, `HANDOFF.md`, `docs/` |

**Cambios aprobados el 16/10/2026** (estos SÍ cambian scores o el flujo de datos; cada uno con tests que fallan con el código anterior):

| Commit | Qué | Archivos |
|---|---|---|
| `21344ac` | M8: si vplan o kund fallan o vuelven vacíos, el sync aborta antes de escribir en SQLite; `sync_y_alertas.bat` corta ante el primer error, guarda log en `logs\` y corre el snapshot con Python 64-bit; `backfill_scores.py` sale con 1 si falla un período | `scripts/sincronizar_informix.py`, `scripts/sync_y_alertas.bat`, `sincronizar_todo.bat`, `scripts/backfill_scores.py`, `tests/fakes/pyodbc.py` |
| `31d7ad3` | M3: `inicializar_db.py` corre a diario como paso 1 (altas, bajas, cambios de grupo y supervisor) y aborta sin escribir si `f040` viene incompleto | `scripts/inicializar_db.py`, `.bat` |
| `4c705d0` | M2: el modo vivo y las sparklines usan solo meses cerrados; Δ mes contra el mes anterior al último cerrado; los sync borran filas de meses futuros en SQLite | `src/score_engine.py`, `dashboard.py`, `pages/Supervisor.py`, `scripts/sincronizar_*.py` |
| `f3ba7c2` | M9: ausencias promediadas sobre los meses de la ventana con dato de Reactor | `src/score_engine.py` |
| `4ce795f` | M15: `.streamlit/config.toml` (sin tracebacks en el navegador, sin telemetría) | `.streamlit/config.toml` |
| `8e0418d` | M1 (parcial): capturas con datos personales quitadas del árbol | `Würth Rotación — Design System/uploads/` |

Lo que **no** se cambió, a propósito:

- pesos, umbrales, `RIESGO_REFERENCIA` y las claves `descripcion=`;
- conexiones a producción;
- configuración de Streamlit y tareas programadas;
- datos existentes en `wurth.db`.

---

## G. Validación

- **Tests:** `python -m pytest tests -q` → **98 passed, 1 skipped**, en Linux con Python 3.13, pandas 3.0.5, Streamlit 1.66. El skip es Historial con rol supervisor: redirige con `st.switch_page`, que AppTest no resuelve fuera del entrypoint.
- **Cobertura:**
  - reglas y umbrales de las 15 señales, dato faltante, normalización, niveles y población del backfill;
  - métricas del evaluador (empates, AUC, censura, riesgo de grupo PIT, apertura en solo lectura y que no modifica la base);
  - chequeo de integridad;
  - estado y detección de alertas, sin envíos;
  - intervenciones: escritura solo en SQLite aunque haya `INFORMIX_SERVER`, alcance por zona, escape;
  - las 9 páginas cargan sin excepciones con Gerencia y con un supervisor.
- **Prueba de que los tests detectan los bugs:** los 3 tests de la página de Intervenciones **fallan con el código anterior** (fuga entre zonas, HTML sin escapar, inserción de datos de ejemplo) y pasan con el nuevo. La migración de esquema se reprodujo: con el DDL viejo, el INSERT de Reactor falla con "no column named dias_no_vac"; con la migración, funciona.
- **Limitaciones:**
  - todo es con datos sintéticos;
  - no se ejecutaron los sync ni COM/Outlook;
  - no se probó en Windows ni en Python de 32 bits;
  - no hubo acceso a `wurth.db`.
- **Verificaciones pendientes, en la PC de producción:**
  1. `python -m pip install -r requirements-dev.txt` y `python -m pytest tests -q` con el Python de 64 bits.
  2. `scripts\chequeo_integridad.bat`.
  3. `scripts\evaluar_ranking.bat`.
  4. `python scripts\enviar_alertas.py --dry-run`.
  5. Revisar la salida de la tarea programada para confirmar si `snapshot_mensual.py` corre con el Python de 32 bits.

## H. Comparación antes/después

| Aspecto | Antes | Después | Cómo se verificó |
|---|---|---|---|
| Scores (todas las señales) | — | **Idénticos** | Los 49 tests de caracterización del motor (75 de la suite en ese momento) pasan antes y después del refactor |
| Supervisor ve notas de otras zonas | Sí | No | AppTest (falla con el código anterior) |
| Abrir Intervenciones con la tabla vacía | Insertaba 7 filas inventadas | No inserta | AppTest |
| Observaciones con HTML | Se renderizaban | Se escapan | AppTest |
| Base nueva + sync de Reactor | El INSERT fallaba; ausencias y acompañamiento quedaban apagadas | Migra y funciona | Reproducción con el DDL viejo |
| Pesos en Aprendizaje | Copia vieja (6 diferencias) | Los del motor | Test de sincronía |
| Estado de alertas corrupto | Excepción en cada corrida | Se aparta y se reinicia | Test |
| Probar alertas | Solo enviando | `--dry-run` | Código + flujo |
| Desempeño predictivo | Separación 10,3 (optimista) | **Sin medir todavía con el método nuevo** | Correr `evaluar_ranking.bat` |

## I. Hoja de ruta

**Ahora (esta semana)**

1. M1: repo privado y purga de la historia. Avisar a RRHH/Legales.
2. Desplegar los cambios aprobados (`git pull` en la PC de producción) y **re-correr `backfill_scores.bat`** (la señal de ausencias cambió).
3. Correr `chequeo_integridad.bat` y `evaluar_ranking.bat`, y compartir la salida. No incluye nombres.
4. Revisar el primer `logs\sync_y_alertas_*.log` de la tarea programada.

**Después (1-2 meses)**

5. Según lo que dé `evaluar_ranking`:
   - M6 (riesgo de grupo PIT);
   - o simplificar el modelo si no supera a la antigüedad.

   Cada cambio de scoring va por separado, con antes y después.
6. M7: motivo de egreso y evaluación solo de renuncias.
7. M10: backups y `sync_log`. M11 y M12: flujo del supervisor (Detección → Revisión → Conversación → Intervención → Seguimiento → Evaluación) usando lo que ya existe.
8. Congelar de verdad el score mensual que vio el supervisor, en una tabla separada que no se recalcula, para poder auditar el sistema en el futuro.

**Más adelante**

9. Evaluación de intervenciones contra no intervenidos comparables (+60/+90 días, la baja cuenta como fracaso). Recién ahí, recomendaciones por perfil.
10. M13 a M18 (UX, rendimiento, limpieza de scripts, rutas).
11. ML solo con 6 meses o más de datos limpios, etiqueta de renuncia voluntaria y un baseline de reglas ya medido con `evaluar_ranking`.

**Principio rector:** el sistema prioriza conversaciones de acompañamiento. Ningún score, nivel o ranking debe usarse para sancionar, excluir o desvincular. Mientras la etiqueta mezcle despidos, ese riesgo es mayor.
