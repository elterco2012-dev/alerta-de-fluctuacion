"""
Pruebas del vigilante de tareas propias (scripts/tareas_propias.py), sin el Programador de tareas:
se le pasa lo que respondería PowerShell.

Correr desde la carpeta del proyecto:
    python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import tareas_propias as tp  # noqa: E402

TABLERO = tp.TAREAS["WurthAlertasTablero"]
DIARIA = tp.TAREAS["WurthAlertas"]


def tablero(**cambios):
    leida = {
        "existe": True,
        "acciones": [r'"C:\Program Files\Python312\pythonw.exe" "C:\alerta-de-fluctuacion\scripts\supervisor_dashboard.py"'],
        "cuenta": "SERVICIO LOCAL", "sid": "S-1-5-19", "inicio": "ServiceAccount", "nivel": "Limited",
    }
    leida.update(cambios)
    return leida


def diaria(**cambios):
    leida = {
        "existe": True,
        "acciones": [r"cmd /c C:\alerta-de-fluctuacion\scripts\sync_y_alertas.bat"],
        "cuenta": r"DOMINIO\usuario", "sid": "S-1-5-21-1-2-3-1001", "inicio": "Interactive", "nivel": "Limited",
    }
    leida.update(cambios)
    return leida


class Comparar(unittest.TestCase):
    def test_las_dos_como_las_deja_el_proyecto(self):
        self.assertEqual(tp.comparar(TABLERO, tablero()), ("bien", ""))
        self.assertEqual(tp.comparar(DIARIA, diaria()), ("bien", ""))

    def test_acepta_una_accion_sola_como_texto_y_mayusculas_distintas(self):
        self.assertEqual(tp.comparar(DIARIA, diaria(acciones=r"CMD /C C:\ALERTA-DE-FLUCTUACION\SCRIPTS\SYNC_Y_ALERTAS.BAT")),
                         ("bien", ""))

    def test_local_service_por_nombre_si_no_se_pudo_traducir(self):
        self.assertEqual(tp.comparar(TABLERO, tablero(sid=None, cuenta="LOCAL SERVICE")), ("bien", ""))

    def test_otra_cosa_con_el_mismo_nombre(self):
        estado, detalle = tp.comparar(TABLERO, tablero(acciones=[r"cmd /c C:\taginfo\iniciar_dashboard.bat"]))
        self.assertEqual(estado, "cambió")
        self.assertIn("taginfo", detalle)

    def test_una_accion_de_mas(self):
        estado, _ = tp.comparar(DIARIA, diaria(acciones=[r"cmd /c C:\alerta-de-fluctuacion\scripts\sync_y_alertas.bat",
                                                         r"cmd /c C:\otro\algo.bat"]))
        self.assertEqual(estado, "cambió")

    def test_el_tablero_como_system(self):
        estado, detalle = tp.comparar(TABLERO, tablero(cuenta="SYSTEM", sid="S-1-5-18"))
        self.assertEqual(estado, "cambió")
        self.assertIn("LOCAL SERVICE", detalle)

    def test_la_diaria_como_cuenta_de_servicio_o_sin_sesion(self):
        for cambios in ({"cuenta": "SYSTEM", "sid": "S-1-5-18", "inicio": "ServiceAccount"},
                        {"cuenta": "SERVICIO LOCAL", "sid": "S-1-5-19", "inicio": "ServiceAccount"},
                        {"inicio": "S4U"}):
            with self.subTest(**cambios):
                self.assertEqual(tp.comparar(DIARIA, diaria(**cambios))[0], "cambió")

    def test_con_mas_privilegios(self):
        self.assertEqual(tp.comparar(TABLERO, tablero(nivel="Highest"))[0], "cambió")

    def test_no_esta(self):
        self.assertEqual(tp.comparar(DIARIA, {"existe": False})[0], "no está")


class Revisar(unittest.TestCase):
    def leer_falso(self, respuestas):
        def leer(nombre):
            respuesta = respuestas[nombre]
            if isinstance(respuesta, Exception):
                raise respuesta
            return respuesta
        return mock.patch.object(tp, "leer", side_effect=leer)

    def test_todo_bien(self):
        with self.leer_falso({"WurthAlertasTablero": tablero(), "WurthAlertas": diaria()}):
            resultados = tp.revisar()
        self.assertEqual([r["estado"] for r in resultados], ["bien", "bien"])

    def test_si_no_se_puede_leer_lo_dice(self):
        with self.leer_falso({"WurthAlertasTablero": tablero(),
                              "WurthAlertas": tp.NoSePudoLeer("Acceso denegado")}):
            resultados = tp.revisar()
        self.assertEqual(resultados[1]["estado"], "no se pudo leer")
        self.assertIn("Acceso denegado", tp.resumen(resultados))

    def test_si_no_ve_ni_su_propia_tarea_no_avisa_que_faltan(self):
        with self.leer_falso({"WurthAlertasTablero": {"existe": False}, "WurthAlertas": {"existe": False}}):
            resultados = tp.revisar(propia="WurthAlertasTablero")
        self.assertEqual([r["estado"] for r in resultados], ["no se pudo leer", "no se pudo leer"])

    def test_si_ve_la_suya_un_no_esta_es_de_verdad(self):
        with self.leer_falso({"WurthAlertasTablero": tablero(), "WurthAlertas": {"existe": False}}):
            resultados = tp.revisar(propia="WurthAlertasTablero")
        self.assertEqual([r["estado"] for r in resultados], ["bien", "no está"])


if __name__ == "__main__":
    unittest.main()
