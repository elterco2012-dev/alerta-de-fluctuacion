"""
sincronizar_informix.py
------------------------
ETL: lee datos de Informix (DSN=MSPA) y los guarda en SQLite data/wurth.db.

Datos que extrae:
  1. adrchr  → clientes nuevos por vendedor/mes (erfuser = vertr1 = id_vendedor)
  2. sbas    → balanza clientes (reactivados, perdidos) + ticket promedio + productos

Lógica de balanza (por vendedor/mes):
  - Nuevo       : cliente cuya erfdat en adrchr cae en ese mes (erfuser = vendedor)
  - Reactivado  : compró este mes Y su venta anterior fue hace 12+ meses
  - Perdido     : última compra fue hace exactamente 12 meses (cruzó umbral de inactividad)
  - Balanza     : nuevos + reactivados - perdidos

REGLA ABSOLUTA: solo lectura de Informix. Nunca INSERT/UPDATE/DELETE en MSPA.

Ejecutar con Python 32 bits:
    C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe scripts\\sincronizar_informix.py

Opciones:
    --dry-run     Muestra totales sin escribir en SQLite
    --full        Toda la historia (por defecto: últimos 6 meses)
    --diagnostico Solo muestra conteos por mes
"""

import sys
import os
import sqlite3
import argparse
from datetime import date, timedelta
from collections import defaultdict

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no instalado.  pip install pyodbc")
    sys.exit(1)

DSN_INFORMIX = "MSPA"
DB_PATH      = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
FIRMA        = 1

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run",     action="store_true")
parser.add_argument("--full",        action="store_true")
parser.add_argument("--diagnostico", action="store_true")
args = parser.parse_args()

DRY_RUN     = args.dry_run
MESES_ATRAS = 99 if args.full else 6

print("=" * 65)
print("SINCRONIZACIÓN Informix (MSPA) → SQLite  (balanza clientes)")
print(f"  DSN:      {DSN_INFORMIX}")
print(f"  DB local: {DB_PATH}")
print(f"  Modo:     {'DRY RUN' if DRY_RUN else 'ESCRITURA'}")
print(f"  Historia: {'completa' if args.full else f'últimos {MESES_ATRAS} meses'}")
print("=" * 65)

hoy = date.today()
fecha_limite    = hoy - timedelta(days=MESES_ATRAS * 30)
anio_inicio     = fecha_limite.year
mes_inicio      = fecha_limite.month
fecha_desde_str = f"{anio_inicio:04d}-{mes_inicio:02d}-01"
fecha_desde_dt  = date(anio_inicio, mes_inicio, 1)
print(f"\n  Período desde: {anio_inicio}/{mes_inicio:02d}  ({fecha_desde_str})")

# ── Leer IDs activos de SQLite ────────────────────────────────────────────────
EXCLUIR_SUPERVISORES = """
    AND nombre NOT IN (
        SELECT DISTINCT supervisor FROM vendedores
        WHERE supervisor IS NOT NULL AND supervisor != ''
    )
"""
try:
    _lcon = sqlite3.connect(DB_PATH)
    _lcur = _lcon.cursor()
    _lcur.execute(f"SELECT id_vendedor FROM vendedores WHERE activo = 1 {EXCLUIR_SUPERVISORES}")
    IDS_ACTIVOS = [str(r[0]) for r in _lcur.fetchall()]
    _lcon.close()
    print(f"  Vendedores activos (sin supervisores): {len(IDS_ACTIVOS)}")
except Exception as e:
    print(f"\nAVISO: no se pudo leer vendedores ({e})")
    IDS_ACTIVOS = []

IN_ACTIVOS = f"({','.join(IDS_ACTIVOS)})" if IDS_ACTIVOS else "(0)"

# ── Conectar a Informix ───────────────────────────────────────────────────────
print("\nConectando a Informix (MSPA)...", end=" ", flush=True)
try:
    icon = pyodbc.connect(f"DSN={DSN_INFORMIX}", timeout=15)
    icur = icon.cursor()
    print("OK")
except Exception as e:
    print(f"FALLÓ\nError: {e}")
    sys.exit(1)

