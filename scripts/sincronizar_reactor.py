"""
sincronizar_reactor.py
-----------------------
ETL: lee llamadas (Televentas) y visitas (Viajantes) de Reactor CRM
(MySQL, DSN="Wurth Reactor Produccion") y los guarda en actividad_mensual
dentro de data/wurth.db (SQLite).

Reactor usa Python 64 bits (MySQL ODBC no requiere 32 bits):
    python scripts\\sincronizar_reactor.py

Tablas de origen:
  customer_management  → llamadas de Televentas (JOIN user ON id_user_author)
  customer_visit       → visitas de Viajantes   (JOIN user ON id_user_author)
  telephony_call_history → llamadas respondidas (campo agent = vertr1 directo)

Tabla destino en SQLite:
  actividad_mensual (id_vendedor, anio, mes, llamadas, llamadas_exitosas,
                     visitas, clientes_llamados, clientes_visitados,
                     llamadas_respondidas)

Opciones:
    --dry-run      Muestra totales sin escribir en SQLite
    --full         Procesa toda la historia (por defecto: últimos 6 meses)
    --diagnostico  Solo muestra conteos por tabla y año/mes
"""

import sys
import os
import sqlite3
import argparse
from datetime import date, datetime
from collections import defaultdict

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

# ── Conectar a Reactor MySQL ───────────────────────────────────────────────────
print("\nConectando a Reactor CRM (MySQL)...", end=" ", flush=True)
try:
    rcn = pyodbc.connect(f"DSN={DSN_REACTOR}", timeout=15)
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

    print("customer_management (llamadas Televentas):")
    rcur.execute("""
        SELECT YEAR(cm.created) AS anio, MONTH(cm.created) AS mes,
               COUNT(*) AS total,
               SUM(CASE WHEN cm.closure_no_action_reason IS NULL THEN 1 ELSE 0 END) AS exitosas
        FROM customer_management cm
        JOIN `user` u ON cm.id_user_author = u.id
        WHERE cm.created >= ?
          AND u.username REGEXP '^[0-9]+$'
          AND CAST(u.username AS UNSIGNED) > 0
        GROUP BY YEAR(cm.created), MONTH(cm.created)
        ORDER BY anio, mes
    """, fecha_desde)
    for row in rcur.fetchall():
        print(f"  {row[0]}/{row[1]:02d}: {row[2]} llamadas, {row[3]} exitosas")

    print("\ncustomer_visit (visitas Viajantes):")
    rcur.execute("""
        SELECT YEAR(cv.start_time) AS anio, MONTH(cv.start_time) AS mes,
               COUNT(*) AS total
        FROM customer_visit cv
        JOIN `user` u ON cv.id_user_author = u.id
        WHERE cv.start_time >= ?
          AND u.username REGEXP '^[0-9]+$'
          AND CAST(u.username AS UNSIGNED) > 0
        GROUP BY YEAR(cv.start_time), MONTH(cv.start_time)
        ORDER BY anio, mes
    """, fecha_desde)
    for row in rcur.fetchall():
        print(f"  {row[0]}/{row[1]:02d}: {row[2]} visitas")

    print("\ntelephony_call_history (llamadas respondidas):")
    rcur.execute("""
        SELECT YEAR(created) AS anio, MONTH(created) AS mes,
               COUNT(*) AS total,
               SUM(CASE WHEN is_answered = 1 THEN 1 ELSE 0 END) AS respondidas
        FROM telephony_call_history
        WHERE type = 'report'
          AND created >= ?
          AND agent REGEXP '^[0-9]+$'
          AND CAST(agent AS UNSIGNED) > 0
        GROUP BY YEAR(created), MONTH(created)
        ORDER BY anio, mes
    """, fecha_desde)
    for row in rcur.fetchall():
        print(f"  {row[0]}/{row[1]:02d}: {row[2]} registros, {row[3]} respondidas")

    rcn.close()
    sys.exit(0)

# ── 1. Llamadas Televentas (customer_management + user) ───────────────────────
print("\n[1/3] Leyendo llamadas Televentas (customer_management)...", end=" ", flush=True)
rcur.execute("""
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
      AND u.username REGEXP '^[0-9]+$'
      AND CAST(u.username AS UNSIGNED) > 0
    GROUP BY CAST(u.username AS UNSIGNED), YEAR(cm.created), MONTH(cm.created)
    ORDER BY id_vendedor, anio, mes
""", fecha_desde)

llamadas_data = {}
for row in rcur.fetchall():
    vid, anio, mes, llamadas, exitosas, clientes = row
    k = (int(vid), int(anio), int(mes))
    llamadas_data[k] = {
        "llamadas":         int(llamadas or 0),
        "llamadas_exitosas": int(exitosas or 0),
        "clientes_llamados": int(clientes or 0),
    }

print(f"OK — {len(llamadas_data)} filas (vendedor/año/mes)")

# ── 2. Visitas Viajantes (customer_visit + user) ───────────────────────────────
print("[2/3] Leyendo visitas Viajantes (customer_visit)...", end=" ", flush=True)
rcur.execute("""
    SELECT CAST(u.username AS UNSIGNED)                          AS id_vendedor,
           YEAR(cv.start_time)                                   AS anio,
           MONTH(cv.start_time)                                  AS mes,
           COUNT(*)                                              AS visitas,
           COUNT(DISTINCT cv.customer_code)                      AS clientes_visitados
    FROM customer_visit cv
    JOIN `user` u ON cv.id_user_author = u.id
    WHERE cv.start_time >= ?
      AND u.username REGEXP '^[0-9]+$'
      AND CAST(u.username AS UNSIGNED) > 0
    GROUP BY CAST(u.username AS UNSIGNED), YEAR(cv.start_time), MONTH(cv.start_time)
    ORDER BY id_vendedor, anio, mes
""", fecha_desde)

