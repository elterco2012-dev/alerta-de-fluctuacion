"""
Pruebas de src/entorno.py: el .env vive en claves\\.env (desde el 25/11), y nada más lo busca por su cuenta.

Correr desde la carpeta del proyecto:
    python -m unittest discover -s tests -v
"""

import contextlib
import io
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import entorno  # noqa: E402


class LeerElEnv(unittest.TestCase):
    def setUp(self):
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        raiz = Path(carpeta.name)
        (raiz / "claves").mkdir()
        self.nuevo = raiz / "claves" / ".env"
        self.viejo = raiz / ".env"
        for parche in (mock.patch.object(entorno, "RUTA", self.nuevo),
                       mock.patch.object(entorno, "_RUTA_VIEJA", self.viejo),
                       mock.patch.object(entorno, "_avisado", False),
                       mock.patch.dict(os.environ)):
            parche.start()
            self.addCleanup(parche.stop)
        for clave in ("ALERT_TO", "AVISOS_TO", "SUN_USER"):
            os.environ.pop(clave, None)

    def valores(self):
        avisos = io.StringIO()
        with contextlib.redirect_stderr(avisos):
            datos = entorno.valores()
        return datos, avisos.getvalue()

    def test_lee_claves_env(self):
        self.nuevo.write_text("# comentario\nALERT_TO=a@b\nAVISOS_TO='c@d'\n", encoding="utf-8")
        self.assertEqual(self.valores(), ({"ALERT_TO": "a@b", "AVISOS_TO": "c@d"}, ""))

    def test_el_nuevo_gana_aunque_quede_el_de_la_raiz(self):
        self.nuevo.write_text("ALERT_TO=nuevo\n", encoding="utf-8")
        self.viejo.write_text("ALERT_TO=viejo\n", encoding="utf-8")
        self.assertEqual(self.valores(), ({"ALERT_TO": "nuevo"}, ""))

    def test_mientras_no_se_mudo_lee_el_de_la_raiz_y_avisa(self):
        self.viejo.write_text("ALERT_TO=viejo\n", encoding="utf-8")
        datos, avisos = self.valores()
        self.assertEqual(datos, {"ALERT_TO": "viejo"})
        self.assertIn("proteger_carpeta.bat", avisos)

    def test_sin_env_no_hay_nada(self):
        self.assertEqual(self.valores(), ({}, ""))

    def test_si_no_lo_puede_leer_no_hay_nada_y_no_falla(self):
        self.nuevo.write_text("ALERT_TO=x\n", encoding="utf-8")
        with mock.patch.object(Path, "read_bytes", side_effect=PermissionError("denegado")):
            self.assertEqual(self.valores(), ({}, ""))

    def test_cargar_no_pisa_lo_que_ya_esta(self):
        self.nuevo.write_text("ALERT_TO=archivo\nAVISOS_TO=archivo\n", encoding="utf-8")
        os.environ["ALERT_TO"] = "entorno"
        entorno.cargar()
        self.assertEqual((os.environ["ALERT_TO"], os.environ["AVISOS_TO"]), ("entorno", "archivo"))


class NadieBuscaElEnvPorSuCuenta(unittest.TestCase):
    """Solo src/entorno.py sabe dónde está el .env: que ningún otro archivo lo vuelva a buscar en la raíz."""

    # Un texto entre comillas, sin espacios, que termina en .env: una ruta, no un mensaje como «falta X en .env».
    RUTA_ENV = re.compile(r"""(['"])[^'"\s]*\.env\1""")

    def test_solo_entorno_lee_el_env(self):
        salteadas = {".git", ".claude", ".python", "__pycache__", "tests"}
        encontrados = []
        for ruta in RAIZ.rglob("*.py"):
            relativa = ruta.relative_to(RAIZ)
            if salteadas & set(relativa.parts) or relativa == Path("src/entorno.py"):
                continue
            for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
                if "load_dotenv" in linea or self.RUTA_ENV.search(linea):
                    encontrados.append(f"{relativa}:{numero}")
        self.assertEqual(encontrados, [], "El .env se lee con src/entorno.py (está en claves\\.env)")


if __name__ == "__main__":
    unittest.main()
