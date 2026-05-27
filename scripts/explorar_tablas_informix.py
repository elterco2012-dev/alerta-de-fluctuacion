"""
explorar_tablas_informix.py
---------------------------
Exploración dirigida del schema de Informix para encontrar las tablas
de vendedores, ventas y clientes que necesita el sistema de alertas.

Ejecutar desde la carpeta del proyecto:
    python scripts/explorar_tablas_informix.py > output_explorar.txt
"""

import sys
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

def contar(tabla):
    try:
        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        return cur.fetchone()[0]
    except:
        return "?"

def columnas(tabla):
    try:
        return [(c.column_name, c.type_name) for c in cur.columns(table=tabla)]
    except:
        return []

def muestra(tabla, n=3):
    try:
        cur.execute(f"SELECT FIRST {n} * FROM {tabla}")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return cols, rows
    except Exception as e:
        return [], []

# ── 1. Todas las tablas del schema ────────────────────────────────────────────
print("=" * 70)
print("TODAS LAS TABLAS (nombre + cantidad de filas)")
print("Buscamos las que tienen datos de vendedores, ventas, clientes")
print("=" * 70)
tablas = sorted([r.table_name for r in cur.tables(tableType="TABLE")])
print(f"Total: {len(tablas)} tablas\n")

# ── 2. Explorar tablas por prefijos clave ─────────────────────────────────────
# En Würth Informix los módulos de Außendienst (vendedores externos)
# suelen empezar con "adi" (Außendienst Informationen)
PREFIJOS_INTERES = [
    "adi",   # Außendienst (vendedores de campo) - muy probable
    "abr",   # Abrechnung (facturación/liquidación)
    "vend",  # vendedores (si está en español)
    "venta", # ventas
    "talat", # Talata (reporte interno mencionado)
    "plan",  # plan de ventas
    "cobr",  # cobranza
    "kund",  # Kunde (cliente en alemán)
    "mit",   # Mitarbeiter (empleado en alemán)
    "verk",  # Verkäufer (vendedor en alemán)
    "ums",   # Umsatz (facturación/ventas en alemán)
    "auf",   # Auftrag (pedido en alemán)
    "grup",  # grupos
    "zona",  # zonas
    "reg",   # region
]

print("=" * 70)
print("TABLAS POR PREFIJOS RELEVANTES")
print("=" * 70)

encontradas_por_prefijo = {}
for prefijo in PREFIJOS_INTERES:
    match = [t for t in tablas if t.lower().startswith(prefijo.lower())]
    if match:
        encontradas_por_prefijo[prefijo] = match
        print(f"\n  Prefijo '{prefijo}': {match}")

# ── 3. Detalle de tablas "adi*" (Außendienst) ─────────────────────────────────
print("\n" + "=" * 70)
print("DETALLE TABLAS 'adi*' (probable módulo de vendedores de campo)")
print("=" * 70)

tablas_adi = [t for t in tablas if t.lower().startswith("adi")]
for tabla in tablas_adi:
    n = contar(tabla)
    cols = columnas(tabla)
    print(f"\n  [{tabla}]  — {n} filas")
    for col_name, col_type in cols:
        print(f"    {col_name:<35} {col_type}")

    # Mostrar 2 filas de muestra si tiene datos
    if isinstance(n, int) and n > 0:
        col_names, rows = muestra(tabla, 2)
        if rows:
            print(f"  Muestra:")
            print(f"    Columnas: {col_names}")
            for row in rows:
                print(f"    {list(row)}")

# ── 4. Detalle tablas "abr*" (facturación) ────────────────────────────────────
print("\n" + "=" * 70)
print("DETALLE TABLAS 'abr*' (posible facturación/ventas)")
print("=" * 70)

tablas_abr = [t for t in tablas if t.lower().startswith("abr")]
for tabla in tablas_abr:
    n = contar(tabla)
    cols = columnas(tabla)
    print(f"\n  [{tabla}]  — {n} filas")
    for col_name, col_type in cols:
        print(f"    {col_name:<35} {col_type}")

# ── 5. Buscar por palabras clave en nombres de COLUMNAS ───────────────────────
print("\n" + "=" * 70)
print("BÚSQUEDA POR COLUMNAS — buscando 'vendedor', 'vend', 'plan', 'cobr'")
print("(revisa todas las tablas — puede tardar 1-2 minutos)")
print("=" * 70)

KEYWORDS_COLS = ["vend", "plan", "cobr", "ingr", "egres", "zona", "grup",
                 "venta", "factu", "pedi", "clien"]

tablas_con_keyword = {}
for tabla in tablas:
    try:
        cols_tabla = [c.column_name.lower() for c in cur.columns(table=tabla)]
        for kw in KEYWORDS_COLS:
            if any(kw in c for c in cols_tabla):
                if tabla not in tablas_con_keyword:
                    tablas_con_keyword[tabla] = []
                cols_match = [c for c in cols_tabla if kw in c]
                tablas_con_keyword[tabla].extend(cols_match)
    except:
        pass

if tablas_con_keyword:
    print(f"\nTablas con columnas relevantes:\n")
    for tabla, cols_match in sorted(tablas_con_keyword.items()):
        n = contar(tabla)
        print(f"  [{tabla}] — {n} filas")
        print(f"    Columnas relevantes: {list(set(cols_match))}")
        all_cols = columnas(tabla)
        for cn, ct in all_cols:
            print(f"      {cn:<35} {ct}")
        print()
else:
    print("No se encontraron columnas con esas palabras clave.")

# ── 6. Tablas con más filas (probablemente transaccionales) ───────────────────
print("\n" + "=" * 70)
print("TOP 20 TABLAS POR CANTIDAD DE FILAS (probablemente las más usadas)")
print("=" * 70)

conteos = []
for tabla in tablas[:200]:  # primera pasada con 200 tablas
    n = contar(tabla)
    if isinstance(n, int):
        conteos.append((n, tabla))

conteos.sort(reverse=True)
print(f"\n{'Filas':>12}  Tabla")
for n, tabla in conteos[:20]:
    print(f"{n:>12,}  {tabla}")

con.close()
print("\n" + "=" * 70)
print("FIN DE EXPLORACIÓN")
print("Enviá el contenido de este output para identificar las tablas correctas.")
print("=" * 70)
