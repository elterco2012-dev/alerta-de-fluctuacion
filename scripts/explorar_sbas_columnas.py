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
from datetime import date

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no instalado en este Python.")
    sys.exit(1)

DSN_INFORMIX = "MSPA"
FIRMA        = 1
anio_desde   = date.today().year  # año en curso, para traer una fila reciente

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

# ── Columnas + fila de ejemplo con un SELECT * normal (sin FIRST ni catálogo) ─
# Usamos exactamente la forma que el sync ya prueba que funciona: un SELECT
# sobre sbas con filtro firma. Leemos UNA fila con fetchone() (sin FIRST, que
# en este Informix daba -201) y sacamos los nombres de columna de
# cursor.description. Así vemos TODAS las columnas y sus valores reales.
print("\n[1] Columnas reales de sbas + fila de ejemplo:")
try:
    cur.execute(f"SELECT * FROM sbas WHERE firma = {FIRMA} AND bujahr >= {anio_desde}")
    row = cur.fetchone()
    cols = [d[0] for d in cur.description]
    if row is None:
        print("    (sin filas para firma=1 en el año en curso; muestro solo nombres)")
        for nombre in cols:
            print(f"    {nombre}")
    else:
        print(f"    {'COLUMNA':22} {'TIPO PYTHON':14} VALOR EJEMPLO")
        print("    " + "-" * 60)
        for nombre, valor in zip(cols, row):
            tipo = type(valor).__name__
            marca = ""
            # date/datetime de Python → candidato a campo de fecha por día
            if tipo in ("date", "datetime"):
                marca = "   <<< CANDIDATO FECHA"
            print(f"    {nombre:22} {tipo:14} {valor!r}{marca}")
except Exception as e:
    print(f"    AVISO: no se pudo leer sbas ({e})")

print("\n" + "=" * 68)
print("QUÉ BUSCAR:")
print("  - Si aparece alguna columna tipo date/datetime (marcada CANDIDATO),")
print("    ESE es el campo de fecha por día que hay que usar para días con venta.")
print("  - Si NO hay ninguna columna de fecha (solo bujahr/bumonat = año/mes),")
print("    entonces sbas está agregada por mes y NO sirve para contar días sin")
print("    venta. Habría que buscar otra tabla de facturas con fecha diaria.")
print("=" * 68)

cn.close()
