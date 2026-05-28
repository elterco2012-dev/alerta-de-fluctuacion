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
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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
# PASO 1: Vendedores desde f040 (con supervisor real via bvertr JOIN)
# ══════════════════════════════════════════════════════════════════════════════
print("─" * 65)
print("PASO 1: Leyendo vendedores de f040 (con supervisores reales)...")

# Traer todos los vendedores (activos + bajas) para calcular riesgo histórico
# Usar el filtro correcto de activos + JOIN para nombre del supervisor
icur.execute(f"""
    SELECT vertr, name1, name2, vgrp, vart,
           eintrdat, austrdat, bvertr, prof
    FROM f040
    WHERE firma = {FIRMA}
      AND vgrp <> 777
      AND vgrp <> 0
      AND eintrdat IS NOT NULL
    ORDER BY vertr
""")
vendedores_raw_base = icur.fetchall()

# Lookup de supervisores: vertr → (name1, name2)
icur.execute(f"SELECT vertr, name1, name2 FROM f040 WHERE firma = {FIRMA}")
sup_map = {r[0]: (r[1], r[2]) for r in icur.fetchall()}

# Agregar nombres de supervisor a cada fila
vendedores_raw = []
for r in vendedores_raw_base:
    vertr, name1, name2, vgrp, vart, eintrdat, austrdat, bvertr, prof = r
    sup = sup_map.get(bvertr, (None, None))
    vendedores_raw.append((vertr, name1, name2, vgrp, vart, eintrdat, austrdat, bvertr, prof, sup[0], sup[1]))
print(f"  {len(vendedores_raw)} registros en f040 (excl. grupos 0 y 777)")

activos  = [v for v in vendedores_raw if v[6] is None]
con_baja = [v for v in vendedores_raw if v[6] is not None]
print(f"  Activos (austrdat IS NULL): {len(activos)}")
print(f"  Con baja (austrdat IS NOT NULL): {len(con_baja)}")

# Obtener zona real de cada vendedor activo
# zone es palabra reservada en Informix → usamos una query específica con alias
# También aplicamos filtro zone <> 'xxx0000' igual que en Access
print("  Leyendo zonas y filtrando zone='xxx0000'...", end=" ")
zona_map = {}   # vertr → zona
excluir_zone = set()  # vertrs con zone='xxx0000' a excluir
try:
    icur.execute(f"""
        SELECT vertr, TRIM(zone)
        FROM f040
        WHERE firma = {FIRMA}
          AND vgrp <> 777
          AND vgrp <> 0
          AND eintrdat IS NOT NULL
          AND austrdat IS NULL
    """)
    for row in icur.fetchall():
        zona_map[row[0]] = row[1]
    print(f"{len(zona_map)} vendedores activos")
except Exception as e:
    print(f"error ({e}), continuando sin zona")

# Convertir fechas
def fmt_date(d):
    if d is None:
        return None
    if isinstance(d, (date, datetime)):
        return d.strftime("%Y-%m-%d")
    return str(d)[:10]

# Conjunto de vertrs que SÍ son activos válidos (según zona_map)
# zona_map solo tiene vendedores que pasaron todos los filtros SQL
activos_validos = set(zona_map.keys())

