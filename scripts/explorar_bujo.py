"""
explorar_bujo.py
----------------
Exploración específica de las tablas bujo / bujoerw para entender
la estructura de ventas reales por vendedor.

Ejecutar desde la carpeta del proyecto:
    python scripts/explorar_bujo.py > output_bujo.txt
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import pyodbc

DSN = os.getenv("INFORMIX_DSN", "MSPA")
UID = os.getenv("INFORMIX_UID", "aarmoa")
PWD = os.getenv("INFORMIX_PWD", "")

print("Conectando...", end=" ")
con = pyodbc.connect(f"DSN={DSN};UID={UID};PWD={PWD};", timeout=10)
print("OK\n")
cur = con.cursor()

def cols(tabla):
    return [(c.column_name, c.type_name) for c in cur.columns(table=tabla)]

def muestra(tabla, n=5, where=""):
    try:
        q = f"SELECT FIRST {n} * FROM {tabla}"
        if where:
            q += f" WHERE {where}"
        cur.execute(q)
        nombres = [d[0] for d in cur.description]
        filas = cur.fetchall()
        return nombres, filas
    except Exception as e:
        return [], []

# ── 1. Estructura de bujo ─────────────────────────────────────────────────────
print("=" * 70)
print("TABLA: bujo  (journal de transacciones)")
print("=" * 70)
for c, t in cols("bujo"):
    print(f"  {c:<35} {t}")

print("\nMuestra (5 filas):")
nombres, filas = muestra("bujo")
if nombres:
    print(f"  Columnas: {nombres}")
    for f in filas:
        print(f"  {list(f)}")

# ── 2. Estructura de bujoerw ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TABLA: bujoerw  (journal extendido)")
print("=" * 70)
for c, t in cols("bujoerw"):
    print(f"  {c:<35} {t}")

print("\nMuestra (5 filas):")
nombres, filas = muestra("bujoerw")
if nombres:
    print(f"  Columnas: {nombres}")
    for f in filas:
        print(f"  {list(f)}")

# ── 3. Ventas reales por vendedor/mes (si hay umsatz en bujo) ─────────────────
print("\n" + "=" * 70)
print("VENTAS REALES — sum(umsatz) por vertr/bujahr/bumonat")
print("(si la tabla tiene esas columnas)")
print("=" * 70)

bujo_cols = [c[0].lower() for c in cols("bujo")]
tiene_umsatz = "umsatz" in bujo_cols
tiene_vertr  = "vertr" in bujo_cols
tiene_bujahr = "bujahr" in bujo_cols
tiene_kdnr   = "kdnr" in bujo_cols

print(f"\n  vertr:   {'SI' if tiene_vertr else 'NO'}")
print(f"  bujahr:  {'SI' if tiene_bujahr else 'NO'}")
print(f"  umsatz:  {'SI' if tiene_umsatz else 'NO'}")
print(f"  kdnr:    {'SI' if tiene_kdnr else 'NO'}")

if tiene_umsatz and tiene_vertr and tiene_bujahr:
    print("\n  Aggregado: ventas por vendedor en el último año disponible")
    try:
        cur.execute("""
            SELECT vertr, bujahr, bumonat, COUNT(*) as transacciones,
                   SUM(umsatz) as venta_total
            FROM bujo
            WHERE bujahr = (SELECT MAX(bujahr) FROM bujo)
            GROUP BY vertr, bujahr, bumonat
            ORDER BY vertr, bumonat
            FETCH FIRST 30 ROWS ONLY
        """)
        rows = cur.fetchall()
        print(f"  {'vertr':>8}  {'año':>6}  {'mes':>4}  {'trans':>8}  {'venta_total':>14}")
        print("  " + "-" * 50)
        for r in rows:
            print(f"  {r[0]:>8}  {r[1]:>6}  {r[2]:>4}  {r[3]:>8}  {r[4]:>14,.2f}")
    except Exception as e:
        print(f"  Error: {e}")

# ── 4. Clientes únicos por vendedor/mes ───────────────────────────────────────
if tiene_kdnr and tiene_vertr and tiene_bujahr:
    print("\n" + "=" * 70)
    print("CLIENTES ÚNICOS por vendedor en el último año")
    print("=" * 70)
    try:
        cur.execute("""
            SELECT vertr, bujahr, bumonat, COUNT(DISTINCT kdnr) as clientes_distintos
            FROM bujo
            WHERE bujahr = (SELECT MAX(bujahr) FROM bujo)
            GROUP BY vertr, bujahr, bumonat
            ORDER BY vertr, bumonat
            FETCH FIRST 30 ROWS ONLY
        """)
        rows = cur.fetchall()
        for r in rows:
            print(f"  vertr={r[0]}  {r[1]}/{r[2]:02d}  clientes={r[3]}")
    except Exception as e:
        print(f"  Error: {e}")

# ── 5. Muestra para vendedor específico ───────────────────────────────────────
print("\n" + "=" * 70)
print("MUESTRA: vendedor con más transacciones en bujo")
print("=" * 70)
if tiene_vertr and tiene_bujahr:
    try:
        cur.execute("""
            SELECT FIRST 1 vertr, COUNT(*) as n
            FROM bujo
            WHERE bujahr = (SELECT MAX(bujahr) FROM bujo)
            GROUP BY vertr
            ORDER BY 2 DESC
        """)
        row = cur.fetchone()
        if row:
            vertr_sample = row[0]
            print(f"\n  Vendedor {vertr_sample} — mostrando 10 filas de bujo:")
            nombres, filas = muestra("bujo", 10, f"vertr={vertr_sample}")
            if nombres:
                print(f"  Columnas: {nombres}")
                for f in filas:
                    print(f"  {list(f)}")
    except Exception as e:
        print(f"  Error: {e}")

# ── 6. Muestra de f040 (vendedores) ──────────────────────────────────────────
print("\n" + "=" * 70)
print("MUESTRA: f040 — primeros 5 vendedores activos (austrdat IS NULL)")
print("=" * 70)
try:
    cur.execute("""
        SELECT FIRST 5 vertr, name1, name2, vgrp, vart, eintrdat, austrdat,
               zone, region, kzleiter
        FROM f040
        WHERE austrdat IS NULL
    """)
    rows = cur.fetchall()
    for r in rows:
        print(f"  vertr={r[0]}  nombre='{str(r[1]).strip()} {str(r[2]).strip()}'  "
              f"vgrp={r[3]}  vart={r[4]}  ingreso={r[5]}  "
              f"zona='{str(r[7]).strip() if r[7] else ''}'  kzleiter={r[9]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n  Muestra con austrdat para entender vendedores inactivos:")
try:
    cur.execute("""
        SELECT FIRST 5 vertr, name1, vgrp, vart, eintrdat, austrdat
        FROM f040
        WHERE austrdat IS NOT NULL
        ORDER BY austrdat DESC
    """)
    rows = cur.fetchall()
    for r in rows:
        print(f"  vertr={r[0]}  nombre='{str(r[1]).strip()}'  "
              f"ingreso={r[4]}  egreso={r[5]}")
except Exception as e:
    print(f"  Error: {e}")

# ── 7. Valores de vart (tipo de vendedor) ────────────────────────────────────
print("\n" + "=" * 70)
print("VALORES DISTINTOS de vart (tipo vendedor) en f040")
print("=" * 70)
try:
    cur.execute("SELECT vart, COUNT(*) as n FROM f040 GROUP BY vart ORDER BY 2 DESC")
    rows = cur.fetchall()
    for r in rows:
        print(f"  vart={r[0]}  ({r[1]} vendedores)")
except Exception as e:
    print(f"  Error: {e}")

# ── 8. Muestra de vplan ───────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("MUESTRA: vplan — últimos 3 meses disponibles")
print("=" * 70)
try:
    cur.execute("""
        SELECT FIRST 15 vertr, bujahr, bumonat, planums, plannutz, planumsk, aktivkd,
               tg_krank, tg_unfall, tg_urlaub
        FROM vplan
        ORDER BY bujahr DESC, bumonat DESC, vertr
    """)
    rows = cur.fetchall()
    print(f"  {'vertr':>8}  {'año':>6}  {'mes':>4}  {'planums':>12}  {'aktivkd':>10}")
    for r in rows:
        print(f"  {r[0]:>8}  {r[1]:>6}  {r[2]:>4}  {r[3]:>12}  {r[6]:>10}")
except Exception as e:
    print(f"  Error: {e}")

con.close()
print("\n" + "=" * 70)
print("FIN — guardá este output y compartilo")
print("=" * 70)
