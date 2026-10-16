"""
Sincronía de pesos y parámetros entre el motor y sus copias.

validar_pesos.py tiene su propia copia de los pesos (corre sin pandas) y
snippets_v3.py otra por etiqueta corta. Si alguien cambia un peso en el motor
y no en las copias, la validación y la explicabilidad mienten en silencio.
"""

import score_engine
import snippets_v3
import validar_pesos


def test_validar_pesos_usa_los_mismos_pesos_que_el_motor():
    assert validar_pesos.PESOS_ACTUAL == score_engine.PESOS


def test_validar_pesos_usa_la_misma_referencia():
    assert validar_pesos.RIESGO_REFERENCIA == score_engine.RIESGO_REFERENCIA


def test_explicabilidad_usa_los_pesos_del_motor():
    for descripcion, peso in score_engine.PESOS.items():
        etiqueta = snippets_v3.senal_corta(descripcion)[0]
        assert snippets_v3.SIGNAL_PESO.get(etiqueta) == peso, (descripcion, etiqueta)


def test_hay_15_senales_con_descripciones_unicas():
    descripciones = [d for _, _, d in score_engine.SEÑALES]
    assert len(descripciones) == 15
    assert len(set(descripciones)) == 15


def test_senales_activas_vigentes():
    activas = {d: p for d, p in score_engine.PESOS.items() if p > 0}
    assert activas == {
        "% Plan < 80% promedio últimos meses": 2.0,
        "En ventana crítica mes 1-3": 1.5,
        "En ventana crítica mes 4-6": 1.0,
        "Grupo con alta rotación histórica": 1.5,
        "Sin clientes nuevos últimos 2 meses": 0.5,
        "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3": 2.0,
        "Balanza clientes negativa 2+ meses consecutivos": 1.5,
        "Ticket promedio cae > 5% por mes": 1.0,
        "Supervisor no acompañó en ventana crítica 1-6": 1.0,
    }
