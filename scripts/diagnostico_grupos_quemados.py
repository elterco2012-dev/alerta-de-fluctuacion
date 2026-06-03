"""
scripts/diagnostico_grupos_quemados.py
--------------------------------------
La hipótesis central del proyecto: los "grupos quemados" (alta rotación
histórica) producen vendedores que duran menos. La señal "grupo_quemado" del
score se enciende si riesgo_base del grupo > 0.60, pero en la pantalla de
Aprendizaje NUNCA se enciende (0% en todos). Este script averigua por qué y con
qué umbral la señal sería útil.

Hace dos cosas (solo LECTURA sobre data/wurth.db):
  1. Muestra la distribución real de riesgo_base entre los grupos.
  2. Para varios umbrales, compara qué % de EGRESADOS vs ACTIVOS pertenece a un
     grupo por encima del umbral, y calcula el lift (egresados/activos). Lift
     alto = estar en un grupo quemado predice fuga = la hipótesis se sostiene y
     conviene bajar el umbral a ese valor.

riesgo_base = % de vendedores del grupo que se fueron en < 6 meses (lo calcula
sincronizar_informix.py). Nota honesta: los propios egresados alimentan el
riesgo_base de su grupo, así que el lift tiene algo de optimismo; aún así sirve
para ver si la señal estructural discrimina y a qué umbral.

Corre con cualquier Python (no usa pandas):
    "C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" scripts\\diagnostico_grupos_quemados.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    print("=" * 68)
    print("DIAGNÓSTICO — Grupos quemados (hipótesis central del proyecto)")
    print("=" * 68)

    # ── 1. Distribución de riesgo_base ───────────────────────────────────────
    cur.execute("SELECT riesgo_base FROM grupos")
    valores = [r[0] for r in cur.fetchall() if r[0] is not None]
    n = len(valores)
    print(f"\n[1] Distribución de riesgo_base ({n} grupos):")
    if n:
        valores.sort()
        def pct(p):
            return valores[min(n - 1, int(p * n))]
        print(f"    mínimo   : {min(valores):.2f}")
        print(f"    percentil 25: {pct(0.25):.2f}")
        print(f"    mediana  : {pct(0.50):.2f}")
        print(f"    percentil 75: {pct(0.75):.2f}")
        print(f"    máximo   : {max(valores):.2f}")
        print(f"    promedio : {sum(valores)/n:.2f}")
        # Buckets
        print("\n    Grupos por rango de riesgo_base:")
        rangos = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)]
        for lo, hi in rangos:
            c = sum(1 for v in valores if lo <= v < hi)
            barra = "█" * c
            print(f"      {lo:.1f}-{hi:.1f}: {c:>3}  {barra}")

    # ── 2. Lift por umbral: egresados vs activos en grupos quemados ──────────
    # Egresados de los últimos 18 meses vs activos. Para cada uno, ¿su grupo
    # supera el umbral? Comparamos la proporción entre los dos colectivos.
    cur.execute("""
        SELECT v.activo, v.fecha_egreso, g.riesgo_base
        FROM vendedores v
        JOIN grupos g ON v.id_grupo = g.id_grupo
        WHERE v.id_vendedor != 9800
          AND v.fecha_ingreso IS NOT NULL
          AND (v.fecha_egreso IS NULL OR v.fecha_egreso != v.fecha_ingreso)
          AND g.riesgo_base IS NOT NULL
    """)
    egres_rb, activ_rb = [], []
    for activo, fegr, rb in cur.fetchall():
        if activo == 0 and fegr:
            egres_rb.append(rb)
        elif activo == 1:
            activ_rb.append(rb)

    print(f"\n[2] ¿Estar en un grupo quemado predice fuga?")
    print(f"    Egresados: {len(egres_rb)}   Activos: {len(activ_rb)}")
    print(f"\n    {'umbral':>7} {'% egresados':>12} {'% activos':>11} {'lift':>7}  lectura")
    print("    " + "-" * 56)
    for umbral in (0.30, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70):
        pe = sum(1 for v in egres_rb if v > umbral) / len(egres_rb) * 100 if egres_rb else 0
        pa = sum(1 for v in activ_rb if v > umbral) / len(activ_rb) * 100 if activ_rb else 0
        lift = pe / pa if pa > 0 else 0
        if pe < 5:
            lectura = "casi no aplica (muy pocos)"
        elif lift >= 1.5:
            lectura = "✅ discrimina — umbral útil"
        elif lift >= 1.2:
            lectura = "🟡 discrimina débil"
        else:
            lectura = "⬜ no discrimina"
        marca = "  <- actual" if abs(umbral - 0.60) < 0.001 else ""
        print(f"    {umbral:>7.2f} {pe:>11.1f}% {pa:>10.1f}% {lift:>6.1f}x  {lectura}{marca}")

    print("\n" + "=" * 68)
    print("CÓMO DECIDIR EL UMBRAL:")
    print("  Buscá el umbral más alto que todavía tenga lift >= 1.5 y donde un")
    print("  porcentaje razonable de egresados quede marcado (no <5%). Ese es el")
    print("  punto donde 'grupo quemado' se vuelve una señal útil sin marcar a")
    print("  medio mundo. Si NINGÚN umbral da lift >= 1.2, la hipótesis no se")
    print("  sostiene con estos datos y la señal debería pesar poco o salir.")
    print("=" * 68)

    con.close()


if __name__ == "__main__":
    main()
