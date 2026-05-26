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


def hay_datos_demo() -> bool:
    con = get_connection()
    n = con.execute("SELECT COUNT(*) FROM intervenciones").fetchone()[0]
    con.close()
    return n > 0


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
