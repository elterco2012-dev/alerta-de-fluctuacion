"""
Tests de caracterización del motor de scoring (src/score_engine.py).

Fijan el comportamiento ACTUAL del motor: señales, umbrales, tratamiento de
datos faltantes, normalización y niveles. Si un cambio de scoring rompe un
test, el cambio tiene que ser intencional, medido con scripts/evaluar_ranking.py
y documentado en CLAUDE.md.

Los tests marcados "COMPORTAMIENTO ACTUAL — HALLAZGO" documentan conductas que
la auditoría de octubre 2026 señaló como problemáticas (ver
docs/AUDITORIA_2026-10.md). Se dejan explícitas para que, si se aprueba
corregirlas, el cambio se vea en el diff de los tests.
"""

import datetime as dt

import pytest

import score_engine
from conftest import meses_atras

# Corte de backfill usado en casi todos los tests: fin de junio 2026.
ANIO, MES = 2026, 6
CORTE = dt.date(2026, 6, 30)


def ingreso_con_meses(meses, corte=CORTE):
    """Fecha de ingreso que da meses_activo == meses al corte (días/30 redondeado)."""
    return (corte - dt.timedelta(days=meses * 30)).isoformat()


def ventas_ultimos(base, vid, pcts, anio=ANIO, mes=MES, **extra):
    """Carga ventas para los últimos len(pcts) meses; pcts va del más VIEJO al más RECIENTE."""
    n = len(pcts)
    for i, pct in enumerate(pcts):
        a, m = meses_atras(anio, mes, n - 1 - i)
        base.venta(vid, a, m, pct_plan=pct, **extra)


def score_de(base):
    return score_engine.calcular_scores(meses_tendencia=3, hasta_anio=ANIO, hasta_mes=MES)


def fila(df, vid):
    sub = df[df["id_vendedor"] == vid]
    assert len(sub) == 1, f"vendedor {vid} no está en el resultado"
    return sub.iloc[0]


@pytest.fixture
def veterano(base):
    """Vendedor sin ninguna señal: 24 meses, grupo sano, plan 80%, clientes nuevos."""
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(100, ingreso_con_meses(24))
    ventas_ultimos(base, 100, [80, 80, 80])
    return base


# ── Línea base ────────────────────────────────────────────────────────────────

def test_vendedor_sin_senales_tiene_score_1_y_nivel_bajo(veterano):
    r = fila(score_de(veterano), 100)
    assert r["score"] == 1.0
    assert r["nivel_riesgo"] == "bajo"
    assert r["señales_activas"] == []
    assert r["meses_activo"] == 24


# ── Señal: % plan promedio bajo (peso 2.0, umbral < 55) ──────────────────────

def test_plan_bajo_enciende_bajo_55(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [50, 50, 50])
    r = fila(score_de(base), 1)
    assert r["señales_activas"] == ["% Plan < 80% promedio últimos meses"]
    assert r["score"] == pytest.approx(3.2)   # 1 + 2.0/8*9 = 3.25 → 3.2
    assert r["pct_plan_3m"] == 50.0


def test_plan_bajo_umbral_es_estricto(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [55, 55, 55])
    assert fila(score_de(base), 1)["señales_activas"] == []


def test_plan_bajo_ignora_meses_sin_plan(base):
    """Dato faltante (plan=0 → pct 0) NO se toma como mal rendimiento."""
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    a, m = meses_atras(ANIO, MES, 2)
    base.venta(1, a, m, pct_plan=0, plan=0)
    a, m = meses_atras(ANIO, MES, 1)
    base.venta(1, a, m, pct_plan=80)
    base.venta(1, ANIO, MES, pct_plan=80)
    assert fila(score_de(base), 1)["señales_activas"] == []


def test_plan_bajo_apagado_si_ningun_mes_tiene_plan(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [0, 0, 0], plan=0)
    r = fila(score_de(base), 1)
    assert r["señales_activas"] == []
    assert r["pct_plan_3m"] == 0   # 0 = "sin dato", no "0% de plan"