# ── Diagnóstico ────────────────────────────────────────────────────────────────
if args.diagnostico:
    print("\n--- DIAGNÓSTICO Informix ---\n")
    print("adrchr (altas totales de clientes, sin filtro por vendedor):")
    icur.execute(f"""
        SELECT YEAR(erfdat), MONTH(erfdat), COUNT(kdnr)
        FROM adrchr
        WHERE firma = {FIRMA}
          AND erfdat >= ?
        GROUP BY 1, 2
        ORDER BY 1 DESC, 2 DESC
    """, fecha_desde_dt)
    for r in icur.fetchall():
        print(f"  {r[0]}/{r[1]:02d}: {r[2]:,} altas")

    print("\nsbas (movimientos, últimos 6 meses):")
    icur.execute(f"""
        SELECT bujahr, bumonat, COUNT(*) AS lineas
        FROM sbas
        WHERE firma = {FIRMA}
          AND bujahr >= {anio_inicio}
          AND vertr1 IN {IN_ACTIVOS}
        GROUP BY 1, 2
        ORDER BY 1 DESC, 2 DESC
    """)
    for r in icur.fetchall():
        print(f"  {r[0]}/{r[1]:02d}: {r[2]:,} líneas")
    icon.close()
    sys.exit(0)

# ── 0. Fechas reales de vendedores desde f040 ─────────────────────────────────
print("\n[0/4] Fechas reales de vendedores (f040)...", end=" ", flush=True)
icur.execute(f"""
    SELECT vertr, eintrdat, austrdat
    FROM f040
    WHERE firma = {FIRMA}
""")
f040_dates = {}
for row in icur.fetchall():
    try:
        vid = int(row[0])
    except (TypeError, ValueError):
        continue
    eintr = row[1]
    austr = row[2]
    # pyodbc devuelve date objects o None; convertir a string ISO
    def _to_iso(d):
        if not d:
            return None
        s = str(d)[:10]
        # Descartar fechas inválidas (año 0001, 1900, etc.)
        if s[:4] in ("0001", "0000", "1900"):
            return None
        return s
    eintr_str = _to_iso(eintr)
    austr_str = _to_iso(austr)
    if eintr_str:
        f040_dates[vid] = {"eintrdat": eintr_str, "austrdat": austr_str}
print(f"OK — {len(f040_dates)} registros en f040")

# ── 1. Clientes nuevos desde sbas (primera venta del vendedor a ese cliente) ──
# Más confiable que adrchr.erfuser que almacena username de texto, no vertr1.
# "Nuevo" = primer mes en que vertr1 vendió a kdnr (dentro del período analizado).
print("\n[1/4] Clientes nuevos (primera venta en sbas)...", end=" ", flush=True)
# Buscamos la primera aparición histórica de cada (vertr1, kdnr)
# ya cargada en el paso 2; se calcula en Python al procesar historial.
nuevos_data = {}  # se completará al procesar historial en el paso 2
print("OK — se calculará al procesar sbas")

# ── 2. Historial de ventas (sbas) — para balanza, ticket, productos ────────────
# Necesitamos 12 meses extra de historia para detectar reactivados y perdidos.
fecha_historico = hoy - timedelta(days=(MESES_ATRAS + 13) * 30)
anio_hist       = fecha_historico.year

print(f"[2/4] Historial sbas (desde {anio_hist})...", end=" ", flush=True)
icur.execute(f"""
    SELECT vertr1, kdnr, bujahr, bumonat, SUM(netwert), COUNT(artnr)
    FROM sbas
    WHERE firma = {FIRMA}
      AND bujahr >= {anio_hist}
      AND vertr1 IN {IN_ACTIVOS}
    GROUP BY 1, 2, 3, 4
    ORDER BY 1, 2, 3, 4
""")

historial   = defaultdict(lambda: defaultdict(list))  # [vid][cli] = [(anio,mes),...]
ticket_data = defaultdict(lambda: {"importe": 0.0, "clientes": set(), "lineas": 0})

