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

# ── Explorar columnas de f040 via API de metadatos pyodbc ────────────────────
print("\nColumnas disponibles en f040:")
try:
    cols_f040 = [c.column_name.lower() for c in icur.columns(table="f040")]
    print(f"  {cols_f040}")
    if not cols_f040:
        raise ValueError("pyodbc no devolvió columnas para f040")
except Exception as e:
    print(f"  ERROR al leer metadatos: {e}")
    print("  Usando columnas mínimas conocidas")
    cols_f040 = ["vertr", "eintrdat", "austrdat"]
print(f"  Total columnas: {len(cols_f040)}")

# ── Pre-cargar mapa vertr→nombre y set de vertr activos ──────────────────────
# vertr_activo: vertr con austrdat NULL (sigue trabajando). Se usa para validar
# que un supervisor/director esté activo, igual que el `austrdat IS NULL` del
# reporte de jerarquía de Access.
vertr_nombre = {}
vertr_activo = set()
if "name1" in cols_f040:
    try:
        icur.execute(f"SELECT vertr, name1, austrdat FROM f040 WHERE firma = {FIRMA}")
        for row in icur.fetchall():
            try:
                _vid = int(row[0])
            except (TypeError, ValueError):
                continue
            vertr_nombre[_vid] = str(row[1]).strip() if row[1] else ""
            # austrdat válido (no NULL, no fecha basura) ⇒ egresado ⇒ NO activo
            _aus = str(row[2])[:10] if row[2] else None
            if not _aus or _aus[:4] in ("0001", "0000", "1900"):
                vertr_activo.add(_vid)
    except Exception:
        pass

# ── Leer todos los vendedores de f040 ─────────────────────────────────────────
print("\nLeyendo vendedores de f040...", end=" ", flush=True)

def _to_iso(d):
    if not d:
        return None
    s = str(d)[:10]
    if s[:4] in ("0001", "0000", "1900"):
        return None
    return s

# Detectar campos disponibles (nombres comunes en Würth Informix)
campo_nombre     = next((c for c in cols_f040 if c in ("name1","vertrname","nam","name")), None)
campo_grupo_id   = next((c for c in cols_f040 if c in ("vgrp","gebiet","bezirk","grp","gruppe","grupid")), None)
campo_grupo_nom  = next((c for c in cols_f040 if c in ("gebinam","gebietname","grpnam","grupnom")), None)
# zone/region son códigos internos (ej: "SUR1500"), no el nombre de grupo visible.
# Si no hay campo específico de nombre, se usa "Grupo {vgrp}" más abajo.
campo_supervisor = next((c for c in cols_f040 if c in ("bvertr","vorgesetzt","supervisor","supvertr")), None)
# zone='TVTAS' es la condición real para Televentas en Würth Argentina.
# vart=2 es un indicador secundario que puede estar mal cargado en el alta
# (ej: vendedores de campo con vart=2 por error en el ERP).
campo_zona       = next((c for c in cols_f040 if c in ("zone","zona")), None)
campo_tipo       = next((c for c in cols_f040 if c in ("vart","vertrtyp","typ","tipo","kategorie")), None)
# kz3 = ID (vertr) del director al que reporta el vendedor/supervisor.
campo_director   = next((c for c in cols_f040 if c in ("kz3","director","kzdirektor")), None)

# Cuentas especiales que NO son vendedores reales (casa central, dummies). Se
# excluyen igual que en el reporte de jerarquía de Access (bvertr = vertr).
VERTR_EXCLUIDOS = {1500, 7777, 9499}

# Correcciones manuales de tipo cuando el ERP tiene el dato mal cargado.
# vart=2 y zone≠TVTAS son igual en Viajantes y Televentas de campo, así que
# no hay forma automática de distinguirlos. Se documenta el error acá hasta
# que el área de sistemas corrija el alta en Informix.
TIPO_MANUAL: dict[int, str] = {
    5082: "Viajante",  # Pozzolo Nicolas Alejandro   - Grupo 103, error de alta en ERP
    5088: "Viajante",  # Robles Sosa Santiago Emanuel - Grupo 103, error de alta en ERP
    5094: "Viajante",  # Ratto Enrique Jose Maria     - Grupo 103, error de alta en ERP
}

