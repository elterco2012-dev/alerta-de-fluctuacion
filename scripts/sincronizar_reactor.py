"""
sincronizar_reactor.py
-----------------------
ETL: lee llamadas (Televentas) y visitas (Viajantes) de Reactor CRM
(MySQL, DSN="Wurth Reactor Produccion") y los guarda en actividad_mensual
dentro de data/wurth.db (SQLite).

Reactor usa Python 64 bits (MySQL ODBC no requiere 32 bits):
    python scripts\\sincronizar_reactor.py

Tablas de origen:
  customer_management   → gestiones realizadas (llamada hecha, sin importar resultado)
  cust_man_schedule     → planificación Televentas (is_done = ejecutada)
  customer_visit        → visitas realizadas
  schedule              → planificación Viajantes (is_visited = ejecutada)
  telephony_call_history→ llamadas respondidas (is_answered)

Columnas en actividad_mensual:
  llamadas              total gestiones en customer_management (inclye buzón, no contesta, etc.)
  llamadas_exitosas     gestiones donde closure_no_action_reason IS NULL (habló con alguien)
  planificadas_llamadas planificadas en cust_man_schedule (active=1)
  gestionadas_llamadas  planificadas ejecutadas (cust_man_schedule active=1, is_done=1)
  visitas               visitas en customer_visit
  clientes_visitados    clientes distintos visitados
  planificadas_visitas  planificadas en schedule (active=1, no deshabilitadas)
  visitadas_schedule    planificadas ejecutadas (schedule is_visited=1)
  clientes_llamados     clientes distintos gestionados
  llamadas_respondidas  llamadas con is_answered=1 en telephony_call_history

Opciones:
    --dry-run      Muestra totales sin escribir en SQLite
    --full         Procesa toda la historia (por defecto: últimos 6 meses)
    --diagnostico  Solo muestra conteos por tabla y año/mes
"""

import sys
import os
import sqlite3
import argparse
from datetime import date

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no instalado.  pip install pyodbc")
    sys.exit(1)

# ── Configuración ─────────────────────────────────────────────────────────────
DSN_REACTOR = "Wurth Reactor Produccion"
DB_PATH     = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run",     action="store_true", help="Mostrar sin guardar")
parser.add_argument("--full",        action="store_true", help="Toda la historia")
parser.add_argument("--diagnostico", action="store_true", help="Solo explorar estructura")
args = parser.parse_args()

DRY_RUN     = args.dry_run
MESES_ATRAS = 99 if args.full else 6

print("=" * 65)
print("SINCRONIZACIÓN Reactor CRM → SQLite  (llamadas + visitas)")
print(f"  DSN:      {DSN_REACTOR}")
print(f"  DB local: {DB_PATH}")
print(f"  Modo:     {'DRY RUN' if DRY_RUN else 'ESCRITURA'}")
print(f"  Historia: {'completa' if args.full else f'últimos {MESES_ATRAS} meses'}")
print("=" * 65)

# ── Fecha límite ───────────────────────────────────────────────────────────────
hoy = date.today()
anio_inicio = hoy.year
mes_inicio  = hoy.month - MESES_ATRAS
while mes_inicio <= 0:
    mes_inicio += 12
    anio_inicio -= 1

fecha_desde = f"{anio_inicio:04d}-{mes_inicio:02d}-01"
print(f"\n  Período desde: {anio_inicio}/{mes_inicio:02d}  ({fecha_desde})")

# ── Leer IDs activos por tipo desde SQLite (excluye supervisores) ─────────────
# Requiere haber ejecutado sincronizar_informix.py primero.
EXCLUIR_SUPERVISORES = """
    AND nombre NOT IN (
        SELECT DISTINCT supervisor FROM vendedores
        WHERE supervisor IS NOT NULL AND supervisor != ''
    )
"""

