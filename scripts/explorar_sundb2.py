"""
explorar_sundb2.py
------------------
Guarda la estructura completa de SUNDB en un archivo de texto.
Ejecutar con:
    C:\\Users\\<usuario>\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe scripts\\explorar_sundb2.py

Genera: data\\sundb_estructura.txt.
"""

import os
import pyodbc, sys

# Candado: a MSPA, SUN y Reactor solo les llega un SELECT (ver src/solo_lectura.py).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from solo_lectura import conectar  # noqa: E402

# En data\, que la cuenta de Claude no puede leer: trae filas de muestra.
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sundb_estructura.txt")

con = conectar("DSN=SUNDB", timeout=10)
cur = con.cursor()

lines = []

# ── Todas las tablas ──────────────────────────────────────────────────────────
cur.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_SCHEMA, TABLE_NAME
""")
tablas = cur.fetchall()
lines.append(f"=== {len(tablas)} TABLAS EN SUNDB ===\n")
for row in tablas:
    lines.append(f"  {row.TABLE_SCHEMA}.{row.TABLE_NAME}")

# ── Columnas y muestra de CADA tabla ─────────────────────────────────────────
lines.append("\n\n=== DETALLE DE TODAS LAS TABLAS ===\n")
for schema, tabla in tablas:
    lines.append(f"\n--- {schema}.{tabla} ---")
    cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, schema, tabla)
    cols = cur.fetchall()
    col_names = [c.COLUMN_NAME for c in cols]
    for c in cols:
        lines.append(f"  {c.COLUMN_NAME:<40} {c.DATA_TYPE}")
    try:
        cur.execute(f"SELECT TOP 2 * FROM [{schema}].[{tabla}]")
        rows = cur.fetchall()
        for r in rows:
            lines.append(f"  MUESTRA: {dict(zip(col_names, list(r)))}")
    except Exception as e:
        lines.append(f"  (sin muestra: {e})")

con.close()

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Listo. Archivo generado: {OUTPUT}")
print(f"Abrilo con el Bloc de notas y pegá el contenido acá.")
