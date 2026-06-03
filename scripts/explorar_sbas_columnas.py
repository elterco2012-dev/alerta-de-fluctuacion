"""
scripts/explorar_sbas_columnas.py
---------------------------------
El sync probaba budat/belegdat/erfdat/liefdat/dat/fdat como campo de fecha de
sbas y NINGUNO existe. Este script lista TODAS las columnas reales de sbas
(con su tipo) y muestra una fila de ejemplo, para identificar cuál es el campo
de fecha que hay que usar para contar días con venta.

Solo LECTURA sobre Informix (DSN=MSPA). Solo SELECT y lectura de catálogo.
No escribe en ninguna base.

Ejecutar con Python 32 bits (ODBC):
    "C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe" scripts\\explorar_sbas_columnas.py
"""

import sys

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no instalado en este Python.")
    sys.exit(1)

DSN_INFORMIX = "MSPA"
FIRMA        = 1

print("=" * 68)
print("EXPLORACIÓN — columnas reales de la tabla sbas")
print("=" * 68)

print("\nConectando a Informix (MSPA)...", end=" ", flush=True)
try:
    cn  = pyodbc.connect(f"DSN={DSN_INFORMIX}", timeout=15)
    cur = cn.cursor()
    print("OK")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    sys.exit(1)

# ── 1. Columnas vía catálogo del sistema (nombre + tipo) ────────────────────
print("\n[1] Columnas de sbas (catálogo syscolumns):")
# coltype mod 256 da el tipo base en Informix; 7=date, 10=datetime son los que buscamos
TIPOS = {
    0: "CHAR", 1: "SMALLINT", 2: "INTEGER", 3: "FLOAT", 4: "SMALLFLOAT",
    5: "DECIMAL", 6: "SERIAL", 7: "DATE", 8: "MONEY", 10: "DATETIME",
    11: "BYTE", 12: "TEXT", 13: "VARCHAR", 14: "INTERVAL", 15: "NCHAR",
    16: "NVARCHAR", 17: "INT8", 18: "SERIAL8", 19: "LVARCHAR",
}
columnas = []
try:
    cur.execute("""
        SELECT c.colname, c.coltype, c.collength
        FROM systables t
        JOIN syscolumns c ON t.tabid = c.tabid
        WHERE t.tabname = 'sbas'
        ORDER BY c.colno
    """)
    for nombre, coltype, collength in cur.fetchall():
        base = coltype % 256
        tipo = TIPOS.get(base, f"tipo{base}")
        es_fecha = " <<< CANDIDATO FECHA" if base in (7, 10) else ""
        columnas.append(nombre)
        print(f"    {nombre:20} {tipo:10}{es_fecha}")
except Exception as e:
    print(f"    AVISO: no se pudo leer syscolumns ({e})")

# ── 2. Fila de ejemplo (FIRST 1) para ver valores reales ────────────────────
print("\n[2] Una fila de ejemplo de sbas (valores reales):")
try:
    cur.execute(f"SELECT FIRST 1 * FROM sbas WHERE firma = {FIRMA}")
    row = cur.fetchone()
    if row:
        cols = [d[0] for d in cur.description]
        for nombre, valor in zip(cols, row):
            print(f"    {nombre:20} = {valor!r}")
    else:
        print("    (sin filas para firma=1)")
except Exception as e:
    print(f"    AVISO: no se pudo leer fila de ejemplo ({e})")

print("\n" + "=" * 68)
print("QUÉ BUSCAR:")
print("  El campo marcado '<<< CANDIDATO FECHA' (tipo DATE/DATETIME) es el que")
print("  hay que usar en sincronizar_informix.py para contar días con venta.")
print("  Confirmá con la fila de ejemplo que tenga una fecha de factura real.")
print("=" * 68)

cn.close()