total_rows = 0
for row in icur.fetchall():
    vid, cli, anio, mes, neto, lineas = row
    vid, cli, anio, mes = int(vid), int(cli), int(anio), int(mes)
    historial[vid][cli].append((anio, mes))
    if (anio * 12 + mes) >= (anio_inicio * 12 + mes_inicio):
        k = (vid, anio, mes)
        ticket_data[k]["importe"]  += float(neto or 0)
        ticket_data[k]["clientes"].add(cli)
        ticket_data[k]["lineas"]   += int(lineas or 0)
    total_rows += 1

for vid in historial:
    for cli in historial[vid]:
        historial[vid][cli].sort()
        # Primera venta de este vendedor a este cliente
        a_first, m_first = historial[vid][cli][0]
        if (a_first * 12 + m_first) >= (anio_inicio * 12 + mes_inicio):
            k = (vid, a_first, m_first)
            nuevos_data[k] = nuevos_data.get(k, 0) + 1

print(f"OK — {total_rows:,} filas, {sum(nuevos_data.values())} clientes nuevos detectados")

# ── 3. Calcular balanza ────────────────────────────────────────────────────────
print("[3/4] Calculando reactivados / perdidos...", end=" ", flush=True)

def meses_diff(a1, m1, a2, m2):
    return (a2 * 12 + m2) - (a1 * 12 + m1)

balanza_data = defaultdict(lambda: {"reactivados": 0, "perdidos": 0})

for vid, clientes in historial.items():
    for cli, meses_venta in clientes.items():
        for i, (anio, mes) in enumerate(meses_venta):
            if (anio * 12 + mes) < (anio_inicio * 12 + mes_inicio):
                continue
            k = (vid, anio, mes)
            # Reactivado: venta este mes y la anterior fue 12+ meses antes
            if i > 0:
                a_prev, m_prev = meses_venta[i - 1]
                if meses_diff(a_prev, m_prev, anio, mes) >= 12:
                    balanza_data[k]["reactivados"] += 1

        # Perdido: cuando se cumplen 12 meses desde la última venta
        if meses_venta:
            a_last, m_last = meses_venta[-1]
            m_p = m_last + 12
            a_p = a_last + (m_p - 1) // 12
            m_p = ((m_p - 1) % 12) + 1
            k_p = (vid, a_p, m_p)
            if (a_p * 12 + m_p) >= (anio_inicio * 12 + mes_inicio):
                # Solo cuenta si el cliente había sido activo (no es su primera y única venta
                # hace 12 meses sin historial previo — igual lo contamos, el usuario definió así)
                balanza_data[k_p]["perdidos"] += 1

print(f"OK — {len(balanza_data)} filas")

# ── [3b] Plan de ventas y clientes activos (vplan) ────────────────────────────
print("[3b/4] Plan de ventas vplan...", end=" ", flush=True)
vplan_data = {}
try:
    icur.execute(f"""
        SELECT vertr, bujahr, bumonat, planums, planumsk, aktivkd
        FROM vplan
        WHERE firma = {FIRMA}
          AND bujahr >= {anio_inicio}
          AND vertr IN {IN_ACTIVOS}
    """)
    for row in icur.fetchall():
        try:
            vid_v, anio_v, mes_v, planums, planumsk, aktivkd = row
            vid_v = int(vid_v); anio_v = int(anio_v); mes_v = int(mes_v)
            vplan_data[(vid_v, anio_v, mes_v)] = {
                "plan":             float(planums  or 0),
                "plan_cobranza":    float(planumsk or 0),
                "clientes_activos": int(aktivkd   or 0),
            }
        except (TypeError, ValueError):
            continue
    print(f"OK — {len(vplan_data)} filas")
except Exception as e:
    print(f"AVISO: no se pudo leer vplan ({e})")

# ── [3b2/4] Portfolio total por vendedor (kund) ───────────────────────────────
print("[3b2/4] Portfolio de clientes por vendedor (kund)...", end=" ", flush=True)
kund_total = {}  # vid → total_clientes en cartera
try:
    icur.execute(f"""
        SELECT vertr1, COUNT(kdnr)
        FROM kund
        WHERE firma = {FIRMA}
          AND vertr1 IN {IN_ACTIVOS}
        GROUP BY 1
    """)
    for row in icur.fetchall():
        try:
            kund_total[int(row[0])] = int(row[1])
        except (TypeError, ValueError):
            continue
    print(f"OK — {len(kund_total)} vendedores en kund")