try:
    import sqlite3 as _sqlite3
    _lcon = _sqlite3.connect(DB_PATH)
    _lcur = _lcon.cursor()

    _lcur.execute(f"""
        SELECT id_vendedor FROM vendedores
        WHERE activo = 1 AND tipo = 'Televentas'
        {EXCLUIR_SUPERVISORES}
    """)
    IDS_TELEVENTAS = [str(r[0]) for r in _lcur.fetchall()]

    _lcur.execute(f"""
        SELECT id_vendedor FROM vendedores
        WHERE activo = 1 AND tipo = 'Viajante'
        {EXCLUIR_SUPERVISORES}
    """)
    IDS_VIAJANTES = [str(r[0]) for r in _lcur.fetchall()]

    _lcon.close()
    print(f"  Televentas activos (sin supervisores): {len(IDS_TELEVENTAS)}")
    print(f"  Viajantes activos  (sin supervisores): {len(IDS_VIAJANTES)}")

except Exception as e:
    print(f"\nAVISO: no se pudo leer vendedores de SQLite ({e})")
    print("  Ejecutá sincronizar_informix.py primero.")
    print("  Continuando con filtro genérico (puede incluir supervisores).")
    IDS_TELEVENTAS = []
    IDS_VIAJANTES  = []

# Helpers para armar cláusula IN en MySQL
def _in_clause(ids):
    """Devuelve 'IN (1,2,3)' o 'IN (0)' si la lista está vacía (sin resultados)."""
    return f"IN ({','.join(ids)})" if ids else "IN (0)"

IN_TELEVENTAS = _in_clause(IDS_TELEVENTAS)
IN_VIAJANTES  = _in_clause(IDS_VIAJANTES)
IN_AMBOS      = _in_clause(list(set(IDS_TELEVENTAS + IDS_VIAJANTES)))

# ── Conectar a Reactor MySQL ───────────────────────────────────────────────────
print("\nConectando a Reactor CRM (MySQL)...", end=" ", flush=True)
try:
    rcn  = pyodbc.connect(f"DSN={DSN_REACTOR}", timeout=15)
    rcur = rcn.cursor()
    print("OK")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    print("\nVerificá:")
    print("  - DSN configurado: 'Wurth Reactor Produccion'")
    print("  - MySQL ODBC driver instalado")
    print("  - Server 10.60.18.51:3306 accesible")
    sys.exit(1)

