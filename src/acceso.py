"""
src/acceso.py
-------------
Control de acceso por rol para la vista de supervisor (y futuras vistas).

A esta pantalla entran cuatro tipos de usuario, con distinto alcance:

  - supervisor → ve SOLO su propia zona
  - director   → ve las zonas de los supervisores que tiene a cargo
  - rrhh       → ve toda la empresa
  - gerencia   → ve toda la empresa

NO hay login con contraseña: el usuario se identifica eligiendo su nombre en un
selector (la pantalla se asume detrás de un acceso corporativo). Este módulo solo
resuelve "quién sos → qué supervisores podés ver".

CÓMO COMPLETARLO CON DATOS REALES
---------------------------------
- Los SUPERVISORES se generan automáticamente desde la tabla `grupos` de la DB:
  no hay que listarlos a mano. Si mañana hay un supervisor nuevo en Informix,
  aparece solo.
- Los DIRECTORES y los usuarios de RRHH/GERENCIA NO están en la DB: definilos en
  los diccionarios DIRECTORES y STAFF de abajo. Los valores actuales son un
  EJEMPLO plausible (GBA vs Interior) — reemplazalos por la estructura real.
"""

from __future__ import annotations
import sqlite3, os
from typing import Optional

# Ruta a la DB (misma que usa score_engine por defecto).
_DB = os.path.join(os.path.dirname(__file__), "..", "data", "wurth.db")

# ── Configuración editable ───────────────────────────────────────────────────
# Director → lista de supervisores (por nombre).
#
# Esto es un FALLBACK: si la base ya trae la jerarquía real (columnas `director`
# y `es_supervisor` en `vendedores`, que pobla inicializar_db.py desde f040.kz3),
# se usa esa y este diccionario se ignora. Sirve mientras la base no tenga el dato
# (p.ej. con datos seed) o para forzar un mapeo a mano.
DIRECTORES_MANUAL: dict[str, list[str]] = {
    "Dirección GBA": [
        "Zerbatto Jose Luis",
        "Kalpokas Gustavo",
        "Galla Gabriel Isaac",
        "Pérez Roberto",
    ],
    "Dirección Interior": [
        "Torres Miguel",
        "Martínez Sandra",
        "Vega Claudia",
    ],
}

# Usuarios con acceso total (RRHH y Gerencia). clave → rol.
# EJEMPLO — reemplazar por las personas reales.
STAFF: dict[str, str] = {
    "RRHH":     "rrhh",
    "Gerencia": "gerencia",
}

# Etiquetas legibles por rol (para el selector y los encabezados).
ROL_LABEL = {
    "supervisor": "Supervisor",
    "director":   "Director",
    "rrhh":       "RRHH",
    "gerencia":   "Gerencia",
}


# ── Resolución ───────────────────────────────────────────────────────────────
def _tiene_columna(con, tabla: str, columna: str) -> bool:
    return any(r[1] == columna for r in con.execute(f"PRAGMA table_info({tabla})"))


def _supervisores_db() -> list[str]:
    """
    Lista de supervisores reales. Une lo que haya en `grupos.supervisor` y en
    `vendedores.supervisor` (según cómo esté poblada la base) para ser robusto a
    datos seed y a datos reales.
    """
    con = sqlite3.connect(_DB)
    try:
        sups: set[str] = set()
        for tabla in ("grupos", "vendedores"):
            try:
                filas = con.execute(
                    f"SELECT DISTINCT supervisor FROM {tabla} "
                    f"WHERE supervisor IS NOT NULL AND supervisor <> ''"
                ).fetchall()
                sups.update(f[0] for f in filas)
            except sqlite3.Error:
                pass
    finally:
        con.close()
    return sorted(sups)


def _directores_db() -> dict[str, list[str]]:
    """
    Jerarquía director → [supervisores] derivada de la base real.
    Cada supervisor (es_supervisor=1) reporta al director de su fila (kz3).
    Devuelve {} si la base no tiene el dato → el caller usa el fallback manual.
    """
    con = sqlite3.connect(_DB)
    try:
        if not (_tiene_columna(con, "vendedores", "director")
                and _tiene_columna(con, "vendedores", "es_supervisor")):
            return {}
        filas = con.execute(
            "SELECT DISTINCT director, supervisor FROM vendedores "
            "WHERE es_supervisor = 1 AND director <> '' AND supervisor <> ''"
        ).fetchall()
    except sqlite3.Error:
        return {}
    finally:
        con.close()
    jer: dict[str, list[str]] = {}
    for director, supervisor in filas:
        jer.setdefault(director, [])
        if supervisor not in jer[director]:
            jer[director].append(supervisor)
    for sups in jer.values():
        sups.sort()
    return jer


def _directores() -> dict[str, list[str]]:
    """Jerarquía efectiva: la real de la base si existe, si no la manual."""
    return _directores_db() or DIRECTORES_MANUAL


def listar_usuarios() -> list[dict]:
    """
    Devuelve todos los usuarios seleccionables, agrupables por rol:
        [{clave, etiqueta, rol}, ...]
    El orden es: gerencia/RRHH primero, luego directores, luego supervisores.
    `clave` es el identificador único que viaja en el query param `?usuario=`.
    """
    usuarios: list[dict] = []
    for clave, rol in STAFF.items():
        usuarios.append({"clave": clave, "etiqueta": clave, "rol": rol})
    for director in _directores():
        usuarios.append({"clave": director, "etiqueta": director, "rol": "director"})
    for sup in _supervisores_db():
        usuarios.append({"clave": sup, "etiqueta": sup, "rol": "supervisor"})
    return usuarios


def resolver(clave: Optional[str]) -> Optional[dict]:
    """
    Resuelve un usuario a su alcance de visión.
    Devuelve None si la clave no existe (o es None).

    Retorno:
        {
          "clave":     str,
          "rol":       'supervisor' | 'director' | 'rrhh' | 'gerencia',
          "etiqueta":  str,
          "supervisores": list[str] | None,   # None = toda la empresa
          "ve_todo":   bool,
        }
    """
    if not clave:
        return None

    # Staff (RRHH / Gerencia): acceso total.
    if clave in STAFF:
        return {"clave": clave, "rol": STAFF[clave], "etiqueta": clave,
                "supervisores": None, "ve_todo": True}

    # Director: ve sus supervisores a cargo.
    directores = _directores()
    if clave in directores:
        return {"clave": clave, "rol": "director", "etiqueta": clave,
                "supervisores": list(directores[clave]), "ve_todo": False}

    # Supervisor: ve solo su zona. Validar contra la DB.
    if clave in _supervisores_db():
        return {"clave": clave, "rol": "supervisor", "etiqueta": clave,
                "supervisores": [clave], "ve_todo": False}

    return None


def puede_ver(usuario: Optional[dict], supervisor: str) -> bool:
    """¿El usuario tiene permiso de ver la zona de `supervisor`?"""
    if usuario is None:
        return False
    if usuario["ve_todo"]:
        return True
    return supervisor in (usuario["supervisores"] or [])