print(f"\n  nombre={campo_nombre}  grupo_id={campo_grupo_id}  grupo_nom={campo_grupo_nom}  superv={campo_supervisor}  zona={campo_zona}  tipo={campo_tipo}  director={campo_director}")

# Construir SELECT dinámico
select_campos = ["vertr", "eintrdat", "austrdat"]
if campo_nombre:     select_campos.append(campo_nombre)
if campo_grupo_id:   select_campos.append(campo_grupo_id)
if campo_grupo_nom:  select_campos.append(campo_grupo_nom)
if campo_supervisor: select_campos.append(campo_supervisor)
if campo_zona:       select_campos.append(campo_zona)   # antes de vart: se lee en orden
if campo_tipo:       select_campos.append(campo_tipo)
if campo_director:   select_campos.append(campo_director)

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

    nombre_raw = str(row[idx]).strip() if campo_nombre and idx < len(row) and row[idx] else ""
    nombre = nombre_raw if nombre_raw else f"ID {vid}"
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

    # Si hay id_grupo pero no nombre, construir "Grupo {id_grupo}"
    if id_grupo:
        if not nombre_grupo:
            nombre_grupo = f"Grupo {id_grupo}"
        if id_grupo not in grupos_set:
            grupos_set[id_grupo] = nombre_grupo

    supervisor_raw = None
    if campo_supervisor and idx < len(row):
        supervisor_raw = str(row[idx]).strip() if row[idx] else None
        idx += 1
    # bvertr es ID numérico del supervisor → resolver nombre desde vertr_nombre
    sup_id = None
    if supervisor_raw:
        try:
            sup_id = int(supervisor_raw)
            supervisor = vertr_nombre.get(sup_id, supervisor_raw)
        except (TypeError, ValueError):
            supervisor = supervisor_raw
    else:
        supervisor = None
    # Un vendedor ES supervisor si su bvertr apunta a sí mismo (bvertr = vertr),
    # NO es una cuenta especial y está activo (austrdat NULL). Réplica exacta del
    # reporte de jerarquía de Access.
    es_supervisor = (
        sup_id is not None and sup_id == vid
        and vid not in VERTR_EXCLUIDOS
        and vid in vertr_activo
    )

    zona_raw = ""
    if campo_zona and idx < len(row):
        zona_raw = str(row[idx]).strip() if row[idx] else ""
        idx += 1

    tipo = "Viajante"
    if zona_raw == "TVTAS":
        # Condición real en Würth Argentina: zone='TVTAS' identifica Televentas.
        # Tiene prioridad sobre vart porque vart puede estar mal cargado en el alta.
        tipo = "Televentas"
        if campo_tipo and idx < len(row):
            idx += 1  # consumir vart igualmente para no correr el índice
    elif campo_tipo and idx < len(row):
        raw_tipo = str(row[idx]).strip() if row[idx] else ""
        # Fallback: vart=2 como Televentas si zone no existe en f040 o está vacío.
        if raw_tipo in ("2", "T", "TV", "Televentas", "I", "Innendienst"):
            tipo = "Televentas"
        idx += 1   # avanzar SIEMPRE: si no, el director leería esta misma columna

    # Override manual para errores de alta en el ERP que no se pueden detectar
    # automáticamente (mismo vart=2 y zona que Televentas reales de campo).
    if vid in TIPO_MANUAL:
        tipo = TIPO_MANUAL[vid]

    # kz3 = ID (vertr) del director → resolver nombre desde vertr_nombre.
    # Solo si el director NO es cuenta especial y está activo (mismo criterio que
    # los supervisores): si no, un kz3 apuntando a 1500/egresado metía un
    # "director" inválido (ej: Kalpokas 1500).
    director = None
    if campo_director and idx < len(row):
        director_raw = str(row[idx]).strip() if row[idx] else None
        idx += 1
        if director_raw:
            try:
                dir_id = int(director_raw)
                if dir_id not in VERTR_EXCLUIDOS and dir_id in vertr_activo:
                    director = vertr_nombre.get(dir_id, director_raw)
            except (TypeError, ValueError):
                director = director_raw  # kz3 no numérico: dejar el valor crudo

    eintr_str = _to_iso(eintrdat)
    austr_str = _to_iso(austrdat)
    activo    = 0 if austr_str else 1

    if not eintr_str:
        continue  # sin fecha de ingreso, no tiene sentido
    if vid in VERTR_EXCLUIDOS:
        continue  # cuenta especial, no es un vendedor real

    vendedores_rows.append((
        vid, tipo, id_grupo, nombre_grupo or (f"Grupo {id_grupo}" if id_grupo else "Sin grupo"),
        supervisor or "", nombre or f"ID {vid}", eintr_str, austr_str, None, activo,
        director or "", 1 if es_supervisor else 0,
    ))