# ── Modo diagnóstico ──────────────────────────────────────────────────────────
if args.diagnostico:
    print("\n--- DIAGNÓSTICO Reactor CRM ---\n")

    print(f"  Televentas activos: {len(IDS_TELEVENTAS)}  |  Viajantes activos: {len(IDS_VIAJANTES)}\n")

    print("customer_management (gestiones Televentas):")
    rcur.execute(f"""
        SELECT YEAR(cm.created) AS anio, MONTH(cm.created) AS mes,
               COUNT(*) AS total,
               SUM(CASE WHEN cm.closure_no_action_reason IS NULL THEN 1 ELSE 0 END) AS exitosas
        FROM customer_management cm
        JOIN `user` u ON cm.id_user_author = u.id
        WHERE cm.created >= ?
          AND CAST(u.username AS UNSIGNED) {IN_TELEVENTAS}
        GROUP BY YEAR(cm.created), MONTH(cm.created)
        ORDER BY anio, mes
    """, fecha_desde)
    for r in rcur.fetchall():
        print(f"  {r[0]}/{r[1]:02d}: {r[2]:>6} gestionadas, {r[3]:>6} exitosas")

    print("\ncust_man_schedule (planificadas Televentas):")
    rcur.execute(f"""
        SELECT YEAR(cs.contact_day) AS anio, MONTH(cs.contact_day) AS mes,
               COUNT(*) AS planificadas,
               SUM(CASE WHEN cs.is_done = 1 THEN 1 ELSE 0 END) AS gestionadas
        FROM cust_man_schedule cs
        JOIN `user` u ON cs.id_user = u.id
        WHERE cs.contact_day >= ?
          AND cs.active = 1
          AND CAST(u.username AS UNSIGNED) {IN_TELEVENTAS}
        GROUP BY YEAR(cs.contact_day), MONTH(cs.contact_day)
        ORDER BY anio, mes
    """, fecha_desde)
    for r in rcur.fetchall():
        pct = round(r[3] / r[2] * 100, 1) if r[2] else 0
        print(f"  {r[0]}/{r[1]:02d}: {r[2]:>6} planificadas, {r[3]:>6} gestionadas ({pct}%)")

    print("\ncustomer_visit (visitas Viajantes):")
    rcur.execute(f"""
        SELECT YEAR(cv.start_time) AS anio, MONTH(cv.start_time) AS mes,
               COUNT(*) AS total
        FROM customer_visit cv
        JOIN `user` u ON cv.id_user_author = u.id
        WHERE cv.start_time >= ?
          AND CAST(u.username AS UNSIGNED) {IN_VIAJANTES}
        GROUP BY YEAR(cv.start_time), MONTH(cv.start_time)
        ORDER BY anio, mes
    """, fecha_desde)
    for r in rcur.fetchall():
        print(f"  {r[0]}/{r[1]:02d}: {r[2]:>6} visitas")

    print("\nschedule (planificadas Viajantes):")
    rcur.execute(f"""
        SELECT YEAR(s.meeting_day) AS anio, MONTH(s.meeting_day) AS mes,
               COUNT(*) AS planificadas,
               SUM(CASE WHEN s.is_visited = 1 THEN 1 ELSE 0 END) AS visitadas
        FROM schedule s
        JOIN `user` u ON s.id_user = u.id
        WHERE s.meeting_day >= ?
          AND s.active = 1
          AND s.disabled IS NULL
          AND CAST(u.username AS UNSIGNED) {IN_VIAJANTES}
        GROUP BY YEAR(s.meeting_day), MONTH(s.meeting_day)
        ORDER BY anio, mes
    """, fecha_desde)
    for r in rcur.fetchall():
        pct = round(r[3] / r[2] * 100, 1) if r[2] else 0
        print(f"  {r[0]}/{r[1]:02d}: {r[2]:>6} planificadas, {r[3]:>6} visitadas ({pct}%)")

    print("\ntelephony_call_history (Televentas):")
    rcur.execute(f"""
        SELECT YEAR(created) AS anio, MONTH(created) AS mes,
               COUNT(*) AS total,
               SUM(CASE WHEN is_answered = 1 THEN 1 ELSE 0 END) AS respondidas
        FROM telephony_call_history
        WHERE type = 'report'
          AND created >= ?
          AND CAST(agent AS UNSIGNED) {IN_TELEVENTAS}
        GROUP BY YEAR(created), MONTH(created)
        ORDER BY anio, mes
    """, fecha_desde)
    for r in rcur.fetchall():
        pct = round(r[3] / r[2] * 100, 1) if r[2] else 0
        print(f"  {r[0]}/{r[1]:02d}: {r[2]:>6} registros, {r[3]:>6} respondidas ({pct}%)")

    rcn.close()
    sys.exit(0)

# ── 1. Gestiones realizadas (customer_management) — solo Televentas activos ────
print("\n[1/5] Gestiones Televentas (customer_management)...", end=" ", flush=True)
rcur.execute(f"""
    SELECT CAST(u.username AS UNSIGNED)                          AS id_vendedor,
           YEAR(cm.created)                                      AS anio,
           MONTH(cm.created)                                     AS mes,
           COUNT(*)                                              AS llamadas,
           SUM(CASE WHEN cm.closure_no_action_reason IS NULL
                    THEN 1 ELSE 0 END)                           AS llamadas_exitosas,
           COUNT(DISTINCT cm.customer_code)                      AS clientes_llamados
    FROM customer_management cm
    JOIN `user` u ON cm.id_user_author = u.id
    WHERE cm.created >= ?
      AND CAST(u.username AS UNSIGNED) {IN_TELEVENTAS}
    GROUP BY CAST(u.username AS UNSIGNED), YEAR(cm.created), MONTH(cm.created)
    ORDER BY id_vendedor, anio, mes
""", fecha_desde)

