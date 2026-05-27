"""
sincronizar_informix.py
-----------------------
ETL: lee datos reales de Informix y los guarda en data/wurth.db (SQLite).
El dashboard y el motor de scoring siguen leyendo SQLite sin cambios.

Ejecutar desde la carpeta del proyecto:
    python scripts/sincronizar_informix.py

Opciones:
    --dry-run    Muestra conteos sin escribir nada en SQLite
    --full       Reconstruye toda la historia (por defecto: últimos 6 meses)
"""

import sys
import os
import sqlite3
import argparse
from datetime import date, datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no instalado. Ejecutá: python -m pip install pyodbc")
    sys.exit(1)

# ── Configuración ─────────────────────────────────────────────────────────────
DSN = os.getenv("INFORMIX_DSN", "MSPA")
UID = os.getenv("INFORMIX_UID", "aarmoa")
PWD = os.getenv("INFORMIX_PWD", "")

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

FIRMA = 1  # número de empresa en Informix (ajustar si es diferente)

# vart → tipo de vendedor (ajustar según valores reales de f040.vart)
VART_TIPO = {
    1: "Viajante",
    2: "Televentas",
    3: "Viajante",   # algunos sistemas usan 3 para externo
}

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true", help="Mostrar sin guardar")
parser.add_argument("--full",    action="store_true", help="Reconstruir toda la historia")
args = parser.parse_args()

DRY_RUN = args.dry_run
MESES_ATRAS = 99 if args.full else 6

print("=" * 65)
print("SINCRONIZACIÓN INFORMIX → SQLite")
print(f"  DSN:      {DSN}")
print(f"  DB local: {DB_PATH}")
print(f"  Modo:     {'DRY RUN (sin cambios)' if DRY_RUN else 'ESCRITURA'}")
print(f"  Historia: {'completa' if args.full else f'últimos {MESES_ATRAS} meses'}")
print("=" * 65)

# ── Conectar a ambas bases ────────────────────────────────────────────────────
print("\nConectando a Informix...", end=" ")
try:
    inf = pyodbc.connect(f"DSN={DSN};UID={UID};PWD={PWD};", timeout=15)
    print("OK")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    sys.exit(1)

print("Abriendo SQLite...", end=" ")
sqlite = sqlite3.connect(DB_PATH)
print("OK\n")

icur = inf.cursor()
scur = sqlite.cursor()

# ── Inicializar tablas SQLite ─────────────────────────────────────────────────
scur.executescript("""
CREATE TABLE IF NOT EXISTS grupos (
    id_grupo   INTEGER PRIMARY KEY,
    nombre_grupo TEXT,
    supervisor   TEXT,
    riesgo_base  REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS vendedores (
    id_vendedor  INTEGER PRIMARY KEY,
    tipo         TEXT,
    nombre       TEXT,
    id_grupo     INTEGER,
    nombre_grupo TEXT,
    supervisor   TEXT,
    fecha_ingreso TEXT,
    fecha_egreso  TEXT,
    motivo_egreso TEXT,
    activo        INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ventas_mensual (
    id_vendedor      INTEGER,
    anio             INTEGER,
    mes              INTEGER,
    mes_numero       INTEGER,
    dias_trabajados  INTEGER DEFAULT 0,
    dias_venta_cero  INTEGER DEFAULT 0,
    venta_total      REAL DEFAULT 0,
    plan             REAL DEFAULT 0,
    pct_plan         REAL DEFAULT 0,
    clientes_activos INTEGER DEFAULT 0,
    total_clientes   INTEGER DEFAULT 0,
    clientes_inactivos INTEGER DEFAULT 0,
    clientes_nuevos  INTEGER DEFAULT 0,
    cobranza_teorica REAL DEFAULT 0,
    cobranza_real    REAL DEFAULT 0,
    pct_cobranza     REAL DEFAULT 100,
    dias_cobro       REAL DEFAULT 0,
    cheques_rechazados INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);
""")
sqlite.commit()


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1: Vendedores desde f040
# ══════════════════════════════════════════════════════════════════════════════
print("─" * 65)
print("PASO 1: Leyendo vendedores de f040...")

icur.execute(f"""
    SELECT vertr, name1, name2, vgrp, vart, eintrdat, austrdat, zone, kzleiter
    FROM f040
    WHERE firma = {FIRMA}
    ORDER BY vertr
""")
vendedores_raw = icur.fetchall()
print(f"  {len(vendedores_raw)} registros encontrados en f040")

# Contar activos vs bajas
activos  = [v for v in vendedores_raw if v[6] is None]
con_baja = [v for v in vendedores_raw if v[6] is not None]
print(f"  Activos (austrdat IS NULL): {len(activos)}")
print(f"  Con baja (austrdat IS NOT NULL): {len(con_baja)}")