print(f"OK — {len(vendedores_rows)} vendedores, {len(grupos_set)} grupos")
icon.close()

# ── Mostrar muestra ────────────────────────────────────────────────────────────
print("\nMuestra (primeros 5):")
for r in vendedores_rows[:5]:
    vid, tipo, gid, gnom, superv, nombre, fi, fe, _, activo, director, es_sup = r
    rol = "SUPERV" if es_sup else "vend"
    print(f"  {vid}  {nombre[:28]:<28}  {gnom:<18}  {rol:<6}  dir={director or '—'}")

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
    activo        INTEGER DEFAULT 1,
    director      TEXT,
    es_supervisor INTEGER DEFAULT 0
);

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

# ── Migración: agregar columnas nuevas a bases ya existentes ───────────────────
# CREATE TABLE IF NOT EXISTS no toca una tabla que ya existe con el esquema viejo.
# Si la base venía sin director/es_supervisor, las agregamos acá (idempotente).
def _asegurar_columna(tabla, columna, definicion):
    cols = [r[1] for r in cur.execute(f"PRAGMA table_info({tabla})")]
    if columna not in cols:
        cur.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")
        print(f"  + columna {tabla}.{columna}")

print("Verificando esquema...", flush=True)
_asegurar_columna("vendedores", "director",      "TEXT")
_asegurar_columna("vendedores", "es_supervisor", "INTEGER DEFAULT 0")
_asegurar_columna("grupos",     "supervisor",    "TEXT")
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
         fecha_ingreso, fecha_egreso, motivo_egreso, activo, director, es_supervisor)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (id_vendedor) DO UPDATE SET
        tipo          = excluded.tipo,
        id_grupo      = excluded.id_grupo,
        nombre_grupo  = excluded.nombre_grupo,
        supervisor    = excluded.supervisor,
        nombre        = excluded.nombre,
        fecha_ingreso = excluded.fecha_ingreso,
        fecha_egreso  = excluded.fecha_egreso,
        activo        = excluded.activo,
        director      = excluded.director,
        es_supervisor = excluded.es_supervisor
""", vendedores_rows)
con.commit()
print("OK")

# ── Completar grupos.supervisor desde los vendedores ──────────────────────────
# Cada grupo toma como supervisor el nombre del supervisor más frecuente entre
# sus vendedores (resuelto de bvertr). Así la tabla grupos queda consistente con
# la jerarquía real, no solo con el id de zona.
print("Asignando supervisor a cada grupo...", end=" ", flush=True)
cur.execute("""
    UPDATE grupos
    SET supervisor = (
        SELECT v.supervisor
        FROM vendedores v
        WHERE v.id_grupo = grupos.id_grupo
          AND v.supervisor IS NOT NULL AND v.supervisor <> ''
        GROUP BY v.supervisor
        ORDER BY COUNT(*) DESC
        LIMIT 1
    )
""")
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
