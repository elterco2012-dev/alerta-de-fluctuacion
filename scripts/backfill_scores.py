"""
backfill_scores.py
------------------
Recalcula el score "como hubiera sido" para cada uno de los últimos N meses
y guarda los resultados en la tabla score_historico de wurth.db.

Luego la pantalla pages/Precision.py cruza esto con los egresados reales
para medir si el sistema los hubiera detectado antes de que se fueran.

Lee de SQLite (no usa ODBC), así que corre con el Python 64-bit:
    "C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" scripts\\backfill_scores.py

Requiere pandas instalado en ese Python:
    "...\\Python312\\python.exe" -m pip install pandas

Puede tardar varios minutos (1 llamada a calcular_scores por mes).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import sqlite3
import pandas as pd
import json
from datetime import date
import calendar

from score_engine import calcular_scores, get_connection, DB_PATH

MESES_ATRAS = 18   # cuántos meses hacia atrás calcular


def mes_anterior(anio, mes, n=1):
    """Devuelve (anio, mes) retrocediendo n meses."""
    for _ in range(n):
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1
    return anio, mes


def crear_tabla_score_historico(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS score_historico (
            periodo        TEXT NOT NULL,
            id_vendedor    INTEGER NOT NULL,
            score          REAL NOT NULL,
            nivel          TEXT NOT NULL,
            señales        TEXT,           -- JSON list
            pct_plan_3m    REAL,
            tendencia_plan REAL,
            dias_cero_prom REAL,
            pct_cobranza   REAL,
            meses_activo   INTEGER,
            PRIMARY KEY (periodo, id_vendedor)
        )
    """)
    con.commit()


def main():
    hoy = date.today()
    anio_base, mes_base = hoy.year, hoy.month

    con_local = sqlite3.connect(DB_PATH)
    crear_tabla_score_historico(con_local)

    # Períodos a calcular (mes actual - 1 hacia atrás N meses)
    periodos = []
    a, m = mes_anterior(anio_base, mes_base, 1)  # mes anterior al actual
    for _ in range(MESES_ATRAS):
        periodos.append((a, m))
        a, m = mes_anterior(a, m, 1)

    print(f"Calculando backfill para {len(periodos)} períodos...")
    print(f"Desde {periodos[-1][0]}-{periodos[-1][1]:02d} hasta {periodos[0][0]}-{periodos[0][1]:02d}\n")

    total_filas = 0

    for anio, mes in periodos:
        periodo_str = f"{anio}-{mes:02d}"
        print(f"  Procesando {periodo_str}...", end=" ", flush=True)

        try:
            df = calcular_scores(meses_tendencia=3, hasta_anio=anio, hasta_mes=mes)
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        if df.empty:
            print("sin datos")
            continue

        # Insertar o reemplazar en score_historico
        filas = []
        for _, r in df.iterrows():
            filas.append((
                periodo_str,
                int(r["id_vendedor"]),
                float(r["score"]),
                r["nivel_riesgo"],
                json.dumps(r["señales_activas"], ensure_ascii=False),
                float(r["pct_plan_3m"])    if pd.notna(r.get("pct_plan_3m"))    else None,
                float(r["tendencia_plan"]) if pd.notna(r.get("tendencia_plan")) else None,
                float(r["dias_cero_promedio"]) if pd.notna(r.get("dias_cero_promedio")) else None,
                float(r["pct_cobranza"])   if pd.notna(r.get("pct_cobranza"))   else None,
                int(r["meses_activo"])     if pd.notna(r.get("meses_activo"))    else None,
            ))

        con_local.executemany("""
            INSERT OR REPLACE INTO score_historico
            (periodo, id_vendedor, score, nivel, señales,
             pct_plan_3m, tendencia_plan, dias_cero_prom, pct_cobranza, meses_activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, filas)
        con_local.commit()

        total_filas += len(filas)
        print(f"{len(df)} vendedores guardados")

    con_local.close()
    print(f"\nListo. {total_filas} registros en score_historico.")
    print("Ahora abrí la pantalla 'Precisión del modelo' en el dashboard.")


if __name__ == "__main__":
    main()
