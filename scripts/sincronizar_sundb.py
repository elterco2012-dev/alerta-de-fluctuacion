"""
sincronizar_sundb.py
---------------------
ETL: lee datos de SUNDB (SQL Server, sistema SUN) y actualiza cobranza_real
en data/wurth.db (SQLite).

IMPORTANTE: Ejecutar con Python 32 bits (mismo requisito que Informix).
   C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe scripts\\sincronizar_sundb.py

Flujo:
  - Lee SALFLDGRAN (+ SALFLDGRAN2) donde ACCNT_CODE empieza en '1130'
  - D_C = 'D' → factura emitida (venta)   → agrega a venta_sun
  - D_C = 'C' → cobro recibido (cobranza) → agrega a cobranza_real
  - ANAL_T2 = ID del vendedor (char, trim)
  - PERIOD formato = año*1000 + mes (ej: 2024002 = Feb 2024)

Ejecutar DESPUÉS de sincronizar_informix.py (que ya cargó vendedores y venta_total).

Opciones:
    --dry-run      Muestra totales sin escribir en SQLite
    --full         Procesa toda la historia (por defecto: últimos 18 meses)
    --diagnostico  Solo muestra tipos de journal y estructura disponible
"""

import sys
import os
import sqlite3
import argparse
from datetime import date, datetime

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no instalado.")
    sys.exit(1)

# ── Configuración ─────────────────────────────────────────────────────────────
DSN_SUN  = "SUNDB"
DB_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

# Prefijo que SUN usa para cuentas de clientes (Informix kdnr 123456 → '1130123456')
PREFIJO_CLIENTE = "1130"

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run",     action="store_true", help="Mostrar sin guardar")
parser.add_argument("--full",        action="store_true", help="Toda la historia (por defecto: últimos 18 meses)")
parser.add_argument("--diagnostico", action="store_true", help="Solo explorar estructura")
args = parser.parse_args()

DRY_RUN     = args.dry_run
# 18 meses por defecto: cubre la cobranza del período pre-egreso de los
# egresados de los últimos 18 meses (alineado con Informix y Reactor). Con 6
# meses, los que se fueron hace más de medio año quedaban sin cobranza que cruzar.
MESES_ATRAS = 99 if args.full else 18

print("=" * 65)
print("SINCRONIZACIÓN SUNDB → SQLite  (cobranza real)")
print(f"  DSN:      {DSN_SUN}")
print(f"  DB local: {DB_PATH}")
print(f"  Modo:     {'DRY RUN' if DRY_RUN else 'ESCRITURA'}")
print(f"  Historia: {'completa' if args.full else f'últimos {MESES_ATRAS} meses'}")
print("=" * 65)

# ── Período de inicio ─────────────────────────────────────────────────────────
hoy = date.today()
anio_inicio = hoy.year
mes_inicio  = hoy.month - MESES_ATRAS
while mes_inicio <= 0:
    mes_inicio += 12
    anio_inicio -= 1

# PERIOD en SUN = año*1000 + mes
periodo_inicio_sun = anio_inicio * 1000 + mes_inicio
print(f"\n  Período desde: {anio_inicio}/{mes_inicio:02d} (PERIOD >= {periodo_inicio_sun})")

# ── Conectar a SUNDB ──────────────────────────────────────────────────────────
print("\nConectando a SUNDB...", end=" ", flush=True)
try:
    sun = pyodbc.connect(f"DSN={DSN_SUN}", timeout=15)
    print("OK")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    print("\nVerificá:")
    print("  1. Estás usando Python 32 bits")
    print("  2. El DSN 'SUNDB' está configurado en ODBC de 32 bits")
    print("  3. El servidor CONTABLE2024 es accesible")
    sys.exit(1)

scur_sun = sun.cursor()

# ── Modo diagnóstico ──────────────────────────────────────────────────────────
if args.diagnostico:
    print("\n" + "─" * 65)
    print("DIAGNÓSTICO: tipos de journal en cuentas de clientes (1130...)")
    print("─" * 65)

    for tabla in ("dbo.SALFLDGRAN", "dbo.SALFLDGRAN2"):
        print(f"\n  Tabla: {tabla}")
        try:
            scur_sun.execute(f"""
                SELECT TOP 1 ACCNT_CODE FROM {tabla}
                WHERE ACCNT_CODE LIKE '{PREFIJO_CLIENTE}%'
            """)
            row = scur_sun.fetchone()
            if not row:
                print("    (sin filas con prefijo 1130)")
                continue

            scur_sun.execute(f"""
                SELECT LTRIM(RTRIM(JRNAL_TYPE)) AS tipo,
                       LTRIM(RTRIM(D_C))        AS dc,
                       COUNT(*)                 AS cant,
                       SUM(AMOUNT)              AS total
                FROM {tabla}
                WHERE ACCNT_CODE LIKE '{PREFIJO_CLIENTE}%'
                  AND PERIOD >= {periodo_inicio_sun}
                GROUP BY LTRIM(RTRIM(JRNAL_TYPE)), LTRIM(RTRIM(D_C))
                ORDER BY cant DESC
            """)
            filas = scur_sun.fetchall()
            if filas:
                print(f"    {'JRNAL_TYPE':<15} {'D_C':<5} {'Cant':>10} {'Total':>20}")
                print(f"    {'-'*15} {'-'*5} {'-'*10} {'-'*20}")
                for f in filas:
                    print(f"    {str(f[0] or ''):<15} {str(f[1] or ''):<5} {f[2]:>10,} {float(f[3] or 0):>20,.2f}")
            else:
                print("    (sin datos en el período)")

            # Muestra de ANAL_T2 (vendedores)
            scur_sun.execute(f"""
                SELECT DISTINCT TOP 10 LTRIM(RTRIM(ANAL_T2)) AS vendedor
                FROM {tabla}
                WHERE ACCNT_CODE LIKE '{PREFIJO_CLIENTE}%'
                  AND LTRIM(RTRIM(ANAL_T2)) <> ''
                  AND PERIOD >= {periodo_inicio_sun}
            """)
            vend_rows = scur_sun.fetchall()
            if vend_rows:
                print(f"\n    ANAL_T2 (muestra vendedores): {[r[0] for r in vend_rows]}")

        except Exception as e:
            print(f"    Error al leer {tabla}: {e}")

    sun.close()
    print("\n  Diagnóstico completo. Usá estos datos para validar el ETL.")
    sys.exit(0)