# Mapear vendedores
vendedores = []
for row in vendedores_raw:
    vertr, name1, name2, vgrp, vart, eintrdat, austrdat, zone, kzleiter = row
    nombre = f"{(name1 or '').strip()} {(name2 or '').strip()}".strip()
    if not nombre:
        nombre = f"Vendedor {vertr}"
    tipo = VART_TIPO.get(vart, "Viajante")
    activo = 1 if austrdat is None else 0

    # Convertir fechas
    def fmt_date(d):
        if d is None:
            return None
        if isinstance(d, (date, datetime)):
            return d.strftime("%Y-%m-%d")
        return str(d)[:10]

    vendedores.append({
        "id_vendedor":  vertr,
        "tipo":         tipo,
        "nombre":       nombre,
        "id_grupo":     vgrp or 0,
        "nombre_grupo": f"Grupo {vgrp}" if vgrp else "Sin grupo",
        "supervisor":   f"Supervisor G{vgrp}" if vgrp else "Sin supervisor",
        "fecha_ingreso": fmt_date(eintrdat),
        "fecha_egreso":  fmt_date(austrdat),
        "motivo_egreso": None,
        "activo":        activo,
    })

if not DRY_RUN:
    scur.execute("DELETE FROM vendedores")
    scur.executemany("""
        INSERT OR REPLACE INTO vendedores
        (id_vendedor, tipo, nombre, id_grupo, nombre_grupo, supervisor,
         fecha_ingreso, fecha_egreso, motivo_egreso, activo)
        VALUES (:id_vendedor, :tipo, :nombre, :id_grupo, :nombre_grupo, :supervisor,
                :fecha_ingreso, :fecha_egreso, :motivo_egreso, :activo)
    """, vendedores)
    sqlite.commit()
    print(f"  Guardados {len(vendedores)} vendedores en SQLite")
else:
    print(f"  DRY RUN — se guardarían {len(vendedores)} vendedores")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2: Grupos con riesgo_base calculado
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("PASO 2: Calculando grupos y riesgo_base desde historial...")

# riesgo_base = % de vendedores que se fueron en menos de 6 meses
icur.execute(f"""
    SELECT vgrp,
           COUNT(*) as total,
           SUM(CASE WHEN austrdat IS NOT NULL THEN 1 ELSE 0 END) as bajas,
           SUM(CASE
               WHEN austrdat IS NOT NULL
                AND (austrdat - eintrdat) < 180
               THEN 1 ELSE 0 END) as bajas_rapidas
    FROM f040
    WHERE firma = {FIRMA}
      AND vgrp IS NOT NULL
      AND eintrdat IS NOT NULL
    GROUP BY vgrp
    ORDER BY vgrp
""")
grupos_raw = icur.fetchall()
print(f"  {len(grupos_raw)} grupos encontrados")

grupos = []
for row in grupos_raw:
    vgrp, total, bajas, bajas_rapidas = row
    if total and total > 0:
        riesgo = round(bajas_rapidas / total, 3) if bajas_rapidas else 0
    else:
        riesgo = 0
    grupos.append({
        "id_grupo":    vgrp,
        "nombre_grupo": f"Grupo {vgrp}",
        "supervisor":   f"Supervisor G{vgrp}",
        "riesgo_base":  riesgo,
    })

if not DRY_RUN:
    scur.execute("DELETE FROM grupos")
    scur.executemany("""
        INSERT OR REPLACE INTO grupos (id_grupo, nombre_grupo, supervisor, riesgo_base)
        VALUES (:id_grupo, :nombre_grupo, :supervisor, :riesgo_base)
    """, grupos)
    sqlite.commit()
    print(f"  Guardados {len(grupos)} grupos en SQLite")
    grupos_alto_riesgo = [g for g in grupos if g["riesgo_base"] > 0.60]
    print(f"  Grupos con riesgo_base > 0.60: {len(grupos_alto_riesgo)}")
    for g in sorted(grupos_alto_riesgo, key=lambda x: -x["riesgo_base"])[:5]:
        print(f"    Grupo {g['id_grupo']:>5}: {g['riesgo_base']*100:.0f}% rotación rápida")
else:
    print(f"  DRY RUN — se guardarían {len(grupos)} grupos")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3: Ventas reales desde bujo + plan desde vplan
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("PASO 3: Leyendo plan de vplan + ventas reales de bujo...")

# Detectar columnas disponibles en bujo
bujo_cols = [c.column_name.lower() for c in icur.columns(table="bujo")]
tiene_umsatz = "umsatz" in bujo_cols
tiene_vertr  = "vertr"  in bujo_cols
tiene_bujahr = "bujahr" in bujo_cols
tiene_kdnr   = "kdnr"   in bujo_cols
tiene_bumonat = "bumonat" in bujo_cols

