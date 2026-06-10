# CLAUDE.md — Wurth Argentina: Sistema de Alertas de Rotación de Vendedores

Lee este archivo completo antes de tocar cualquier archivo del proyecto.

---

## Qué es este proyecto

Sistema de detección temprana de riesgo de fuga de vendedores para Wurth Argentina.
La permanencia promedio cayó de 18 meses (hace 10 años) a 5 meses hoy.
El objetivo es detectar señales de deterioro ANTES de que el vendedor renuncie,
no analizar por qué se fue.

---

## Contexto de negocio — crítico para entender las decisiones de código

- Los vendedores tienen ID numérico único (ej: 1119, 6453, 5855)
- Cada vendedor pertenece a un **grupo** con un supervisor asignado
  → El "grupo" es la unidad equivalente a "zona geográfica"
- Hay dos tipos de vendedor: **Viajante** (campo) y **Televentas**
- Cada vendedor tiene una **cartera propia de clientes** asignada
- Las métricas vienen del reporte interno llamado "Talata-Talatin" (mensual por vendedor)
- El ERP es **Informix**, accedido via ODBC desde Access hoy
- Hay +1000 vendedores en el historial (activos + bajas)

### Hipótesis principal validada
Los grupos con alta rotación histórica ("grupos quemados") producen
vendedores que duran menos independientemente del perfil del vendedor.
Esto es un problema **estructural**, no individual.

### Ventanas críticas de renuncia (del análisis histórico)
- Mes 1-3: onboarding, riesgo muy alto
- Mes 4-6: adaptación, riesgo alto
- Mes 7+: si llegó acá, el riesgo baja significativamente

---

## Estructura del proyecto

```
alerta-de-fluctuacion/
├── CLAUDE.md                              ← este archivo
├── README.md
├── requirements.txt
├── dashboard.py                           ← app Streamlit, pantalla Inicio (gerencia/director)
├── assets/
│   └── dashboard-v3.css                  ← estilos únicos, clases wz-* (inyectado una vez)
├── src/
│   ├── score_engine.py                   ← motor de scoring 1-10 (NO tocar sin actualizar este archivo)
│   ├── snippets_v3.py                    ← helpers HTML/formato/navegación (fmt_num, badge, nav_links…)
│   ├── acceso.py                         ← control de acceso por rol (supervisor/director/gerencia)
│   ├── intervenciones.py                 ← CRUD de intervenciones + cálculo de impacto
│   └── alertas.py                        ← envío de email via Outlook COM (no SMTP)
├── pages/
│   ├── Supervisor.py                     ← vista por zona (todos los roles)
│   ├── Vendedor.py                       ← detalle individual + señales activas
│   ├── Intervenciones.py                 ← registro y seguimiento de intervenciones
│   ├── Historial.py                      ← evolución histórica de rotación
│   ├── Actividad.py                      ← llamadas/visitas (Televentas y Viajantes separados)
│   ├── Costo_Rotacion.py                 ← costo por baja: histórico + exposición futura
│   ├── Precision.py                      ← precisión del modelo (requiere score_snapshot)
│   └── Aprendizaje.py                    ← análisis de señales y pesos
├── scripts/
│   ├── inicializar_db.py                 ← crea/repobla wurth.db desde Informix (Python 32-bit)
│   ├── inicializar_db.bat                ← wrapper que llama al Python 32-bit correcto
│   ├── sincronizar_informix.py           ← sync ventas/legajo desde Informix (solo SELECT)
│   ├── sincronizar_reactor.py            ← sync actividad/ausencias desde Reactor (solo SELECT)
│   ├── sincronizar_sundb.py              ← sync cobranza desde SUN SQL Server (solo SELECT)
│   ├── sincronizar_todo.bat              ← corre los 3 sync en secuencia
│   ├── backfill_scores.py                ← recalcula score_historico para períodos pasados
│   ├── enviar_alertas.py                 ← dispara alertas por email para vendedores críticos
│   ├── sync_y_alertas.bat                ← automatización diaria: sync → snapshot → alertas
│   ├── programar_alertas.bat             ← registra la tarea diaria en el Programador de Windows
│   ├── validar_pesos.py                  ← backtest: lift por señal + barrido REF (solo SQLite)
│   ├── explorar_senales_nuevas.py        ← lift de señales candidatas con holdout temporal
│   ├── diagnostico_vart.py               ← cruza f040 con SQLite para verificar clasificación TV/VJ
│   └── diagnostico_valores.py            ← distribución de indicadores (calibrar umbrales)
└── data/
    ├── wurth.db                          ← SQLite local (NO commitear — en .gitignore)
    └── estado_alertas.json               ← timestamps de última alerta por vendedor (NO commitear)
```

---

## Conexión a base de datos — estado actual

**Flujo de producción (ya activo):** los scripts `sincronizar_*.py` leen
(SOLO SELECT) de las tres fuentes reales y vuelcan a `data/wurth.db`:
- `sincronizar_informix.py` → ventas/legajo desde **Informix** (ERP, DSN MSPA)
- `sincronizar_reactor.py`  → actividad/ausencias/acompañamiento desde **Reactor** (CRM, MySQL)
- `sincronizar_sundb.py`    → cobranza desde **SUN** (SQL Server, DSN SUNDB)

El dashboard y el motor de scoring leen siempre de `data/wurth.db` (no golpean
las fuentes en cada recarga). Ya **no hay datos simulados**: el generador ficticio
se eliminó del repo. `data/wurth.db` está en `.gitignore` (nunca se commitea).

`get_connection()` en `src/score_engine.py` lee SQLite por defecto, y puede
conectar directo a Informix via pyodbc si se definen las variables de entorno
INFORMIX_* en `.env` (no se usa en el flujo normal). No toques la lógica de
scoring al cambiar la conexión.

---

## Tablas de la base de datos

