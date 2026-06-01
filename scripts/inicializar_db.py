"""
inicializar_db.py
------------------
Crea el schema de wurth.db desde cero y lo pobla con datos reales de Informix.
Ejecutar UNA VEZ cuando la base no existe o quedó vacía.

Ejecutar con Python 32 bits:
    C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe scripts\\inicializar_db.py
"""

import sys
import os
import sqlite3
import pyodbc

DSN_INFORMIX = "MSPA"
DB_PATH      = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
FIRMA        = 1

print("=" * 65)
print("INICIALIZACION wurth.db desde Informix")
print(f"  DB local: {DB_PATH}")
print("=" * 65)

# ── Conectar a Informix ───────────────────────────────────────────────────────
print("\nConectando a Informix...", end=" ", flush=True)
try:
    icon = pyodbc.connect(f"DSN={DSN_INFORMIX}", timeout=15)
    icur = icon.cursor()
    print("OK")
except Exception as e:
    print(f"FALLÓ: {e}")
    sys.exit(1)

# ── Explorar columnas de f040 via catálogo del sistema ───────────────────────
print("\nColumnas disponibles en f040:")
try:
    icur.execute("""
        SELECT c.colname
        FROM syscolumns c
        JOIN systables t ON c.tabid = t.tabid
        WHERE t.tabname = 'f040'
        ORDER BY c.colno
    """)
    cols_f040 = [row[0].lower() for row in icur.fetchall()]
    print(f"  {cols_f040}")
    if not cols_f040:
        raise ValueError("No se encontraron columnas para f040 en el catálogo")
except Exception as e:
    print(f"  ERROR al leer catálogo: {e}")
    print("  Intentando detección directa...")
    try:
        icur.execute(f"SELECT vertr, eintrdat, austrdat FROM f040 WHERE firma = {FIRMA} AND ROWNUM = 1")
    except Exception:
        try:
            icur.execute(f"SELECT FIRST 1 vertr, eintrdat, austrdat FROM f040 WHERE firma = {FIRMA}")
        except Exception as e2:
            print(f"  No se puede acceder a f040: {e2}")
            sys.exit(1)
    cols_f040 = ["vertr", "eintrdat", "austrdat"]
    print(f"  Usando columnas mínimas: {cols_f040}")

# ── Leer todos los vendedores de f040 ─────────────────────────────────────────
print("\nLeyendo vendedores de f040...", end=" ", flush=True)

def _to_iso(d):
    if not d:
        return None
    s = str(d)[:10]
    if s[:4] in ("0001", "0000", "1900"):
        return None
    return s

# Detectar campos disponibles
campo_nombre     = next((c for c in cols_f040 if c in ("name1","vertrname","nam","name")), None)
campo_grupo_id   = next((c for c in cols_f040 if c in ("gebiet","bezirk","grp","gruppe","grupid")), None)
campo_grupo_nom  = next((c for c in cols_f040 if c in ("gebinam","gebietname","grpnam","grupnom")), None)
campo_supervisor = next((c for c in cols_f040 if c in ("vorgesetzt","supervisor","supvertr")), None)
campo_tipo       = next((c for c in cols_f040 if c in ("vertrtyp","typ","tipo","kategorie")), None)

print(f"\n  nombre={campo_nombre}  grupo_id={campo_grupo_id}  grupo_nom={campo_grupo_nom}  superv={campo_supervisor}  tipo={campo_tipo}")

# Construir SELECT dinámico
select_campos = ["vertr", "eintrdat", "austrdat"]
if campo_nombre:     select_campos.append(campo_nombre)
if campo_grupo_id:   select_campos.append(campo_grupo_id)
if campo_grupo_nom:  select_campos.append(campo_grupo_nom)
if campo_supervisor: select_campos.append(campo_supervisor)
if campo_tipo:       select_campos.append(campo_tipo)

icur.execute(f"""
    SELECT {', '.join(select_campos)}
    FROM f040
    WHERE firma = {FIRMA}
""")

vendedores_rows = []
grupos_set = {}  # id_grupo -> (nombre_grupo)

for row in icur.fetchall():
    idx = 0
    vertr    = row[idx]; idx += 1
    eintrdat = row[idx]; idx += 1
    austrdat = row[idx]; idx += 1

    try:
        vid = int(vertr)
    except (TypeError, ValueError):
        continue

    nombre     = str(row[idx]).strip() if campo_nombre     and idx < len(row) else f"ID {vid}"
    if campo_nombre: idx += 1

    id_grupo   = None
    if campo_grupo_id and idx < len(row):
        try:
            id_grupo = int(row[idx])
        except (TypeError, ValueError):
            id_grupo = None
        idx += 1

    nombre_grupo = None
    if campo_grupo_nom and idx < len(row):
        nombre_grupo = str(row[idx]).strip() if row[idx] else None
        idx += 1

    if id_grupo and nombre_grupo:
        grupos_set[id_grupo] = nombre_grupo
    elif id_grupo and id_grupo not in grupos_set:
        grupos_set[id_grupo] = f"Grupo {id_grupo}"

    supervisor = None
    if campo_supervisor and idx < len(row):
        supervisor = str(row[idx]).strip() if row[idx] else None
        idx += 1

    tipo = "Viajante"
    if campo_tipo and idx < len(row):
        raw_tipo = str(row[idx]).strip() if row[idx] else ""
        if raw_tipo in ("T", "TV", "Televentas", "2"):
            tipo = "Televentas"

    eintr_str = _to_iso(eintrdat)
    austr_str = _to_iso(austrdat)
    activo    = 0 if austr_str else 1

    if not eintr_str:
        continue  # sin fecha de ingreso, no tiene sentido

    vendedores_rows.append((
        vid, tipo, id_grupo, nombre_grupo or (f"Grupo {id_grupo}" if id_grupo else "Sin grupo"),
        supervisor or "", nombre or f"ID {vid}", eintr_str, austr_str, None, activo
    ))

