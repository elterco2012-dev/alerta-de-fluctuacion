"""
pyodbc FALSO para tests de los scripts de sincronización.

Nunca conecta a nada: responde a cada SELECT con filas sintéticas según la
tabla consultada. Se activa poniendo tests/fakes primero en PYTHONPATH.

  FAKE_PYODBC_DATA  ruta a un JSON {"clave": [[fila], ...]} con las filas por
                    consulta (claves: f040, f040_nombres, f040_padron,
                    sbas_hist, vplan, kund, sbas_dias, work_days_log) y
                    "columnas_<tabla>" para cursor.columns()
  FAKE_PYODBC_FAIL  claves separadas por coma cuya consulta debe fallar

Cualquier sentencia que no sea SELECT levanta AssertionError: los sync deben
ser de solo lectura sobre producción.
"""

import json
import os


class Error(Exception):
    pass


def _clave(sql):
    s = " ".join(sql.split())
    if "work_days_log" in s:
        return "work_days_log"
    if "FROM vplan" in s:
        return "vplan"
    if "FROM kund" in s:
        return "kund"
    if "1=0" in s:
        return "sonda"
    if "IS NOT NULL" in s and "FROM sbas" in s:
        return "sbas_dias"
    if "SUM(netwert)" in s:
        return "sbas_hist"
    if "FROM f040" in s and "bvertr" in s:
        return "f040_padron"
    if "FROM f040" in s and "name1" in s and "eintrdat" not in s:
        return "f040_nombres"
    if "FROM f040" in s:
        return "f040"
    return "otra"


class _Cursor:
    def __init__(self):
        self._filas = []
        self.description = []

    def execute(self, sql, *params):
        if not sql.lstrip().upper().startswith("SELECT"):
            raise AssertionError(f"escritura contra producción: {sql[:80]}")
        clave = _clave(sql)
        fallar = {c for c in os.getenv("FAKE_PYODBC_FAIL", "").split(",") if c}
        if clave in fallar:
            raise Error(f"falla simulada en {clave}")
        datos = {}
        if os.getenv("FAKE_PYODBC_DATA"):
            with open(os.environ["FAKE_PYODBC_DATA"], encoding="utf-8") as fh:
                datos = json.load(fh)
        self._filas = [tuple(f) for f in datos.get(clave, [])]
        return self

    def fetchall(self):
        return list(self._filas)

    def columns(self, table=None):
        """Metadatos: nombres en FAKE_PYODBC_DATA["columnas_<tabla>"]."""
        if "columnas" in {c for c in os.getenv("FAKE_PYODBC_FAIL", "").split(",") if c}:
            raise Error("falla simulada en metadatos")
        datos = {}
        if os.getenv("FAKE_PYODBC_DATA"):
            with open(os.environ["FAKE_PYODBC_DATA"], encoding="utf-8") as fh:
                datos = json.load(fh)

        class _Col:
            def __init__(self, nombre):
                self.column_name = nombre
        return [_Col(c) for c in datos.get(f"columnas_{table}", [])]

    def close(self):
        pass


class _Conexion:
    def cursor(self):
        return _Cursor()

    def close(self):
        pass


def connect(*args, **kwargs):
    return _Conexion()