### Estructura de `data/wurth.db` (poblada por los sync desde las fuentes reales)

**vendedores**
| campo | tipo | descripción |
|---|---|---|
| id_vendedor | INTEGER | ID único del ERP |
| tipo | TEXT | 'Viajante' o 'Televentas' |
| id_grupo | INTEGER | FK a grupos |
| nombre_grupo | TEXT | nombre del grupo/zona |
| supervisor | TEXT | nombre del supervisor |
| fecha_ingreso | TEXT | ISO date |
| fecha_egreso | TEXT | ISO date, NULL si activo |
| motivo_egreso | TEXT | 'Renuncia voluntaria', 'Despido', 'Acuerdo mutuo', 'Abandono' |
| activo | INTEGER | 1=activo, 0=baja |
| director | TEXT | nombre del director (resuelto de `f040.kz3`), NULL si no aplica |
| es_supervisor | INTEGER | 1 si `f040.bvertr == vertr` (es supervisor de sí mismo) |

**ventas_mensual** (una fila por vendedor por mes)
| campo | tipo | descripción |
|---|---|---|
| id_vendedor | INTEGER | FK a vendedores |
| anio / mes | INTEGER | período |
| mes_numero | INTEGER | mes N de su carrera (1=primer mes) |
| dias_trabajados | INTEGER | |
| dias_venta_cero | INTEGER | días sin registrar ninguna venta ← señal clave |
| venta_total | REAL | |
| plan | REAL | objetivo del mes |
| pct_plan | REAL | venta_total/plan*100 ← señal clave |
| clientes_activos | INTEGER | cartera activa ese mes ← señal clave |
| clientes_inactivos | INTEGER | |
| clientes_nuevos | INTEGER | |
| cobranza_teorica | REAL | |
| cobranza_real | REAL | ← señal clave |
| pct_cobranza | REAL | |
| dias_cobro | REAL | días promedio de cobro |
| cheques_rechazados | INTEGER | |

**grupos**
| campo | tipo | descripción |
|---|---|---|
| id_grupo | INTEGER | |
| nombre_grupo | TEXT | |
| supervisor | TEXT | |
| riesgo_base | REAL | 0-1, calculado del historial de rotación |

---

## Motor de scoring — lógica de negocio

El score es 1-10. **NO es una foto mensual. Es una tendencia de 3 meses.**
Esta decisión es intencional y no debe cambiarse sin discutirlo.

### Señales y pesos actuales (9 activas + 6 deshabilitadas)
| señal | peso | umbral | estado |
|---|---|---|---|
| % Plan en caída fuerte | ~~2.5~~ → **0** | — | **deshabilitada** |
| Días venta cero altos | ~~2.5~~ → **0** | — | **deshabilitada** |
| % Plan promedio bajo | 2.0 | media < 55 | activa |
| Cobranza real < 90% teórica | 2.0 | pct_cobranza < 90 | activa |
| Ausencias tempranas (mes 1-3) | 2.0 | > 2 días/mes no-vac | activa |
| En ventana crítica mes 1-3 | 1.5 | mes_numero 1-3 | activa |
| Grupo con alta rotación histórica | 1.5 | riesgo_base > 0.40 | activa |
| Balanza clientes muy negativa | 1.5 | 2+ meses + suma < -60 | activa |
| En ventana crítica mes 4-6 | 1.0 | mes_numero 4-6 | activa |
| Ticket promedio cayendo | 1.0 | pendiente > 5%/mes | activa |
| Supervisor no acompañó | 1.0 | < 1 visita/mes en 1-6 | activa |
| Sin clientes nuevos 2 meses | 0.5 | sum(nuevos últimos 2m) == 0 | activa |
| Cartera activa baja | ~~1.5~~ → **0** | — | **deshabilitada** |
| Cobranza real < 90% teórica | ~~2.0~~ → **0** | — | **deshabilitada** |
| Llamadas bajas (Televentas) | ~~1.5~~ → **0** | — | **deshabilitada** |
| Visitas bajas (Viajante) | ~~1.5~~ → **0** | — | **deshabilitada** |

> **Señales deshabilitadas (peso=0):** tienen un problema estructural de
> cobertura de datos en egresados que las invierte o las hace estadísticamente
> irrelevantes en el dataset real:
> - **% Plan en caída fuerte (pendiente):** con umbral <-50 pp/mes dispara solo en el
>   1.1% de los egresados y 0% de los activos — muestra insignificante, Δsep=0. El
>   %plan de la fuerza de ventas Würth 2026 es tan volátil mes a mes que la pendiente
>   no discrimina a ningún umbral útil: a <-3 dispara en el 93% de todos; a <-20
>   todavía en el 92%; a <-50 (el único punto donde no dispara en casi todos) ya
>   es tan extremo que casi nadie llega. Se deshabilita hasta tener datos más estables.
> - **Días venta cero (la "señal estrella" histórica):** con el umbral recalibrado a
>   `> 8` (datos 2026) se INVIRTIÓ: dispara más en activos (12.8%) que en egresados
>   (10.2%), lift 0.80, Δsep +2.7 al sacarla. Mismo problema de cobertura que
>   llamadas/visitas: los egresados tienen datos incompletos en sus últimos meses
>   activos → `dias_venta_cero` faltante = 0 = no enciende → subcuenta a los que se
>   van. Con el umbral viejo (`>3`, disparaba en el 99%) el problema quedaba tapado.
>   Tenía lift 3.44 en los datos viejos del contenedor, pero en producción 2026 no
>   separa. Re-evaluar cuando los egresados tengan datos completos de sus últimos meses.
> - **Cartera activa baja:** Informix reasigna los clientes al egreso → el histórico
>   del vendedor que se fue queda con `total_clientes=0` → el fix de dato faltante
>   desactiva la señal correctamente para egresados, pero sigue activa para el 98%
>   de los activos (lift 0.01, Δsep +13.4). No hay forma de reconstruir el historial
>   de asignación de cartera: se deshabilita hasta tener snapshots históricos.
> - **Llamadas/Visitas bajas:** los egresados raramente tienen datos de Reactor en
>   sus últimos meses activos → la señal casi no dispara para ellos (lift 0.05/0.51).
> - **Cobranza real < 90%:** lift 1.07 en datos reales — la cobranza baja está
>   distribuida uniformemente en la empresa (~48% egresados vs ~46% activos), no
>   concentrada en los que se van. Δsep +3.2 al sacarla: infla scores de todos por
>   igual sin mejorar la separación. Re-evaluar si en el futuro el dato muestra un
>   lift más claro (hoy la cobertura es 88.5% para egresados).
>
> Deshabilitarlas (no solo bajarles peso) fue el cambio de mayor impacto: la falsa
> alarma cayó ~32% → 16% sin perder detección, y la separación detección-vs-falsa
> alarma pasó de ~8 a ~24 a REF=16 (eso, a su vez, habilitó bajar la referencia a
> 12; ver calibración abajo).

