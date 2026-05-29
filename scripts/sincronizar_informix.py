"""
sincronizar_informix.py
------------------------
ETL: lee datos de Informix (DSN=MSPA) y los guarda en SQLite data/wurth.db.

Datos que extrae:
  1. adrchr  → clientes nuevos por vendedor/mes (erfuser = vertr1 = id_vendedor)
  2. sbas    → balanza clientes (reactivados, perdidos) + ticket promedio + productos

Lógica de balanza (por vendedor/mes):
  - Nuevo       : cliente cuya erfdat en adrchr cae en ese mes (erfuser = vendedor)
  - Reactivado  : compró este mes Y su venta anterior fue hace 12+ meses
  - Perdido     : última compra fue hace exactamente 12 meses (cruzó umbral de inactividad)
  - Balanza     : nuevos + reactivados - perdidos

REGLA ABSOLUTA: solo lectura de Informix. Nunca INSERT/UPDATE/DELETE en MSPA.

Ejecutar con Python 32 bits:
    C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe scripts\\sincronizar_informix.py

Opciones:
    --dry-run     Muestra totales sin escribir en SQLite
    --full        Toda la historia (por defecto: últimos 6 meses)
    --diagnostico Solo muestra conteos por mes
"""

import sys
import os
import sqlite3
import argparse
from datetime import date, timedelta
from collections import defaultdict

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no instalado.  pip install pyodbc")
    sys.exit(1)

DSN_INFORMIX = "MSPA"
DB_PATH      = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
FIRMA        = 1

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run",     action="store_true")
parser.add_argument("--full",        action="store_true")
parser.add_argument("--diagnostico", action="store_true")
args = parser.parse_args()

DRY_RUN     = args.dry_run
MESES_ATRAS = 99 if args.full else 6

print("=" * 65)
print("SINCRONIZACIÓN Informix (MSPA) → SQLite  (balanza clientes)")
print(f"  DSN:      {DSN_INFORMIX}")
print(f"  DB local: {DB_PATH}")
print(f"  Modo:     {'DRY RUN' if DRY_RUN else 'ESCRITURA'}")
print(f"  Historia: {'completa' if args.full else f'últimos {MESES_ATRAS} meses'}")
print("=" * 65)

hoy = date.today()
fecha_limite    = hoy - timedelta(days=MESES_ATRAS * 30)
anio_inicio     = fecha_limite.year
mes_inicio      = fecha_limite.month
fecha_desde_str = f"{anio_inicio:04d}-{mes_inicio:02d}-01"
fecha_desde_dt  = date(anio_inicio, mes_inicio, 1)
print(f"\n  Período desde: {anio_inicio}/{mes_inicio:02d}  ({fecha_desde_str})")

# ── Leer IDs activos de SQLite ────────────────────────────────────────────────
EXCLUIR_SUPERVISORES = """
    AND nombre NOT IN (
        SELECT DISTINCT supervisor FROM vendedores
        WHERE supervisor IS NOT NULL AND supervisor != ''
    )
"""
try:
    _lcon = sqlite3.connect(DB_PATH)
    _lcur = _lcon.cursor()
    _lcur.execute(f"SELECT id_vendedor FROM vendedores WHERE activo = 1 {EXCLUIR_SUPERVISORES}")
    IDS_ACTIVOS = [str(r[0]) for r in _lcur.fetchall()]
    _lcon.close()
    print(f"  Vendedores activos (sin supervisores): {len(IDS_ACTIVOS)}")
except Exception as e:
    print(f"\nAVISO: no se pudo leer vendedores ({e})")
    IDS_ACTIVOS = []

IN_ACTIVOS = f"({','.join(IDS_ACTIVOS)})" if IDS_ACTIVOS else "(0)"

# ── Conectar a Informix ───────────────────────────────────────────────────────
print("\nConectando a Informix (MSPA)...", end=" ", flush=True)
try:
    icon = pyodbc.connect(f"DSN={DSN_INFORMIX}", timeout=15)
    icur = icon.cursor()
    print("OK")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    sys.exit(1)

