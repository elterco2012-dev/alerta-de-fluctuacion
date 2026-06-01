import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
con = sqlite3.connect(DB_PATH)

print("=" * 70)
print("DIAGNOSTICO GRUPO 112 — Permanencia de vendedores")
print("=" * 70)

rows = con.execute("""
    SELECT id_vendedor, nombre, activo, fecha_ingreso, fecha_egreso,
           CAST(
               (julianday(COALESCE(fecha_egreso, date('now'))) - julianday(fecha_ingreso))
               / 30.0 AS INTEGER
           ) AS meses_tenure
    FROM vendedores
    WHERE nombre_grupo = 'Grupo 112'
    ORDER BY activo DESC, fecha_ingreso
""").fetchall()

bajas = [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows if r[2] == 0]
activos = [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows if r[2] == 1]

print(f"\nTOTAL: {len(rows)} vendedores  |  ACTIVOS: {len(activos)}  |  BAJAS: {len(bajas)}")

print("\n--- VENDEDORES DE BAJA (usados para calcular duración prom.) ---")
print(f"{'ID':>6}  {'Nombre':<30}  {'Ingreso':>12}  {'Egreso':>12}  {'Meses':>6}")
print("-" * 70)

total_meses = 0
sospechosos = []

for r in bajas:
    vid, nombre, activo, fi, fe, meses = r
    flag = ""
    if meses is None or meses < 0:
        flag = " ← ERROR: meses negativos o nulos"
        sospechosos.append(r)
    elif meses > 120:
        flag = " ← SOSPECHOSO: >10 años"
        sospechosos.append(r)
    elif meses > 60:
        flag = " ← alto: >5 años"
    total_meses += meses or 0
    print(f"{vid:>6}  {(nombre or ''):<30}  {(fi or '?'):>12}  {(fe or '?'):>12}  {str(meses):>6}{flag}")

if bajas:
    prom = total_meses / len(bajas)
    print(f"\n{'':>50} PROMEDIO: {prom:.1f} meses")

print("\n--- ACTIVOS (NO incluidos en el promedio) ---")
print(f"{'ID':>6}  {'Nombre':<30}  {'Ingreso':>12}  {'Meses activo':>13}")
print("-" * 70)
for r in activos:
    vid, nombre, activo, fi, fe, meses = r
    print(f"{vid:>6}  {(nombre or ''):<30}  {(fi or '?'):>12}  {str(meses):>13}")

if sospechosos:
    print(f"\n{'='*70}")
    print(f"REGISTROS SOSPECHOSOS ({len(sospechosos)}):")
    for r in sospechosos:
        print(f"  ID {r[0]} {r[1]}: ingreso={r[3]}  egreso={r[4]}  meses={r[5]}")
    print("Verificar estas fechas directamente en Informix (tabla f040)")

con.close()
print("\nFin del diagnostico.")
