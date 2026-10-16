"""Tests de scripts/evaluar_ranking.py con datos sintéticos (sin producción)."""

import datetime as dt
import hashlib
import json
import sqlite3

import pytest

import evaluar_ranking as er
from conftest import BaseSintetica

D = dt.date


# ── Métricas ─────────────────────────────────────────────────────────────────

def test_tp_top_k_sin_empates():
    assert er.tp_esperado_top_k([5, 4, 3, 2, 1], [1, 0, 1, 0, 0], 2) == (1.0, 2)
    assert er.tp_esperado_top_k([5, 4, 3, 2, 1], [1, 0, 1, 0, 0], 3) == (2.0, 3)


def test_tp_top_k_empate_en_el_borde_se_reparte():
    # top 2 = el 9 seguro + 1 de los 3 empatados en 5 (1 positivo de 3 → 1/3)
    tp, k = er.tp_esperado_top_k([9, 5, 5, 5], [0, 1, 0, 0], 2)
    assert k == 2
    assert tp == pytest.approx(1 / 3)


def test_tp_top_k_todos_empatados_da_la_tasa_base():
    tp, k = er.tp_esperado_top_k([0] * 10, [1, 1] + [0] * 8, 5)
    assert tp / k == pytest.approx(0.2)


def test_tp_top_k_mayor_que_poblacion():
    assert er.tp_esperado_top_k([1, 2], [1, 0], 10) == (1.0, 2)


@pytest.mark.parametrize("valores, etiquetas, esperado", [
    ([3, 2, 1], [1, 0, 0], 1.0),
    ([1, 2, 3], [1, 0, 0], 0.0),
    ([1, 1, 1, 1], [1, 0, 1, 0], 0.5),
    ([1, 2, 3], [0, 0, 0], None),
])
def test_auc(valores, etiquetas, esperado):
    r = er.auc(valores, etiquetas)
    assert r == (pytest.approx(esperado) if esperado is not None else None)


def test_imputar_mediana_es_neutral():
    assert er.imputar_mediana([None, 1, 3, None]) == [2, 1, 3, 2]
    assert er.imputar_mediana([None, None]) == [0.0, 0.0]


# ── Riesgo de grupo point-in-time ────────────────────────────────────────────

def test_riesgo_base_pit_no_usa_bajas_futuras_ni_al_propio_vendedor():
    corte = D(2026, 3, 31)
    miembros = [
        (1, D(2025, 1, 1), D(2025, 3, 1)),     # baja rápida ANTES del corte → cuenta
        (2, D(2025, 1, 1), None),              # activo
        (3, D(2026, 1, 1), D(2026, 5, 1)),     # baja rápida DESPUÉS del corte → no cuenta como baja
        (4, D(2026, 6, 1), None),              # ingresó después del corte → fuera
        (5, D(2025, 5, 1), D(2025, 5, 1)),     # egreso == ingreso (registro basura) → fuera
        (6, D(2025, 2, 1), D(2025, 4, 1)),     # el vendedor evaluado → se excluye
    ]
    # total = {1, 2, 3} → 3 ; rápidas = {1} → 1/3
    assert er.riesgo_base_pit(miembros, corte, excluir_vid=6) == pytest.approx(1 / 3)
    # sin excluirlo, 6 también es baja rápida previa: 2/4
    assert er.riesgo_base_pit(miembros, corte) == pytest.approx(2 / 4)


def test_riesgo_base_pit_grupo_vacio():
    assert er.riesgo_base_pit([], D(2026, 1, 31)) is None


# ── Etiquetas y censura ──────────────────────────────────────────────────────

def test_etiqueta_por_horizonte():
    reg = {"egreso": D(2026, 2, 14), "corte": D(2026, 1, 31)}   # 14 días después
    assert er.etiqueta(reg, 30) == 1
    reg = {"egreso": D(2026, 3, 17), "corte": D(2026, 1, 31)}   # 45 días después
    assert (er.etiqueta(reg, 30), er.etiqueta(reg, 60)) == (0, 1)
    reg = {"egreso": D(2026, 1, 15), "corte": D(2026, 1, 31)}   # antes del corte
    assert er.etiqueta(reg, 90) == 0


def test_periodos_con_horizonte_abierto_se_excluyen():
    periodos = {"2026-01": [], "2026-06": [], "2026-09": []}
    assert er.periodos_evaluables(periodos, 90, D(2026, 10, 1)) == ["2026-01", "2026-06"]
    assert er.periodos_evaluables(periodos, 30, D(2026, 10, 31)) == ["2026-01", "2026-06", "2026-09"]


# ── Extremo a extremo sobre una base sintética ───────────────────────────────

