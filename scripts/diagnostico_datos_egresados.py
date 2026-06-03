"""
scripts/diagnostico_datos_egresados.py
---------------------------------------
¿Por qué la pantalla de Aprendizaje muestra señales en 0% para los que se fueron?

Compara la COMPLETITUD de datos entre dos grupos:
  - ACTIVOS          (activo = 1)
  - EGRESADOS 18m    (activo = 0, fecha_egreso en los últimos 18 meses)

Para cada tabla y columna clave reporta qué % de cada grupo tiene el dato.
Si los egresados tienen mucho menos que los activos, la comparación de esa
señal en Aprendizaje es inválida (parece "ausente en los que se fueron" solo
porque falta el dato, no porque sea una conducta real).

Solo LECTURA sobre data/wurth.db (SQLite local). No toca ninguna base externa.
Se corre con Python 64-bit (no necesita ODBC):

    python scripts\\diagnostico_datos_egresados.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')


def _pct(n, total):
    return f"{n/total*100:5.1f}%" if total else "  n/a"


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # ── Definir los dos grupos ──────────────────────────────────────────────
    cur.execute("""
        SELECT id_vendedor FROM vendedores
        WHERE activo = 1 AND id_vendedor != 9800
    """)
    activos = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT id_vendedor FROM vendedores
        WHERE activo = 0 AND fecha_egreso IS NOT NULL
          AND fecha_egreso >= date('now', '-18 months')
          AND id_vendedor != 9800
    """)
    egresados = [r[0] for r in cur.fetchall()]

    print("=" * 70)
    print("DIAGNÓSTICO DE COMPLETITUD DE DATOS — Activos vs Egresados (18m)")
    print("=" * 70)
    print(f"  Activos:        {len(activos)}")
    print(f"  Egresados 18m:  {len(egresados)}")
    print()

    if not activos or not egresados:
        print("No hay suficientes vendedores en algún grupo. Abortando.")
        con.close()
        return

    def cobertura(grupo, sql_template):
        """% del grupo que cumple la condición (tiene al menos una fila)."""
        if not grupo:
            return 0, 0
        marks = ",".join("?" * len(grupo))
        cur.execute(sql_template.format(marks=marks), grupo)
        n = cur.fetchone()[0]
        return n, len(grupo)

    # ── Tablas que alimentan cada grupo de señales ──────────────────────────
    tablas = [
        ("ventas_mensual",        "ventas (plan, cobranza, días cero, cartera)"),
        ("actividad_mensual",     "actividad Reactor (llamadas/visitas)"),
        ("ausencias_mensual",     "ausencias tempranas"),
        ("balanza_clientes",      "balanza negativa + ticket cayendo"),
        ("acompanamiento_mensual","acompañamiento del supervisor"),
    ]

    print(f"{'TABLA / FUENTE':48} {'ACTIVOS':>10} {'EGRESADOS':>10}")
    print("-" * 70)
    for tabla, desc in tablas:
        # ¿La tabla existe?
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
        if not cur.fetchone():
            print(f"{desc:48} {'(tabla no existe)':>21}")
            continue
        sql = f"SELECT COUNT(DISTINCT id_vendedor) FROM {tabla} WHERE id_vendedor IN ({{marks}})"
        na, ta = cobertura(activos, sql)
        ne, te = cobertura(egresados, sql)
        print(f"{desc:48} {_pct(na,ta):>10} {_pct(ne,te):>10}")

    # ── Columnas clave dentro de ventas_mensual ─────────────────────────────
    print()
    print("COLUMNAS CLAVE en ventas_mensual (con dato NO nulo y > 0):")
    print("-" * 70)
    columnas = [
        ("dias_venta_cero",   "días sin venta (señal días cero)"),
        ("clientes_activos",  "cartera activa (señal cartera baja)"),
        ("total_clientes",    "total cartera (denominador de cartera)"),
        ("pct_cobranza",      "cobranza (señal cobranza baja)"),
        ("pct_plan",          "% plan (señales de plan)"),
    ]
    for col, desc in columnas:
        # ¿La columna existe?
        cur.execute("PRAGMA table_info(ventas_mensual)")
        cols = [r[1] for r in cur.fetchall()]
        if col not in cols:
            print(f"{desc:48} {'(columna no existe)':>21}")
            continue
        sql = (f"SELECT COUNT(DISTINCT id_vendedor) FROM ventas_mensual "
               f"WHERE id_vendedor IN ({{marks}}) AND {col} IS NOT NULL AND {col} != 0")
        na, ta = cobertura(activos, sql)
        ne, te = cobertura(egresados, sql)
        print(f"{desc:48} {_pct(na,ta):>10} {_pct(ne,te):>10}")

    print()
    print("=" * 70)
    print("CÓMO LEER ESTO:")
    print("  Si una fila tiene ACTIVOS alto y EGRESADOS bajo → a los que se")
    print("  fueron les falta ese dato. La señal correspondiente aparece en 0%")
    print("  en Aprendizaje por falta de dato, NO porque sea una conducta real.")
    print()
    print("  Para arreglarlo hay que extender el sync de Informix/Reactor para")
    print("  que traiga esas tablas también para los egresados (solo lectura).")
    print("=" * 70)

    con.close()


if __name__ == "__main__":
    main()
