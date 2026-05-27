"""
explorar_sbpr.py
----------------
Explora sbpr, sb104, sbas y sbae para confirmar la tabla de ventas reales.
sbpr parece ser la más directa (ya tiene umsatz por vertr/mes).

Ejecutar:
    python scripts/explorar_sbpr.py > output_sbpr.txt
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
    try:
        return [(c.column_name, c.type_name) for c in cur.columns(table=tabla)]
    except:
        return []

def contar(tabla, where=""):
    try:
        q = f"SELECT COUNT(*) FROM {tabla}"
        if where:
            q += f" WHERE {where}"
        cur.execute(q)
        return cur.fetchone()[0]
    except Exception as e:
        return f"? ({e})"

def primeras(tabla, n=5, where=""):
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

# ── sbpr — ventas reales por vendedor/mes ─────────────────────────────────────
print("=" * 70)
print("TABLA: sbpr  (ventas mensuales por vendedor — la más prometedora)")
print("=" * 70)
sbpr_cols = cols("sbpr")
for c, t in sbpr_cols:
    print(f"  {c:<35} {t}")

print(f"\n  Total filas: {contar('sbpr')}")

print("\n  Primeras 10 filas:")
nombres, filas = primeras("sbpr", 10)
if nombres:
    print(f"  {nombres}")
    for f in filas:
        print(f"  {list(f)}")

print("\n  Últimos años disponibles en sbpr:")
try:
    cur.execute("SELECT DISTINCT bujahr FROM sbpr ORDER BY bujahr DESC")
    anios = [str(r[0]) for r in cur.fetchall()]
    print(f"  {anios}")
except Exception as e:
    print(f"  Error: {e}")

print("\n  Vendedores distintos en sbpr:")
try:
    cur.execute("SELECT COUNT(DISTINCT vertr) FROM sbpr")
    print(f"  {cur.fetchone()[0]} vendedores con datos")
except Exception as e:
    print(f"  Error: {e}")

print("\n  Muestra del año más reciente (top 5 por umsatz):")
try:
    cur.execute("""
        SELECT FIRST 5 vertr, bujahr, bumonat, umsatz, prov
        FROM sbpr
        WHERE bujahr = (SELECT MAX(bujahr) FROM sbpr)
        ORDER BY umsatz DESC
    """)
    filas = cur.fetchall()
    print(f"  {'vertr':>8}  {'año':>6}  {'mes':>4}  {'umsatz':>14}  {'prov':>10}")
    for r in filas:
        print(f"  {r[0]:>8}  {r[1]:>6}  {r[2]:>4}  {float(r[3] or 0):>14,.2f}  {float(r[4] or 0):>10,.2f}")
except Exception as e:
    print(f"  Error: {e}")

print("\n  ¿sbpr tiene suma de umsatz por vendedor en el último año?")
try:
    cur.execute("""
        SELECT FIRST 5 vertr,
               SUM(umsatz) as total_anio
        FROM sbpr
        WHERE bujahr = (SELECT MAX(bujahr) FROM sbpr)
        GROUP BY vertr
        ORDER BY total_anio DESC
    """)
    filas = cur.fetchall()
    for r in filas:
        print(f"  vertr={r[0]}  total={float(r[1] or 0):,.2f}")
except Exception as e:
    print(f"  Error: {e}")

# ── sb104 — cabeceras de pedidos ───────────────────────────────────────────────
print("\n" + "=" * 70)
print("TABLA: sb104  (cabeceras de pedidos según el usuario)")
print("=" * 70)
sb104_cols = cols("sb104")
if sb104_cols:
    for c, t in sb104_cols:
        print(f"  {c:<35} {t}")
    print(f"\n  Total filas: {contar('sb104')}")
    print("\n  Primeras 3 filas:")
    nombres, filas = primeras("sb104", 3)
    if nombres:
        print(f"  {nombres}")
        for f in filas:
            print(f"  {list(f)}")
else:
    print("  No encontrada (puede que no exista o no haya permisos)")

# ── sbas — facturas (comprobante 11) ──────────────────────────────────────────
print("\n" + "=" * 70)
print("TABLA: sbas  (facturas — comprobante tipo 11)")
print("=" * 70)
sbas_cols = cols("sbas")
if sbas_cols:
    for c, t in sbas_cols:
        print(f"  {c:<35} {t}")
    print(f"\n  Total filas: {contar('sbas')}")

    # Ver tipos de comprobante disponibles
    belegtyp_col = next((c for c, _ in sbas_cols if "beleg" in c.lower() or "typ" in c.lower() or "art" in c.lower()), None)
    if belegtyp_col:
        print(f"\n  Valores distintos de '{belegtyp_col}':")
        try:
            cur.execute(f"SELECT {belegtyp_col}, COUNT(*) FROM sbas GROUP BY {belegtyp_col} ORDER BY 2 DESC")
            for r in cur.fetchall():
                print(f"    {belegtyp_col}={r[0]}  ({r[1]} filas)")
        except Exception as e:
            print(f"    Error: {e}")

    print("\n  Primeras 3 filas:")
    nombres, filas = primeras("sbas", 3)
    if nombres:
        print(f"  {nombres}")
        for f in filas:
            print(f"  {list(f)}")

    # Si tiene vertr y umsatz, contar registros tipo factura
    sbas_col_names = [c.lower() for c, _ in sbas_cols]
    if "vertr" in sbas_col_names:
        print(f"\n  sbas tiene columna 'vertr' — puede ser útil para ventas por vendedor")
        try:
            cur.execute("SELECT COUNT(DISTINCT vertr) FROM sbas")
            print(f"  Vendedores distintos: {cur.fetchone()[0]}")
        except:
            pass
else:
    print("  No encontrada")

# ── sbae — otra tabla de ventas ───────────────────────────────────────────────
print("\n" + "=" * 70)
print("TABLA: sbae")
print("=" * 70)
sbae_cols = cols("sbae")
if sbae_cols:
    for c, t in sbae_cols:
        print(f"  {c:<35} {t}")
    print(f"\n  Total filas: {contar('sbae')}")
    print("\n  Primeras 3 filas:")
    nombres, filas = primeras("sbae", 3)
    if nombres:
        print(f"  {nombres}")
        for f in filas:
            print(f"  {list(f)}")
else:
    print("  No encontrada")

# ── Buscar tablas sb* ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TODAS LAS TABLAS con prefijo 'sb'")
print("=" * 70)
tablas = sorted([r.table_name for r in cur.tables(tableType="TABLE")])
tablas_sb = [t for t in tablas if t.lower().startswith("sb")]
for tabla in tablas_sb:
    n = contar(tabla)
    print(f"  [{tabla}]  — {n} filas")

con.close()
print("\n" + "=" * 70)
print("FIN — mandame el output_sbpr.txt")
print("=" * 70)