def test_usa_solo_los_ultimos_3_meses(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [10, 10, 10, 80, 80, 80])
    assert fila(score_de(base), 1)["señales_activas"] == []


def test_backfill_ignora_ventas_posteriores_al_corte(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [80, 80, 80])
    base.venta(1, 2026, 7, pct_plan=5)
    base.venta(1, 2026, 8, pct_plan=5)
    assert fila(score_de(base), 1)["señales_activas"] == []


# ── Ventanas críticas por antigüedad ─────────────────────────────────────────

@pytest.mark.parametrize("meses, esperada", [
    (0, None),
    (1, "En ventana crítica mes 1-3"),
    (3, "En ventana crítica mes 1-3"),
    (4, "En ventana crítica mes 4-6"),
    (6, "En ventana crítica mes 4-6"),
    (7, None),
])
def test_ventanas_criticas(base, meses, esperada):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(meses))
    ventas_ultimos(base, 1, [80])
    r = fila(score_de(base), 1)
    assert r["meses_activo"] == meses
    assert r["señales_activas"] == ([esperada] if esperada else [])


def test_meses_activo_es_dias_sobre_30_redondeado(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, (CORTE - dt.timedelta(days=104)).isoformat())   # 3.47 → 3
    base.vendedor(2, (CORTE - dt.timedelta(days=106)).isoformat())   # 3.53 → 4
    ventas_ultimos(base, 1, [80])
    ventas_ultimos(base, 2, [80])
    df = score_de(base)
    assert fila(df, 1)["meses_activo"] == 3
    assert fila(df, 2)["meses_activo"] == 4


# ── Grupo con alta rotación histórica (peso 1.5, riesgo_base > 0.40) ─────────

@pytest.mark.parametrize("rb, enciende", [(0.40, False), (0.41, True)])
def test_grupo_quemado_umbral(base, rb, enciende):
    base.grupo(1, riesgo_base=rb)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [80, 80, 80])
    activas = fila(score_de(base), 1)["señales_activas"]
    assert ("Grupo con alta rotación histórica" in activas) is enciende


def test_backfill_usa_riesgo_base_actual_sin_corte_temporal(base):
    """COMPORTAMIENTO ACTUAL — HALLAZGO (fuga temporal).

    grupos.riesgo_base es una foto de HOY (calculada con todas las bajas,
    incluidas las posteriores al período). El backfill la usa tal cual para
    cualquier período pasado: el score histórico 'sabe' bajas futuras.
    """
    base.grupo(1, riesgo_base=0.50)
    base.vendedor(1, ingreso_con_meses(24, dt.date(2025, 1, 31)))
    for m in (11, 12):
        base.venta(1, 2024, m, pct_plan=80)
    base.venta(1, 2025, 1, pct_plan=80)
    df = score_engine.calcular_scores(meses_tendencia=3, hasta_anio=2025, hasta_mes=1)
    assert "Grupo con alta rotación histórica" in fila(df, 1)["señales_activas"]


# ── Sin clientes nuevos (peso 0.5) ───────────────────────────────────────────

def test_sin_clientes_nuevos_2_meses(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [80, 80, 80], clientes_nuevos=0)
    r = fila(score_de(base), 1)
    assert r["señales_activas"] == ["Sin clientes nuevos últimos 2 meses"]
    assert r["score"] == pytest.approx(1.6)   # 1 + 0.5/8*9 = 1.5625


def test_sin_clientes_nuevos_requiere_2_meses_de_historial(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [80], clientes_nuevos=0)
    assert fila(score_de(base), 1)["señales_activas"] == []


# ── Ausencias tempranas (peso 2.0, solo mes 1-3) ─────────────────────────────

def test_ausencias_enciende_en_ventana_1_3(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(2))
    ventas_ultimos(base, 1, [80, 80])
    for i, d in enumerate([3, 3]):
        a, m = meses_atras(ANIO, MES, 1 - i)
        base.ausencia(1, a, m, d)
    activas = fila(score_de(base), 1)["señales_activas"]
    assert "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3" in activas


