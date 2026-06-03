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
wurth-rotacion/
├── CLAUDE.md                          ← este archivo
├── README.md                          ← documentación general
├── requirements.txt
├── dashboard.py                       ← app Streamlit principal
├── src/
│   └── score_engine.py               ← motor de scoring (1-10 por vendedor)
├── scripts/
│   ├── sincronizar_informix.py      ← ventas/legajo desde Informix (ERP, solo SELECT)
│   ├── sincronizar_reactor.py       ← actividad/ausencias desde Reactor (CRM, solo SELECT)
│   ├── sincronizar_sundb.py         ← cobranza desde SUN (SQL Server, solo SELECT)
│   └── validar_pesos.py             ← banco de pruebas de pesos/señales (solo lee SQLite)
└── data/
    └── wurth.db                      ← SQLite local poblada por los sync (NO commitear)
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

### Señales y pesos actuales (11 activas + 4 deshabilitadas)
| señal | peso | umbral | estado |
|---|---|---|---|
| % Plan cayendo 3 meses seguidos | 2.5 | pendiente < -3 | activa |
| Días venta cero altos | 2.5 | promedio > 3 días | activa |
| % Plan promedio < 80% | 2.0 | media < 80 | activa |
| Cobranza real < 90% teórica | 2.0 | pct_cobranza < 90 | activa |
| Ausencias tempranas (mes 1-3) | 2.0 | > 2 días/mes no-vac | activa |
| En ventana crítica mes 1-3 | 1.5 | mes_numero 1-3 | activa |
| Grupo con alta rotación histórica | 1.5 | riesgo_base > 0.40 | activa |
| Balanza clientes negativa | 1.5 | 2+ meses + pérdida > 3 | activa |
| En ventana crítica mes 4-6 | 1.0 | mes_numero 4-6 | activa |
| Ticket promedio cayendo | 1.0 | pendiente > 5%/mes | activa |
| Supervisor no acompañó | 1.0 | < 1 visita/mes en 1-6 | activa |
| Sin clientes nuevos 2 meses | 0.5 | sum(nuevos últimos 2m) == 0 | activa |
| Cartera activa baja | ~~1.5~~ → **0** | — | **deshabilitada** |
| Cobranza real < 90% teórica | ~~2.0~~ → **0** | — | **deshabilitada** |
| Llamadas bajas (Televentas) | ~~1.5~~ → **0** | — | **deshabilitada** |
| Visitas bajas (Viajante) | ~~1.5~~ → **0** | — | **deshabilitada** |

> **Señales deshabilitadas (peso=0):** las tres tienen un problema estructural de
> cobertura de datos en egresados que las invierte (disparan más en activos que en
> egresados, lift < 1, Δsep positivo al sacarlas):
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

### Normalización del score (calibración)
El `riesgo_total` (suma de pesos de señales activas) se normaliza a 1-10 contra
un **riesgo de referencia fijo** definido en `RIESGO_REFERENCIA = 12.0`:

```python
score = 1 + min(riesgo_total / RIESGO_REFERENCIA, 1.0) * 9
```

`RIESGO_REFERENCIA = 12` representa un vendedor en deterioro claro (combinación
de varias señales fuertes: plan cayendo 2.5 + plan<80% 2.0 + días cero 2.5 +
ventana crítica 1.5 + grupo quemado 1.5 ≈ 10 puntos, más cualquier señal adicional).

**Por qué NO se divide por la suma de todos los pesos (~21):** eso exigía
activar >50% de las señales a la vez para llegar a score 6, algo que ningún
vendedor real hace. Resultado: todos los egresados quedaban con score < 6 y la
pantalla de Precisión mostraba 0% detectado. La calibración por referencia fija
arregla esto. Si se ajusta el valor, actualizar este archivo.

