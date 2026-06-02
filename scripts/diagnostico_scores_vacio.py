import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
con = sqlite3.connect(DB_PATH)
cur = con.cursor()

def q1(sql, params=()):
    return cur.execute(sql, params).fetchone()[0]

print("=" * 60)
print("DIAGNOSTICO: por que scores = 0 vendedores")
print("=" * 60)

print("\n--- Conteos base ---")
print(f"  vendedores total:        {q1('SELECT COUNT(*) FROM vendedores')}")
print(f"  vendedores activo=1:     {q1('SELECT COUNT(*) FROM vendedores WHERE activo=1')}")
print(f"  grupos:                  {q1('SELECT COUNT(*) FROM grupos')}")
print(f"  ventas_mensual filas:    {q1('SELECT COUNT(*) FROM ventas_mensual')}")

print("\n--- Paso 1: activos con JOIN a grupos (lo que usa el score engine) ---")
n_join = q1("""
    SELECT COUNT(*)
    FROM vendedores v
    JOIN grupos g ON v.id_grupo = g.id_grupo
    WHERE v.activo = 1
      AND (v.fecha_egreso IS NULL OR v.fecha_egreso != v.fecha_ingreso)
      AND v.id_vendedor != 9800
      AND v.nombre NOT IN (
          SELECT DISTINCT supervisor FROM vendedores
          WHERE supervisor IS NOT NULL AND supervisor != ''
      )
""")
print(f"  Activos que pasan el JOIN + filtros: {n_join}")

print("\n--- Diagnostico del JOIN ---")
print(f"  Activos con id_grupo NULL:           {q1('SELECT COUNT(*) FROM vendedores WHERE activo=1 AND id_grupo IS NULL')}")
n_sin_grupo = q1("""
    SELECT COUNT(*) FROM vendedores v
    WHERE v.activo=1 AND v.id_grupo NOT IN (SELECT id_grupo FROM grupos)
""")
print(f"  Activos con id_grupo NO en grupos:   {n_sin_grupo}")
n_excluidos_sup = q1("""
    SELECT COUNT(*) FROM vendedores v
    WHERE v.activo=1
      AND v.nombre IN (SELECT DISTINCT supervisor FROM vendedores
                       WHERE supervisor IS NOT NULL AND supervisor != '')
""")
print(f"  Activos excluidos por ser supervisor: {n_excluidos_sup}")

print("\n--- Paso 2: activos que tienen ventas ---")
n_con_ventas = q1("""
    SELECT COUNT(DISTINCT v.id_vendedor)
    FROM vendedores v
    JOIN ventas_mensual vm ON v.id_vendedor = vm.id_vendedor
    WHERE v.activo = 1
""")
print(f"  Activos con al menos 1 fila en ventas_mensual: {n_con_ventas}")

print("\n--- Muestra: id_grupo de los activos vs grupos existentes ---")
print("  Primeros 10 id_grupo de activos:")
for r in cur.execute("SELECT id_vendedor, id_grupo, nombre_grupo FROM vendedores WHERE activo=1 LIMIT 10"):
    en_grupos = q1("SELECT COUNT(*) FROM grupos WHERE id_grupo=?", (r[1],))
    print(f"    vendedor={r[0]}  id_grupo={r[1]}  nombre_grupo={r[2]}  -> en tabla grupos: {'SI' if en_grupos else 'NO'}")

print("\n  Primeros 10 id_grupo en tabla grupos:")
for r in cur.execute("SELECT id_grupo, nombre_grupo FROM grupos LIMIT 10"):
    print(f"    id_grupo={r[0]}  {r[1]}")

print("\n--- Muestra: ids en ventas_mensual vs activos ---")
ids_ventas = [r[0] for r in cur.execute("SELECT DISTINCT id_vendedor FROM ventas_mensual LIMIT 10")]
print(f"  Primeros 10 ids en ventas_mensual: {ids_ventas}")
ids_activos = [r[0] for r in cur.execute("SELECT id_vendedor FROM vendedores WHERE activo=1 LIMIT 10")]
print(f"  Primeros 10 ids activos:           {ids_activos}")

con.close()
print("\nFin del diagnostico.")