print(f"  bujo columnas detectadas:")
print(f"    vertr:   {'SI' if tiene_vertr else 'NO - no se pueden calcular ventas por vendedor'}")
print(f"    bujahr:  {'SI' if tiene_bujahr else 'NO'}")
print(f"    bumonat: {'SI' if tiene_bumonat else 'NO'}")
print(f"    umsatz:  {'SI' if tiene_umsatz else 'NO - no se pueden calcular ventas totales'}")
print(f"    kdnr:    {'SI' if tiene_kdnr else 'NO - no se pueden contar clientes únicos'}")

# Período a sincronizar
hoy = date.today()
anio_inicio = hoy.year
mes_inicio  = hoy.month - MESES_ATRAS
while mes_inicio <= 0:
    mes_inicio += 12
    anio_inicio -= 1

print(f"\n  Período: desde {anio_inicio}/{mes_inicio:02d}")

# Leer planes de vplan
print("\n  Leyendo vplan...", end=" ")
icur.execute(f"""
    SELECT vertr, bujahr, bumonat, planums, aktivkd,
           tg_krank, tg_unfall, tg_urlaub
    FROM vplan
    WHERE firma = {FIRMA}
      AND (bujahr > {anio_inicio}
           OR (bujahr = {anio_inicio} AND bumonat >= {mes_inicio}))
    ORDER BY vertr, bujahr, bumonat
""")
vplan_rows = icur.fetchall()
print(f"{len(vplan_rows)} filas")

# Armar dict: (vertr, año, mes) → datos de plan
plan_dict = {}
for row in vplan_rows:
    vertr, bujahr, bumonat, planums, aktivkd, tg_krank, tg_unfall, tg_urlaub = row
    plan_dict[(vertr, bujahr, bumonat)] = {
        "plan":     float(planums or 0),
        "aktivkd":  int(aktivkd or 0),
        "dias_off": int((tg_krank or 0) + (tg_unfall or 0) + (tg_urlaub or 0)),
    }

# Leer ventas reales de bujo (si tiene las columnas)
ventas_dict = {}
if tiene_umsatz and tiene_vertr and tiene_bujahr and tiene_bumonat:
    print("  Leyendo ventas reales de bujo...", end=" ")
    try:
        kdnr_select = ", COUNT(DISTINCT kdnr) as clientes_unicos" if tiene_kdnr else ", 0 as clientes_unicos"
        icur.execute(f"""
            SELECT vertr, bujahr, bumonat,
                   SUM(umsatz) as venta_total,
                   COUNT(*) as num_trans
                   {kdnr_select}
            FROM bujo
            WHERE firma = {FIRMA}
              AND (bujahr > {anio_inicio}
                   OR (bujahr = {anio_inicio} AND bumonat >= {mes_inicio}))
            GROUP BY vertr, bujahr, bumonat
            ORDER BY vertr, bujahr, bumonat
        """)
        bujo_rows = icur.fetchall()
        print(f"{len(bujo_rows)} combinaciones vertr/año/mes")
        for row in bujo_rows:
            vertr, bujahr, bumonat, venta_total, num_trans, clientes_unicos = row
            ventas_dict[(vertr, bujahr, bumonat)] = {
                "venta_total":    float(venta_total or 0),
                "num_trans":      int(num_trans or 0),
                "clientes_unicos": int(clientes_unicos or 0),
            }
    except Exception as e:
        print(f"  Error leyendo bujo: {e}")
        print("  Continuando sin ventas reales (score usará solo plan)")
else:
    print("  AVISO: bujo no tiene columnas esperadas — usando solo datos de vplan")
    print("         Ejecutá scripts/explorar_bujo.py para diagnosticar")

# Construir ventas_mensual
print("\n  Construyendo ventas_mensual...")

# Necesitamos fecha_ingreso por vendedor para calcular mes_numero
vendedor_ingreso = {
    v["id_vendedor"]: v["fecha_ingreso"]
    for v in vendedores if v["fecha_ingreso"]
}

ventas_mensual = []
periodos = set(plan_dict.keys()) | set(ventas_dict.keys())