**Calibración por backtest (cómo se llegó a 12):** con `RIESGO_REFERENCIA=10`
el modelo (con las señales rotas todavía activas) marcaba con score ≥ 6 al
**69% de los activos** — falsa alarma inservible. El barrido en
`scripts/validar_pesos.py` (curva detección-vs-falsa-alarma con holdout temporal)
define el punto óptimo, y se movió en dos etapas:
  - Un primer ajuste a 14 usó datos de cobranza incompletos para egresados, que
    INFLABAN la detección (ver bug abajo): aparentaba 62% de detección.
  - Con la cobranza sincronizada y el bug de dato faltante corregido, la curva
    honesta ubicó el óptimo en **REF=16** (~40% detección OOS, ~32% falsa alarma,
    separación ≈ 8). PERO ese 16 estaba inflado por las **tres señales rotas**
    (cartera/llamadas/visitas) que encendían el score de casi todos los activos:
    había que subir mucho la referencia para contener la falsa alarma.
  - Al **deshabilitar esas señales**, la falsa alarma se desplomó (~32% → 16% a
    REF=16) y la separación trepó a ~24. Eso dejó margen para BAJAR la referencia
    y recuperar detección. El barrido honesto post-limpieza ubica el óptimo en
    **REF=12**: ~62% de detección out-of-sample con ~31% de falsa alarma
    (separación ≈ 32). A REF=12 el nivel **crítico (≥8)** vuelve a ser alcanzable
    (dispara en ~23% de egresados vs ~10% de activos; a REF=16 era 2% vs 0,6%).
  - La separación real sigue siendo modesta: es alerta temprana sobre datos
    ruidosos de RRHH, no un oráculo. Detectar ~62% de las fugas con 3 meses de
    anticipación es valor real.
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
deshabilitar las señales rotas y bajar a REF=12 (~32, antes ~8), pero sigue sin
haber un corte que parta limpio: a REF=12 el nivel crítico (≥8) detecta ~23% de
egresados pero también marca ~10% de activos.

Lo que SÍ tiene señal es el **orden**: los vendedores de mayor score se van más
seguido. Por eso el dashboard NO dice "todos los que pasen de 8 = reunión"; dice
**"empezá por los de mayor score y bajá según tu capacidad"** (FOCO_SEMANA ≈ 20
en la vista global; el top de cada zona en la vista por supervisor). Las tablas
van ordenadas por score descendente. Los niveles crítico/alto quedan como
indicador visual de color y de urgencia, no como corte accionable rígido.

Por qué REF=12 (y no más alto): tras limpiar las señales rotas, REF=12 da la
mejor separación del barrido honesto y mantiene los scores bien distribuidos
para el ranking. Subir a 16 ya no hace falta para contener la falsa alarma (eso
lo resolvió quitar la señal de cartera) y sólo apagaría el nivel crítico. Ver el
barrido de niveles en `validar_pesos.py`.

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

## Usuarios del sistema

1. **RRHH** → necesita vista agregada, tendencias, motivos históricos
2. **Supervisor del vendedor** → necesita ver sus vendedores, señales concretas
3. **Gerencia** → necesita KPIs, grupos problemáticos, costo estimado de rotación

El dashboard actual cubre los 3 casos. Las vistas por supervisor son el próximo feature.

---

## Decisiones técnicas tomadas y por qué

- **Streamlit** sobre React/Vue: equipo no tiene frontend developer. Prioridad = velocidad de iteración.
- **SQLite** como intermedio: no golpear Informix en cada recarga del dashboard.
- **Reglas con pesos** antes que ML: el modelo de reglas es explicable al supervisor. Un modelo black-box no genera confianza en este contexto.
- **ML en el futuro**: cuando haya datos reales limpios y el equipo entienda el sistema.

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

## Próximos features planeados (en orden de prioridad)

1. Vista filtrada por supervisor (cada supervisor ve solo sus vendedores)
2. Conexión real a Informix via pyodbc
3. Alerta por email/Teams cuando un vendedor sube a nivel crítico
4. Análisis de costo de rotación (costo estimado por baja)
5. Modelo ML cuando haya 6+ meses de datos reales