> **Señal candidata probada y descartada — tenure×grupo:** se exploró la interacción
> "vendedor nuevo (mes 1-6) en grupo quemado (rb>0.30)" con
> `scripts/explorar_senales_nuevas.py` (lift aislado 2.04, prometedor). Se implementó
> y backfilleó, pero la auditoría marginal en `validar_pesos.py` dio **Δsep +1.7**:
> mete ruido en vez de señal porque ya está cubierta por "ventana crítica 1-3" +
> "grupo quemado". Lección: un buen lift aislado NO garantiza aporte marginal si la
> candidata se solapa con señales existentes. Por eso el flujo exige validar el
> Δseparación post-backfill, no solo el lift. Se revirtió a peso 0 (no está en el motor).

> **Recalibración de umbrales a datos reales 2026 (cuatro señales):** en el primer
> run real con datos de producción (188 activos), **154 (82%) salían críticos** —
> inservible operativamente. El diagnóstico (`scripts/diagnostico_valores.py`) mostró
> que los umbrales originales estaban pensados para un negocio sano, pero la fuerza
> de ventas Würth 2026 está estructuralmente deteriorada: la **mediana** del vendedor
> tiene ~7 días-cero/mes, ~65% de cumplimiento de plan y balanza de cartera -49. Con
> los umbrales viejos las cuatro señales más pesadas disparaban en casi todos (no
> discriminaban): días-cero `>3` → 99%, plan `<80` → 84%, pendiente `<-3` → 93%,
> balanza `<-3` → 94%. Se recalibró cada umbral al punto donde dispara en el **peor
> ~25-30%** de la población (≈ p25-p30 de su distribución):
> - **Días venta cero:** `> 3` → **`> 8`** (99% → ~31%)
> - **% Plan promedio:** `< 80` → **`< 55`** (84% → ~28%)
> - **Pendiente % plan:** `< -3` → **`< -50`** (93% → ~25%; el %plan es muy volátil
>   mes a mes, la mediana de pendiente es -44, por eso hace falta un corte tan abajo)
> - **Balanza clientes (suma 2m):** `< -3` → **`< -60`** (94% → ~30%)
>
> Lección: un umbral absoluto ("plan < 80%") deja de discriminar cuando la población
> entera cae por debajo. La señal sirve solo si marca a los **peores relativos** al
> resto, no un absoluto de "negocio sano". Caveat: pendiente y balanza apenas
> discriminan a ningún umbral (a `<-20` todavía disparan ~90%); el corte a p25 las
> deja rankear el cuarto peor, pero conviene validar su lift egresados-vs-activos con
> `validar_pesos.py` cuando haya suficiente historial real. **Si se re-sincronizan
> datos, re-correr `diagnostico_valores.py` + `diagnostico_distribucion.py` y reajustar.**
>
> **OJO — la descripción de la señal es su CLAVE en todo el sistema.** El texto
> `descripcion=` de cada `Señal` (ej. "Días sin venta > 3 en promedio") se usa como
> clave en dashboard, páginas, alertas, `score_historico` y `validar_pesos.py`. Por
> eso NO se cambió aunque el umbral pasó a 8: cambiar el string rompería todos esos
> lookups y la validación. Los nombres de la tabla de arriba son legibles para
> humanos (umbral actualizado), pero la clave interna sigue diciendo "> 3" etc.
> Al recalibrar un umbral se toca SOLO la lógica del motor, nunca el `descripcion=`.

### Normalización del score (calibración)
El `riesgo_total` (suma de pesos de señales activas) se normaliza a 1-10 contra
un **riesgo de referencia fijo** definido en `RIESGO_REFERENCIA = 8.0`:

```python
score = 1 + min(riesgo_total / RIESGO_REFERENCIA, 1.0) * 9
```

`RIESGO_REFERENCIA = 8` representa un vendedor en deterioro claro con las
señales activas actuales: plan<55% (2.0) + ventana crítica 1-3 (1.5) + grupo
quemado (1.5) + ausencias (2.0) ≈ 7-8 puntos → score 9-10.

**Por qué NO se divide por la suma de todos los pesos (~18):** eso exigía
activar >50% de las señales a la vez para llegar a score 6, algo que ningún
vendedor real hace. Resultado: todos los egresados quedaban con score < 6 y la
pantalla de Precisión mostraba 0% detectado. La calibración por referencia fija
arregla esto. Si se ajusta el valor, actualizar este archivo.