def test_ausencias_no_aplica_fuera_de_ventana(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(10))
    ventas_ultimos(base, 1, [80, 80, 80])
    base.ausencia(1, ANIO, MES, 10)
    assert fila(score_de(base), 1)["señales_activas"] == []


AUSENCIAS = "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3"


def test_ausencias_promedia_sobre_los_meses_de_la_ventana(base):
    """Corregido (oct 2026): ausencias_mensual solo tiene filas en meses CON
    ausencias. Antes se promediaban esas filas: 3 días en uno de tres meses
    encendía "> 2 días/mes". Ahora, con dato de Reactor en los 3 meses, el
    promedio es 1 y la señal no enciende."""
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(3))
    ventas_ultimos(base, 1, [80, 80, 80])
    for i in range(3):
        a, m = meses_atras(ANIO, MES, i)
        base.actividad(1, a, m, visitas=10)      # Reactor tiene al vendedor los 3 meses
    a, m = meses_atras(ANIO, MES, 2)
    base.ausencia(1, a, m, 3)                   # los otros dos meses: sin fila (= 0)
    assert AUSENCIAS not in fila(score_de(base), 1)["señales_activas"]


def test_ausencias_mes_sin_dato_de_reactor_es_desconocido(base):
    """Si el vendedor no tiene NINGÚN dato de Reactor en un mes, ese mes no cuenta
    como 'cero ausencias': queda fuera del promedio (dato faltante ≠ conducta)."""
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(3))
    ventas_ultimos(base, 1, [80, 80, 80])
    a, m = meses_atras(ANIO, MES, 2)
    base.ausencia(1, a, m, 3)                   # único mes con dato de Reactor
    assert AUSENCIAS in fila(score_de(base), 1)["señales_activas"]


def test_ausencias_fuera_de_la_ventana_del_score_no_cuentan(base):
    """Solo cuentan los meses que usa el score (los últimos 3 de ventas)."""
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(3))
    ventas_ultimos(base, 1, [80, 80])
    for i in range(2):
        a, m = meses_atras(ANIO, MES, i)
        base.ausencia(1, a, m, 0)
    a, m = meses_atras(ANIO, MES, 4)
    base.ausencia(1, a, m, 9)                   # mes viejo, fuera de la ventana
    assert AUSENCIAS not in fila(score_de(base), 1)["señales_activas"]


def test_ausencias_con_ceros_explicitos_no_enciende(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(3))
    ventas_ultimos(base, 1, [80, 80, 80])
    for i, d in enumerate([3, 0, 0]):
        a, m = meses_atras(ANIO, MES, 2 - i)
        base.ausencia(1, a, m, d)
    activas = fila(score_de(base), 1)["señales_activas"]
    assert "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3" not in activas


# ── Balanza de clientes (peso 1.5) y ticket (peso 1.0) ───────────────────────

@pytest.mark.parametrize("ultimos, enciende", [
    ((-40, -30), True),     # ambos negativos y suma -70 < -60
    ((-40, 10), False),     # uno positivo
    ((-20, -20), False),    # suma -40, no alcanza
])
def test_balanza_negativa(base, ultimos, enciende):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [80, 80, 80])
    a, m = meses_atras(ANIO, MES, 1)
    base.balanza(1, a, m, balanza=ultimos[1])
    base.balanza(1, ANIO, MES, balanza=ultimos[0])
    activas = fila(score_de(base), 1)["señales_activas"]
    assert ("Balanza clientes negativa 2+ meses consecutivos" in activas) is enciende


@pytest.mark.parametrize("tickets, enciende", [
    ((100, 90, 80), True),     # cae ~11%/mes del promedio
    ((100, 100, 100), False),
    ((100, 98, 96), False),    # cae ~2%/mes
])
def test_ticket_cayendo(base, tickets, enciende):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [80, 80, 80])
    for i, t in enumerate(tickets):   # del más viejo al más reciente
        a, m = meses_atras(ANIO, MES, 2 - i)
        base.balanza(1, a, m, balanza=0, ticket_promedio=t)
    activas = fila(score_de(base), 1)["señales_activas"]
    assert ("Ticket promedio cae > 5% por mes" in activas) is enciende


