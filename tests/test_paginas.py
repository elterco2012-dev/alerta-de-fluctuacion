"""
Smoke tests de páginas Streamlit con streamlit.testing (AppTest) sobre una base
sintética. Verifican que la página carga sin excepciones y que el alcance por
rol se respeta. No levantan servidor ni tocan data/wurth.db.
"""

import os
import sqlite3

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

import acceso
import intervenciones
import score_engine
from conftest import RAIZ


@pytest.fixture
def base_dos_zonas(base, monkeypatch):
    monkeypatch.setattr(acceso, "_DB", base.path)
    base.grupo(1, nombre="Grupo 1", riesgo_base=0.1, supervisor="Sup Uno")
    base.grupo(2, nombre="Grupo 2", riesgo_base=0.1, supervisor="Sup Dos")
    base.vendedor(1, "2026-08-01", id_grupo=1, supervisor="Sup Uno", nombre_grupo="Grupo 1")
    base.vendedor(2, "2026-08-01", id_grupo=2, supervisor="Sup Dos", nombre_grupo="Grupo 2")
    intervenciones._init_table()
    intervenciones.registrar(1, "Reunión 1:1", "Sup Uno", 8.0, "critico", "nota zona uno")
    intervenciones.registrar(2, "Reunión 1:1", "Sup Dos", 8.0, "critico",
                             "nota <b>zona dos</b>")
    return base


def _correr_intervenciones(usuario):
    at = AppTest.from_file(os.path.join(RAIZ, "pages", "Intervenciones.py"), default_timeout=30)
    at.query_params["usuario"] = usuario
    at.run()
    assert not at.exception, at.exception
    return " ".join(m.value for m in at.markdown)


def test_supervisor_no_ve_intervenciones_de_otra_zona(base_dos_zonas):
    html = _correr_intervenciones("Sup Uno")
    assert "nota zona uno" in html
    assert "zona dos" not in html


def test_gerencia_ve_todo_y_el_texto_libre_se_escapa(base_dos_zonas):
    html = _correr_intervenciones("Gerencia")
    assert "nota zona uno" in html
    assert "nota &lt;b&gt;zona dos&lt;/b&gt;" in html
    assert "<b>zona dos</b>" not in html


def test_abrir_la_pagina_con_tabla_vacia_no_inserta_datos_de_ejemplo(base_dos_zonas):
    con = sqlite3.connect(base_dos_zonas.path)
    con.execute("DELETE FROM intervenciones")
    con.commit()
    _correr_intervenciones("Gerencia")
    n = con.execute("SELECT COUNT(*) FROM intervenciones").fetchone()[0]
    con.close()
    assert n == 0
