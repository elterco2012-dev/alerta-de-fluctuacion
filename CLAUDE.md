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
│   └── generar_datos_simulados.py    ← genera SQLite de prueba
└── data/
    └── wurth.db                       ← SQLite simulada (NO commitear datos reales)
```

---

## Conexión a base de datos — estado actual

**HOY:** SQLite simulada en `data/wurth.db`
**OBJETIVO:** Informix via pyodbc

La función `get_connection()` en `src/score_engine.py` es el único lugar
donde cambia la conexión. Está documentada con el string de conexión exacto
para Informix. No toques la lógica de scoring cuando cambies la conexión.

```python
# String de conexión Informix (completar con datos reales el lunes)
conn_str = (
    "DRIVER={IBM INFORMIX ODBC DRIVER};"
    "SERVER=<servidor>;"
    "DATABASE=<base>;"
    "HOST=<host>;"
    "UID=<usuario>;"
    "PWD=<password>;"
)
```

---

## Tablas de la base de datos

### SQLite simulada (estructura idéntica a lo que vendrá de Informix)

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

### Señales y pesos actuales
| señal | peso | umbral |
|---|---|---|
| % Plan cayendo 3 meses seguidos | 2.5 | pendiente < -3 |
| % Plan promedio < 80% | 2.0 | media < 80 |
| Días venta cero altos | 1.5 | promedio > 3 días |
| Cartera activa baja | 1.5 | < 60% activos |
| Grupo con alta rotación histórica | 1.5 | riesgo_base > 0.60 |
| En ventana crítica mes 1-3 | 1.5 | mes_numero 1-3 |
| En ventana crítica mes 4-6 | 1.0 | mes_numero 4-6 |
| Cobranza real < 90% teórica | 1.0 | pct_cobranza < 90 |
| Sin clientes nuevos 2 meses | 0.5 | sum(nuevos últimos 2m) == 0 |

### Niveles de riesgo
- 8-10 → **crítico** → acción inmediata del supervisor
- 6-7  → **alto**    → seguimiento activo
- 4-5  → **medio**   → monitoreo mensual
- 1-3  → **bajo**    → seguimiento normal

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
