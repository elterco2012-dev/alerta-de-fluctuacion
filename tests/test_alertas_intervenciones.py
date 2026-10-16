"""Tests de alertas (estado y detección) e intervenciones. Nunca envían mensajes."""

import json
from datetime import datetime, timedelta

import pandas as pd
import pytest

import alertas
import intervenciones


# ── Alertas: estado y detección ──────────────────────────────────────────────

@pytest.fixture
def estado_tmp(tmp_path, monkeypatch):
    path = tmp_path / "estado_alertas.json"
    monkeypatch.setattr(alertas, "ESTADO_PATH", str(path))
    return path


def _scores(*filas):
    return pd.DataFrame([{"id_vendedor": v, "nivel_riesgo": n, "score": s} for v, n, s in filas])


def test_primer_run_alerta_a_todos_los_criticos(estado_tmp):
    scores = _scores((1, "critico", 9.0), (2, "alto", 6.5), (3, "critico", 8.1))
    nuevos = alertas.detectar_nuevos_criticos(scores, alertas.cargar_estado())
    assert sorted(nuevos["id_vendedor"]) == [1, 3]


def test_no_realerta_antes_de_7_dias_y_si_despues(estado_tmp):
    scores = _scores((1, "critico", 9.0), (2, "critico", 9.0))
    hace_3 = (datetime.now() - timedelta(days=3)).isoformat(timespec="seconds")
    hace_8 = (datetime.now() - timedelta(days=8)).isoformat(timespec="seconds")
    estado = {"criticos": {"1": hace_3, "2": hace_8}}
    nuevos = alertas.detectar_nuevos_criticos(scores, estado, dias_realerta=7)
    assert list(nuevos["id_vendedor"]) == [2]


def test_guardar_estado_es_atomico_y_conserva_timestamps(estado_tmp):
    ts_viejo = "2026-01-01T10:00:00"
    estado_tmp.write_text(json.dumps({"criticos": {"1": ts_viejo, "9": ts_viejo}}))
    scores = _scores((1, "critico", 9.0), (2, "critico", 8.5), (9, "medio", 4.0))
    alertas.guardar_estado(scores, alertados_ids={"2"})
    guardado = json.loads(estado_tmp.read_text())
    assert guardado["criticos"]["1"] == ts_viejo         # sigue crítico, no se alertó
    assert guardado["criticos"]["2"] != ts_viejo         # alertado ahora
    assert "9" not in guardado["criticos"]               # bajó de crítico
    assert not (estado_tmp.parent / "estado_alertas.json.tmp").exists()


def test_estado_corrupto_no_bloquea_las_alertas(estado_tmp, capsys):
    estado_tmp.write_text('{"criticos": {"1": "2026-01')   # JSON cortado
    estado = alertas.cargar_estado()
    assert estado == {"criticos": {}, "ultima_ejecucion": None}
    assert (estado_tmp.parent / "estado_alertas.json.corrupto").exists()
    assert "ilegible" in capsys.readouterr().out


# ── Intervenciones ───────────────────────────────────────────────────────────

def test_intervenciones_escriben_solo_en_sqlite_aunque_haya_informix(base, monkeypatch):
    """Regla absoluta: aunque haya INFORMIX_* configurado, las escrituras van a SQLite."""
    import sqlite3
    monkeypatch.setenv("INFORMIX_SERVER", "servidor-produccion")
    base.grupo(1, riesgo_base=0.1)
    base.vendedor(1, "2026-01-01", supervisor="Sup Uno")
    intervenciones._init_table()
    nuevo_id = intervenciones.registrar(1, "Reunión 1:1", "Sup Uno", 8.5, "critico", "nota")
    con = sqlite3.connect(base.path)
    fila = con.execute("SELECT id_vendedor, tipo, observaciones FROM intervenciones WHERE id=?",
                       (nuevo_id,)).fetchone()
    con.close()
    assert fila == (1, "Reunión 1:1", "nota")


def test_obtener_todas_trae_la_zona_para_filtrar_alcance(base):
    base.grupo(1, riesgo_base=0.1)
    base.vendedor(1, "2026-01-01", supervisor="Sup Uno")
    base.vendedor(2, "2026-01-01", supervisor="Sup Dos")
    intervenciones._init_table()
    intervenciones.registrar(1, "Reunión 1:1", "Sup Uno", 8.0, "critico")
    intervenciones.registrar(2, "Reunión 1:1", "Sup Dos", 8.0, "critico")
    df = intervenciones.obtener_todas()
    assert set(df["supervisor_zona"]) == {"Sup Uno", "Sup Dos"}
    assert list(df[df["supervisor_zona"].isin({"Sup Uno"})]["id_vendedor"]) == [1]


def test_no_hay_carga_de_datos_de_ejemplo():
    """Las intervenciones 'demo' (con nombres reales y notas inventadas) se escribían
    en la base real al abrir la página. Ya no existen."""
    assert not hasattr(intervenciones, "cargar_demo")
    assert not hasattr(intervenciones, "hay_datos_demo")
