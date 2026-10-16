"""Tests de scripts/chequeo_integridad.py con datos sintéticos."""

import datetime as dt
import hashlib

import chequeo_integridad as ci
from conftest import BaseSintetica, meses_atras


def test_detecta_filas_futuras_y_no_modifica_la_base(tmp_path, capsys):
    path = str(tmp_path / "ci.db")
    db = BaseSintetica(path)
    hoy = dt.date.today()
    db.grupo(1, riesgo_base=0.5)
    db.vendedor(1, "2025-01-01")
    db.vendedor(2, "2025-01-01")                     # activo sin ventas → fuera del score
    a, m = meses_atras(hoy.year, hoy.month, 1)
    db.venta(1, a, m)
    fa, fm = meses_atras(hoy.year, hoy.month, -3)    # 3 meses en el FUTURO
    db.balanza(1, fa, fm, balanza=-5)
    db.close()
    with open(path, "rb") as fh:
        antes = hashlib.sha256(fh.read()).hexdigest()

    assert ci.main(["--db", path]) == 0
    out = capsys.readouterr().out
    assert "[!] balanza_clientes" in out and "FUTUROS: 1" in out
    assert "sin ninguna fila de ventas (quedan FUERA del score): 1" in out
    assert "motivo_egreso cargado: 0" in out
    with open(path, "rb") as fh:
        assert hashlib.sha256(fh.read()).hexdigest() == antes
