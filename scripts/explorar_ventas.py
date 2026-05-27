"""
explorar_ventas.py
------------------
Busca la tabla de ventas reales (facturación por vendedor).
bujo = diario de almacén (no sirve para ventas).
Exploramos buar, arae, y otras candidatas.

Ejecutar:
    python scripts/explorar_ventas.py > output_ventas.txt
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

def contar(tabla):
    try:
        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        return cur.fetchone()[0]
    except:
        return "?"

# ── 1. Explorar buar (Buchungsarchiv — posible historial de ventas) ───────────
print("=" * 70)
print("TABLA: buar  (Buchungsarchiv — archivo de contabilidad/ventas)")
print("=" * 70)
buar_cols = cols("buar")
for c, t in buar_cols:
    print(f"  {c:<35} {t}")

print("\nPrimeras 3 filas:")
nombres, filas = primeras("buar", 3)
if nombres:
    print(f"  Columnas: {nombres}")
    for f in filas:
        print(f"  {list(f)}")

# ── 2. Explorar arae ──────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TABLA: arae  (843K filas — candidata a ventas)")
print("=" * 70)
arae_cols = cols("arae")
for c, t in arae_cols:
    print(f"  {c:<35} {t}")

print("\nPrimeras 3 filas:")
nombres, filas = primeras("arae", 3)
if nombres:
    print(f"  Columnas: {nombres}")
    for f in filas:
        print(f"  {list(f)}")

# ── 3. Buscar tablas con vertr + umsatz (ventas por vendedor) ─────────────────
print("\n" + "=" * 70)
print("BÚSQUEDA: tablas que tienen tanto 'vertr' como 'umsatz'")
print("=" * 70)
tablas = sorted([r.table_name for r in cur.tables(tableType="TABLE")])
candidatas = []
for tabla in tablas:
    nombres_cols = [c.column_name.lower() for c in cur.columns(table=tabla)]
    tiene_vertr  = "vertr"  in nombres_cols
    tiene_umsatz = "umsatz" in nombres_cols
    if tiene_vertr and tiene_umsatz:
        n = contar(tabla)
        candidatas.append((tabla, n, nombres_cols))
        print(f"\n  [{tabla}]  — {n} filas")
        for c in nombres_cols:
            print(f"    {c}")

if not candidatas:
    print("  No encontradas — buscando tablas con 'vertr' solamente...")
    for tabla in tablas:
        nombres_cols = [c.column_name.lower() for c in cur.columns(table=tabla)]
        if "vertr" in nombres_cols:
            n = contar(tabla)
            print(f"\n  [{tabla}]  — {n} filas")
            for c in nombres_cols:
                print(f"    {c}")

# ── 4. Muestra de f040 (arreglada — sin columna reservada 'zone') ─────────────
print("\n" + "=" * 70)
print("f040 — vendedores activos (austrdat vacío o nulo)")
print("=" * 70)
try:
    cur.execute("""
        SELECT FIRST 5 vertr, name1, name2, vgrp, vart, eintrdat, austrdat, region
        FROM f040
    """)
    filas = cur.fetchall()
    print("  vertr  | nombre                    | vgrp | vart | ingreso    | egreso")
    print("  " + "-" * 70)
    for r in filas:
        nombre = f"{(r[1] or '').strip()} {(r[2] or '').strip()}".strip()
        egreso = str(r[6])[:10] if r[6] else "activo"
        print(f"  {r[0]:>6} | {nombre:<25} | {str(r[3]):>4} | {str(r[4]):>4} | {str(r[5])[:10]} | {egreso}")
except Exception as e:
    print(f"  Error: {e}")

# ── 5. Contar activos vs bajas en f040 ────────────────────────────────────────
print("\n" + "=" * 70)
print("f040 — ¿cómo se distingue activo de dado de baja?")
print("=" * 70)
try:
    # Ver cuántos tienen austrdat no nulo vs nulo
    cur.execute("SELECT COUNT(*) FROM f040 WHERE austrdat IS NOT NULL")
    con_egreso = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM f040 WHERE austrdat IS NULL")
    sin_egreso = cur.fetchone()[0]
    print(f"  austrdat IS NOT NULL (tiene fecha egreso): {con_egreso}")
    print(f"  austrdat IS NULL     (sin fecha egreso):   {sin_egreso}")
except Exception as e:
    print(f"  Error IS NULL: {e}")
    # Alternativa: comparar con string vacío
    try:
        cur.execute("SELECT COUNT(*) FROM f040 WHERE austrdat > '2000-01-01'")
        con_egreso2 = cur.fetchone()[0]
        print(f"  austrdat > '2000-01-01': {con_egreso2}")
    except Exception as e2:
        print(f"  Error alternativo: {e2}")

# ── 6. vplan corregido (SELECT FIRST, no FETCH FIRST) ────────────────────────
print("\n" + "=" * 70)
print("vplan — últimos registros disponibles")
print("=" * 70)
try:
    cur.execute("""
        SELECT FIRST 10 vertr, bujahr, bumonat, planums, aktivkd
        FROM vplan
        ORDER BY bujahr DESC, bumonat DESC, vertr
    """)
    filas = cur.fetchall()
    print(f"  {'vertr':>8}  {'año':>6}  {'mes':>4}  {'planums':>12}  {'aktivkd':>10}")
    print("  " + "-" * 50)
    for r in filas:
        print(f"  {r[0]:>8}  {r[1]:>6}  {r[2]:>4}  {str(r[3]):>12}  {str(r[4]):>10}")
except Exception as e:
    print(f"  Error: {e}")

# ── 7. Revisar cuit (146K filas — específico Argentina) ───────────────────────
print("\n" + "=" * 70)
print("TABLA: cuit  (146K filas — CUIT argentino, posible tabla de clientes)")
print("=" * 70)
cuit_cols = cols("cuit")
for c, t in cuit_cols:
    print(f"  {c:<35} {t}")

print("\nPrimeras 3 filas:")
nombres, filas = primeras("cuit", 3)
if nombres:
    print(f"  Columnas: {nombres}")
    for f in filas:
        print(f"  {list(f)}")

con.close()
print("\n" + "=" * 70)
print("FIN — mandame el output_ventas.txt")
print("=" * 70)