except Exception as e:
    print(f"AVISO: no se pudo leer kund ({e})")

# ── [3b3/4] Días con venta por vendedor/mes (sbas, campo fecha auto-detectado) ─
print("[3b3/4] Días con venta (sbas)...", end=" ", flush=True)
dias_con_venta = {}  # (vid, anio, mes) → int
_sbas_date_field = None
for _campo in ("budat", "belegdat", "erfdat", "liefdat", "dat", "fdat"):
    try:
        icur.execute(f"SELECT FIRST 1 {_campo} FROM sbas WHERE firma = {FIRMA}")
        icur.fetchone()
        _sbas_date_field = _campo
        break
    except Exception:
        continue

if _sbas_date_field:
    try:
        icur.execute(f"""
            SELECT vertr1, bujahr, bumonat, {_sbas_date_field}
            FROM sbas
            WHERE firma = {FIRMA}
              AND bujahr >= {anio_inicio}
              AND vertr1 IN {IN_ACTIVOS}
              AND {_sbas_date_field} IS NOT NULL
        """)
        from collections import defaultdict as _dd
        _days_set = _dd(set)
        for row in icur.fetchall():
            try:
                vid_d, anio_d, mes_d, fecha_d = row
                _days_set[(int(vid_d), int(anio_d), int(mes_d))].add(str(fecha_d)[:10])
            except (TypeError, ValueError):
                continue
        for k, dset in _days_set.items():
            dias_con_venta[k] = len(dset)
        print(f"OK — campo '{_sbas_date_field}', {len(dias_con_venta)} filas")
    except Exception as e:
        print(f"AVISO: no se pudo leer días de sbas ({e}) — dias_venta_cero quedará en 0")
else:
    print("AVISO: no se encontró campo de fecha en sbas — dias_venta_cero quedará en 0")

# ── [3b4/4] Días hábiles por mes (works_days_log) ────────────────────────────
print("[3b4/4] Días hábiles (works_days_log)...", end=" ", flush=True)
dias_habiles = {}  # (anio, mes) → int
try:
    icur.execute("""
        SELECT YEAR(fecha), MONTH(fecha), COUNT(fecha)
        FROM works_days_log
        WHERE fecha >= ?
        GROUP BY 1, 2
    """, fecha_desde_dt)
    for row in icur.fetchall():
        try:
            dias_habiles[(int(row[0]), int(row[1]))] = int(row[2])
        except (TypeError, ValueError):
            continue
    print(f"OK — {len(dias_habiles)} meses cargados")
except Exception as e:
    print(f"AVISO: no se pudo leer works_days_log ({e}) — se usará 20 días/mes por defecto")

icon.close()

todas_keys = set(nuevos_data) | set(balanza_data) | set(ticket_data)
print(f"\nTotal filas a sincronizar: {len(todas_keys)}")

if DRY_RUN:
    print("\n--- DRY RUN: muestra (primeras 20 filas) ---")
    print(f"  {'Vend':>6}  {'Mes':>7}  {'Nuev':>4}  {'Reac':>4}  {'Perd':>4}  {'Bal':>4}  {'Ticket':>8}  {'Prods':>5}")
    for k in sorted(todas_keys)[:20]:
        vid, anio, mes = k
        n   = nuevos_data.get(k, 0)
        b   = balanza_data.get(k, {"reactivados": 0, "perdidos": 0})
        re  = b["reactivados"]
        pe  = b["perdidos"]
        td  = ticket_data.get(k, {})
        imp = td.get("importe", 0)
        nc  = len(td.get("clientes", set()))
        ticket = round(imp / nc) if nc else 0
        lineas = td.get("lineas", 0)
        print(f"  {vid:>6}  {anio}/{mes:02d}  {n:>4}  {re:>4}  {pe:>4}  {n+re-pe:>4}  {ticket:>8}  {lineas:>6}")
    print("\nDRY RUN completado. Sin cambios en SQLite.")
    sys.exit(0)

