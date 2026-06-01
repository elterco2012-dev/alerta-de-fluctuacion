"""
fix_vendedor_1407.py
---------------------
Marca al vendedor 1407 (Carlos Rodolfo Alegre) como inactivo con la
fecha de egreso real confirmada en Informix (04.08.2017 = 2017-08-04).

NOTA: Este fix es necesario porque el campo austrdat en f040 está en NULL
para este vendedor, a pesar de que la pantalla de Informix muestra fecha
de egreso. El campo que usa la pantalla es distinto de austrdat.

Ejecutar una sola vez:
  python scripts\fix_vendedor_1407.py
"""

import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
FECHA_EGRESO = "2017-08-04"
ID_VENDEDOR  = 1407

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("SELECT id_vendedor, nombre, activo, fecha_egreso FROM vendedores WHERE id_vendedor = ?", (ID_VENDEDOR,))
row = cur.fetchone()
if not row:
    print(f"ERROR: vendedor {ID_VENDEDOR} no encontrado en SQLite.")
    con.close()
    exit(1)

print(f"Antes: {row}")

cur.execute("""
    UPDATE vendedores
    SET activo = 0, fecha_egreso = ?
    WHERE id_vendedor = ?
""", (FECHA_EGRESO, ID_VENDEDOR))
con.commit()

cur.execute("SELECT id_vendedor, nombre, activo, fecha_egreso FROM vendedores WHERE id_vendedor = ?", (ID_VENDEDOR,))
row = cur.fetchone()
print(f"Después: {row}")
print(f"\nVendedor {ID_VENDEDOR} marcado como inactivo con egreso {FECHA_EGRESO}.")
print("\nIMPORTANTE: Este cambio se revertirá si corrés sincronizar_informix.py")
print("porque f040.austrdat sigue en NULL en Informix.")
print("Para una solución permanente: corregir austrdat en Informix para este vendedor,")
print("o buscar el campo correcto de fecha egreso (ver diagnostico_f040_campo_egreso.py).")
con.close()