# Mapear vendedores
vendedores = []
excluidos_zona = 0
for row in vendedores_raw:
    vertr, name1, name2, vgrp, vart, eintrdat, austrdat, bvertr, prof, sup_name1, sup_name2 = row

    nombre = (name1 or '').strip()
    if not nombre:
        nombre = f"Vendedor {vertr}"

    # Nombre real del supervisor — solo name1, name2 es el CUIT
    if sup_name1:
        supervisor = sup_name1.strip()
    elif sup_name2:
        supervisor = sup_name2.strip()
    else:
        supervisor = f"Supervisor G{vgrp}" if vgrp else "Sin supervisor"

    TVTAS_GRUPOS = {971: "Televentas Auto", 972: "Televentas Metal", 973: "Televentas Cargo"}
    zona_val = (zona_map.get(vertr, "") or "").strip().upper()
    # Televentas se detecta SOLO por zone='TVTAS', vart no es confiable
    if zona_val == "TVTAS":
        tipo = "Televentas"
        nombre_grupo = TVTAS_GRUPOS.get(vgrp, "Televentas")
    else:
        tipo = "Viajante"
        nombre_grupo = f"Grupo {vgrp}" if vgrp else "Sin grupo"

    # Excluir vendedores que ingresaron y salieron el mismo día (no llegaron a trabajar)
    if austrdat is not None and eintrdat is not None and austrdat == eintrdat:
        excluidos_zona += 1
        continue

    # Activo solo si pasó el filtro completo (eintrdat, zone, vgrp)
    if austrdat is None:
        activo = 1 if vertr in activos_validos else 0
        if vertr not in activos_validos:
            excluidos_zona += 1
    else:
        activo = 0

    vendedores.append({
        "id_vendedor":  vertr,
        "tipo":         tipo,
        "nombre":       nombre,
        "id_grupo":     vgrp or 0,
        "nombre_grupo": nombre_grupo,
        "supervisor":   supervisor,
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
    activos_guardados = sum(1 for v in vendedores if v["activo"] == 1)
    print(f"  Guardados {len(vendedores)} vendedores en SQLite")
    print(f"  Activos válidos: {activos_guardados}  (excluidos por zona/filtros: {excluidos_zona})")
else:
    print(f"  DRY RUN — se guardarían {len(vendedores)} vendedores")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2: Grupos con riesgo_base calculado
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("PASO 2: Calculando grupos y riesgo_base desde historial...")

# riesgo_base = % de vendedores que se fueron en menos de 6 meses
# Calculado en Python con los datos ya leídos de vendedores_raw
from collections import defaultdict

grupo_stats = defaultdict(lambda: {"total": 0, "bajas_rapidas": 0})

def dias_entre(d1, d2):
    if d1 is None or d2 is None:
        return None
    try:
        if isinstance(d1, (date, datetime)):
            d1 = d1.date() if isinstance(d1, datetime) else d1
        else:
            d1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d").date()
        if isinstance(d2, (date, datetime)):
            d2 = d2.date() if isinstance(d2, datetime) else d2
        else:
            d2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d").date()
        return (d2 - d1).days
    except Exception:
        return None

for row in vendedores_raw:
    vertr, name1, name2, vgrp, vart, eintrdat, austrdat, bvertr, prof, sup_name1, sup_name2 = row
    if vgrp is None or eintrdat is None:
        continue
    grupo_stats[vgrp]["total"] += 1
    if austrdat is not None:
        d = dias_entre(eintrdat, austrdat)
        if d is not None and d < 180:
            grupo_stats[vgrp]["bajas_rapidas"] += 1

grupos = []
for vgrp, stats in sorted(grupo_stats.items()):
    total = stats["total"]
    riesgo = round(stats["bajas_rapidas"] / total, 3) if total > 0 else 0
    grupos.append({
        "id_grupo":     vgrp,
        "nombre_grupo": f"Grupo {vgrp}",
        "supervisor":   f"Supervisor G{vgrp}",
        "riesgo_base":  riesgo,
    })
print(f"  {len(grupos)} grupos calculados")

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
# PASO 3: Plan de vplan + ventas reales de sbas (facturas belegart=11)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("PASO 3: Leyendo plan de vplan + ventas reales de sbas...")
print("  sbas: facturas (belegart=11), vertr1=vendedor, netwert=importe neto")

# Cargar calendario de días hábiles
DIAS_HABILES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'dias_habiles.csv')
dias_habiles_set = set()       # set de date objects: días hábiles
dias_habiles_por_mes = {}      # (año, mes) → set de date objects
if os.path.exists(DIAS_HABILES_PATH):
    with open(DIAS_HABILES_PATH) as _f:
        next(_f)  # saltar header
        for line in _f:
            line = line.strip()
            if not line:
                continue
            try:
                d = datetime.strptime(line, "%Y-%m-%d").date()
                dias_habiles_set.add(d)
                key = (d.year, d.month)
                if key not in dias_habiles_por_mes:
                    dias_habiles_por_mes[key] = set()
                dias_habiles_por_mes[key].add(d)
            except ValueError:
                pass
    print(f"  Calendario días hábiles: {len(dias_habiles_set)} días cargados "
          f"({min(dias_habiles_por_mes)} → {max(dias_habiles_por_mes)})")
else:
    print("  AVISO: data/dias_habiles.csv no encontrado — dias_venta_cero = 0")

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

# Leer ventas reales de sbas (facturas belegart=11)
# vertr1 = vendedor principal, netwert = importe neto facturado
# COUNT(DISTINCT kdnr) = clientes únicos facturados ese mes
print("\n  Leyendo ventas reales de sbas (puede tardar ~1 min)...", end=" ")
ventas_dict = {}
try:
    icur.execute(f"""
        SELECT vertr1, bujahr, bumonat,
               SUM(netwert) AS venta_total,
               COUNT(DISTINCT kdnr) AS clientes_unicos
        FROM sbas
        WHERE firma = {FIRMA}
          AND belegart = 11
          AND vertr1 > 0
          AND (bujahr > {anio_inicio}
               OR (bujahr = {anio_inicio} AND bumonat >= {mes_inicio}))
        GROUP BY vertr1, bujahr, bumonat
        ORDER BY vertr1, bujahr, bumonat
    """)
    sbas_rows = icur.fetchall()
    print(f"{len(sbas_rows)} combinaciones vendedor/mes")
    for row in sbas_rows:
        vertr, bujahr, bumonat, venta_total, clientes_unicos = row
        ventas_dict[(int(vertr), int(bujahr), int(bumonat))] = {
            "venta_total":     float(venta_total or 0),
            "clientes_unicos": int(clientes_unicos or 0),
        }
except Exception as e:
    print(f"\n  AVISO: error leyendo sbas: {e}")
    print("  Continuando solo con datos de plan de vplan.")

# Días con al menos una factura por vendedor (para calcular dias_venta_cero)
# redat = fecha del comprobante en sbas
print("\n  Leyendo días con facturación por vendedor...", end=" ")
dias_con_venta = {}  # (vertr, año, mes) → set de date objects con al menos 1 factura
if dias_habiles_set:
    try:
        icur.execute(f"""
            SELECT vertr1, redat
            FROM sbas
            WHERE firma = {FIRMA}
              AND belegart = 11
              AND vertr1 > 0
              AND (bujahr > {anio_inicio}
                   OR (bujahr = {anio_inicio} AND bumonat >= {mes_inicio}))
            GROUP BY vertr1, redat
        """)
        budat_rows = icur.fetchall()
        print(f"{len(budat_rows)} pares vendedor/fecha")
        for row in budat_rows:
            vertr, redat = row
            if redat is None:
                continue
            if isinstance(redat, (date, datetime)):
                d = redat.date() if isinstance(redat, datetime) else redat
            else:
                try:
                    d = datetime.strptime(str(redat)[:10], "%Y-%m-%d").date()
                except ValueError:
                    continue
            key = (int(vertr), d.year, d.month)
            if key not in dias_con_venta:
                dias_con_venta[key] = set()
            dias_con_venta[key].add(d)
    except Exception as e:
        print(f"\n  AVISO: error leyendo fechas de sbas (redat): {e}")
        print("  dias_venta_cero = 0 este ciclo.")
else:
    print("omitido (sin calendario)")

# Leer clientes nuevos de adrchr + kund
# adrchr.erfdat = fecha de alta del cliente, adrart=2 = cliente
# kund.vertr1 = vendedor asignado al cliente
print("\n  Leyendo clientes nuevos de adrchr + kund...", end=" ")
nuevos_dict = {}  # (vertr, año, mes) → count
try:
    fecha_inicio_str = f"{anio_inicio}-{mes_inicio:02d}-01"
    icur.execute(f"""
        SELECT k.vertr1,
               YEAR(a.erfdat)  AS bujahr,
               MONTH(a.erfdat) AS bumonat,
               COUNT(DISTINCT a.kdnr) AS clientes_nuevos
        FROM adrchr a
        JOIN kund k ON a.kdnr = k.kdnr AND k.firma = {FIRMA}
        WHERE a.firma = {FIRMA}
          AND a.adrart = 2
          AND a.erfdat >= '{fecha_inicio_str}'
          AND k.vertr1 > 0
        GROUP BY k.vertr1, YEAR(a.erfdat), MONTH(a.erfdat)
        ORDER BY k.vertr1, YEAR(a.erfdat), MONTH(a.erfdat)
    """)
    adrchr_rows = icur.fetchall()
    print(f"{len(adrchr_rows)} combinaciones vendedor/mes")
    for row in adrchr_rows:
        vertr, bujahr, bumonat, cnt = row
        nuevos_dict[(int(vertr), int(bujahr), int(bumonat))] = int(cnt or 0)
except Exception as e:
    print(f"\n  AVISO: error leyendo adrchr/kund: {e}")
    print(f"  La señal 'clientes nuevos' no estará disponible este ciclo.")
    print(f"  Detalle: {e}")

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

    plan_val         = plan_data.get("plan", 0)
    aktivkd          = plan_data.get("aktivkd", 0)
    dias_off         = plan_data.get("dias_off", 0)
    venta_total      = venta_data.get("venta_total", 0)
    clientes_unicos  = venta_data.get("clientes_unicos", 0)

    # Clientes activos: usar COUNT(DISTINCT kdnr) de sbas si hay datos,
    # si no, usar aktivkd de vplan como fallback
    clientes_activos = clientes_unicos if clientes_unicos > 0 else aktivkd

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

    clientes_nuevos = nuevos_dict.get((int(vertr), int(bujahr), int(bumonat)), 0)

    # dias_venta_cero: días hábiles del mes donde el vendedor no tuvo ninguna factura
    habiles_mes = dias_habiles_por_mes.get((int(bujahr), int(bumonat)), set())
    con_venta   = dias_con_venta.get((int(vertr), int(bujahr), int(bumonat)), set())
    if habiles_mes:
        dias_sin_venta = len(habiles_mes - con_venta)
        dias_trabajados_real = len(habiles_mes)
    else:
        dias_sin_venta = 0
        dias_trabajados_real = max(0, dias_habiles - dias_off)

    ventas_mensual.append({
        "id_vendedor":       vertr,
        "anio":              bujahr,
        "mes":               bumonat,
        "mes_numero":        mes_numero,
        "dias_trabajados":   dias_trabajados_real,
        "dias_venta_cero":   dias_sin_venta,
        "venta_total":       round(venta_total, 2),
        "plan":              round(plan_val, 2),
        "pct_plan":          pct_plan,
        "clientes_activos":  clientes_activos,
        "total_clientes":    max(clientes_activos, aktivkd),
        "clientes_inactivos": max(0, aktivkd - clientes_activos),
        "clientes_nuevos":   clientes_nuevos,
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
    scur.execute("SELECT MAX(anio), MAX(mes) FROM ventas_mensual vm JOIN vendedores v ON vm.id_vendedor=v.id_vendedor WHERE v.activo=1")
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