# ── SQLite ─────────────────────────────────────────────────────────────────────
print("\nConectando a SQLite...", end=" ", flush=True)
lcon = sqlite3.connect(DB_PATH)
lcur = lcon.cursor()
print("OK")

lcur.execute("""
    CREATE TABLE IF NOT EXISTS balanza_clientes (
        id_vendedor          INTEGER NOT NULL,
        anio                 INTEGER NOT NULL,
        mes                  INTEGER NOT NULL,
        clientes_nuevos      INTEGER DEFAULT 0,
        clientes_reactivados INTEGER DEFAULT 0,
        clientes_perdidos    INTEGER DEFAULT 0,
        balanza              INTEGER DEFAULT 0,
        ticket_promedio      REAL    DEFAULT 0,
        productos_distintos  INTEGER DEFAULT 0,
        PRIMARY KEY (id_vendedor, anio, mes)
    )
""")
lcon.commit()

upsert_sql = """
    INSERT INTO balanza_clientes
        (id_vendedor, anio, mes,
         clientes_nuevos, clientes_reactivados, clientes_perdidos, balanza,
         ticket_promedio, productos_distintos)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (id_vendedor, anio, mes) DO UPDATE SET
        clientes_nuevos      = excluded.clientes_nuevos,
        clientes_reactivados = excluded.clientes_reactivados,
        clientes_perdidos    = excluded.clientes_perdidos,
        balanza              = excluded.balanza,
        ticket_promedio      = excluded.ticket_promedio,
        productos_distintos  = excluded.productos_distintos
"""

insertados = 0
for k in sorted(todas_keys):
    vid, anio, mes = k
    n   = nuevos_data.get(k, 0)
    b   = balanza_data.get(k, {"reactivados": 0, "perdidos": 0})
    re  = b["reactivados"]
    pe  = b["perdidos"]
    td  = ticket_data.get(k, {})
    imp = td.get("importe", 0)
    nc  = len(td.get("clientes", set()))
    ticket = round(imp / nc, 0) if nc else 0
    lineas = td.get("lineas", 0)

    lcur.execute(upsert_sql, (
        vid, anio, mes,
        n, re, pe, n + re - pe,
        ticket, lineas,
    ))
    insertados += 1

lcon.commit()

# ── [3c] Actualizar ventas_mensual con datos reales de Informix ───────────────
print("\n[3c/4] Actualizando ventas_mensual (venta_total + plan + clientes)...", end=" ", flush=True)
from datetime import date as _date

# Fechas de ingreso para calcular mes_numero
lcur.execute("SELECT id_vendedor, fecha_ingreso FROM vendedores")
fecha_ingreso_map = {r[0]: r[1] for r in lcur.fetchall()}

lcur.execute("""
    CREATE TABLE IF NOT EXISTS ventas_mensual (
        id_vendedor        INTEGER NOT NULL,
        anio               INTEGER NOT NULL,
        mes                INTEGER NOT NULL,
        mes_numero         INTEGER DEFAULT 0,
        dias_trabajados    INTEGER DEFAULT 20,
        dias_venta_cero    INTEGER DEFAULT 0,
        venta_total        REAL DEFAULT 0,
        plan               REAL DEFAULT 0,
        pct_plan           REAL DEFAULT 0,
        clientes_activos   INTEGER DEFAULT 0,
        clientes_inactivos INTEGER DEFAULT 0,
        clientes_nuevos    INTEGER DEFAULT 0,
        total_clientes     INTEGER DEFAULT 0,
        cobranza_teorica   REAL DEFAULT 0,
        cobranza_real      REAL DEFAULT 0,
        pct_cobranza       REAL DEFAULT 0,
        dias_cobro         REAL DEFAULT 0,
        cheques_rechazados INTEGER DEFAULT 0,
        PRIMARY KEY (id_vendedor, anio, mes)
    )
""")
# Si la tabla fue creada por el simulador sin PRIMARY KEY compuesto, agregar el índice único
lcur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_vm_unique
    ON ventas_mensual (id_vendedor, anio, mes)