gestion_data = {}
for row in rcur.fetchall():
    vid, anio, mes, llamadas, exitosas, clientes = row
    k = (int(vid), int(anio), int(mes))
    gestion_data[k] = {
        "llamadas":          int(llamadas or 0),
        "llamadas_exitosas":  int(exitosas or 0),
        "clientes_llamados":  int(clientes or 0),
    }
print(f"OK — {len(gestion_data)} filas")

# ── 2. Planificación Televentas (cust_man_schedule) — solo Televentas activos ──
print("[2/5] Planificación Televentas (cust_man_schedule)...", end=" ", flush=True)
rcur.execute(f"""
    SELECT CAST(u.username AS UNSIGNED)                          AS id_vendedor,
           YEAR(cs.contact_day)                                  AS anio,
           MONTH(cs.contact_day)                                 AS mes,
           COUNT(*)                                              AS planificadas,
           SUM(CASE WHEN cs.is_done = 1 THEN 1 ELSE 0 END)      AS gestionadas
    FROM cust_man_schedule cs
    JOIN `user` u ON cs.id_user = u.id
    WHERE cs.contact_day >= ?
      AND cs.active = 1
      AND CAST(u.username AS UNSIGNED) {IN_TELEVENTAS}
    GROUP BY CAST(u.username AS UNSIGNED), YEAR(cs.contact_day), MONTH(cs.contact_day)
    ORDER BY id_vendedor, anio, mes
""", fecha_desde)

plan_llamadas_data = {}
for row in rcur.fetchall():
    vid, anio, mes, planificadas, gestionadas = row
    k = (int(vid), int(anio), int(mes))
    plan_llamadas_data[k] = {
        "planificadas_llamadas": int(planificadas or 0),
        "gestionadas_llamadas":  int(gestionadas or 0),
    }
print(f"OK — {len(plan_llamadas_data)} filas")

# ── 3. Visitas realizadas (customer_visit) — solo Viajantes activos ───────────
print("[3/5] Visitas realizadas (customer_visit)...", end=" ", flush=True)
rcur.execute(f"""
    SELECT CAST(u.username AS UNSIGNED)                          AS id_vendedor,
           YEAR(cv.start_time)                                   AS anio,
           MONTH(cv.start_time)                                  AS mes,
           COUNT(*)                                              AS visitas,
           COUNT(DISTINCT cv.customer_code)                      AS clientes_visitados
    FROM customer_visit cv
    JOIN `user` u ON cv.id_user_author = u.id
    WHERE cv.start_time >= ?
      AND CAST(u.username AS UNSIGNED) {IN_VIAJANTES}
    GROUP BY CAST(u.username AS UNSIGNED), YEAR(cv.start_time), MONTH(cv.start_time)
    ORDER BY id_vendedor, anio, mes
""", fecha_desde)

visitas_data = {}
for row in rcur.fetchall():
    vid, anio, mes, visitas, clientes = row
    k = (int(vid), int(anio), int(mes))
    visitas_data[k] = {
        "visitas":            int(visitas or 0),
        "clientes_visitados": int(clientes or 0),
    }
print(f"OK — {len(visitas_data)} filas")

# ── 4. Planificación Viajantes (schedule) — solo Viajantes activos ────────────
print("[4/5] Planificación Viajantes (schedule)...", end=" ", flush=True)
rcur.execute(f"""
    SELECT CAST(u.username AS UNSIGNED)                          AS id_vendedor,
           YEAR(s.meeting_day)                                   AS anio,
           MONTH(s.meeting_day)                                  AS mes,
           COUNT(*)                                              AS planificadas,
           SUM(CASE WHEN s.is_visited = 1 THEN 1 ELSE 0 END)    AS visitadas
    FROM schedule s
    JOIN `user` u ON s.id_user = u.id
    WHERE s.meeting_day >= ?
      AND s.active = 1
      AND s.disabled IS NULL
      AND CAST(u.username AS UNSIGNED) {IN_VIAJANTES}
    GROUP BY CAST(u.username AS UNSIGNED), YEAR(s.meeting_day), MONTH(s.meeting_day)
    ORDER BY id_vendedor, anio, mes
""", fecha_desde)