**Calibración por backtest (cómo se llegó a 8):** la referencia se movió a lo
largo de toda la limpieza de señales. El barrido en `scripts/validar_pesos.py`
(curva detección-vs-falsa-alarma con holdout temporal) define el punto óptimo en
cada estado del modelo:
  - Con las señales rotas activas, REF=10 daba **69% de falsa alarma** (inservible)
    y un primer ajuste a 14 usó cobranza incompleta que inflaba la detección.
  - Con la cobranza sincronizada y el bug de dato faltante corregido, el óptimo
    honesto fue **REF=16** (~40% detección OOS, ~32% falsa alarma, separación ≈ 8).
    Pero ese 16 estaba inflado por **cuatro señales que no separan** (cartera,
    llamadas, visitas y cobranza: lift ~1, disparan casi igual en egresados y
    activos): había que subir mucho la referencia para contener la falsa alarma.
  - A medida que se deshabilitaron esas señales, los scores bajaron parejo, la
    falsa alarma se desplomó y el óptimo del barrido fue cayendo: **16 → 12 → 10**.
    Con las cuatro fuera, el barrido honesto ubica el óptimo en **REF=10**: ~62%
    de detección out-of-sample con ~25% de falsa alarma (separación ≈ 37, la mejor
    de todo el recorrido). A REF=10 el nivel **crítico (≥8)** detecta ~41% de
    egresados vs ~11% de activos (a REF=16 era 2% vs 0,6%).
  - Tras recalibrar umbrales a datos reales 2026 (ver sección anterior), los scores
    volvieron a comprimirse (REF=10 daba separación 1.8, detección OOS 4.5%). El
    barrido re-corrido con umbrales nuevos + pendiente y días-cero deshabilitadas
    (y el `score_historico` limpio de entradas huérfanas, `[chequeo]=0.00`) ubica el
    óptimo en **REF=8**: ~15% de detección OOS con ~4.5% de falsa alarma (separación
    ≈ 10.3, la mejor del barrido; a REF≥10 la detección colapsa a 0 porque los
    scores quedan comprimidos). La separación sigue siendo modesta: es alerta
    temprana sobre datos ruidosos de RRHH, no un oráculo, y el historial de
    egresados aún es corto.
  - El nivel **crítico (≥8)** es el indicador visual de mayor urgencia (la acción
    operativa sigue siendo por ranking; ver abajo).

**Bug de dato faltante corregido (importante):** en `ventas_mensual` un dato
ausente queda en 0. El motor tomaba ese 0 como valor real y encendía señales
FALSAMENTE (cobranza ausente → pct 0 → "cobranza < 90"; plan ausente → pct 0 →
"plan < 80%"). Ahora cada señal usa solo los meses con BASE del dato:
plan → `plan > 0`; cobranza → `cobranza_teorica > 0`.
La señal de cartera (`total_clientes > 0`) fue deshabilitada (peso=0): Informix reasigna
los clientes al egreso y el histórico queda sin datos → no es recuperable sin snapshots.
Si no hay ningún mes con base, la señal queda apagada (dato desconocido ≠ riesgo).
Días venta cero ya era conservador (faltante = 0 = no enciende). Al cambiar esto,
re-correr siempre el backfill.

**Señal "grupo quemado" rescatada (umbral 0.60 → 0.40):** la hipótesis central
del proyecto (grupos de alta rotación producen fugas) tenía la señal muerta: el
umbral pedía `riesgo_base > 0.60` pero el grupo más quemado tiene 0.51, así que
nunca disparaba. El diagnóstico (`scripts/diagnostico_grupos_quemados.py`) mostró
que a `> 0.40` los egresados están 2,1× más seguido en grupos quemados que los
activos (11% vs 5%). Es señal estructural de alerta temprana: marca a vendedores
nuevos en grupos históricamente malos antes de que muestren deterioro individual.
Caveat honesto: los egresados alimentan el riesgo_base de su grupo, lo que infla
algo el lift retrospectivo; para un vendedor nuevo (uso real) no hay circularidad.

**Backfill: entradas huérfanas en `score_historico` (gotcha del `[chequeo]`).**
El backfill usa `INSERT OR REPLACE`, que solo sobreescribe filas de vendedores que
`calcular_scores()` devuelve para ese período. Si un vendedor sale del motor (ej.
pasó a ser supervisor y lo excluye el filtro), su fila vieja —calculada con pesos
y REF anteriores— queda **intacta** y `validar_pesos.py` reporta `[chequeo] != 0`
al no poder reconstruirla con los pesos actuales (un caso real: vendedor 6183,
2025-10, score 8.2 viejo vs 4.4 reconstruido). Por eso `backfill_scores.py` ahora,
antes de insertar cada período, hace `DELETE ... WHERE periodo=? AND id_vendedor
NOT IN (<ids devueltos>)`. Si el `[chequeo]` vuelve a despegarse, correr
`scripts/diagnostico_chequeo.bat`: muestra la peor fila y si el problema es REF
desincronizado, peso `??` (string desincronizado) o una entrada huérfana.

### Niveles de riesgo (etiquetas visuales, NO el disparador de acción)
- 8-10 → **crítico**
- 6-7  → **alto**
- 4-5  → **medio**
- 1-3  → **bajo**

### Acción operativa: por RANKING, no por umbral fijo
Decisión de diseño validada con `scripts/validar_pesos.py`. En esta población el
deterioro es generalizado (cobranza floja, días cero, plan cayendo en casi
todos), así que **ningún umbral de score separa limpio a los que se van de los
que se quedan**. La separación detección-vs-falsa-alarma mejoró bastante al
deshabilitar las señales rotas y bajar a REF=10 (~37, antes ~8), pero sigue sin
haber un corte que parta limpio: a REF=10 el nivel crítico (≥8) detecta ~41% de
egresados pero también marca ~11% de activos.

Lo que SÍ tiene señal es el **orden**: los vendedores de mayor score se van más
seguido. Por eso el dashboard NO dice "todos los que pasen de 8 = reunión"; dice
**"empezá por los de mayor score y bajá según tu capacidad"** (FOCO_SEMANA ≈ 20
en la vista global; el top de cada zona en la vista por supervisor). Las tablas
van ordenadas por score descendente. Los niveles crítico/alto quedan como
indicador visual de color y de urgencia, no como corte accionable rígido.