# ── Conectar a SQLite ─────────────────────────────────────────────────────────
print("\nAbriendo SQLite...", end=" ")
if not os.path.exists(DB_PATH):
    print(f"FALLÓ — no existe {DB_PATH}")
    print("Ejecutá sincronizar_informix.py primero.")
    sys.exit(1)
sqlite = sqlite3.connect(DB_PATH)
scur_sq = sqlite.cursor()
print("OK")


# ── PASO 1: Agregar ventas y cobranzas desde SALFLDGRAN + SALFLDGRAN2 ─────────
print("\n" + "─" * 65)
print("PASO 1: Leyendo ventas y cobranza de SALFLDGRAN + SALFLDGRAN2...")

# Construir UNION de las tablas disponibles
def _tabla_existe(cur, tabla):
    try:
        cur.execute(f"SELECT TOP 1 ACCNT_CODE FROM {tabla}")
        cur.fetchone()
        return True
    except Exception:
        return False

tablas_sun = []
for t in ("dbo.SALFLDGRAN", "dbo.SALFLDGRAN2"):
    if _tabla_existe(scur_sun, t):
        tablas_sun.append(t)
        print(f"  {t}: encontrada")
    else:
        print(f"  {t}: no disponible")

if not tablas_sun:
    print("ERROR: ninguna tabla SALFLDGRAN disponible en SUNDB.")
    sun.close()
    sqlite.close()
    sys.exit(1)

# Query única con UNION ALL
# CHRBA = cheque rechazado (D_C='D', JRNAL_TYPE='CHRBA') — excluido de venta_sun
union_sql = " UNION ALL ".join([f"""
    SELECT LTRIM(RTRIM(ANAL_T2))      AS id_vendedor_sun,
           PERIOD,
           AMOUNT,
           LTRIM(RTRIM(D_C))          AS dc,
           LTRIM(RTRIM(JRNAL_TYPE))   AS jrnal_type
    FROM {t}
    WHERE ACCNT_CODE LIKE '{PREFIJO_CLIENTE}%'
      AND LTRIM(RTRIM(ANAL_T2)) <> ''
      AND PERIOD >= {periodo_inicio_sun}
""" for t in tablas_sun])

query = f"""
    SELECT id_vendedor_sun,
           PERIOD,
           SUM(CASE WHEN dc = 'D' AND jrnal_type <> 'CHRBA' THEN AMOUNT ELSE 0 END) AS venta_sun,
           SUM(CASE WHEN dc = 'C' THEN AMOUNT ELSE 0 END) AS cobranza_sun,
           SUM(CASE WHEN jrnal_type = 'CHRBA' AND dc = 'D' THEN 1 ELSE 0 END) AS cheques_rechazados
    FROM ({union_sql}) AS t
    GROUP BY id_vendedor_sun, PERIOD
    ORDER BY id_vendedor_sun, PERIOD
"""

print("\n  Ejecutando query (puede tardar ~30s)...", end=" ", flush=True)
try:
    scur_sun.execute(query)
    rows = scur_sun.fetchall()
    print(f"OK — {len(rows)} combinaciones vendedor/período")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    sun.close()
    sqlite.close()
    sys.exit(1)

# Convertir PERIOD → (año, mes)
def period_to_anio_mes(period):
    """2024002 → (2024, 2)"""
    p = int(period)
    return p // 1000, p % 1000

# Construir dict: (id_vendedor_int, anio, mes) → {venta_sun, cobranza_sun, cheques_rechazados}
sun_data = {}
vendedores_sun_set = set()
for row in rows:
    vid_str, period, venta_sun, cobranza_sun, cheques_rech = row
    try:
        vid = int(vid_str.strip())
    except (ValueError, AttributeError):
        continue
    anio, mes = period_to_anio_mes(period)
    if mes < 1 or mes > 12:
        continue
    vendedores_sun_set.add(vid)
    sun_data[(vid, anio, mes)] = {
        "venta_sun":          float(venta_sun or 0),
        "cobranza_sun":       float(cobranza_sun or 0),
        "cheques_rechazados": int(cheques_rech or 0),
    }

