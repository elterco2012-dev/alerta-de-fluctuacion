import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
con = sqlite3.connect(DB_PATH)

print("=== Vendedores activos en Grupo 212 ===")
rows = con.execute("""
    SELECT id_vendedor, nombre, fecha_ingreso, fecha_egreso
    FROM vendedores
    WHERE nombre_grupo = 'Grupo 212' AND activo = 1
""").fetchall()

if rows:
    for r in rows:
        print(f"  ID: {r[0]}  Nombre: {r[1]}  Ingreso: {r[2]}  Egreso: {r[3]}")
else:
    print("  (ninguno — el grupo ya no tiene activos)")

print()
print("=== Todos los vendedores en Grupo 212 (activos + bajas) ===")
rows2 = con.execute("""
    SELECT id_vendedor, nombre, activo, fecha_ingreso, fecha_egreso
    FROM vendedores
    WHERE nombre_grupo = 'Grupo 212'
    ORDER BY activo DESC
""").fetchall()
for r in rows2:
    estado = "ACTIVO" if r[2] == 1 else "baja"
    print(f"  [{estado}] ID: {r[0]}  Nombre: {r[1]}  Ingreso: {r[3]}  Egreso: {r[4]}")

con.close()