Por qué REF=10 (y no más alto): tras deshabilitar las cuatro señales que no
separan (cartera, llamadas, visitas, cobranza), REF=10 da la mejor separación
del barrido honesto (~37) y mantiene los scores bien distribuidos para el
ranking. Los REF altos (12-16) sólo hacían falta para contener la falsa alarma
que metían esas señales rotas; sin ellas, subir el REF sólo apaga detección y el
nivel crítico. Ver el barrido de niveles en `validar_pesos.py`.

### Banco de pruebas para auditar y descubrir señales (solo lectura SQLite)
Dos scripts trabajan juntos para mantener el set de señales afilado, sin tocar
ninguna base externa (reconstruyen todo desde `score_historico` / `ventas_mensual`):

- **`scripts/validar_pesos.py`** — además del barrido de `RIESGO_REFERENCIA` y los
  niveles operativos, tiene una **auditoría por señal**: para cada una de las 15
  reporta su `lift` (frecuencia en egresados vs activos) y su **contribución
  marginal a la separación** (cuánto cae la separación detección-vs-falsa-alarma
  si se le pone peso 0). Sirve para decidir a qué señal débil bajarle el peso o
  quitarla. *Caveat de lectura:* `lift` y contribución marginal pueden discrepar
  — una señal presente en casi todos tiene `lift≈1` (no separa) pero gran impacto
  en el score; mirar ambas columnas.

