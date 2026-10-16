"""Tests de scripts/sincronizar_reactor.py con pyodbc FALSO (sin producción)."""

import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys

from conftest import RAIZ, BaseSintetica, meses_atras

FAKES = os.path.join(RAIZ, "tests", "fakes")


def test_descarta_filas_de_meses_futuros_y_conserva_las_pasadas(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "data").mkdir()
    shutil.copy(os.path.join(RAIZ, "scripts", "sincronizar_reactor.py"), tmp_path / "scripts")
    hoy = dt.date.today()
    pa, pm = meses_atras(hoy.year, hoy.month, 1)
    fa, fm = meses_atras(hoy.year, hoy.month, -2)
    db = BaseSintetica(str(tmp_path / "data" / "wurth.db"))
    db.grupo(1)
    db.vendedor(1, "2025-01-01")
    for a, m in ((pa, pm), (fa, fm)):          # una fila pasada y una futura por tabla
        db.ausencia(1, a, m, 3)
        db.acompanamiento(1, a, m, 1)
        db.actividad(1, a, m, visitas=10)
    db.close()
    (tmp_path / "d.json").write_text(json.dumps({}), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=FAKES, FAKE_PYODBC_DATA=str(tmp_path / "d.json"),
               PYTHONUTF8="1")
    r = subprocess.run([sys.executable, str(tmp_path / "scripts" / "sincronizar_reactor.py")],
                       capture_output=True, text=True, env=env, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    con = sqlite3.connect(tmp_path / "data" / "wurth.db")
    for tabla in ("ausencias_mensual", "acompanamiento_mensual", "actividad_mensual"):
        meses = con.execute(f"SELECT anio*100+mes FROM {tabla}").fetchall()
        assert meses == [(pa * 100 + pm,)], tabla
    con.close()
