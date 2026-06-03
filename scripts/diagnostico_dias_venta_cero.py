"""
scripts/diagnostico_dias_venta_cero.py
--------------------------------------
¿Por qué la señal "días venta cero" sale 0% para TODOS (activos y egresados)?

dias_venta_cero se calcula en sincronizar_informix.py como:
    dias_venta_cero = max(0, dias_habiles - dias_con_venta)

Si queda siempre en 0 hay solo tres causas posibles:
  A) No se detecta ningún campo de fecha en sbas → dias_con_venta vacío → 0
  B) works_days_log no tiene datos → dias_habiles cae al default 20
  C) dias_con_venta >= dias_habiles siempre (hay "venta" todos los días) → 0

Este script consulta Informix (DSN=MSPA) en SOLO LECTURA y reporta cuál es.
No escribe nada en ninguna base. Solo SELECT.

Ejecutar con Python 32 bits (igual que sincronizar_informix.py):
    "C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe" scripts\\diagnostico_dias_venta_cero.py
"""

import sys
from datetime import date

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no instalado en este Python.")
    print('  "...\\Python312-32\\python.exe" -m pip install pyodbc')
    sys.exit(1)

DSN_INFORMIX = "MSPA"
FIRMA        = 1
CANDIDATOS   = ("budat", "belegdat", "erfdat", "liefdat", "dat", "fdat")

hoy        = date.today()
anio_desde = hoy.year  # solo el año en curso, suficiente para el diagnóstico

print("=" * 68)
print("DIAGNÓSTICO — días venta cero (sbas + works_days_log)")
print("=" * 68)

print("\nConectando a Informix (MSPA)...", end=" ", flush=True)
try:
    cn  = pyodbc.connect(f"DSN={DSN_INFORMIX}", timeout=15)
    cur = cn.cursor()
    print("OK")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    sys.exit(1)

# ── A) ¿Qué campo de fecha existe en sbas? ──────────────────────────────────
print("\n[A] Detección de campo de fecha en sbas:")
campo_ok = None
for c in CANDIDATOS:
    try:
        cur.execute(f"SELECT FIRST 1 {c} FROM sbas WHERE firma = {FIRMA}")
        val = cur.fetchone()
        print(f"    {c:10} → EXISTE   (ej. valor: {val[0] if val else 'sin filas'})")
        if campo_ok is None:
            campo_ok = c
    except Exception:
        print(f"    {c:10} → no existe")

if campo_ok is None:
    print("\n  >>> CAUSA A CONFIRMADA: ningún campo de fecha existe en sbas.")
    print("      dias_con_venta nunca se calcula → dias_venta_cero siempre 0.")
    print("      Hay que averiguar el nombre real del campo fecha de sbas.")
    cn.close()
    sys.exit(0)

print(f"\n    Campo que usaría el sync: '{campo_ok}'")

# ── B) ¿works_days_log tiene días hábiles? ──────────────────────────────────
print("\n[B] Días hábiles en works_days_log (año en curso):")
try:
    cur.execute("""
        SELECT YEAR(fecha), MONTH(fecha), COUNT(fecha)
        FROM works_days_log
        WHERE YEAR(fecha) = ?
        GROUP BY 1, 2 ORDER BY 1, 2
    """, anio_desde)
    filas = cur.fetchall()
    if not filas:
        print("    >>> VACÍO. dias_habiles cae al default 20 (no es la causa principal,")
        print("        pero conviene revisarlo).")
    else:
        for r in filas:
            print(f"    {int(r[0])}/{int(r[1]):02d}: {int(r[2])} días hábiles")
except Exception as e:
    print(f"    AVISO: no se pudo leer works_days_log ({e})")

# ── C) Días con venta reales por vendedor/mes (muestra) ─────────────────────
print(f"\n[C] Días DISTINTOS con venta por vendedor/mes (usando '{campo_ok}', muestra):")
try:
    cur.execute(f"""
        SELECT FIRST 15
               vertr1, bujahr, bumonat,
               COUNT(DISTINCT {campo_ok}) AS dias_con_venta
        FROM sbas
        WHERE firma = {FIRMA}
          AND bujahr = {anio_desde}
          AND {campo_ok} IS NOT NULL
          AND vertr1 IS NOT NULL
        GROUP BY vertr1, bujahr, bumonat
        ORDER BY vertr1, bujahr, bumonat
    """)
    filas = cur.fetchall()
    if not filas:
        print("    >>> Sin filas. O no hay ventas este año, o el filtro no matchea.")
    else:
        print(f"    {'vendedor':>9} {'periodo':>9} {'dias_con_venta':>15}")
        for r in filas:
            print(f"    {int(r[0]):>9} {int(r[1])}/{int(r[2]):02d} {int(r[3]):>15}")
        print("\n    Si 'dias_con_venta' es >= 20 en casi todas las filas, entonces")
        print("    (dias_habiles - dias_con_venta) da <= 0 y la señal nunca dispara:")
        print("    esto significa que en sbas hay un registro por cada día, no solo")
        print("    los días con factura real → el campo no sirve para 'días sin venta'.")
except Exception as e:
    print(f"    AVISO: no se pudo agrupar sbas ({e})")

print("\n" + "=" * 68)
print("CÓMO LEER:")
print("  [A] vacío  → falta el campo fecha: hay que encontrar el correcto.")
print("  [C] dias_con_venta siempre alto (>=20) → sbas tiene una fila por día")
print("      hábil (no por factura), así que NO sirve para medir días sin venta.")
print("      Habría que usar otra tabla de facturas reales.")
print("=" * 68)

cn.close()
