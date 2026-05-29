"""
explorar_reactor_nuevas.py
--------------------------
Explora las tablas nuevas de Reactor CRM que alimentarán las nuevas señales:
  - supervisor_schedule   (planificaciones del supervisor)
  - supervisor_visit      (visitas reales del supervisor)
  - absence               (ausencias de empleados)
  - employee              (empleados, vincula con user)
  - reason                (motivos de ausencia)
  - visits_route_calculation  (distancia recorrida por vendedor/día)

Ejecutar con Python 32 bits:
    C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe scripts\\explorar_reactor_nuevas.py

Genera: reactor_nuevas_estructura.txt
"""

import pyodbc, sys, datetime

DSN    = "Wurth Reactor Produccion"
OUTPUT = "reactor_nuevas_estructura.txt"

TABLAS_OBJETIVO = [
    "supervisor_schedule",
    "supervisor_visit",
    "absence",
    "employee",
    "reason",
    "visits_route_calculation",
]

print(f"Conectando a '{DSN}'...", end=" ", flush=True)
try:
    con = pyodbc.connect(f"DSN={DSN}", timeout=10)
    print("OK")
except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)

cur = con.cursor()
lines = []
HOY = datetime.date.today()
HACE_3M = HOY.replace(month=HOY.month - 3 if HOY.month > 3 else HOY.month + 9,
                       year=HOY.year if HOY.month > 3 else HOY.year - 1)

for tabla in TABLAS_OBJETIVO:
    lines.append(f"\n{'='*60}")
    lines.append(f"TABLA: {tabla}")
    lines.append('='*60)
    try:
        cur.execute(f"SELECT * FROM `{tabla}` WHERE 1=0")
        cols = [(d[0], d[1]) for d in cur.description]
        lines.append(f"Columnas ({len(cols)}):")
        for nombre, tipo in cols:
            lines.append(f"  {nombre:40s} {str(tipo)}")

        cur.execute(f"SELECT COUNT(*) FROM `{tabla}`")
        total = cur.fetchone()[0]
        lines.append(f"\nTotal filas: {total:,}")

        # Muestra 3 filas recientes
        col_names = [c[0] for c in cols]
        # Buscar columna de fecha para ordenar
        fecha_col = None
        for fc in ["event_date", "created", "start_date", "visit_day", "updated_at", "created_at"]:
            if fc in col_names:
                fecha_col = fc
                break

        if fecha_col:
            cur.execute(f"SELECT * FROM `{tabla}` ORDER BY `{fecha_col}` DESC LIMIT 3")
        else:
            cur.execute(f"SELECT * FROM `{tabla}` LIMIT 3")

        rows = cur.fetchall()
        lines.append(f"\nMuestra (3 filas más recientes por {fecha_col or 'orden natural'}):")
        for r in rows:
            d = dict(zip(col_names, list(r)))
            lines.append(f"  {d}")

        # Stats adicionales por tabla
        if tabla == "supervisor_schedule":
            lines.append("\n--- Stats supervisor_schedule ---")
            try:
                cur.execute(f"""
                    SELECT COUNT(DISTINCT user_seller) as vendedores_planificados,
                           MIN(event_date), MAX(event_date),
                           COUNT(*) as total_planificaciones
                    FROM `{tabla}`
                    WHERE event_date >= ?
                """, str(HACE_3M))
                r = cur.fetchone()
                lines.append(f"  Últimos 3 meses: {r[3]:,} planificaciones, {r[0]} vendedores, rango {r[1]} → {r[2]}")
            except Exception as e:
                lines.append(f"  (error stats: {e})")

        elif tabla == "supervisor_visit":
            lines.append("\n--- Stats supervisor_visit ---")
            try:
                cur.execute(f"""
                    SELECT COUNT(DISTINCT user_seller) as vendedores,
                           MIN(created), MAX(created),
                           COUNT(*) as total_visitas
                    FROM `{tabla}`
                    WHERE created >= ?
                """, str(HACE_3M))
                r = cur.fetchone()
                lines.append(f"  Últimos 3 meses: {r[3]:,} visitas, {r[0]} vendedores, rango {r[1]} → {r[2]}")
            except Exception as e:
                lines.append(f"  (error stats: {e})")

        elif tabla == "absence":
            lines.append("\n--- Stats absence ---")
            try:
                cur.execute(f"""
                    SELECT COUNT(DISTINCT id_employee) as empleados,
                           MIN(start_date), MAX(start_date),
                           COUNT(*) as total_ausencias
                    FROM `{tabla}`
                    WHERE start_date >= ?
                """, str(HACE_3M))
                r = cur.fetchone()
                lines.append(f"  Últimos 3 meses: {r[3]:,} ausencias, {r[0]} empleados, rango {r[1]} → {r[2]}")
            except Exception as e:
                lines.append(f"  (error stats: {e})")

        elif tabla == "reason":
            lines.append("\n--- Todos los motivos ---")
            try:
                cur.execute(f"SELECT * FROM `{tabla}` ORDER BY id LIMIT 50")
                rows_r = cur.fetchall()
                col_r = [c[0] for c in cols]
                for rr in rows_r:
                    lines.append(f"  {dict(zip(col_r, list(rr)))}")
            except Exception as e:
                lines.append(f"  (error: {e})")

        elif tabla == "visits_route_calculation":
            lines.append("\n--- Stats visits_route_calculation ---")
            try:
                cur.execute(f"""
                    SELECT COUNT(DISTINCT id_user) as vendedores,
                           MIN(visit_day), MAX(visit_day),
                           ROUND(AVG(distance)/1000, 1) as km_promedio,
                           COUNT(*) as total_dias
                    FROM `{tabla}`
                    WHERE visit_day >= ?
                """, str(HACE_3M))
                r = cur.fetchone()
                lines.append(f"  Últimos 3 meses: {r[4]:,} registros, {r[0]} vendedores")
                lines.append(f"  Rango fechas: {r[1]} → {r[2]}")
                lines.append(f"  Distancia promedio/día: {r[3]} km")
            except Exception as e:
                lines.append(f"  (error stats: {e})")

        elif tabla == "employee":
            lines.append("\n--- Sample employee + user join ---")
            try:
                cur.execute(f"""
                    SELECT e.id, e.id_user, u.username, u.first_name, u.last_name
                    FROM employee e
                    JOIN `user` u ON e.id_user = u.id
                    WHERE CAST(u.username AS UNSIGNED) > 0
                    LIMIT 5
                """)
                rows_e = cur.fetchall()
                for re in rows_e:
                    lines.append(f"  employee.id={re[0]}, id_user={re[1]}, username={re[2]}, nombre={re[3]} {re[4]}")
            except Exception as e:
                lines.append(f"  (error join: {e})")

    except Exception as e:
        lines.append(f"  ERROR accediendo tabla: {e}")

con.close()

output = "\n".join(lines)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(output)

print(f"\nListo. Guardado en: {OUTPUT}")
print("Pegá el contenido acá para continuar con el ETL.")
