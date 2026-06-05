"""
intervenciones.py
-----------------
Registro y seguimiento de intervenciones sobre vendedores en riesgo.
Cierra el ciclo: alerta → acción → impacto medido.
"""

import pandas as pd
from datetime import date, datetime
from score_engine import get_connection

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


def hay_datos_demo() -> bool:
    try:
        _init_table()
        con = get_connection()
        n = con.execute("SELECT COUNT(*) FROM intervenciones").fetchone()[0]
        con.close()
        return n > 0
    except Exception:
        return False


def cargar_demo(scores: pd.DataFrame):
    """Inserta intervenciones de ejemplo para los vendedores en riesgo."""
    from datetime import timedelta
    hoy = date(2025, 1, 24)

    demo = [
        (10008, "Reunión 1:1",           "Kalpokas Gustavo",   9.3, "critico",
         "Revisamos objetivos del mes. Vendedor muy desmotivado, dice que la zona está muy trabajada.", "2025-01-10"),
        (10002, "Acompañamiento en campo","Kalpokas Gustavo",   9.3, "critico",
         "Salida de campo con 4 clientes. Detectamos problemas de presentación del producto.", "2025-01-08"),
        (10006, "Conversación motivacional","Zerbatto Jose Luis",8.3, "critico",
         "Charla informal sobre expectativas. Vendedor tiene problemas personales que afectan rendimiento.", "2025-01-15"),
        (10004, "Revisión de cartera",    "Kalpokas Gustavo",   8.6, "critico",
         "Depuramos clientes inactivos y reasignamos 15 cuentas nuevas.", "2025-01-05"),
        (10011, "Ajuste de objetivos",    "Zerbatto Jose Luis", 8.3, "critico",
         "Bajamos el plan un 15% para los próximos 2 meses mientras se adapta.", "2025-01-12"),
        (10015, "Reunión 1:1",            "Galla Gabriel Isaac",7.9, "alto",
         "Primera reunión formal. El vendedor no tenía claro cómo priorizar la cartera.", "2025-01-18"),
        (10009, "Capacitación técnica",   "Torres Miguel",      7.4, "alto",
         "Capacitación sobre nuevos productos de fijación. Muy receptivo.", "2025-01-07"),
    ]

    for vid, tipo, sup, score, nivel, obs, fecha in demo:
        registrar(vid, tipo, sup, score, nivel, obs, fecha)