- **`scripts/explorar_senales_nuevas.py`** — mide el `lift` con holdout temporal
  de señales **candidatas nuevas** calculadas desde datos crudos (variabilidad
  mes a mes del %plan, coef. de variación de venta, caída abrupta MoM, días cero
  creciendo, cobranza empeorando, e interacción **tenure×grupo quemado**). Barre
  umbrales para cada una. Una candidata vale la pena solo si su `lift` OOS supera
  con holgura a las débiles actuales (visitas ~1.2, balanza ~1.4) → apuntar a
  `lift ≥ 1.8-2.0`. **Flujo para adoptar una candidata:** (1) confirmar lift acá
  → (2) implementarla como `Señal(...)` en `score_engine.py` → (3) re-correr
  backfill → (4) validar el Δseparación en `validar_pesos.py` (no alcanza el lift:
  hay que confirmar que sube la separación out-of-sample, sobre todo si se solapa
  con señales existentes como tenure×grupo, que ya cuenta doble con "ventana
  crítica" + "grupo quemado"). Recién entonces actualizar este archivo con el
  peso elegido.

---

## Usuarios del sistema y acceso por rol

A la vista por supervisor (`pages/Supervisor.py`) entran tres tipos de usuario,
con **alcance jerárquico** distinto. Lo resuelve `src/acceso.py`:

| Rol | Qué ve | Origen del dato |
|---|---|---|
| **Supervisor** | solo su propia zona (entra directo, sin landing) | tabla `grupos`/`vendedores` (automático desde f040) |
| **Director** | las zonas de los supervisores que tiene a cargo | derivado de `f040.kz3` (automático), fallback `DIRECTORES_MANUAL` |
| **Gerencia** | toda la empresa (KPIs, grupos, costo) — lo usan gerencia y RRHH | config `STAFF` en `acceso.py` (no está en f040, lo creamos) |

**Sin login con contraseña:** el usuario se identifica eligiendo su nombre en un
selector (se asume la pantalla detrás de un acceso corporativo). La identidad
viaja en el query param `?usuario=`. El control de acceso es real: `acceso.puede_ver()`
bloquea ver una zona fuera del alcance aunque se manipule el deep-link.

**De dónde sale la jerarquía:** `inicializar_db.py` la lee de `f040`:
- **supervisor** de cada vendedor = `f040.bvertr` (resuelto a nombre). Un vendedor
  es supervisor si `bvertr == vertr` (`es_supervisor=1`).
- **director** de cada supervisor = `f040.kz3` (resuelto a nombre).
- cuentas especiales `vertr` 1500/7777/9499 y los **egresados** (`austrdat` no NULL)
  se excluyen tanto de supervisores como de directores (réplica del reporte de
  jerarquía de Access).

`src/acceso.py` arma la jerarquía director→supervisor **sola** desde `vendedores`
(`_directores_db()`); si la base todavía no trae esas columnas (datos seed), cae al
fallback `DIRECTORES_MANUAL`. Los **supervisores** salen de `grupos`/`vendedores`
automáticamente. Lo único manual: el usuario **Gerencia** (no está en f040) →
diccionario `STAFF` en `src/acceso.py`. Hoy hay un solo usuario "Gerencia" de
acceso total que comparten gerencia (Daniel) y RRHH.

### Matriz de acceso por página (el control está en TODAS, no solo Supervisor)

Cada página llama a `acceso.requerir_acceso(roles=...)` al inicio. Si no hay
usuario, muestra el selector de identidad; si el rol no alcanza, bloquea. La
identidad sobrevive a `st.switch_page()` vía `st.session_state["_acc_usuario"]`
(además del query param `?usuario=`).

| Página | Gerencia | Director | Supervisor |
|---|---|---|---|
| `Precision`, `Aprendizaje`, `Costo_Rotacion` | ✅ todo | ⛔ bloqueado | ⛔ bloqueado |
| `Inicio` (dashboard.py), `Historial` | ✅ todo | ✅ solo sus zonas | ↪ redirigido a `Supervisor` |
| `Vendedor`, `Intervenciones`, `Actividad` | ✅ todo | ✅ filtrado a su alcance | ✅ filtrado a su alcance |
| `Supervisor` | ✅ elige zona | ✅ sus supervisores | ✅ entra directo a su zona |

Helpers reutilizables en `acceso.py`: `requerir_acceso(roles)` (gate + selector),
`barra_usuario_st(usuario)` (chip "ingresaste como…" + cambiar usuario),
`puede_ver(usuario, supervisor)` (chequeo de alcance, también usado en `Vendedor`
para bloquear deep-links a vendedores fuera de la zona). Los links a `/Vendedor`
arrastran `?usuario=` para no romper la sesión al navegar.

---

## Clasificación Televentas / Viajante — decisión crítica

**El ÚNICO criterio para clasificar a un vendedor como Televentas es `f040.zone = 'TVTAS'`.**

`vart=2` fue eliminado como fallback porque puede estar cargado incorrectamente en el ERP
(hay viajantes reales con `vart=2` por errores de alta). La regla en `inicializar_db.py`:

```python
tipo = "Televentas" if zona_raw == "TVTAS" else "Viajante"
```

Hay exactamente **3 grupos TVTAS** en producción (971, 972, 973) con ~56 vendedores.
El resto (~190 activos) son Viajantes, incluyendo todos los grupos 200-209, 119, 901 etc.
que antes se clasificaban como Televentas por `vart=2` — eso era incorrecto.

**`VERTR_EXCLUIDOS = {1500, 7777, 9499}`**: cuentas especiales (ex-directores, dummies).
Se excluyen en el INSERT **y** se borran explícitamente post-insert para eliminar registros
de runs anteriores. Si el diagnóstico muestra a 1500 (Kalpokas) con DISCREPANCIA,
es porque `inicializar_db.bat` no corrió con el código nuevo.

**Script de verificación:** `scripts/diagnostico_vart.py` cruza f040 de Informix con
SQLite y exporta `scripts/vart_diagnostico.csv`. Correrlo después de cada `inicializar_db.bat`
para confirmar 0 discrepancias. Acepta `--inspeccionar-f040` para ver los campos raw.

**`TIPO_MANUAL`** en `inicializar_db.py`: dict vacío por ahora. Si en el futuro aparece
un vendedor mal clasificado que no se puede corregir automáticamente, agregarlo ahí.

---

## Navegación y login — decisiones técnicas de la UI

**Identidad por query param:** el usuario viaja en `?usuario=NombreUsuario` en todos
los links. `nav_links()` en `snippets_v3.py` lee `st.query_params` internamente y
propaga `?usuario=` en todos los hrefs. Es la única fuente de verdad de la navegación.

**Sin login con contraseña:** el usuario elige su nombre en un selector. La identidad
se guarda en `localStorage` para auto-login en recargas. Se asume que la pantalla está
detrás de un acceso corporativo.

**Problema de sandbox de Streamlit:** los iframes de `st.components.v1.html()` tienen
`allow-same-origin allow-scripts` pero NO `allow-top-navigation`. Intentar
`window.parent.location.replace()` lanza SecurityError. Solución implementada: inyectar
un `<script>` en `window.parent.document.head` (accesible via `allow-same-origin`);
ese script corre en el contexto del padre (sin sandbox) y puede navegar libremente.

**Filtrado de nav por rol:** `nav_links()` llama a `acceso.resolver()` y oculta items
según el rol. Supervisores no ven Inicio, Historial, Precisión, Aprendizaje, Costo.
Directores no ven Precisión, Aprendizaje, Costo. Gerencia ve todo.

---

## UI — componentes y decisiones de presentación

**CSS único:** `assets/dashboard-v3.css` con clases `wz-*` es la única fuente de verdad
de estilos. Se inyecta una vez al inicio. El bloque `<style>` inline en cada página
debe contener solo estilos específicos de esa página (`.zc`, `.sec-header`, etc.).
NO duplicar en inline lo que ya está en el CSS file.

**Helpers en `src/snippets_v3.py`** (importar desde ahí, no reimplementar):
- `fmt_num(n, dec)` — formato es-AR (punto miles, coma decimal)
- `fmt_pesos(n)` / `fmt_pesos_corto(n)` — `$1.400.000` / `$1,4 M`
- `fmt_meses(n)` — `"4,1 m"`
- `badge(nivel, label, shape, title)` — badge con forma ▲◆■● para accesibilidad
- `accion_tag(nivel)` — "Reunión esta semana" / "—" para bajo
- `score_circle(score, nivel, title)` — círculo coloreado
- `score_delta(delta)` — `▲ 1.2` (rojo=peor) / `▼ 0.8` (verde=mejor)
- `banner(emoji, titulo, sub, tono)` — banner de acción del día
- `hero_kpi(label, valor, sub, red)` — KPI dominante
- `stat_kpi(label, valor)` — KPI secundario
- `fresh(ts_str)` — indicador de frescura del dato
- `nav_links(current)` / `page_header(titulo, current, sub)` — navegación estándar
- `HIDE_CHROME_CSS` — CSS para ocultar sidebar/header de Streamlit
- `score_breakdown_rows(senales)` — desglose ponderado del score
- `recomendar_accion(meses, riesgo_base, senales, efectividad)` — recomendación

**Regla de tablas:** usar `class="wz-table"` en todos lados. La clase `.ot` fue
eliminada. La tabla principal usa 7 columnas (Score y Δ mes fusionados en una).

**Vista default de la tabla principal:** top 5 en "Todos" sin filtrar. Cuando el
filtro es Crítico, Alto, hay supervisor seleccionado o hay búsqueda, muestra todo
sin expander (no esconder accionables detrás de un "Ver más").

---

## Configuración del entorno de ejecución

**Dos entornos de Python coexisten en la misma máquina Windows:**

| Python | Versión | Para qué | Por qué |
|---|---|---|---|
| 32-bit | 3.12 | `inicializar_db.py`, `sincronizar_*.py` | ODBC de Informix solo funciona en 32-bit |
| 64-bit | 3.x | `dashboard.py`, `enviar_alertas.py` | `pywin32` (Outlook COM) requiere 64-bit |

`sync_y_alertas.bat` maneja este split automáticamente.

**Variables de entorno (`.env`, NO commitear):**
- No hay variables requeridas para el flujo normal (los DSN de ODBC están en el sistema)
- `INFORMIX_*` opcionales para conexión directa desde `score_engine.py` (no se usa)

**Cómo correr:**
1. `inicializar_db.bat` → solo la primera vez o cuando cambia la estructura de vendedores
2. `sincronizar_todo.bat` → sync diario de ventas/cobranza/actividad
3. `streamlit run dashboard.py` / `iniciar_dashboard.bat`
4. `sync_y_alertas.bat` → automatización completa (sync + alertas)
5. `programar_alertas.bat` → registrar tarea diaria en Windows (una sola vez)

**Git:** todas las features van en `claude/sales-turnover-alerts-l8pO6`. Nunca pushear `data/wurth.db` ni `data/estado_alertas.json`.

---

## Decisiones técnicas tomadas y por qué

- **Streamlit** sobre React/Vue: equipo no tiene frontend developer. Prioridad = velocidad de iteración.
- **SQLite** como intermedio: no golpear Informix en cada recarga del dashboard.
- **Reglas con pesos** antes que ML: el modelo de reglas es explicable al supervisor. Un modelo black-box no genera confianza en este contexto.
- **ML en el futuro**: cuando haya datos reales limpios y el equipo entienda el sistema.
- **`zone='TVTAS'` como único criterio Televentas**: `vart` puede estar mal cargado en el ERP. Zone es el campo confiable.
- **Acción por ranking, no por umbral**: en esta población el deterioro es generalizado; ningún score separa limpio. El orden sí tiene señal.
- **`badge()` con `title=`**: el parámetro es obligatorio en `_bdg()` del dashboard; si se regenera el helper, asegurarse de incluirlo.

---

## Modelo de costo de rotación (`pages/Costo_Rotacion.py`)

Estima cuánto cuesta cada baja. Misma fórmula para el **costo histórico** (bajas
reales ya ocurridas) y la **exposición futura** (activos en riesgo). Todos los
parámetros están arriba del archivo y son ajustables.

### Costo directo
- Último mes improductivo del que se va: `1 sueldo`
- Reclutamiento (aviso + entrevistas): `1 sueldo`
- Inducción del reemplazo: `SALARIO_INDUCCION × MESES_RAMPA_NUEVO`
  → **solo la rampa** (el nuevo ya contratado pero todavía sin rendir). **NO** se
  cuenta `MESES_HASTA_NUEVO` (vacante): en la vacante no se paga sueldo y esa
  pérdida ya está en la cobertura. Contarla ahí duplicaba ~2M por baja (corregido).

### Costo indirecto — pérdida de cartera (modelo de cobertura Würth)
Cuando un vendedor se va, **televentas cubre la zona** hasta que entra el reemplazo,
así que la pérdida es parcial, no total:
- `plan × MESES_HASTA_NUEVO (1.5) × PCT_PERDIDA_COBERTURA (8%)`
- `plan × MESES_RAMPA_NUEVO (2) × PCT_PERDIDA_RAMPA (12%)`

### Plan escalonado por antigüedad — decisión clave
La pérdida de cartera se calcula sobre el **plan del vendedor que se va, según su
antigüedad**, NO sobre un promedio único del tipo. Esto importa porque la mayoría
de las bajas ocurren en los primeros 6 meses, donde el plan es ~2× menor que el de
un veterano: aplicarles el plan del veterano inflaba la pérdida al doble.
`_plan_por_tenure(tipo, meses)` devuelve (valores reales Würth 2026):

| Tramo | Viajante | Televentas |
|---|---|---|
| meses 1-2 | $9.450.000 | $9.450.000 |
| meses 3-4 | $11.550.000 | $11.550.000 |
| meses 5-6 | $13.650.000 | $13.650.000 |
| meses 7+ | $20.740.007 | $16.351.480 |

> Antes había un `_cargar_plan_promedio()` que sacaba un solo promedio por tipo de
> `ventas_mensual`; se eliminó. También se corrigió el fallback de Televentas que
> estaba en $6M (real $16.35M, casi 3× menos).

### Parámetros aún supuestos (validar con datos reales)
`PCT_PERDIDA_COBERTURA` (8%) y `PCT_PERDIDA_RAMPA` (12%) son los valores más "a ojo"
del modelo. Son lo que más mueve el número final: si en algún momento hay datos de
cuánta cartera se pierde realmente al irse un vendedor, ajustarlos ahí.

---

## Lo que NO hacer

- No cambiar la lógica de scoring sin actualizar este archivo
- No commitear `data/wurth.db` con datos reales de Informix (agregar a .gitignore)
- No agregar dependencias pesadas sin consultar (el entorno puede ser Windows con pyodbc)
- No reemplazar el sistema de reglas por ML todavía

## REGLA ABSOLUTA — Bases de datos externas: SOLO LECTURA

Las tres bases de producción son **intocables**. Está terminantemente prohibido
ejecutar cualquier instrucción que modifique datos en ellas:

| Base | DSN | Prohibido |
|---|---|---|
| Informix (ERP) | MSPA | INSERT, UPDATE, DELETE, DDL |
| SQL Server (SUN) | SUNDB | INSERT, UPDATE, DELETE, DDL |
| MySQL (Reactor CRM) | Wurth Reactor Produccion | INSERT, UPDATE, DELETE, DDL |

**Solo se permite:** SELECT y consultas de lectura.

La única base donde se escribe es `data/wurth.db` (SQLite local, propiedad del proyecto).
Cualquier script que necesite guardar datos lo hace en SQLite, nunca en las fuentes.

---

## Estado de features (actualizado junio 2026)

1. ✅ Vista filtrada por supervisor — acceso por rol en `pages/Supervisor.py` + `src/acceso.py`
2. ✅ Costo de rotación — `pages/Costo_Rotacion.py` (histórico + exposición futura)
3. ✅ Conexión real a Informix via pyodbc (sync desde Windows con Python 32-bit)
4. ✅ Alertas por email — `src/alertas.py` + `scripts/enviar_alertas.py` (Outlook COM)
5. ✅ Clasificación Televentas/Viajante corregida — solo `zone='TVTAS'`
6. ✅ Ocultamiento de secciones según rol en la navegación
7. ✅ Login persistente via localStorage + auto-login sin selector repetido
8. ✅ Formato es-AR en todas las tablas (`fmt_num`, `fmt_pesos`, `fmt_meses`)
9. ✅ Badges con forma ▲◆■● para accesibilidad
10. ✅ Score + Δ mes fusionados, tabla de 7 columnas
11. ✅ Vista default top 5, sin esconder accionables cuando hay filtro activo
12. ✅ `try/except` en `cargar_datos()` con mensaje de error amable
13. ⏳ **Precisión del modelo** — bloqueado hasta tener tabla `score_snapshot`.
    Ver `queries-v3.sql` (Camino A: snapshot mensual; Camino B: backfill histórico).
    La pantalla `pages/Precision.py` existe pero usa datos de ejemplo.
14. ⏳ **Recomendación de acción por perfil** — `recomendar_accion()` en snippets_v3.py
    existe pero devuelve `None` si no hay datos reales de intervenciones medidas.
    La query para conectarla está en `queries-v3.sql` (#3 efectividad).
15. ⏳ **Cohortes de retención** en Historial — query lista en `queries-v3.sql` (#2).
16. ⏳ **Modelo ML** — cuando haya 6+ meses de datos reales limpios.

### Alertas (#4) — cómo funciona el envío de email

El tenant de Office 365 tiene **SMTP AUTH deshabilitado por IT** (error 535), así
que NO se puede mandar por `smtplib`. El canal real es **Outlook clásico via COM**
(`win32com`), que usa la sesión de Outlook sin contraseña ni SMTP AUTH.

Complicación: la organización migró al **"nuevo Outlook" de Windows, que no soporta
COM**. Solución en `src/alertas.py`:
- `_buscar_outlook_clasico()` localiza el `OUTLOOK.EXE` **clásico** en los directorios
  de Office (`Program Files\Microsoft Office\root\Office*`), NO por App Paths del
  registro (que puede apuntar al nuevo Outlook).
- `_obtener_outlook()` conecta a una instancia abierta (`GetActiveObject`); si no hay,
  lanza el clásico en segundo plano (sin `/recycle`, que cedería el control al nuevo)
  y reintenta con backoff hasta 90s. El usuario puede seguir usando el nuevo Outlook
  a diario; el script spinea el clásico solo cuando manda la alerta.
- `enviar_email()` solo cae a SMTP si `pywin32` NO está instalado; si COM está pero
  falla, propaga el error (no intenta SMTP, que fallaría con 535).

Estado y re-alerta: `data/estado_alertas.json` guarda `{id_vendedor: timestamp última
alerta}`. Se alerta cuando un vendedor es **nuevo en crítico** o sigue crítico hace
**≥ 7 días** (`DIAS_REALERTA`). Probar el canal: `scripts/test_email.bat`.

Automatización: `scripts/sync_y_alertas.bat` corre sync (Python 32-bit, ODBC) →
snapshot → alertas (Python 64-bit, con pywin32). `scripts/programar_alertas.bat`
registra la tarea diaria en el Programador de Windows (con `/IT`: corre en la sesión
interactiva, necesario para Outlook COM y los DSN del usuario).

---

## Problemas conocidos y sus soluciones

### `git pull` falla con "untracked files would be overwritten"
`scripts/diagnostico_vart.py` puede existir localmente sin estar trackeado si se corrió
antes de hacer pull. Solución: `del scripts\diagnostico_vart.py && git pull`.

### `badge() got an unexpected keyword argument 'title'`
`_bdg()` en `dashboard.py` llama a `wz_badge(nivel, label, title=tip)`. Si `badge()`
en `snippets_v3.py` no tiene el parámetro `title=`, agregar `title=""` a la firma.

### Kalpokas (1500) aparece como Televentas en el diagnóstico
`inicializar_db.py` lo excluye en el INSERT pero no borraba el registro viejo. Fix ya
aplicado: hay un DELETE explícito de `VERTR_EXCLUIDOS` post-insert. Si persiste, correr
`inicializar_db.bat` con el código actualizado (hacer `git pull` primero).

### Score histórico con `[chequeo] != 0`
Entradas huérfanas en `score_historico` de vendedores que ya no salen del motor.
`backfill_scores.py` hace un DELETE previo por período. Si aparecen, correr
`scripts/diagnostico_chequeo.bat` para identificar la fila y re-correr el backfill.

### Dashboard muestra datos viejos
Verificar que `sync_y_alertas.bat` corrió recientemente. Revisar
`data/estado_alertas.json` para ver el timestamp. El caché de Streamlit es 5 min (TTL=300).

### Login no navega al hacer click en "Ingresar"
El iframe de `st.components.v1.html()` bloquea `window.parent.location`. La solución
implementada inyecta un `<script>` en `window.parent.document.head`. Si vuelve a fallar,
revisar que el componente en `acceso.py` use la técnica del parent DOM script injection,
no `window.parent.location.replace()` directo.

### Selector de perfil aparece en cada página
Ocurre cuando los links de navegación no propagan `?usuario=`. `nav_links()` en
`snippets_v3.py` lee `st.query_params` y agrega `?usuario=X` a todos los hrefs.
Si una página genera links propios (fuera de `nav_links`), agregar `?usuario=` manualmente.
