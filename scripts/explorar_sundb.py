"""
explorar_sundb.py
-----------------
Exploración de la estructura de SUNDB (SQL Server, sistema SUN).
Ejecutar desde C:\\alerta-de-fluctuacion con:

    python scripts\\explorar_sundb.py

No modifica nada. Solo lectura.
"""

import pyodbc
import sys

print("Conectando a SUNDB...", end=" ", flush=True)
try:
    con = pyodbc.connect("DSN=SUNDB", timeout=10)
    print("OK")
except Exception as e:
    print(f"\nERROR al conectar: {e}")
    sys.exit(1)

cur = con.cursor()

# ── 1. Todas las tablas ────────────────────────────────────────────────────────
print("\n=== TABLAS EN SUNDB ===")
cur.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_SCHEMA, TABLE_NAME
""")
tablas = cur.fetchall()
for row in tablas:
    print(f"  {row.TABLE_SCHEMA}.{row.TABLE_NAME}")

print(f"\n  Total: {len(tablas)} tablas")

# ── 2. Buscar tablas con nombres que sugieren ventas / cobros ─────────────────
KEYWORDS = [
    "cobr", "pago", "recib", "factur", "venta", "ingres",
    "compr", "movim", "asient", "cuenta", "cuota", "vend",
    "sale", "paym", "invo", "receiv", "order",
]

print("\n=== TABLAS POSIBLEMENTE RELEVANTES (por nombre) ===")
relevantes = []
for schema, tabla in tablas:
    nombre_lower = tabla.lower()
    if any(kw in nombre_lower for kw in KEYWORDS):
        relevantes.append((schema, tabla))
        print(f"  {schema}.{tabla}")

if not relevantes:
    print("  (ninguna encontrada por nombre — ver lista completa arriba)")

# ── 3. Columnas de cada tabla relevante ───────────────────────────────────────
if relevantes:
    print("\n=== COLUMNAS DE TABLAS RELEVANTES ===")
    for schema, tabla in relevantes:
        print(f"\n--- {schema}.{tabla} ---")
        cur.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, schema, tabla)
        for col in cur.fetchall():
            tipo = col.DATA_TYPE
            if col.CHARACTER_MAXIMUM_LENGTH:
                tipo += f"({col.CHARACTER_MAXIMUM_LENGTH})"
            print(f"    {col.COLUMN_NAME:<35} {tipo}")

        # Muestra de 3 filas
        try:
            cur.execute(f"SELECT TOP 3 * FROM [{schema}].[{tabla}]")
            rows = cur.fetchall()
            if rows:
                print(f"  (muestra de {len(rows)} filas):")
                for row in rows:
                    print(f"    {list(row)}")
        except Exception as e:
            print(f"  (no se pudo leer muestra: {e})")

con.close()
print("\n=== FIN ===")