# ── Acompañamiento del supervisor (peso 1.0, mes 1-6) ────────────────────────

def test_supervisor_no_acompano(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(5))
    ventas_ultimos(base, 1, [80, 80, 80])
    for i in range(3):
        a, m = meses_atras(ANIO, MES, i)
        base.acompanamiento(1, a, m, 0)
    activas = fila(score_de(base), 1)["señales_activas"]
    assert "Supervisor no acompañó en ventana crítica 1-6" in activas


def test_sin_filas_de_acompanamiento_no_enciende(base):
    """Dato faltante ≠ 'no acompañó': sin filas en Reactor la señal queda apagada."""
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(5))
    ventas_ultimos(base, 1, [80, 80, 80])
    activas = fila(score_de(base), 1)["señales_activas"]
    assert "Supervisor no acompañó en ventana crítica 1-6" not in activas


# ── Señales deshabilitadas (peso 0) ──────────────────────────────────────────

def test_senales_deshabilitadas_no_suman_ni_se_muestran(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24), tipo="Viajante")
    # pendiente muy negativa (150 → 90 → 30, media 90: no enciende plan bajo),
    # días cero altos, cartera inactiva, cobranza baja
    ventas_ultimos(base, 1, [150, 90, 30], dias_venta_cero=20, total_clientes=100,
                   clientes_activos=10, cobranza_teorica=1000, pct_cobranza=20)
    for i in range(3):
        a, m = meses_atras(ANIO, MES, i)
        base.actividad(1, a, m, planificadas_visitas=100, visitadas_schedule=1)
    r = fila(score_de(base), 1)
    assert r["score"] == 1.0
    assert r["señales_activas"] == []
    assert r["tendencia_plan"] == pytest.approx(-60.0)
    assert r["dias_cero_promedio"] == 20.0


# ── Normalización y niveles ──────────────────────────────────────────────────

@pytest.mark.parametrize("riesgo, score", [
    (0.0, 1.0), (0.5, 1.6), (1.0, 2.1), (2.0, 3.2), (3.0, 4.4),
    (4.0, 5.5), (5.0, 6.6), (6.0, 7.8), (7.0, 8.9), (8.0, 10.0), (12.0, 10.0),
])
def test_formula_de_normalizacion(riesgo, score):
    calc = round(min(10, max(1, 1 + min(riesgo / score_engine.RIESGO_REFERENCIA, 1.0) * 9)), 1)
    assert calc == pytest.approx(score)


def test_riesgo_de_referencia_vigente():
    assert score_engine.RIESGO_REFERENCIA == 8.0


def test_nivel_alto_y_tope_critico(base):
    base.grupo(1, riesgo_base=0.50)
    base.grupo(2, nombre="Grupo 2", riesgo_base=0.10)
    # plan 2.0 + ventana 1-3 1.5 + grupo 1.5 = 5.0 → 6.6 alto
    base.vendedor(1, ingreso_con_meses(2))
    ventas_ultimos(base, 1, [40, 40])
    # plan 2.0 + v13 1.5 + grupo 1.5 + ausencias 2.0 + acomp 1.0 + nuevos 0.5 = 8.5 → 10 crítico
    base.vendedor(2, ingreso_con_meses(2))
    ventas_ultimos(base, 2, [40, 40], clientes_nuevos=0)
    for i in range(2):
        a, m = meses_atras(ANIO, MES, i)
        base.ausencia(2, a, m, 4)
        base.acompanamiento(2, a, m, 0)
    # plan 2.0 + ventana 4-6 1.0 = 3.0 → 4.4 medio (grupo sano)
    base.vendedor(3, ingreso_con_meses(5), id_grupo=2)
    ventas_ultimos(base, 3, [40, 40, 40])
    df = score_de(base)
    assert (fila(df, 1)["score"], fila(df, 1)["nivel_riesgo"]) == (pytest.approx(6.6), "alto")
    assert (fila(df, 2)["score"], fila(df, 2)["nivel_riesgo"]) == (10.0, "critico")
    assert (fila(df, 3)["score"], fila(df, 3)["nivel_riesgo"]) == (pytest.approx(4.4), "medio")
    assert list(df["id_vendedor"]) == [2, 1, 3]   # orden por score descendente


