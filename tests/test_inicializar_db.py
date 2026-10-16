"""
Tests de scripts/inicializar_db.py (padrón de vendedores) con pyodbc FALSO.

Desde octubre 2026 corre a diario: tiene que dar de alta a los nuevos, ser
idempotente y NO pisar datos si f040 viene incompleto.
"""

import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys

import pytest

from conftest import RAIZ, BaseSintetica

FAKES = os.path.join(RAIZ, "tests", "fakes")
COLUMNAS = ["vertr", "eintrdat", "austrdat", "name1", "vgrp", "bvertr", "zone", "vart", "kz3"]


def _f040(hoy):
    ingreso_nuevo = (hoy - dt.timedelta(days=10)).isoformat()
    return {
        "columnas_f040": COLUMNAS,
        "f040_nombres": [[50, "Sup Cincuenta", None], [1, "Vendedor Uno", None],
                         [2, "Vendedora Nueva", None]],
        "f040_padron": [
            [50, "2020-01-01", None, "Sup Cincuenta", 1, 50, "SUR", 1, None],
            [1, "2025-01-01", None, "Vendedor Uno", 1, 50, "SUR", 1, None],
            [2, ingreso_nuevo, None, "Vendedora Nueva", 1, 50, "TVTAS", 2, None],
        ],
    }


@pytest.fixture
def proyecto(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data").mkdir()
    shutil.copy(os.path.join(RAIZ, "scripts", "inicializar_db.py"), tmp_path / "scripts")
    db = BaseSintetica(str(tmp_path / "data" / "wurth.db"))
    db.grupo(1, riesgo_base=0.5, supervisor="Viejo")
    db.vendedor(1, "2025-01-01", supervisor="Viejo")
    db.con.execute("UPDATE vendedores SET motivo_egreso='dato a conservar' WHERE id_vendedor=1")
    db.con.commit()
    db.close()
    return tmp_path


def correr(proyecto, datos, fallar=""):
    ruta = proyecto / "datos_fake.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=FAKES, FAKE_PYODBC_DATA=str(ruta),
               FAKE_PYODBC_FAIL=fallar, PYTHONUTF8="1")
    return subprocess.run([sys.executable, str(proyecto / "scripts" / "inicializar_db.py")],
                          capture_output=True, text=True, env=env, timeout=120)


def vendedores(proyecto):
    con = sqlite3.connect(proyecto / "data" / "wurth.db")
    filas = con.execute("SELECT id_vendedor, tipo, supervisor, motivo_egreso, es_supervisor "
                        "FROM vendedores ORDER BY id_vendedor").fetchall()
    rb = con.execute("SELECT riesgo_base FROM grupos WHERE id_grupo=1").fetchone()[0]
    con.close()
    return filas, rb


def test_da_de_alta_a_los_nuevos_y_actualiza_sin_pisar(proyecto):
    r = correr(proyecto, _f040(dt.date.today()))
    assert r.returncode == 0, r.stdout + r.stderr
    filas, rb = vendedores(proyecto)
    assert [f[0] for f in filas] == [1, 2, 50]                     # la nueva entró
    assert filas[0][2] == "Sup Cincuenta"                          # supervisor actualizado
    assert filas[0][3] == "dato a conservar"                       # motivo_egreso no se pisa
    assert filas[1][1] == "Televentas"                             # zone=TVTAS
    assert filas[2][4] == 1                                        # 50 es supervisor
    assert rb == 0.5                                               # riesgo_base no se pisa


def test_es_idempotente(proyecto):
    datos = _f040(dt.date.today())
    assert correr(proyecto, datos).returncode == 0
    primera = vendedores(proyecto)
    assert correr(proyecto, datos).returncode == 0
    assert vendedores(proyecto) == primera


@pytest.mark.parametrize("fallar", ["columnas", "f040_nombres"])
def test_f040_incompleto_aborta_sin_escribir(proyecto, fallar):
    antes = vendedores(proyecto)
    r = correr(proyecto, _f040(dt.date.today()), fallar=fallar)
    assert r.returncode == 1, r.stdout
    assert "ERROR" in r.stdout
    assert vendedores(proyecto) == antes