print(f"OK — {len(vendedores_rows)} vendedores, {len(grupos_set)} grupos")
icon.close()

# ── Mostrar muestra ────────────────────────────────────────────────────────────
print("\nMuestra (primeros 5):")
for r in vendedores_rows[:5]:
    vid, tipo, gid, gnom, superv, nombre, fi, fe, _, activo = r
    print(f"  {vid}  {nombre[:30]:<30}  {gnom:<20}  {fi}  {'activo' if activo else 'baja'}")

# ── Crear SQLite ──────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
print(f"\nCreando/conectando SQLite: {DB_PATH}...", end=" ", flush=True)
con = sqlite3.connect(DB_PATH)
cur = con.cursor()
print("OK")

cur.executescript("""
CREATE TABLE IF NOT EXISTS grupos (
    id_grupo     INTEGER PRIMARY KEY,
    nombre_grupo TEXT,
    supervisor   TEXT,
    riesgo_base  REAL DEFAULT 0.35
);

CREATE TABLE IF NOT EXISTS vendedores (
    id_vendedor  INTEGER PRIMARY KEY,
    tipo         TEXT,
    id_grupo     INTEGER,
    nombre_grupo TEXT,
    supervisor   TEXT,
    nombre       TEXT,
    fecha_ingreso TEXT,
    fecha_egreso  TEXT,
    motivo_egreso TEXT,
    activo        INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ventas_mensual (
    id_vendedor       INTEGER,
    anio              INTEGER,
    mes               INTEGER,
    mes_numero        INTEGER,
    venta_total       REAL DEFAULT 0,
    plan              REAL DEFAULT 0,
    pct_plan          REAL DEFAULT 0,
    clientes_activos  INTEGER DEFAULT 0,
    clientes_inactivos INTEGER DEFAULT 0,
    clientes_totales  INTEGER DEFAULT 0,
    clientes_nuevos   INTEGER DEFAULT 0,
    dias_venta_cero   INTEGER DEFAULT 0,
    plan_cobranza     REAL DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);

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
);

CREATE TABLE IF NOT EXISTS actividad_mensual (
    id_vendedor     INTEGER,
    anio            INTEGER,
    mes             INTEGER,
    llamadas        INTEGER DEFAULT 0,
    visitas         INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);

CREATE TABLE IF NOT EXISTS acompanamiento_mensual (
    id_vendedor     INTEGER,
    anio            INTEGER,
    mes             INTEGER,
    acompaniamientos INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);

CREATE TABLE IF NOT EXISTS ausencias_mensual (
    id_vendedor     INTEGER,
    anio            INTEGER,
    mes             INTEGER,
    dias_ausente    INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);

CREATE TABLE IF NOT EXISTS cobranza_mensual (
    id_vendedor      INTEGER,
    anio             INTEGER,
    mes              INTEGER,
    cobranza_real    REAL DEFAULT 0,
    cobranza_teorica REAL DEFAULT 0,
    pct_cobranza     REAL DEFAULT 0,
    dias_cobro       REAL DEFAULT 0,
    cheques_rechazados INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);
""")
con.commit()

# ── Insertar grupos ───────────────────────────────────────────────────────────
print(f"Insertando {len(grupos_set)} grupos...", end=" ", flush=True)
for gid, gnom in grupos_set.items():
    cur.execute("""
        INSERT INTO grupos (id_grupo, nombre_grupo, riesgo_base)
        VALUES (?, ?, 0.35)
        ON CONFLICT (id_grupo) DO UPDATE SET nombre_grupo = excluded.nombre_grupo
    """, (gid, gnom))
con.commit()
print("OK")

# ── Insertar vendedores ───────────────────────────────────────────────────────
print(f"Insertando {len(vendedores_rows)} vendedores...", end=" ", flush=True)
cur.executemany("""
    INSERT INTO vendedores
        (id_vendedor, tipo, id_grupo, nombre_grupo, supervisor, nombre,
         fecha_ingreso, fecha_egreso, motivo_egreso, activo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (id_vendedor) DO UPDATE SET
        fecha_ingreso = excluded.fecha_ingreso,
        fecha_egreso  = excluded.fecha_egreso,
        activo        = excluded.activo
""", vendedores_rows)
con.commit()
print("OK")

activos = sum(1 for r in vendedores_rows if r[9] == 1)
bajas   = sum(1 for r in vendedores_rows if r[9] == 0)
print(f"\nResumen:")
print(f"  Activos: {activos}")
print(f"  Bajas:   {bajas}")
print(f"  Grupos:  {len(grupos_set)}")
print(f"\nBase inicializada. Ahora ejecutar sincronizar_todo.bat para cargar ventas.")
con.close()