# ── Diagnóstico ────────────────────────────────────────────────────────────────
if args.diagnostico:
    print("\n--- DIAGNÓSTICO Informix ---\n")
    print("adrchr (altas de clientes, últimos 6 meses):")
    icur.execute(f"""
        SELECT YEAR(erfdat), MONTH(erfdat), COUNT(DISTINCT kdnr)
        FROM adrchr
        WHERE firma = {FIRMA}
          AND erfdat >= ?
          AND erfuser IN {IN_ACTIVOS}
        GROUP BY 1, 2
        ORDER BY 1 DESC, 2 DESC
    """, fecha_desde_dt)
    for r in icur.fetchall():
        print(f"  {r[0]}/{r[1]:02d}: {r[2]:,} clientes nuevos")

    print("\nsbas (movimientos, últimos 6 meses):")
    icur.execute(f"""
        SELECT bujahr, bumonat,
               COUNT(DISTINCT kdnr)  AS clientes,
               COUNT(DISTINCT artnr) AS productos,
               COUNT(*)              AS lineas
        FROM sbas
        WHERE firma = {FIRMA}
          AND bujahr >= {anio_inicio}
          AND vertr1 IN {IN_ACTIVOS}
        GROUP BY 1, 2
        ORDER BY 1 DESC, 2 DESC
    """)
    for r in icur.fetchall():
        print(f"  {r[0]}/{r[1]:02d}: {r[2]:,} clientes, {r[3]:,} productos, {r[4]:,} líneas")
    icon.close()
    sys.exit(0)

# ── 1. Clientes nuevos (adrchr) ───────────────────────────────────────────────
print("\n[1/3] Clientes nuevos (adrchr)...", end=" ", flush=True)
icur.execute(f"""
    SELECT erfuser, YEAR(erfdat), MONTH(erfdat), COUNT(DISTINCT kdnr)
    FROM adrchr
    WHERE firma = {FIRMA}
      AND erfdat >= ?
      AND erfuser IN {IN_ACTIVOS}
    GROUP BY 1, 2, 3
    ORDER BY 1, 2, 3
""", fecha_desde_dt)

nuevos_data = {}
for row in icur.fetchall():
    vid, anio, mes, nuevos = row
    nuevos_data[(int(vid), int(anio), int(mes))] = int(nuevos or 0)
print(f"OK — {len(nuevos_data)} filas")

# ── 2. Historial de ventas (sbas) — para balanza, ticket, productos ────────────
# Necesitamos 12 meses extra de historia para detectar reactivados y perdidos.
fecha_historico = hoy - timedelta(days=(MESES_ATRAS + 13) * 30)
anio_hist       = fecha_historico.year

print(f"[2/3] Historial sbas (desde {anio_hist})...", end=" ", flush=True)
icur.execute(f"""
    SELECT vertr1, kdnr, bujahr, bumonat,
           SUM(netwert), COUNT(DISTINCT artnr)
    FROM sbas
    WHERE firma = {FIRMA}
      AND bujahr >= {anio_hist}
      AND bumonat >= 1
      AND vertr1 IN {IN_ACTIVOS}
    GROUP BY 1, 2, 3, 4
    ORDER BY 1, 2, 3, 4
""")

historial   = defaultdict(lambda: defaultdict(list))  # [vid][cli] = [(anio,mes),...]
ticket_data = defaultdict(lambda: {"importe": 0.0, "clientes": set(), "prods_set": set()})

total_rows = 0
for row in icur.fetchall():
    vid, cli, anio, mes, neto, prods = row
    vid, cli, anio, mes = int(vid), int(cli), int(anio), int(mes)
    historial[vid][cli].append((anio, mes))
    if (anio * 12 + mes) >= (anio_inicio * 12 + mes_inicio):
        k = (vid, anio, mes)
        ticket_data[k]["importe"] += float(neto or 0)
        ticket_data[k]["clientes"].add(cli)
        ticket_data[k]["prods_set"].add(int(prods or 0))
    total_rows += 1

for vid in historial:
    for cli in historial[vid]:
        historial[vid][cli].sort()

print(f"OK — {total_rows:,} filas")

# ── 3. Calcular balanza ────────────────────────────────────────────────────────
print("[3/3] Calculando reactivados / perdidos...", end=" ", flush=True)

def meses_diff(a1, m1, a2, m2):
    return (a2 * 12 + m2) - (a1 * 12 + m1)

balanza_data = defaultdict(lambda: {"reactivados": 0, "perdidos": 0})

for vid, clientes in historial.items():
    for cli, meses_venta in clientes.items():
        for i, (anio, mes) in enumerate(meses_venta):
            if (anio * 12 + mes) < (anio_inicio * 12 + mes_inicio):
                continue
            k = (vid, anio, mes)
            # Reactivado: venta este mes y la anterior fue 12+ meses antes
            if i > 0:
                a_prev, m_prev = meses_venta[i - 1]
                if meses_diff(a_prev, m_prev, anio, mes) >= 12:
                    balanza_data[k]["reactivados"] += 1

        # Perdido: cuando se cumplen 12 meses desde la última venta
        if meses_venta:
            a_last, m_last = meses_venta[-1]
            m_p = m_last + 12
            a_p = a_last + (m_p - 1) // 12
            m_p = ((m_p - 1) % 12) + 1
            k_p = (vid, a_p, m_p)
            if (a_p * 12 + m_p) >= (anio_inicio * 12 + mes_inicio):
                # Solo cuenta si el cliente había sido activo (no es su primera y única venta
                # hace 12 meses sin historial previo — igual lo contamos, el usuario definió así)
                balanza_data[k_p]["perdidos"] += 1

