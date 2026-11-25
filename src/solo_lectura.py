"""
Candado de solo lectura para las bases de afuera: MSPA (Informix), SUN (SQL Server)
y Reactor (MySQL).

Esas tres bases son de producción y este proyecto solo las lee (CLAUDE.md, «REGLA
ABSOLUTA»). Hasta que haya usuarios de solo lectura en SUN y en MSPA, los usuarios
de los DSN pueden escribir, así que la defensa está en el código: toda conexión a
esas bases se abre con `conectar()`, y cada consulta pasa por `exigir_select()`
antes de salir. Si no es un SELECT solo, no sale y el script falla.

No se usa para data/wurth.db (SQLite): esa base es nuestra y se escribe.

Qué frena `exigir_select()`:
- lo que no empieza con SELECT, después de espacios y comentarios;
- más de una sentencia (un «;» que no sea el último carácter);
- una palabra que escribe o ejecuta (INSERT, UPDATE, DELETE, DROP, CREATE, EXEC,
  INTO...) en cualquier parte del texto, también dentro de comillas y comentarios.
  SQL Server acepta otra sentencia después de un SELECT sin «;», y SELECT ... INTO
  crea una tabla (en MySQL, escribe un archivo en el servidor). Si una de esas
  palabras aparece en un texto o en un nombre, la consulta se frena aunque no
  escriba: es preferible a dejar pasar una que escribe.

Es un control del texto de la consulta, no un permiso de la base: la solución de
fondo siguen siendo los usuarios de solo lectura.
"""

import re


class ConsultaNoPermitida(RuntimeError):
    """Una consulta a una base de afuera que no es un SELECT solo."""


# Lo que se saltea al principio: espacios y comentarios. El «--» termina en el primer
# fin de línea (\r o \n) y el «/* */» en el primer «*/», así nunca se saltea más de lo
# que saltea la base. «/*!» no es un comentario en MySQL (lo de adentro se ejecuta):
# no se saltea, y entonces la consulta no empieza con SELECT.
_INICIO = re.compile(r"(?:\s|--[^\r\n]*|/\*(?!!).*?\*/)*", re.S)
_SELECT = re.compile(r"SELECT\b", re.I)
_PROHIBIDAS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|TRUNCATE|DROP|ALTER|CREATE|RENAME|GRANT|REVOKE|"
    r"DENY|EXEC|EXECUTE|CALL|INTO|BULK|BACKUP|RESTORE|DBCC|KILL|SHUTDOWN|"
    r"RECONFIGURE|OPENQUERY|OPENROWSET|OPENDATASOURCE)\b",
    re.I,
)


def _muestra(sql):
    texto = " ".join(str(sql).split())
    return texto if len(texto) <= 120 else texto[:117] + "..."


def exigir_select(sql):
    """Devuelve `sql` si es un SELECT solo; si no, lanza ConsultaNoPermitida."""
    if not isinstance(sql, str):
        raise ConsultaNoPermitida(
            f"La consulta tiene que ser un texto, no {type(sql).__name__}."
        )
    resto = sql[_INICIO.match(sql).end():]
    if not _SELECT.match(resto):
        raise ConsultaNoPermitida(
            "En las bases de afuera solo se permite SELECT: " + _muestra(sql)
        )
    cuerpo = sql.rstrip()
    if cuerpo.endswith(";"):
        cuerpo = cuerpo[:-1]
    if ";" in cuerpo:
        raise ConsultaNoPermitida(
            "Una sola sentencia por consulta (hay un «;» en el medio): " + _muestra(sql)
        )
    prohibida = _PROHIBIDAS.search(sql)
    if prohibida:
        raise ConsultaNoPermitida(
            f"La consulta tiene «{prohibida.group(1).upper()}», que escribe o ejecuta: "
            + _muestra(sql)
        )
    return sql


class _CursorSoloLectura:
    """Un cursor de pyodbc al que cada consulta le pasa por exigir_select()."""

    __slots__ = ("_cursor",)

    def __init__(self, cursor):
        object.__setattr__(self, "_cursor", cursor)

    def execute(self, sql, *parametros):
        exigir_select(sql)
        self._cursor.execute(sql, *parametros)
        return self

    def executemany(self, sql, parametros):
        exigir_select(sql)
        return self._cursor.executemany(sql, parametros)

    def __getattr__(self, nombre):
        return getattr(self._cursor, nombre)

    def __setattr__(self, nombre, valor):
        setattr(self._cursor, nombre, valor)

    def __iter__(self):
        return iter(self._cursor)

    def __next__(self):
        return next(self._cursor)

    def __enter__(self):
        self._cursor.__enter__()
        return self

    def __exit__(self, *excepcion):
        return self._cursor.__exit__(*excepcion)


class _ConexionSoloLectura:
    """Una conexión de pyodbc cuyos cursores tienen el candado puesto."""

    __slots__ = ("_conexion",)

    def __init__(self, conexion):
        object.__setattr__(self, "_conexion", conexion)

    def cursor(self):
        return _CursorSoloLectura(self._conexion.cursor())

    def execute(self, sql, *parametros):
        return self.cursor().execute(sql, *parametros)

    def __getattr__(self, nombre):
        return getattr(self._conexion, nombre)

    def __setattr__(self, nombre, valor):
        setattr(self._conexion, nombre, valor)

    def __enter__(self):
        self._conexion.__enter__()
        return self

    def __exit__(self, *excepcion):
        return self._conexion.__exit__(*excepcion)


def envolver(conexion):
    """Le pone el candado a una conexión ya abierta (ver conectar())."""
    if isinstance(conexion, _ConexionSoloLectura):
        return conexion
    return _ConexionSoloLectura(conexion)


def conectar(cadena, **opciones):
    """pyodbc.connect() con el candado puesto: para MSPA, SUN y Reactor.

    Es la única forma en que el proyecto se conecta a esas bases: la prueba
    tests/test_solo_lectura.py falla si algún archivo llama a pyodbc.connect()
    por su cuenta.
    """
    import pyodbc

    return envolver(pyodbc.connect(cadena, **opciones))