print(f"  Vendedores con datos en SUN: {len(vendedores_sun_set)}")
if vendedores_sun_set:
    print(f"  Ejemplo IDs: {sorted(list(vendedores_sun_set))[:10]}")

# ── PASO 2: Actualizar ventas_mensual en SQLite ───────────────────────────────
print("\n" + "─" * 65)
print("PASO 2: Actualizando ventas_mensual en SQLite...")

# Cargar filas existentes de ventas_mensual para el período
scur_sq.execute(f"""
    SELECT id_vendedor, anio, mes, venta_total, cobranza_teorica
    FROM ventas_mensual
    WHERE (anio > {anio_inicio})
       OR (anio = {anio_inicio} AND mes >= {mes_inicio})
""")
existing = {(r[0], r[1], r[2]): {"venta_total": r[3], "cobr_teo": r[4]}
            for r in scur_sq.fetchall()}

print(f"  Filas en ventas_mensual para el período: {len(existing)}")

actualizados = 0
sin_match    = 0
updates = []

for (vid, anio, mes), datos in sun_data.items():
    clave = (vid, anio, mes)
    cobranza_real = datos["cobranza_sun"]
    venta_sun     = datos["venta_sun"]

    if clave in existing:
        # Jerarquía: planumsk (vplan) > venta_total Informix > venta SUN
        cobr_teo_plan = existing[clave]["cobr_teo"]
        venta_inf     = existing[clave]["venta_total"]
        cobr_teo = (cobr_teo_plan if cobr_teo_plan and cobr_teo_plan > 0
                    else venta_inf  if venta_inf  and venta_inf  > 0
                    else venta_sun)

        pct_cobr = round(cobranza_real / cobr_teo * 100, 1) if cobr_teo > 0 else 0.0

        updates.append({
            "id_vendedor":       vid,
            "anio":              anio,
            "mes":               mes,
            "cobranza_real":     round(cobranza_real, 2),
            "cobranza_teorica":  round(cobr_teo, 2),
            "pct_cobranza":      pct_cobr,
            "cheques_rechazados": datos["cheques_rechazados"],
        })
        actualizados += 1
    else:
        sin_match += 1

print(f"  Matches con ventas_mensual: {actualizados}")
print(f"  En SUN pero no en Informix: {sin_match}  (vendedor no en f040 o período fuera de rango)")

if DRY_RUN:
    print("\n  DRY RUN — no se guarda nada.")
    print(f"  Se actualizarían {actualizados} filas de cobranza_real.")

    if updates:
        print("\n  Muestra de 5 actualizaciones:")
        for u in updates[:5]:
            print(f"    Vendedor {u['id_vendedor']} {u['anio']}/{u['mes']:02d} → "
                  f"cobranza_real={u['cobranza_real']:,.0f}  "
                  f"pct={u['pct_cobranza']:.1f}%")
else:
    if updates:
        scur_sq.executemany("""
            UPDATE ventas_mensual
            SET cobranza_real      = :cobranza_real,
                cobranza_teorica   = :cobranza_teorica,
                pct_cobranza       = :pct_cobranza,
                cheques_rechazados = :cheques_rechazados
            WHERE id_vendedor = :id_vendedor
              AND anio        = :anio
              AND mes         = :mes
        """, updates)
        sqlite.commit()
        print(f"\n  Actualizadas {actualizados} filas de cobranza_real en SQLite.")
    else:
        print("\n  AVISO: nada que actualizar. Verificá el diagnóstico.")

# ── Diagnóstico de cobranza ───────────────────────────────────────────────────
print("\n" + "─" * 65)
if not DRY_RUN and updates:
    scur_sq.execute(f"""
        SELECT COUNT(*) FROM ventas_mensual
        WHERE pct_cobranza < 90
          AND (anio > {anio_inicio} OR (anio = {anio_inicio} AND mes >= {mes_inicio}))
    """)
    bajo_cobr = scur_sq.fetchone()[0]
    scur_sq.execute(f"""
        SELECT AVG(pct_cobranza) FROM ventas_mensual
        WHERE cobranza_real > 0
          AND (anio > {anio_inicio} OR (anio = {anio_inicio} AND mes >= {mes_inicio}))
    """)
    avg_cobr = scur_sq.fetchone()[0]
    print(f"  % cobranza promedio: {avg_cobr:.1f}%")
    print(f"  Vendedores con cobranza < 90%: {bajo_cobr}")

print("\n" + "=" * 65)
print("RESUMEN FINAL")
print("=" * 65)
print(f"  Períodos procesados:  {len(sun_data)}")
print(f"  Filas actualizadas:   {actualizados}")
print(f"  Sin match Informix:   {sin_match}")
if not DRY_RUN:
    print("\n  Próximo paso: streamlit run dashboard.py")

sun.close()
sqlite.close()
print("\nListo.")
