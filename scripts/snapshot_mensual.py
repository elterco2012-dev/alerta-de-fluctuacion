"""
snapshot_mensual.py
-------------------
Guarda el score del mes anterior (completo) en score_historico de wurth.db.
Ejecutar a principios de cada mes, idealmente el mismo día que sync_y_alertas.bat.

Ejecutar con Python 32-bit (el que tiene ODBC):
    C:\\...\\Python312-32\\python.exe scripts\\snapshot_mensual.py

Tiempo estimado: 15-30 segundos (una sola llamada a calcular_scores).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import sqlite3
import pandas as pd
import json
from datetime import date

from score_engine import calcular_scores, DB_PATH


def crear_tabla_score_historico(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS score_historico (
            periodo        TEXT NOT NULL,
            id_vendedor    INTEGER NOT NULL,
            score          REAL NOT NULL,
            nivel          TEXT NOT NULL,
            señales        TEXT,
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

    # Snapshot del mes anterior completo (el mes actual puede tener datos parciales)
    mes  = hoy.month - 1 or 12
    anio = hoy.year if hoy.month > 1 else hoy.year - 1

    periodo_str = f"{anio}-{mes:02d}"
    print(f"Generando snapshot de scores para período {periodo_str}...")

    try:
        df = calcular_scores(meses_tendencia=3, hasta_anio=anio, hasta_mes=mes)
    except Exception as e:
        print(f"ERROR al calcular scores: {e}")
        sys.exit(1)

    if df.empty:
        print("Sin datos de ventas para este período. Revisá que sincronizar_informix.py ya corrió.")
        sys.exit(0)

    con = sqlite3.connect(DB_PATH)
    crear_tabla_score_historico(con)

    filas = []
    for _, r in df.iterrows():
        filas.append((
            periodo_str,
            int(r["id_vendedor"]),
            float(r["score"]),
            r["nivel_riesgo"],
            json.dumps(r["señales_activas"], ensure_ascii=False),
            float(r["pct_plan_3m"])        if pd.notna(r.get("pct_plan_3m"))        else None,
            float(r["tendencia_plan"])     if pd.notna(r.get("tendencia_plan"))     else None,
            float(r["dias_cero_promedio"]) if pd.notna(r.get("dias_cero_promedio")) else None,
            float(r["pct_cobranza"])       if pd.notna(r.get("pct_cobranza"))       else None,
            int(r["meses_activo"])         if pd.notna(r.get("meses_activo"))        else None,
        ))

    con.executemany("""
        INSERT OR REPLACE INTO score_historico
        (periodo, id_vendedor, score, nivel, señales,
         pct_plan_3m, tendencia_plan, dias_cero_prom, pct_cobranza, meses_activo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, filas)
    con.commit()

    # Contar cuántos períodos hay acumulados
    n_periodos = con.execute("SELECT COUNT(DISTINCT periodo) FROM score_historico").fetchone()[0]
    con.close()

    print(f"Listo. {len(df)} vendedores guardados para {periodo_str}.")
    print(f"score_historico acumula {n_periodos} período(s) en total.")


if __name__ == "__main__":
    main()