plan_visitas_data = {}
for row in rcur.fetchall():
    vid, anio, mes, planificadas, visitadas = row
    k = (int(vid), int(anio), int(mes))
    plan_visitas_data[k] = {
        "planificadas_visitas": int(planificadas or 0),
        "visitadas_schedule":   int(visitadas or 0),
    }
print(f"OK — {len(plan_visitas_data)} filas")

# ── 5. Llamadas respondidas (telephony_call_history) — solo Televentas activos ─
print("[5/5] Llamadas respondidas (telephony_call_history)...", end=" ", flush=True)
rcur.execute(f"""
    SELECT CAST(agent AS UNSIGNED)                               AS id_vendedor,
           YEAR(created)                                         AS anio,
           MONTH(created)                                        AS mes,
           SUM(CASE WHEN is_answered = 1 THEN 1 ELSE 0 END)     AS respondidas
    FROM telephony_call_history
    WHERE type = 'report'
      AND created >= ?
      AND CAST(agent AS UNSIGNED) {IN_TELEVENTAS}
    GROUP BY CAST(agent AS UNSIGNED), YEAR(created), MONTH(created)
    ORDER BY id_vendedor, anio, mes
""", fecha_desde)

respondidas_data = {}
for row in rcur.fetchall():
    vid, anio, mes, respondidas = row
    k = (int(vid), int(anio), int(mes))
    respondidas_data[k] = int(respondidas or 0)
print(f"OK — {len(respondidas_data)} filas")

rcn.close()

# ── Unir todos los datasets ───────────────────────────────────────────────────
todas_keys = (
    set(gestion_data)
    | set(plan_llamadas_data)
    | set(visitas_data)
    | set(plan_visitas_data)
    | set(respondidas_data)
)
print(f"\nTotal filas a sincronizar: {len(todas_keys)}")

if DRY_RUN:
    print("\n--- DRY RUN: muestra de primeras 20 filas ---")
    print(f"  {'Vendedor':>8}  {'Mes':>7}  {'Plan.Ll':>7}  {'Gest.Ll':>7}  {'%':>5}  {'Exitosas':>8}  {'Plan.Vi':>7}  {'Visit.':>7}  {'%':>5}")
    for k in sorted(todas_keys)[:20]:
        vid, anio, mes = k
        gl  = gestion_data.get(k, {})
        pl  = plan_llamadas_data.get(k, {})
        vv  = visitas_data.get(k, {})
        pv  = plan_visitas_data.get(k, {})

        plan_ll = pl.get("planificadas_llamadas", 0)
        gest_ll = pl.get("gestionadas_llamadas", 0)
        plan_vi = pv.get("planificadas_visitas", 0)
        visit   = pv.get("visitadas_schedule", 0)
        pct_ll  = f"{gest_ll/plan_ll*100:.0f}%" if plan_ll else "—"
        pct_vi  = f"{visit/plan_vi*100:.0f}%"   if plan_vi else "—"

        print(
            f"  {vid:>8}  {anio}/{mes:02d}  "
            f"{plan_ll:>7}  {gest_ll:>7}  {pct_ll:>5}  "
            f"{gl.get('llamadas_exitosas',0):>8}  "
            f"{plan_vi:>7}  {visit:>7}  {pct_vi:>5}"
        )
    print("\nDRY RUN completado. Sin cambios en SQLite.")
    sys.exit(0)

# ── Conectar a SQLite ─────────────────────────────────────────────────────────
print("\nConectando a SQLite...", end=" ", flush=True)
try:
    lcon = sqlite3.connect(DB_PATH)
    lcur = lcon.cursor()
    print("OK")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    sys.exit(1)

