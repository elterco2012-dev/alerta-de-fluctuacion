"""
intervenciones.py
-----------------
Registro y seguimiento de intervenciones sobre vendedores en riesgo.
Cierra el ciclo: alerta → acción → impacto medido.
"""

import sqlite3

import pandas as pd
from datetime import date, datetime

import score_engine


def get_connection():
    """Las intervenciones viven SIEMPRE en la SQLite local (data/wurth.db).

    No usa score_engine.get_connection(): esa función puede devolver una
    conexión a Informix si hay variables INFORMIX_* en .env, y este módulo
    escribe (CREATE TABLE / INSERT). Las bases de producción son solo lectura.
    """
    return sqlite3.connect(score_engine.DB_PATH)

TIPOS = [
    "Reunión 1:1",
    "Acompañamiento en campo",
    "Revisión de cartera",
    "Ajuste de objetivos",
    "Conversación motivacional",
    "Derivación a RRHH",
    "Cambio de zona",
    "Capacitación técnica",
    "Otro",
]


def _init_table():
    con = get_connection()
    con.execute("""
        CREATE TABLE IF NOT EXISTS intervenciones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            id_vendedor     INTEGER NOT NULL,
            fecha           TEXT NOT NULL,
            tipo            TEXT NOT NULL,
            supervisor      TEXT NOT NULL,
            score_inicial   REAL NOT NULL,
            nivel_inicial   TEXT NOT NULL,
            observaciones   TEXT DEFAULT '',
            FOREIGN KEY (id_vendedor) REFERENCES vendedores(id_vendedor)
        )
    """)
    con.commit()
    con.close()


_init_table()


def registrar(id_vendedor: int, tipo: str, supervisor: str,
              score_inicial: float, nivel_inicial: str,
              observaciones: str = "", fecha: str = None) -> int:
    """Guarda una intervención. Retorna el id generado."""
    fecha = fecha or date.today().isoformat()
    con = get_connection()
    cur = con.execute("""
        INSERT INTO intervenciones
            (id_vendedor, fecha, tipo, supervisor, score_inicial, nivel_inicial, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (id_vendedor, fecha, tipo, supervisor, score_inicial, nivel_inicial, observaciones))
    con.commit()
    new_id = cur.lastrowid
    con.close()
    return new_id


def obtener_todas() -> pd.DataFrame:
    """Retorna todas las intervenciones ordenadas por fecha desc."""
    try:
        _init_table()
        con = get_connection()
        df = pd.read_sql("""
            SELECT i.*, v.tipo as tipo_vendedor, v.nombre_grupo, v.supervisor as supervisor_zona,
                   v.activo, v.motivo_egreso
            FROM intervenciones i
            JOIN vendedores v ON i.id_vendedor = v.id_vendedor
            ORDER BY i.fecha DESC, i.id DESC
        """, con)
        con.close()
        return df
    except Exception:
        return pd.DataFrame()


def calcular_impacto(intervenciones: pd.DataFrame,
                     scores_actuales: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columna 'score_actual' e 'impacto' a cada intervención.
    impacto = score_inicial - score_actual (positivo = mejoró, negativo = empeoró).
    Si el vendedor ya no está activo, impacto = None y se marca como 'Baja'.
    """
    if intervenciones.empty:
        return intervenciones

    score_map = dict(zip(scores_actuales["id_vendedor"], scores_actuales["score"]))
    nivel_map = dict(zip(scores_actuales["id_vendedor"], scores_actuales["nivel_riesgo"]))

    rows = []
    for _, r in intervenciones.iterrows():
        vid = r["id_vendedor"]
        if r["activo"] == 0:
            rows.append({**r, "score_actual": None, "nivel_actual": "baja",
                         "impacto": None, "estado": "Baja"})
        elif vid in score_map:
            sa = score_map[vid]
            impacto = round(r["score_inicial"] - sa, 1)
            rows.append({**r, "score_actual": sa,
                         "nivel_actual": nivel_map[vid],
                         "impacto": impacto,
                         "estado": "activo"})
        else:
            rows.append({**r, "score_actual": None, "nivel_actual": None,
                         "impacto": None, "estado": "sin datos"})

    return pd.DataFrame(rows)


def efectividad_por_perfil(scores_actuales: pd.DataFrame,
                           intervenciones: pd.DataFrame = None,
                           min_casos: int = 2) -> dict:
    """
    Efectividad REAL de cada tipo de intervención, por perfil de vendedor.
    Reemplaza el dict EFECTIVIDAD inventado que había en snippets_v3.

    Para cada intervención cuyo vendedor sigue ACTIVO y tiene score actual, mide
    impacto = score_inicial - score_actual (positivo = el score bajó = mejoró).
    Agrupa por (perfil × tipo) y promedia.

    El PERFIL sale de perfil_de(meses, riesgo_base, señales) con los valores
    ACTUALES del vendedor (aprox: su perfil hoy, no necesariamente el del día que
    se intervino).

    Caveat honesto: solo entran vendedores activos. Una baja no tiene score contra
    el cual medir, así que una intervención tras la que el vendedor IGUAL se fue no
    baja el promedio acá → sobreestima la efectividad. Es "cuánto bajó el score de
    los que se quedaron", no "a cuántos retuvo".

    Devuelve {perfil: [(tipo, impacto_prom, n_casos), ...]} ordenado por impacto
    desc, incluyendo solo combinaciones con >= min_casos. Perfiles sin datos
    suficientes no aparecen → la UI muestra "sin datos" en vez de inventar.
    """
    from collections import defaultdict
    from snippets_v3 import perfil_de, senal_corta

    if intervenciones is None:
        intervenciones = obtener_todas()
    if (intervenciones is None or intervenciones.empty
            or scores_actuales is None or scores_actuales.empty):
        return {}

    score_map = dict(zip(scores_actuales["id_vendedor"], scores_actuales["score"]))
    meses_map = dict(zip(scores_actuales["id_vendedor"], scores_actuales["meses_activo"]))
    rb_map    = dict(zip(scores_actuales["id_vendedor"], scores_actuales["grupo_riesgo_base"]))
    sen_map   = dict(zip(scores_actuales["id_vendedor"], scores_actuales["señales_activas"]))

    acc = defaultdict(list)   # (perfil, tipo) -> [impactos]
    for _, r in intervenciones.iterrows():
        vid = r["id_vendedor"]
        if vid not in score_map:          # baja o sin score actual → no medible
            continue
        impacto = r["score_inicial"] - score_map[vid]
        señales = [senal_corta(s)[0] for s in (sen_map.get(vid) or [])]
        perfil  = perfil_de(meses_map.get(vid) or 0, rb_map.get(vid) or 0, señales)
        acc[(perfil, r["tipo"])].append(impacto)

    tabla = defaultdict(list)
    for (perfil, tipo), imps in acc.items():
        if len(imps) < min_casos:
            continue
        tabla[perfil].append((tipo, round(sum(imps) / len(imps), 1), len(imps)))
    for perfil in tabla:
        tabla[perfil].sort(key=lambda x: -x[1])
    return dict(tabla)
