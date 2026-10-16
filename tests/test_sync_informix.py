"""
Tests de scripts/sincronizar_informix.py con un pyodbc FALSO (tests/fakes).

El script corre en un subproceso sobre una COPIA temporal del proyecto con una
SQLite sintética: nunca toca producción ni data/wurth.db.
"""

import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys

import pytest

from conftest import RAIZ, BaseSintetica, meses_atras

FAKES = os.path.join(RAIZ, "tests", "fakes")


def _datos_base(hoy, meses=3, futuros_vplan=0):
    """Filas sintéticas de Informix/Reactor para el vendedor 1 (últimos `meses`)."""
    datos = {"f040": [[1, "2025-01-01", None]], "kund": [[1, 50]], "sbas_hist": [],
             "vplan": [], "sbas_dias": [], "work_days_log": []}
    for i in range(meses):
        a, m = meses_atras(hoy.year, hoy.month, i)
        datos["sbas_hist"].append([1, 500, a, m, 1000.0, 3])
        datos["vplan"].append([1, a, m, 2000.0, 500.0, 10])
        datos["sbas_dias"].append([1, a, m, f"{a}-{m:02d}-05"])
        datos["work_days_log"].append([a, m, 20])
    for i in range(1, futuros_vplan + 1):          # planes ya cargados para meses futuros
        a, m = meses_atras(hoy.year, hoy.month, -i)
        datos["vplan"].append([1, a, m, 2000.0, 500.0, 10])
    return datos


@pytest.fixture
def proyecto(tmp_path):
    """Copia mínima del proyecto: scripts/sincronizar_informix.py + data/wurth.db sintética."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data").mkdir()
    shutil.copy(os.path.join(RAIZ, "scripts", "sincronizar_informix.py"), tmp_path / "scripts")
    db = BaseSintetica(str(tmp_path / "data" / "wurth.db"))
    db.grupo(1, riesgo_base=0.1)
    db.vendedor(1, "2025-01-01")
    db.close()
    return tmp_path


def correr(proyecto, datos, fallar=""):
    ruta = proyecto / "datos_fake.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("SMTP_", "ALERT_", "TEAMS_"))}
    env.update({"PYTHONPATH": FAKES, "FAKE_PYODBC_DATA": str(ruta),
                "FAKE_PYODBC_FAIL": fallar, "PYTHONUTF8": "1"})
    return subprocess.run([sys.executable, str(proyecto / "scripts" / "sincronizar_informix.py")],
                          capture_output=True, text=True, env=env, timeout=120)


def planes(proyecto):
    con = sqlite3.connect(proyecto / "data" / "wurth.db")
    filas = con.execute("SELECT anio, mes, plan FROM ventas_mensual WHERE id_vendedor=1 "
                        "ORDER BY anio, mes").fetchall()
    con.close()
    return filas


def test_sync_normal_escribe_plan(proyecto):
    r = correr(proyecto, _datos_base(dt.date.today()))
    assert r.returncode == 0, r.stdout + r.stderr
    assert [p for _, _, p in planes(proyecto)] == [2000.0, 2000.0, 2000.0]


@pytest.mark.parametrize("fuente", ["vplan", "kund"])
def test_si_falla_una_fuente_obligatoria_aborta_sin_pisar_datos(proyecto, fuente):
    hoy = dt.date.today()
    assert correr(proyecto, _datos_base(hoy)).returncode == 0
    antes = planes(proyecto)
    r = correr(proyecto, _datos_base(hoy), fallar=fuente)
    assert r.returncode == 1, r.stdout
    assert "ERROR" in r.stdout
    assert planes(proyecto) == antes          # el plan NO quedó en 0


def test_vplan_vacio_aborta(proyecto):
    datos = _datos_base(dt.date.today())
    datos["vplan"] = []
    r = correr(proyecto, datos)
    assert r.returncode == 1, r.stdout
    assert planes(proyecto) == []


def test_no_quedan_filas_de_meses_futuros(proyecto):
    """vplan con planes futuros y 'perdidos' a +12 meses de la última compra
    creaban filas de meses que no ocurrieron; el sync ahora las descarta."""
    hoy = dt.date.today()
    con = sqlite3.connect(proyecto / "data" / "wurth.db")
    fa, fm = meses_atras(hoy.year, hoy.month, -4)       # basura futura de un sync viejo
    con.execute("INSERT INTO balanza_clientes (id_vendedor, anio, mes, balanza) VALUES (1,?,?,-50)",
                (fa, fm))
    con.commit()
    con.close()
    r = correr(proyecto, _datos_base(hoy, futuros_vplan=3))
    assert r.returncode == 0, r.stdout + r.stderr
    tope = hoy.year * 100 + hoy.month
    con = sqlite3.connect(proyecto / "data" / "wurth.db")
    futuras = {t: con.execute(f"SELECT COUNT(*) FROM {t} WHERE anio*100+mes > ?", (tope,)).fetchone()[0]
               for t in ("ventas_mensual", "balanza_clientes")}
    pasadas = con.execute("SELECT COUNT(*) FROM ventas_mensual WHERE anio*100+mes <= ?",
                          (tope,)).fetchone()[0]
    con.close()
    assert futuras == {"ventas_mensual": 0, "balanza_clientes": 0}
    assert pasadas == 3