visitas_data = {}
for row in rcur.fetchall():
    vid, anio, mes, visitas, clientes = row
    k = (int(vid), int(anio), int(mes))
    visitas_data[k] = {
        "visitas":           int(visitas or 0),
        "clientes_visitados": int(clientes or 0),
    }

print(f"OK — {len(visitas_data)} filas (vendedor/año/mes)")

# ── 3. Llamadas respondidas (telephony_call_history, agent = vertr1 directo) ──
print("[3/3] Leyendo llamadas respondidas (telephony_call_history)...", end=" ", flush=True)
rcur.execute("""
    SELECT CAST(agent AS UNSIGNED)                               AS id_vendedor,
           YEAR(created)                                         AS anio,
           MONTH(created)                                        AS mes,
           SUM(CASE WHEN is_answered = 1 THEN 1 ELSE 0 END)     AS respondidas
    FROM telephony_call_history
    WHERE type = 'report'
      AND created >= ?
      AND agent REGEXP '^[0-9]+$'
      AND CAST(agent AS UNSIGNED) > 0
    GROUP BY CAST(agent AS UNSIGNED), YEAR(created), MONTH(created)
    ORDER BY id_vendedor, anio, mes
""", fecha_desde)

respondidas_data = {}
for row in rcur.fetchall():
    vid, anio, mes, respondidas = row
    k = (int(vid), int(anio), int(mes))
    respondidas_data[k] = int(respondidas or 0)

print(f"OK — {len(respondidas_data)} filas (vendedor/año/mes)")

rcn.close()

# ── Unir los tres datasets ────────────────────────────────────────────────────
todas_keys = set(llamadas_data) | set(visitas_data) | set(respondidas_data)
print(f"\nTotal filas a sincronizar: {len(todas_keys)}")

if DRY_RUN:
    print("\n--- DRY RUN: muestra de primeras 20 filas ---")
    for k in sorted(todas_keys)[:20]:
        vid, anio, mes = k
        ll  = llamadas_data.get(k, {})
        vv  = visitas_data.get(k, {})
        rr  = respondidas_data.get(k, 0)
        print(
            f"  Vendedor {vid:>5}  {anio}/{mes:02d} → "
            f"llamadas={ll.get('llamadas',0):>4}  exitosas={ll.get('llamadas_exitosas',0):>4}  "
            f"visitas={vv.get('visitas',0):>4}  "
            f"respondidas={rr:>4}"
        )
    print("\nDRY RUN completado. Sin cambios en SQLite.")
    sys.exit(0)

# ── Conectar a SQLite y crear tabla si no existe ──────────────────────────────
print("\nConectando a SQLite...", end=" ", flush=True)
try:
    lcon = sqlite3.connect(DB_PATH)
    lcur = lcon.cursor()
    print("OK")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    sys.exit(1)

lcur.execute("""
    CREATE TABLE IF NOT EXISTS actividad_mensual (
        id_vendedor          INTEGER NOT NULL,
        anio                 INTEGER NOT NULL,
        mes                  INTEGER NOT NULL,
        llamadas             INTEGER DEFAULT 0,
        llamadas_exitosas    INTEGER DEFAULT 0,
        visitas              INTEGER DEFAULT 0,
        clientes_llamados    INTEGER DEFAULT 0,
        clientes_visitados   INTEGER DEFAULT 0,
        llamadas_respondidas INTEGER DEFAULT 0,
        PRIMARY KEY (id_vendedor, anio, mes)
    )
""")
lcon.commit()

# ── Insertar / actualizar ─────────────────────────────────────────────────────
upsert_sql = """
    INSERT INTO actividad_mensual
        (id_vendedor, anio, mes, llamadas, llamadas_exitosas,
         visitas, clientes_llamados, clientes_visitados, llamadas_respondidas)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (id_vendedor, anio, mes) DO UPDATE SET
        llamadas             = excluded.llamadas,
        llamadas_exitosas    = excluded.llamadas_exitosas,
        visitas              = excluded.visitas,
        clientes_llamados    = excluded.clientes_llamados,
        clientes_visitados   = excluded.clientes_visitados,
        llamadas_respondidas = excluded.llamadas_respondidas
"""

insertados = 0
for k in sorted(todas_keys):
    vid, anio, mes = k
    ll = llamadas_data.get(k, {})
    vv = visitas_data.get(k, {})
    rr = respondidas_data.get(k, 0)

    lcur.execute(upsert_sql, (
        vid, anio, mes,
        ll.get("llamadas", 0),
        ll.get("llamadas_exitosas", 0),
        vv.get("visitas", 0),
        ll.get("clientes_llamados", 0),
        vv.get("clientes_visitados", 0),
        rr,
    ))
    insertados += 1

lcon.commit()
lcon.close()

print(f"\n✓ {insertados} filas insertadas/actualizadas en actividad_mensual")
print("\nResumen:")
print(f"  Vendedores con llamadas : {len({k[0] for k in llamadas_data})}")
print(f"  Vendedores con visitas  : {len({k[0] for k in visitas_data})}")
print(f"  Vendedores con tel. hist: {len({k[0] for k in respondidas_data})}")
print("\nListo. Ejecutá el dashboard para ver las señales actualizadas.")
