"""
Fixtures compartidas para la suite de tests.

REGLA: ningún test toca bases de producción (Informix / Reactor / SUN) ni
data/wurth.db, ni envía correos. Todo corre contra una SQLite temporal con
datos sintéticos que se crea en cada test.
"""

import os
import sqlite3
import sys

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("src", "scripts"):
    p = os.path.join(RAIZ, sub)
    if p not in sys.path:
        sys.path.insert(0, p)


# Esquema mínimo equivalente al que dejan inicializar_db.py + los sync
# (columnas de Reactor incluidas: dias_no_vac, visitas_sup_realizadas, etc.).
ESQUEMA = """
CREATE TABLE grupos (
    id_grupo INTEGER PRIMARY KEY, nombre_grupo TEXT, supervisor TEXT,
    riesgo_base REAL DEFAULT 0.35
);
CREATE TABLE vendedores (
    id_vendedor INTEGER PRIMARY KEY, tipo TEXT, id_grupo INTEGER,
    nombre_grupo TEXT, supervisor TEXT, nombre TEXT,
    fecha_ingreso TEXT, fecha_egreso TEXT, motivo_egreso TEXT,
    activo INTEGER DEFAULT 1, director TEXT, es_supervisor INTEGER DEFAULT 0
);
CREATE TABLE ventas_mensual (
    id_vendedor INTEGER NOT NULL, anio INTEGER NOT NULL, mes INTEGER NOT NULL,
    mes_numero INTEGER DEFAULT 0, dias_trabajados INTEGER DEFAULT 20,
    dias_venta_cero INTEGER DEFAULT 0, venta_total REAL DEFAULT 0,
    plan REAL DEFAULT 0, pct_plan REAL DEFAULT 0,
    clientes_activos INTEGER DEFAULT 0, clientes_inactivos INTEGER DEFAULT 0,
    clientes_nuevos INTEGER DEFAULT 0, total_clientes INTEGER DEFAULT 0,
    cobranza_teorica REAL DEFAULT 0, cobranza_real REAL DEFAULT 0,
    pct_cobranza REAL DEFAULT 0, dias_cobro REAL DEFAULT 0,
    cheques_rechazados INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);
CREATE TABLE balanza_clientes (
    id_vendedor INTEGER NOT NULL, anio INTEGER NOT NULL, mes INTEGER NOT NULL,
    clientes_nuevos INTEGER DEFAULT 0, clientes_reactivados INTEGER DEFAULT 0,
    clientes_perdidos INTEGER DEFAULT 0, balanza INTEGER DEFAULT 0,
    ticket_promedio REAL DEFAULT 0, productos_distintos INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);
CREATE TABLE actividad_mensual (
    id_vendedor INTEGER NOT NULL, anio INTEGER NOT NULL, mes INTEGER NOT NULL,
    llamadas INTEGER DEFAULT 0, llamadas_exitosas INTEGER DEFAULT 0,
    planificadas_llamadas INTEGER DEFAULT 0, gestionadas_llamadas INTEGER DEFAULT 0,
    visitas INTEGER DEFAULT 0, clientes_visitados INTEGER DEFAULT 0,
    planificadas_visitas INTEGER DEFAULT 0, visitadas_schedule INTEGER DEFAULT 0,
    clientes_llamados INTEGER DEFAULT 0, llamadas_respondidas INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);
CREATE TABLE acompanamiento_mensual (
    id_vendedor INTEGER NOT NULL, anio INTEGER NOT NULL, mes INTEGER NOT NULL,
    visitas_sup_planificadas INTEGER DEFAULT 0, visitas_sup_realizadas INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);
CREATE TABLE ausencias_mensual (
    id_vendedor INTEGER NOT NULL, anio INTEGER NOT NULL, mes INTEGER NOT NULL,
    dias_ausente INTEGER DEFAULT 0, dias_no_vac INTEGER DEFAULT 0,
    PRIMARY KEY (id_vendedor, anio, mes)
);
"""


def meses_atras(anio, mes, n):
    """(anio, mes) retrocediendo n meses."""
    idx = anio * 12 + (mes - 1) - n
    return idx // 12, idx % 12 + 1


class BaseSintetica:
    """Helper para poblar una SQLite temporal con datos sintéticos."""

    def __init__(self, path):
        self.path = path
        self.con = sqlite3.connect(path)
        self.con.executescript(ESQUEMA)
        self.con.commit()

    def grupo(self, id_grupo=1, nombre="Grupo 1", riesgo_base=0.10, supervisor="Sup Uno"):
        self.con.execute(
            "INSERT INTO grupos (id_grupo, nombre_grupo, supervisor, riesgo_base) VALUES (?,?,?,?)",
            (id_grupo, nombre, supervisor, riesgo_base),
        )
        self.con.commit()

    def vendedor(self, vid, ingreso, egreso=None, id_grupo=1, tipo="Viajante",
                 nombre=None, supervisor="Sup Uno", nombre_grupo="Grupo 1", es_supervisor=0):
        self.con.execute(
            """INSERT INTO vendedores (id_vendedor, tipo, id_grupo, nombre_grupo, supervisor,
                   nombre, fecha_ingreso, fecha_egreso, activo, es_supervisor)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (vid, tipo, id_grupo, nombre_grupo, supervisor, nombre or f"Vendedor {vid}",
             ingreso, egreso, 0 if egreso else 1, es_supervisor),
        )
        self.con.commit()

    def venta(self, vid, anio, mes, pct_plan=80.0, plan=1000.0, clientes_nuevos=1, **extra):
        cols = {"id_vendedor": vid, "anio": anio, "mes": mes, "pct_plan": pct_plan,
                "plan": plan, "venta_total": plan * pct_plan / 100,
                "clientes_nuevos": clientes_nuevos}
        cols.update(extra)
        self._insert("ventas_mensual", cols)

    def balanza(self, vid, anio, mes, balanza=0, ticket_promedio=100.0):
        self._insert("balanza_clientes", {"id_vendedor": vid, "anio": anio, "mes": mes,
                                          "balanza": balanza, "ticket_promedio": ticket_promedio})

    def ausencia(self, vid, anio, mes, dias_no_vac):
        self._insert("ausencias_mensual", {"id_vendedor": vid, "anio": anio, "mes": mes,
                                           "dias_ausente": dias_no_vac, "dias_no_vac": dias_no_vac})

    def acompanamiento(self, vid, anio, mes, realizadas):
        self._insert("acompanamiento_mensual", {"id_vendedor": vid, "anio": anio, "mes": mes,
                                                "visitas_sup_realizadas": realizadas})

    def actividad(self, vid, anio, mes, **cols):
        cols.update({"id_vendedor": vid, "anio": anio, "mes": mes})
        self._insert("actividad_mensual", cols)

    def _insert(self, tabla, cols):
        nombres = ",".join(cols)
        marcas = ",".join("?" * len(cols))
        self.con.execute(f"INSERT INTO {tabla} ({nombres}) VALUES ({marcas})", list(cols.values()))
        self.con.commit()

    def close(self):
        self.con.close()


@pytest.fixture
def base(tmp_path, monkeypatch):
    """SQLite temporal + score_engine apuntando a ella (nunca a producción)."""
    import score_engine

    path = str(tmp_path / "test.db")
    db = BaseSintetica(path)
    monkeypatch.setattr(score_engine, "DB_PATH", path)
    # Blindaje: aunque exista un .env con INFORMIX_*, el motor usa la SQLite temporal.
    monkeypatch.setattr(score_engine, "get_connection", lambda: sqlite3.connect(path))
    yield db
    db.close()
