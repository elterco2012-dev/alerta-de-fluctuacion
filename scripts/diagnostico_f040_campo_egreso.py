"""
diagnostico_f040_campo_egreso.py
---------------------------------
Busca en f040 de Informix cual es el campo real donde esta almacenada
la fecha de egreso del vendedor 1407 (que austrdat tiene en NULL pero
la pantalla muestra 04.08.2017).

Requiere Python 32 bits (ejemplo de ruta):
  python312-32 scripts/diagnostico_f040_campo_egreso.py
"""

import sys
try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no instalado.")
    sys.exit(1)

DSN_INFORMIX = "MSPA"
ID_VENDEDOR  = 1407

print(f"Conectando a Informix ({DSN_INFORMIX})...", end=" ", flush=True)
try:
    con = pyodbc.connect(f"DSN={DSN_INFORMIX}", timeout=15)
    cur = con.cursor()
    print("OK")
except Exception as e:
    print(f"FALLÓ: {e}")
    sys.exit(1)

# 1. Mostrar TODOS los valores de f040 para vendedor 1407
print(f"\n=== Todos los campos de f040 para vendedor {ID_VENDEDOR} ===")
try:
    cur.execute(f"SELECT * FROM f040 WHERE vertr = {ID_VENDEDOR}")
    row = cur.fetchone()
    if row:
        cols = [desc[0] for desc in cur.description]
        for col, val in zip(cols, row):
            if val is not None and str(val).strip() not in ("", "0", "0.0", "0.00"):
                print(f"  {col:<20} = {val!r}")
        print("\n--- Campos con None o vacíos ---")
        for col, val in zip(cols, row):
            if val is None or str(val).strip() in ("", "0", "0.0", "0.00"):
                print(f"  {col:<20} = {val!r}")
    else:
        print(f"  No encontrado en f040")
except Exception as e:
    print(f"  Error: {e}")

# 2. Buscar columnas en f040 que contengan "austr", "egre", "egr", "salida", "baja", "dat"
print(f"\n=== Columnas de f040 que contienen 'aus', 'egr', 'dat', 'end', 'exit' ===")
try:
    cur.execute(f"SELECT * FROM f040 WHERE vertr = {ID_VENDEDOR}")
    cols = [desc[0] for desc in cur.description]
    keywords = ("aus", "egr", "dat", "end", "exit", "sal", "baj", "beel", "term", "ceas")
    for col in cols:
        if any(kw in col.lower() for kw in keywords):
            print(f"  {col}")
except Exception as e:
    print(f"  Error: {e}")

# 3. Buscar en tablas relacionadas con f040 que puedan tener la fecha
print(f"\n=== Intentando tablas relacionadas ===")
for tabla in ("f040h", "f040a", "f040e", "vertr_hist", "vertr_egre"):
    try:
        cur.execute(f"SELECT FIRST 1 * FROM {tabla} WHERE vertr = {ID_VENDEDOR}")
        row = cur.fetchone()
        if row:
            cols = [desc[0] for desc in cur.description]
            print(f"\n  Tabla {tabla}:")
            for col, val in zip(cols, row):
                print(f"    {col:<20} = {val!r}")
        else:
            print(f"  {tabla}: existe pero sin datos para vendedor {ID_VENDEDOR}")
    except Exception:
        pass  # tabla no existe, ignorar

con.close()
print("\nDiagnóstico completo.")