""")
# Si la tabla existía con esquema viejo, agregar columnas nuevas que puedan faltar
for _col, _def in [
    ("clientes_inactivos", "INTEGER DEFAULT 0"),
    ("total_clientes",     "INTEGER DEFAULT 0"),
    ("dias_venta_cero",    "INTEGER DEFAULT 0"),
    ("cobranza_teorica",   "REAL DEFAULT 0"),
]:
    try:
        lcur.execute(f"ALTER TABLE ventas_mensual ADD COLUMN {_col} {_def}")
    except Exception:
        pass  # columna ya existe
lcon.commit()

vm_upsert = """
    INSERT INTO ventas_mensual
        (id_vendedor, anio, mes, mes_numero,
         venta_total, plan, pct_plan,
         clientes_activos, clientes_inactivos, total_clientes,
         clientes_nuevos, dias_venta_cero, cobranza_teorica)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (id_vendedor, anio, mes) DO UPDATE SET
        mes_numero         = excluded.mes_numero,
        venta_total        = excluded.venta_total,
        plan               = excluded.plan,
        pct_plan           = excluded.pct_plan,
        clientes_activos   = excluded.clientes_activos,
        clientes_inactivos = excluded.clientes_inactivos,
        total_clientes     = excluded.total_clientes,
        clientes_nuevos    = excluded.clientes_nuevos,
        dias_venta_cero    = excluded.dias_venta_cero,
        cobranza_teorica   = excluded.cobranza_teorica
"""

# Solo el período de análisis (sin el extra histórico para balanza)
todas_keys_vm = {k for k in (set(ticket_data) | set(vplan_data))
                 if (k[1] * 12 + k[2]) >= (anio_inicio * 12 + mes_inicio)}

vm_count = 0
for k in sorted(todas_keys_vm):
    vid, anio, mes = k
    td  = ticket_data.get(k, {})
    vp  = vplan_data.get(k, {})
    venta_total = td.get("importe", 0)
    plan        = vp.get("plan", 0)
    # clientes_activos: clientes que facturaron este mes (fuente real: sbas)
    clientes_activos   = len(td.get("clientes", set()))
    # total_clientes: cartera asignada al vendedor (fuente: kund, snapshot actual)
    total_clientes     = kund_total.get(vid, max(clientes_activos, 1))
    clientes_inactivos = max(0, total_clientes - clientes_activos)
    pct_plan           = round(venta_total / plan * 100, 1) if plan > 0 else 0.0
    clientes_nuevos    = nuevos_data.get(k, 0)

    # dias_venta_cero: días hábiles sin ninguna factura (fuente: sbas.budat + works_days_log)
    dcv             = dias_con_venta.get(k, None)
    dh              = dias_habiles.get((anio, mes), 20)
    dias_venta_cero = max(0, dh - dcv) if dcv is not None else 0

    # cobranza_teorica desde vplan.planumsk (plan de cobranza oficial)
    plan_cobranza = vp.get("plan_cobranza", 0)

    fi_str = fecha_ingreso_map.get(vid)
    mes_numero = 0
    if fi_str:
        try:
            fi = _date.fromisoformat(str(fi_str)[:10])
            mes_numero = max(1, (anio - fi.year) * 12 + (mes - fi.month) + 1)
        except Exception:
            pass

    lcur.execute(vm_upsert, (
        vid, anio, mes, mes_numero,
        round(venta_total, 2), round(plan, 2), pct_plan,
        clientes_activos, clientes_inactivos, total_clientes,
        clientes_nuevos, dias_venta_cero, round(plan_cobranza, 2),
    ))
    vm_count += 1

lcon.commit()
print(f"OK — {vm_count} filas en ventas_mensual")

# ── [4/4] Actualizar fechas reales de vendedores desde f040 ──────────────────
print("\n[4/4] Actualizando fechas ingreso/egreso en vendedores (f040)...", end=" ", flush=True)
actualiz = 0
for vid, fechas in f040_dates.items():
    eintr = fechas["eintrdat"]
    austr = fechas["austrdat"]
    activo = 0 if austr else 1
    lcur.execute("""
        UPDATE vendedores
        SET fecha_ingreso = ?, fecha_egreso = ?, activo = ?
        WHERE id_vendedor = ?
    """, (eintr, austr, activo, vid))
    if lcur.rowcount > 0:
        actualiz += 1
lcon.commit()
print(f"OK — {actualiz} vendedores actualizados")

# ── [5/4] Recalcular riesgo_base por grupo desde datos reales ─────────────────
# riesgo_base = % de vendedores del grupo que se fueron en menos de 6 meses
print("\n[5/4] Recalculando riesgo_base de grupos...", end=" ", flush=True)
lcur.execute("SELECT id_grupo FROM grupos")
grupos_ids = [r[0] for r in lcur.fetchall()]
actualizados_riesgo = 0
for gid in grupos_ids:
    lcur.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE
                   WHEN activo = 0
                     AND fecha_egreso IS NOT NULL
                     AND fecha_egreso != fecha_ingreso
                     AND CAST((julianday(fecha_egreso) - julianday(fecha_ingreso)) / 30.0 AS INTEGER) < 6
                   THEN 1 ELSE 0
               END) AS bajas_rapidas
        FROM vendedores
        WHERE id_grupo = ?
          AND fecha_ingreso IS NOT NULL
          AND (fecha_egreso IS NULL OR fecha_egreso != fecha_ingreso)
          AND id_vendedor != 9800
    """, (gid,))
    row = lcur.fetchone()
    total         = row[0] or 0
    bajas_rapidas = row[1] or 0
    riesgo = round(bajas_rapidas / total, 3) if total > 0 else 0.5
    lcur.execute("UPDATE grupos SET riesgo_base = ? WHERE id_grupo = ?", (riesgo, gid))
    actualizados_riesgo += lcur.rowcount