# ── Población evaluada ───────────────────────────────────────────────────────

def test_vendedor_sin_ventas_queda_fuera(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(2))
    assert score_de(base).empty


def test_supervisores_excluidos_por_nombre(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24), nombre="Sup Uno", supervisor="Sup Uno")
    base.vendedor(2, ingreso_con_meses(24))
    ventas_ultimos(base, 1, [80, 80, 80])
    ventas_ultimos(base, 2, [80, 80, 80])
    assert list(score_de(base)["id_vendedor"]) == [2]


def test_backfill_incluye_solo_activos_al_corte(base):
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, ingreso_con_meses(24), egreso="2026-05-15")   # ya se había ido
    base.vendedor(2, ingreso_con_meses(24), egreso="2026-08-10")   # se fue después del corte
    base.vendedor(3, "2026-07-01")                                  # entró después del corte
    for vid in (1, 2, 3):
        ventas_ultimos(base, vid, [80, 80, 80])
    assert list(score_de(base)["id_vendedor"]) == [2]


def test_modo_vivo_usa_solo_meses_cerrados(base):
    """Corregido (oct 2026): antes el modo vivo tomaba las 3 filas más recientes,
    incluido el mes en curso con ventas parciales (70/70/10 encendía "plan bajo").
    Ahora corta en el último mes cerrado y coincide con el backfill de ese mes."""
    hoy = dt.date.today()
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, (hoy - dt.timedelta(days=24 * 30)).isoformat())
    a2, m2 = meses_atras(hoy.year, hoy.month, 2)
    a1, m1 = meses_atras(hoy.year, hoy.month, 1)
    base.venta(1, a2, m2, pct_plan=70)
    base.venta(1, a1, m1, pct_plan=70)
    base.venta(1, hoy.year, hoy.month, pct_plan=10)   # mes en curso, parcial

    vivo = fila(score_engine.calcular_scores(meses_tendencia=3), 1)
    cerrado = fila(score_engine.calcular_scores(meses_tendencia=3, hasta_anio=a1, hasta_mes=m1), 1)
    assert vivo["señales_activas"] == cerrado["señales_activas"] == []
    assert vivo["pct_plan_3m"] == cerrado["pct_plan_3m"] == 70.0


def test_modo_vivo_ignora_filas_de_meses_futuros(base):
    """Los 'perdidos' a +12 meses dejaban filas futuras de balanza muy negativas."""
    hoy = dt.date.today()
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, (hoy - dt.timedelta(days=24 * 30)).isoformat())
    for i in (1, 2, 3):
        a, m = meses_atras(hoy.year, hoy.month, i)
        base.venta(1, a, m, pct_plan=80)
        base.balanza(1, a, m, balanza=5, ticket_promedio=100)
    for i in (1, 2):                                   # meses que todavía no ocurrieron
        a, m = meses_atras(hoy.year, hoy.month, -i)
        base.venta(1, a, m, pct_plan=0, plan=1000)
        base.balanza(1, a, m, balanza=-90, ticket_promedio=0)
    assert fila(score_engine.calcular_scores(meses_tendencia=3), 1)["señales_activas"] == []


def test_ultimo_mes_cerrado():
    assert score_engine.ultimo_mes_cerrado(dt.date(2026, 10, 16)) == (2026, 9)
    assert score_engine.ultimo_mes_cerrado(dt.date(2026, 1, 1)) == (2025, 12)


def test_sparklines_usan_los_mismos_meses_que_el_score(base):
    hoy = dt.date.today()
    base.grupo(1, riesgo_base=0.10)
    base.vendedor(1, (hoy - dt.timedelta(days=24 * 30)).isoformat())
    for i, pct in ((3, 60), (2, 70), (1, 80), (0, 5), (-1, 0)):
        a, m = meses_atras(hoy.year, hoy.month, i)
        base.venta(1, a, m, pct_plan=pct)
    assert score_engine.obtener_sparklines(3)[1] == [60, 70, 80]
