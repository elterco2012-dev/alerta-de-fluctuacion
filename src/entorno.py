"""
Dónde está el .env del proyecto y cómo se lee.

Desde el 25/11 vive en claves\\.env y no en la raíz (decisión del usuario): la subcarpeta claves\\ le niega la lectura
a LOCAL SERVICE (el tablero) y a la cuenta de Claude con herencia, así un editor que reescribe el archivo con un
temporal no le saca el «Denegar». La crea y la cierra scripts\\proteger_carpeta.bat, que también copia ahí el .env de
la raíz si todavía no se mudó.

Solo para la mudanza: si claves\\.env no está y el .env de la raíz sí, se lee el de la raíz y se avisa. El de la raíz
se borra cuando la tarea diaria corrió bien con el nuevo.

Todo lo que necesita el .env lo lee con este módulo: tests/test_entorno.py falla si otro archivo lo busca por su cuenta.
Solo biblioteca estándar: lo usan el Python de 32 bits y el de 64.
"""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA = RAIZ / "claves" / ".env"
_RUTA_VIEJA = RAIZ / ".env"  # solo para la mudanza; se saca cuando el de la raíz ya no exista en la VM

_avisado = False


def ruta():
    """El .env que se usa: claves\\.env, o el de la raíz si todavía no se mudó."""
    # os.path.exists y no Path.exists: si la cuenta no puede leer la carpeta, devuelve False en vez de fallar.
    if not os.path.exists(RUTA) and os.path.exists(_RUTA_VIEJA):
        return _RUTA_VIEJA
    return RUTA


def _lineas(archivo):
    """Las líneas del archivo. Acepta lo que guarda el Bloc de notas: UTF-8 con o sin BOM, o ANSI."""
    try:
        datos = Path(archivo).read_bytes()
    except OSError:
        return []
    try:
        texto = datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = datos.decode("cp1252", errors="replace")
    return texto.splitlines()


def valores():
    """Las variables del .env como diccionario ({} si no hay archivo o no se puede leer)."""
    global _avisado
    archivo = ruta()
    datos = {}
    for linea in _lineas(archivo):
        clave, igual, valor = linea.strip().partition("=")
        clave = clave.strip()
        if not igual or not clave or clave.startswith("#"):
            continue
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        datos[clave] = valor
    if datos and archivo == _RUTA_VIEJA and not _avisado:
        _avisado = True
        print("AVISO: el .env sigue en la carpeta del proyecto. Corré scripts\\proteger_carpeta.bat como "
              "administrador para mudarlo a claves\\.env.", file=sys.stderr)
    return datos


def leer(nombre):
    """El valor de una variable: del entorno o, si no está, del .env ("" si no hay)."""
    if os.environ.get(nombre):
        return os.environ[nombre]
    return valores().get(nombre, "")


def cargar():
    """Pone las variables del .env en el entorno, sin pisar las que ya están."""
    for clave, valor in valores().items():
        os.environ.setdefault(clave, valor)
