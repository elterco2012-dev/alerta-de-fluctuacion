import sqlite3, os
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
con = sqlite3.connect(DB_PATH)
print("=== Estado actual Grupo 212 ===")
for r in con.execute("SELECT id_vendedor, nombre, activo, fecha_egreso FROM vendedores WHERE nombre_grupo='Grupo 212' ORDER BY activo DESC").fetchall():
    print(f"  [{('ACTIVO' if r[2]==1 else 'baja')}] {r[0]} {r[1]}  egreso={r[3]}")
con.close()