PLAN = "% Plan < 80% promedio últimos meses"
V13 = "En ventana crítica mes 1-3"
GRUPO = "Grupo con alta rotación histórica"


def _crear_base(path):
    db = BaseSintetica(path)
    db.con.execute("""CREATE TABLE score_historico (
        periodo TEXT, id_vendedor INTEGER, score REAL, nivel TEXT, señales TEXT,
        pct_plan_3m REAL, tendencia_plan REAL, dias_cero_prom REAL, pct_cobranza REAL,
        meses_activo INTEGER, PRIMARY KEY (periodo, id_vendedor))""")
    db.grupo(1, riesgo_base=0.10)
    db.grupo(2, nombre="Grupo 2", riesgo_base=0.50)   # "quemado" HOY por bajas posteriores
    return db


def _score_row(db, periodo, vid, senales, meses, plan):
    from validar_pesos import PESOS_ACTUAL
    score = er.score_desde_riesgo(sum(PESOS_ACTUAL[s] for s in senales))
    db.con.execute("INSERT INTO score_historico VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (periodo, vid, score, "x", json.dumps(senales), plan, 0, 0, 0, meses))
    db.con.commit()


def test_extremo_a_extremo(tmp_path, capsys):
    path = str(tmp_path / "eval.db")
    db = _crear_base(path)
    # 20 vendedores en grupo 1 puntuados en 2026-01..2026-03.
    # Los 4 con plan bajo egresan ~20 días después del corte de 2026-03.
    for vid in range(1, 21):
        malo = vid <= 4
        egreso = "2026-04-20" if malo else None
        db.vendedor(vid, "2024-01-01", egreso=egreso, id_grupo=1)
        for periodo in ("2026-01", "2026-02", "2026-03"):
            _score_row(db, periodo, vid, [PLAN] if malo else [], 27, 40 if malo else 80)
    # Grupo 2: sus bajas rápidas ocurren DESPUÉS de los cortes evaluados.
    for vid in range(30, 34):
        db.vendedor(vid, "2026-03-01", egreso="2026-05-15", id_grupo=2, nombre_grupo="Grupo 2")
    db.vendedor(40, "2024-01-01", id_grupo=2, nombre_grupo="Grupo 2")
    _score_row(db, "2026-03", 40, [GRUPO], 27, 80)
    db.close()

    with open(path, "rb") as fh:
        hash_antes = hashlib.sha256(fh.read()).hexdigest()

    assert er.main(["--db", path, "--fecha-datos", "2026-10-01"]) == 0
    out = capsys.readouterr().out
    assert "EVALUACIÓN POINT-IN-TIME" in out
    assert "motivo_egreso vacío" in out

    with open(path, "rb") as fh:
        assert hashlib.sha256(fh.read()).hexdigest() == hash_antes, "el script modificó la base"

    con = er.abrir_solo_lectura(path)
    filas, vendedores, rb, ventas = er.cargar(con)
    con.close()
    periodos = er.preparar_periodos(filas, vendedores, rb, ventas)
    lista = er.periodos_evaluables(periodos, 30, D(2026, 10, 1))
    modelo = er.evaluar_criterio(periodos, lista, "modelo", 30)
    azar = er.evaluar_criterio(periodos, lista, "azar", 30)
    # En 2026-03 hay 21 puntuados y 4 bajas a 30 días; el modelo los pone primeros.
    assert modelo["bajas"] == 4
    assert modelo["prec@5"] == pytest.approx(4 / 15)   # 3 períodos × top 5; solo 2026-03 tiene bajas
    assert modelo["recall@5"] == pytest.approx(1.0)
    assert azar["lift@5"] == pytest.approx(1.0)
    assert modelo["lift@5"] > 3

    # El vendedor 40 tiene la señal de grupo por el riesgo_base de HOY, pero al
    # corte de 2026-03 su grupo no tenía ninguna baja: la versión PIT se la saca.
    reg40 = next(r for r in periodos["2026-03"] if r["id"] == 40)
    assert reg40["criterios"]["modelo"] > 1.0
    assert reg40["criterios"]["modelo_grupo_pit"] == 1.0
    assert reg40["criterios"]["grupo_pit"] == 0.0


def test_abre_la_base_en_solo_lectura(tmp_path):
    path = str(tmp_path / "ro.db")
    db = _crear_base(path)
    db.close()
    con = er.abrir_solo_lectura(path)
    with pytest.raises(sqlite3.OperationalError):
        con.execute("INSERT INTO grupos (id_grupo) VALUES (99)")
    con.close()


def test_score_historico_vacio(tmp_path, capsys):
    path = str(tmp_path / "vacio.db")
    db = _crear_base(path)
    db.close()
    assert er.main(["--db", path]) == 1
    assert "score_historico está vacío" in capsys.readouterr().out