# Crear tabla con todas las columnas
lcur.execute("""
    CREATE TABLE IF NOT EXISTS actividad_mensual (
        id_vendedor           INTEGER NOT NULL,
        anio                  INTEGER NOT NULL,
        mes                   INTEGER NOT NULL,
        llamadas              INTEGER DEFAULT 0,
        llamadas_exitosas     INTEGER DEFAULT 0,
        planificadas_llamadas INTEGER DEFAULT 0,
        gestionadas_llamadas  INTEGER DEFAULT 0,
        visitas               INTEGER DEFAULT 0,
        clientes_visitados    INTEGER DEFAULT 0,
        planificadas_visitas  INTEGER DEFAULT 0,
        visitadas_schedule    INTEGER DEFAULT 0,
        clientes_llamados     INTEGER DEFAULT 0,
        llamadas_respondidas  INTEGER DEFAULT 0,
        PRIMARY KEY (id_vendedor, anio, mes)
    )
""")

# Agregar columnas nuevas si la tabla ya existía sin ellas
for col in ("planificadas_llamadas", "gestionadas_llamadas",
            "planificadas_visitas", "visitadas_schedule"):
    try:
        lcur.execute(f"ALTER TABLE actividad_mensual ADD COLUMN {col} INTEGER DEFAULT 0")
    except Exception:
        pass  # columna ya existe

lcon.commit()

# ── Insertar / actualizar ─────────────────────────────────────────────────────
upsert_sql = """
    INSERT INTO actividad_mensual
        (id_vendedor, anio, mes,
         llamadas, llamadas_exitosas, planificadas_llamadas, gestionadas_llamadas,
         visitas, clientes_visitados, planificadas_visitas, visitadas_schedule,
         clientes_llamados, llamadas_respondidas)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (id_vendedor, anio, mes) DO UPDATE SET
        llamadas              = excluded.llamadas,
        llamadas_exitosas     = excluded.llamadas_exitosas,
        planificadas_llamadas = excluded.planificadas_llamadas,
        gestionadas_llamadas  = excluded.gestionadas_llamadas,
        visitas               = excluded.visitas,
        clientes_visitados    = excluded.clientes_visitados,
        planificadas_visitas  = excluded.planificadas_visitas,
        visitadas_schedule    = excluded.visitadas_schedule,
        clientes_llamados     = excluded.clientes_llamados,
        llamadas_respondidas  = excluded.llamadas_respondidas
"""

insertados = 0
for k in sorted(todas_keys):
    vid, anio, mes = k
    gl = gestion_data.get(k, {})
    pl = plan_llamadas_data.get(k, {})
    vv = visitas_data.get(k, {})
    pv = plan_visitas_data.get(k, {})
    rr = respondidas_data.get(k, 0)

    lcur.execute(upsert_sql, (
        vid, anio, mes,
        gl.get("llamadas", 0),
        gl.get("llamadas_exitosas", 0),
        pl.get("planificadas_llamadas", 0),
        pl.get("gestionadas_llamadas", 0),
        vv.get("visitas", 0),
        vv.get("clientes_visitados", 0),
        pv.get("planificadas_visitas", 0),
        pv.get("visitadas_schedule", 0),
        gl.get("clientes_llamados", 0),
        rr,
    ))
    insertados += 1

lcon.commit()
lcon.close()

print(f"\n✓ {insertados} filas insertadas/actualizadas en actividad_mensual")
print("\nResumen por fuente:")
print(f"  Vendedores con gestiones (cm)     : {len({k[0] for k in gestion_data})}")
print(f"  Vendedores con plan llamadas      : {len({k[0] for k in plan_llamadas_data})}")
print(f"  Vendedores con visitas (cv)       : {len({k[0] for k in visitas_data})}")
print(f"  Vendedores con plan visitas       : {len({k[0] for k in plan_visitas_data})}")
print(f"  Vendedores en tel. history        : {len({k[0] for k in respondidas_data})}")
print("\nListo. Ejecutá el dashboard para ver las señales actualizadas.")
