"""
diagnostico_valores.py
----------------------
Muestra la DISTRIBUCIÓN de los valores brutos de las 4 señales que más
disparan entre los activos (días venta cero, % plan promedio, pendiente
plan, balanza clientes). Sirve para elegir umbrales que discriminen mejor.

Correr ANTES de ajustar umbrales en score_engine.py.
    python scripts\\diagnostico_valores.py
"""

import os
import sys
import sqlite3
import numpy as np
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

con = sqlite3.connect(DB_PATH)

vendedores = pd.read_sql("""
    SELECT v.id_vendedor
    FROM vendedores v
    WHERE v.activo = 1
      AND (v.fecha_egreso IS NULL OR v.fecha_egreso != v.fecha_ingreso)
      AND v.id_vendedor != 9800
      AND v.nombre NOT IN (
          SELECT DISTINCT supervisor FROM vendedores
          WHERE supervisor IS NOT NULL AND supervisor != ''
      )
""", con)

ventas = pd.read_sql("""
    SELECT vm.*
    FROM ventas_mensual vm
    JOIN vendedores v ON vm.id_vendedor = v.id_vendedor
    WHERE v.activo = 1
    ORDER BY vm.id_vendedor, vm.anio DESC, vm.mes DESC
""", con)

try:
    balanza = pd.read_sql("""
        SELECT bc.*
        FROM balanza_clientes bc
        JOIN vendedores v ON bc.id_vendedor = v.id_vendedor
        WHERE v.activo = 1
        ORDER BY bc.id_vendedor, bc.anio DESC, bc.mes DESC
    """, con)
except Exception:
    balanza = pd.DataFrame()

con.close()

MESES = 3

dias_cero_vals   = []
pct_plan_vals    = []
pendiente_vals   = []
balanza_sum_vals = []

for _, v in vendedores.iterrows():
    vid = v["id_vendedor"]
    hist = ventas[ventas["id_vendedor"] == vid].head(MESES)
    if hist.empty:
        continue

    dias_cero_vals.append(hist["dias_venta_cero"].mean())

    plan = hist["plan"].values
    pct  = hist["pct_plan"].values
    validos = pct[plan > 0]
    if len(validos):
        pct_plan_vals.append(validos.mean())
        if len(validos) >= 2:
            x = np.arange(len(validos))
            pendiente = np.polyfit(x[::-1], validos, 1)[0]
            pendiente_vals.append(pendiente)

    if not balanza.empty and "balanza" in balanza.columns:
        bal = balanza[balanza["id_vendedor"] == vid].head(MESES)
        if len(bal) >= 2:
            balanza_sum_vals.append(bal["balanza"].values[:2].sum())


def mostrar_distribucion(vals, titulo, umbral_actual, modo="mayor"):
    """
    modo='mayor'  → dispara cuando valor > umbral  (dias_cero)
    modo='menor'  → dispara cuando valor < umbral  (pct_plan, pendiente, balanza)
    """
    arr = np.array(vals)
    n   = len(arr)
    print(f"\n{'=' * 65}")
    print(f"  {titulo}")
    print(f"  Umbral actual: {'> ' if modo == 'mayor' else '< '}{umbral_actual}"
          f"  |  n = {n} vendedores")
    print(f"{'=' * 65}")

    pcts = [5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95]
    print("  Percentiles:")
    for p in pcts:
        v = np.percentile(arr, p)
        print(f"    p{p:3d}: {v:8.2f}")

    print(f"\n  % de vendedores que DISPARAN la señal a distintos umbrales:")
    if modo == "mayor":
        umbrales = sorted({umbral_actual, 3, 5, 8, 10, 12, 15})
        for u in umbrales:
            pct = (arr > u).mean() * 100
            marca = " ← actual" if u == umbral_actual else ""
            print(f"    > {u:5.1f}:  {pct:5.1f}%{marca}")
    else:
        if umbral_actual < 0:
            umbrales = sorted({umbral_actual, -3, -5, -8, -10, -15, -20}, reverse=True)
        else:
            umbrales = sorted({umbral_actual, 40, 50, 60, 65, 70, 75, 80}, reverse=True)
        for u in umbrales:
            pct = (arr < u).mean() * 100
            marca = " ← actual" if u == umbral_actual else ""
            print(f"    < {u:5.1f}:  {pct:5.1f}%{marca}")


mostrar_distribucion(dias_cero_vals,   "DÍAS VENTA CERO — promedio últimos 3 meses",    3,   "mayor")
mostrar_distribucion(pct_plan_vals,    "% PLAN — promedio últimos 3 meses",             80,  "menor")
mostrar_distribucion(pendiente_vals,   "PENDIENTE % PLAN (pp/mes, negativo = cae)",     -3,  "menor")
mostrar_distribucion(balanza_sum_vals, "BALANZA CLIENTES — suma últimos 2 meses",       -3,  "menor")

print("\n" + "=" * 65)
print("  CÓMO LEER ESTO:")
print("  Para que una señal DISCRIMINE hay que apuntar a que dispare")
print("  en el 20-30% de los activos (no en el 80-99%).")
print("  Elegir el umbral donde la columna '% dispara' queda ~25-30%.")
print("=" * 65)