print(f"OK — {len(balanza_data)} filas")
icon.close()

todas_keys = set(nuevos_data) | set(balanza_data) | set(ticket_data)
print(f"\nTotal filas a sincronizar: {len(todas_keys)}")

if DRY_RUN:
    print("\n--- DRY RUN: muestra (primeras 20 filas) ---")
    print(f"  {'Vend':>6}  {'Mes':>7}  {'Nuev':>4}  {'Reac':>4}  {'Perd':>4}  {'Bal':>4}  {'Ticket':>8}  {'Prods':>5}")
    for k in sorted(todas_keys)[:20]:
        vid, anio, mes = k
        n   = nuevos_data.get(k, 0)
        b   = balanza_data.get(k, {"reactivados": 0, "perdidos": 0})
        re  = b["reactivados"]
        pe  = b["perdidos"]
        td  = ticket_data.get(k, {})
        imp = td.get("importe", 0)
        nc  = len(td.get("clientes", set()))
        ticket = round(imp / nc) if nc else 0
        prods  = sum(td.get("prods_set", {0})) // max(1, len(td.get("prods_set", {1})))
        print(f"  {vid:>6}  {anio}/{mes:02d}  {n:>4}  {re:>4}  {pe:>4}  {n+re-pe:>4}  {ticket:>8}  {prods:>5}")
    print("\nDRY RUN completado. Sin cambios en SQLite.")
    sys.exit(0)

# ── SQLite ─────────────────────────────────────────────────────────────────────
print("\nConectando a SQLite...", end=" ", flush=True)
lcon = sqlite3.connect(DB_PATH)
lcur = lcon.cursor()
print("OK")

lcur.execute("""
    CREATE TABLE IF NOT EXISTS balanza_clientes (
        id_vendedor          INTEGER NOT NULL,
        anio                 INTEGER NOT NULL,
        mes                  INTEGER NOT NULL,
        clientes_nuevos      INTEGER DEFAULT 0,
        clientes_reactivados INTEGER DEFAULT 0,
        clientes_perdidos    INTEGER DEFAULT 0,
        balanza              INTEGER DEFAULT 0,
        ticket_promedio      REAL    DEFAULT 0,
        productos_distintos  INTEGER DEFAULT 0,
        PRIMARY KEY (id_vendedor, anio, mes)
    )
""")
lcon.commit()

upsert_sql = """
    INSERT INTO balanza_clientes
        (id_vendedor, anio, mes,
         clientes_nuevos, clientes_reactivados, clientes_perdidos, balanza,
         ticket_promedio, productos_distintos)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (id_vendedor, anio, mes) DO UPDATE SET
        clientes_nuevos      = excluded.clientes_nuevos,
        clientes_reactivados = excluded.clientes_reactivados,
        clientes_perdidos    = excluded.clientes_perdidos,
        balanza              = excluded.balanza,
        ticket_promedio      = excluded.ticket_promedio,
        productos_distintos  = excluded.productos_distintos
"""

insertados = 0
for k in sorted(todas_keys):
    vid, anio, mes = k
    n   = nuevos_data.get(k, 0)
    b   = balanza_data.get(k, {"reactivados": 0, "perdidos": 0})
    re  = b["reactivados"]
    pe  = b["perdidos"]
    td  = ticket_data.get(k, {})
    imp = td.get("importe", 0)
    nc  = len(td.get("clientes", set()))
    ticket = round(imp / nc, 0) if nc else 0
    prods  = len(td.get("prods_set", set()))

    lcur.execute(upsert_sql, (
        vid, anio, mes,
        n, re, pe, n + re - pe,
        ticket, prods,
    ))
    insertados += 1

lcon.commit()
lcon.close()

print(f"\n✓ {insertados} filas insertadas/actualizadas en balanza_clientes")
pos = sum(1 for k in todas_keys if
          nuevos_data.get(k, 0)
          + balanza_data.get(k, {"reactivados":0})["reactivados"]
          - balanza_data.get(k, {"perdidos":0})["perdidos"] > 0)
neg = sum(1 for k in todas_keys if
          nuevos_data.get(k, 0)
          + balanza_data.get(k, {"reactivados":0})["reactivados"]
          - balanza_data.get(k, {"perdidos":0})["perdidos"] < 0)
print(f"  Meses con balanza positiva: {pos}")
print(f"  Meses con balanza negativa: {neg}")
print("\nListo. Ejecutá el score engine para ver las nuevas señales.")