lcon.commit()
print(f"OK — {actualizados_riesgo} grupos actualizados con datos reales")

lcon.close()

print(f"\n✓ {insertados} filas insertadas/actualizadas en balanza_clientes")
pos = sum(1 for k in todas_keys if
          nuevos_data.get(k, 0)
          + balanza_data.get(k, {"reactivados":0})["reactivados"]
          - balanza_data.get(k, {"perdidos":0})["perdidos"] > 0)
neg = sum(1 for k in todas_keys if
          nuevos_data.get(k, 0)
          + balanza_data.get(k, {"reactivados":0})["reactivados"]
          - balanza_data.get(k, {"perdidos":0})["perdidos"] < 0)
print(f"  Meses con balanza positiva: {pos}")
print(f"  Meses con balanza negativa: {neg}")

# ── Alertas por email ──────────────────────────────────────────────────────────
if not DRY_RUN:
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from score_engine import calcular_scores
        from alertas import cargar_estado, detectar_nuevos_criticos, guardar_estado, enviar_email

        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pwd  = os.getenv("SMTP_PWD", "")
        alert_to  = [e.strip() for e in os.getenv("ALERT_TO", "").split(",") if e.strip()]

        if smtp_user and smtp_pwd and alert_to:
            print("\n─" * 33)
            print("ALERTAS EMAIL")
            scores = calcular_scores(meses_tendencia=3)
            estado = cargar_estado()
            nuevos = detectar_nuevos_criticos(scores, estado)

            if nuevos.empty:
                print("  Sin nuevos vendedores críticos — no se envía email.")
            else:
                print(f"  {len(nuevos)} nuevo(s) crítico(s). Enviando email a {alert_to}...")
                enviar_email({
                    "host":     "smtp.office365.com",
                    "port":     587,
                    "user":     smtp_user,
                    "password": smtp_pwd,
                    "to":       alert_to,
                }, nuevos)
                print("  Email enviado OK.")

            guardar_estado(scores)
        else:
            print("\n  (Alertas email no configuradas — agregar SMTP_USER/SMTP_PWD/ALERT_TO al .env)")
    except Exception as e:
        print(f"\n  AVISO: Error en alertas email: {e}")

print("\nListo. Ejecutá el score engine para ver las nuevas señales.")
