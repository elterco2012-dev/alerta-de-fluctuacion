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


# ── Smoke de todas las páginas ───────────────────────────────────────────────

PAGINAS = ["dashboard.py"] + sorted(
    f"pages/{p}" for p in os.listdir(os.path.join(RAIZ, "pages")) if p.endswith(".py"))


@pytest.fixture
def base_completa(base, monkeypatch):
    """Dos zonas, 12 vendedores con 6 meses de datos de todas las fuentes y backfill."""
    import contextlib
    import datetime as dt
    import io

    import backfill_scores
    from conftest import meses_atras

    monkeypatch.setattr(acceso, "_DB", base.path)
    monkeypatch.setattr(backfill_scores, "DB_PATH", base.path)
    hoy = dt.date.today()
    for g in (1, 2):
        base.grupo(g, nombre=f"Grupo {g}", riesgo_base=0.45 if g == 2 else 0.1,
                   supervisor=f"Sup {g}")
    for vid in range(1, 13):
        g = 1 + vid % 2
        ingreso = hoy - dt.timedelta(days=(40, 100, 200, 700)[vid % 4])
        egreso = (hoy - dt.timedelta(days=20)).isoformat() if vid in (11, 12) else None
        base.vendedor(vid, ingreso.isoformat(), egreso, id_grupo=g, supervisor=f"Sup {g}",
                      nombre_grupo=f"Grupo {g}", tipo="Televentas" if vid % 3 == 0 else "Viajante")
        for i in range(6):
            a, m = meses_atras(hoy.year, hoy.month, i)
            base.venta(vid, a, m, pct_plan=20 + (vid * 13 + i * 7) % 100,
                       clientes_nuevos=(vid + i) % 3, total_clientes=50, clientes_activos=30,
                       cobranza_teorica=100, pct_cobranza=90)
            base.balanza(vid, a, m, balanza=-((vid * 7 + i) % 50), ticket_promedio=100 - i)
            base.ausencia(vid, a, m, (vid + i) % 5)
            base.acompanamiento(vid, a, m, (vid + i) % 3)
            base.actividad(vid, a, m, llamadas=600, visitas=400, planificadas_visitas=100,
                           visitadas_schedule=40, planificadas_llamadas=100, gestionadas_llamadas=40)
    with contextlib.redirect_stdout(io.StringIO()):
        backfill_scores.main()
    intervenciones._init_table()
    intervenciones.registrar(1, "Reunión 1:1", "Sup 2", 8.0, "critico", "nota")
    return base


@pytest.mark.parametrize("usuario", ["Gerencia", "Sup 1"])
@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_carga_sin_excepciones(base_completa, pagina, usuario):
    if usuario != "Gerencia" and pagina == "pages/Historial.py":
        pytest.skip("redirige con st.switch_page, que AppTest no resuelve fuera del entrypoint")
    at = AppTest.from_file(os.path.join(RAIZ, pagina), default_timeout=60)
    at.query_params["usuario"] = usuario
    if pagina.endswith("Vendedor.py"):
        at.query_params["id"] = "1"
    at.run()
    assert not at.exception, [e.message for e in at.exception]