for (vertr, bujahr, bumonat) in sorted(periodos):
    plan_data = plan_dict.get((vertr, bujahr, bumonat), {})
    venta_data = ventas_dict.get((vertr, bujahr, bumonat), {})

    plan_val = plan_data.get("plan", 0)
    aktivkd  = plan_data.get("aktivkd", 0)
    dias_off = plan_data.get("dias_off", 0)
    venta_total = venta_data.get("venta_total", 0)
    clientes_unicos = venta_data.get("clientes_unicos", aktivkd)

    pct_plan = round((venta_total / plan_val * 100), 1) if plan_val > 0 else 0

    # Calcular mes_numero (mes de carrera del vendedor)
    mes_numero = 1
    ingreso_str = vendedor_ingreso.get(vertr)
    if ingreso_str:
        try:
            ingreso = datetime.strptime(ingreso_str[:10], "%Y-%m-%d")
            periodo_dt = datetime(bujahr, bumonat, 1)
            delta_meses = (periodo_dt.year - ingreso.year) * 12 + (periodo_dt.month - ingreso.month)
            mes_numero = max(1, delta_meses + 1)
        except Exception:
            pass

    # Días trabajados estimados (días hábiles - días ausente)
    dias_habiles = 22
    dias_trabajados = max(0, dias_habiles - dias_off)

    ventas_mensual.append({
        "id_vendedor":       vertr,
        "anio":              bujahr,
        "mes":               bumonat,
        "mes_numero":        mes_numero,
        "dias_trabajados":   dias_trabajados,
        "dias_venta_cero":   0,  # sin datos granulares por ahora
        "venta_total":       round(venta_total, 2),
        "plan":              round(plan_val, 2),
        "pct_plan":          pct_plan,
        "clientes_activos":  aktivkd,
        "total_clientes":    max(aktivkd, clientes_unicos),
        "clientes_inactivos": max(0, clientes_unicos - aktivkd) if clientes_unicos > aktivkd else 0,
        "clientes_nuevos":   0,  # sin datos granulares por ahora
        "cobranza_teorica":  round(venta_total * 0.95, 2),  # estimado
        "cobranza_real":     round(venta_total * 0.95, 2),  # sin datos reales aún
        "pct_cobranza":      95.0,
        "dias_cobro":        30.0,
        "cheques_rechazados": 0,
    })

print(f"  {len(ventas_mensual)} filas de ventas_mensual preparadas")

if not DRY_RUN:
    scur.execute(f"""
        DELETE FROM ventas_mensual
        WHERE (anio > {anio_inicio})
           OR (anio = {anio_inicio} AND mes >= {mes_inicio})
    """)
    scur.executemany("""
        INSERT OR REPLACE INTO ventas_mensual
        (id_vendedor, anio, mes, mes_numero, dias_trabajados, dias_venta_cero,
         venta_total, plan, pct_plan, clientes_activos, total_clientes,
         clientes_inactivos, clientes_nuevos, cobranza_teorica, cobranza_real,
         pct_cobranza, dias_cobro, cheques_rechazados)
        VALUES (:id_vendedor, :anio, :mes, :mes_numero, :dias_trabajados, :dias_venta_cero,
                :venta_total, :plan, :pct_plan, :clientes_activos, :total_clientes,
                :clientes_inactivos, :clientes_nuevos, :cobranza_teorica, :cobranza_real,
                :pct_cobranza, :dias_cobro, :cheques_rechazados)
    """, ventas_mensual)
    sqlite.commit()
    print(f"  Guardadas en SQLite")
else:
    print(f"  DRY RUN — se guardarían {len(ventas_mensual)} filas")


# ══════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("RESUMEN")
print("=" * 65)

if not DRY_RUN:
    scur.execute("SELECT COUNT(*) FROM vendedores WHERE activo = 1")
    n_activos = scur.fetchone()[0]
    scur.execute("SELECT COUNT(*) FROM vendedores WHERE activo = 0")
    n_bajas = scur.fetchone()[0]
    scur.execute("SELECT COUNT(*) FROM grupos")
    n_grupos = scur.fetchone()[0]
    scur.execute("SELECT COUNT(*) FROM ventas_mensual")
    n_ventas = scur.fetchone()[0]
    scur.execute("SELECT MAX(anio), MAX(bumonat) FROM ventas_mensual vm JOIN vendedores v ON vm.id_vendedor=v.id_vendedor WHERE v.activo=1")
    ultimo = scur.fetchone()

    print(f"  Vendedores activos:  {n_activos}")
    print(f"  Vendedores con baja: {n_bajas}")
    print(f"  Grupos:              {n_grupos}")
    print(f"  Registros de ventas: {n_ventas}")
    if ultimo and ultimo[0]:
        print(f"  Último período:      {ultimo[0]}/{ultimo[1]:02d}")

    if not ventas_dict:
        print("\n  AVISO IMPORTANTE:")
        print("  No se encontraron ventas reales en bujo.")
        print("  Las señales de % plan y tendencia no estarán disponibles.")
        print("  Ejecutá scripts/explorar_bujo.py para diagnosticar.")

print("\n  Para ver el resultado: streamlit run dashboard.py")

inf.close()
sqlite.close()
print("\nListo.")
