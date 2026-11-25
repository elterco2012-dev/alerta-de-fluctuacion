"""
Pruebas del candado de solo lectura (src/solo_lectura.py).

Correr desde la carpeta del proyecto, con cualquiera de los dos Python:
    python -m unittest discover -s tests -v
No necesitan pyodbc ni conexión a ninguna base.
"""

import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from solo_lectura import ConsultaNoPermitida, envolver, exigir_select  # noqa: E402


class ExigirSelect(unittest.TestCase):
    def test_deja_pasar_un_select(self):
        for sql in (
            "SELECT 1",
            "select vertr, name1 from f040",
            "SELECT * FROM t;",
            "SELECT * FROM t ;  \n",
            "  \n\t SELECT 1",
            "-- un comentario\nSELECT 1",
            "/* un comentario */ SELECT 1",
            "\n  -- uno\n  /* dos\n  líneas */\n  SELECT TOP 1 ACCNT_CODE FROM dbo.SALFLDGRAN",
            "SELECT fecha_update, x_delete FROM t",
            "SELECT REPLACE(nombre, 'a', 'b') FROM t",
        ):
            with self.subTest(sql=sql):
                self.assertEqual(exigir_select(sql), sql)

    def test_frena_lo_que_escribe(self):
        for sql in (
            "INSERT INTO t VALUES (1)",
            "UPDATE t SET x = 1",
            "DELETE FROM t",
            "MERGE INTO t USING s ON 1 = 1 WHEN MATCHED THEN DELETE",
            "TRUNCATE TABLE t",
            "  delete from t",
            "REPLACE INTO t VALUES (1)",
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(ConsultaNoPermitida):
                    exigir_select(sql)

    def test_frena_el_ddl_y_los_permisos(self):
        for sql in (
            "CREATE TABLE t (x INT)",
            "DROP TABLE t",
            "ALTER TABLE t ADD y INT",
            "RENAME TABLE t TO u",
            "GRANT SELECT ON t TO public",
            "REVOKE ALL ON t FROM public",
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(ConsultaNoPermitida):
                    exigir_select(sql)

    def test_frena_dos_sentencias_juntas(self):
        for sql in (
            "SELECT 1; DELETE FROM t",
            "SELECT 1; SELECT 2",
            "SELECT 1;\nDROP TABLE t;",
            # SQL Server acepta otra sentencia sin «;»
            "SELECT 1 DELETE FROM t",
            "SELECT * FROM t WHERE x = 1\nUPDATE t SET x = 2",
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(ConsultaNoPermitida):
                    exigir_select(sql)

    def test_frena_select_into(self):
        for sql in (
            "SELECT * INTO nueva FROM t",              # SQL Server: crea la tabla
            "SELECT * FROM t INTO TEMP tmp",            # Informix
            "SELECT * FROM t INTO OUTFILE '/tmp/x'",   # MySQL: escribe un archivo
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(ConsultaNoPermitida):
                    exigir_select(sql)

    def test_frena_lo_que_ejecuta(self):
        for sql in (
            "EXEC sp_algo",
            "EXECUTE PROCEDURE p()",
            "{call borrar()}",
            "SELECT 1 EXEC('DELETE FROM t')",
            "SELECT * FROM OPENQUERY(srv, 'SELECT 1')",
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(ConsultaNoPermitida):
                    exigir_select(sql)

    def test_los_comentarios_no_esconden_nada(self):
        for sql in (
            "/* SELECT */ DELETE FROM t",
            "-- SELECT\nDELETE FROM t",
            # el «--» termina en el primer fin de línea, también en un \r solo
            "-- x\rDELETE FROM t\nSELECT 1",
            # en MySQL lo que va en /*! */ se ejecuta
            "/*!DELETE FROM t WHERE 1 OR (*/ SELECT 1 /*!)*/",
            "/* sin cerrar SELECT 1",
        ):
            with self.subTest(sql=sql):
                with self.assertRaises(ConsultaNoPermitida):
                    exigir_select(sql)

    def test_frena_lo_que_no_es_un_select_solo(self):
        for sql in ("", "   ", "SELECTX 1", "WITH x AS (SELECT 1) SELECT * FROM x",
                    "SHOW TABLES", "(SELECT 1)", None, b"SELECT 1"):
            with self.subTest(sql=sql):
                with self.assertRaises(ConsultaNoPermitida):
                    exigir_select(sql)


class _CursorFalso:
    def __init__(self):
        self.ejecutadas = []
        self.arraysize = 1
        self.filas = [(1,), (2,)]

    def execute(self, sql, *parametros):
        self.ejecutadas.append((sql, parametros))
        return self

    def executemany(self, sql, parametros):
        self.ejecutadas.append((sql, tuple(parametros)))

    def fetchall(self):
        return list(self.filas)

    def __iter__(self):
        return iter(self.filas)

    def __enter__(self):
        return self

    def __exit__(self, *excepcion):
        return False


class _ConexionFalsa:
    def __init__(self):
        self.cursores = []
        self.timeout = 0

    def cursor(self):
        cursor = _CursorFalso()
        self.cursores.append(cursor)
        return cursor

    def __enter__(self):
        return self

    def __exit__(self, *excepcion):
        return False


class ConexionEnvuelta(unittest.TestCase):
    def setUp(self):
        self.real = _ConexionFalsa()
        self.con = envolver(self.real)

    def test_el_select_sale_y_se_puede_encadenar(self):
        cursor = self.con.cursor()
        filas = cursor.execute("SELECT x FROM t WHERE y = ?", 5).fetchall()
        self.assertEqual(filas, [(1,), (2,)])
        self.assertEqual(self.real.cursores[0].ejecutadas, [("SELECT x FROM t WHERE y = ?", (5,))])
        self.assertEqual(list(cursor), [(1,), (2,)])

    def test_lo_que_escribe_no_sale(self):
        cursor = self.con.cursor()
        with self.assertRaises(ConsultaNoPermitida):
            cursor.execute("DELETE FROM t")
        with self.assertRaises(ConsultaNoPermitida):
            cursor.executemany("INSERT INTO t VALUES (?)", [(1,), (2,)])
        with self.assertRaises(ConsultaNoPermitida):
            self.con.execute("UPDATE t SET x = 1")
        for real in self.real.cursores:
            self.assertEqual(real.ejecutadas, [])

    def test_execute_de_la_conexion_tambien_pasa_por_el_candado(self):
        self.con.execute("SELECT 1")
        self.assertEqual(self.real.cursores[-1].ejecutadas, [("SELECT 1", ())])

    def test_los_atributos_van_a_la_conexion_y_al_cursor_reales(self):
        self.con.timeout = 30
        self.assertEqual(self.real.timeout, 30)
        cursor = self.con.cursor()
        cursor.arraysize = 500
        self.assertEqual(self.real.cursores[-1].arraysize, 500)

    def test_with_devuelve_lo_envuelto(self):
        with self.con as con:
            with con.cursor() as cursor:
                with self.assertRaises(ConsultaNoPermitida):
                    cursor.execute("DROP TABLE t")

    def test_envolver_dos_veces_no_cambia_nada(self):
        self.assertIs(envolver(self.con), self.con)


class NadieSeConectaSinElCandado(unittest.TestCase):
    """Toda conexión a MSPA, SUN o Reactor se abre con solo_lectura.conectar()."""

    PERMITIDO = RAIZ / "src" / "solo_lectura.py"
    DIRECTA = re.compile(r"pyodbc\s*\.\s*connect\s*\(|from\s+pyodbc\s+import\s+[^\n]*\bconnect\b")

    def test_ningun_archivo_llama_a_pyodbc_connect(self):
        salteadas = {".git", ".claude", ".python", "__pycache__", "tests"}
        directas = []
        for ruta in RAIZ.rglob("*.py"):
            if salteadas & set(ruta.relative_to(RAIZ).parts) or ruta == self.PERMITIDO:
                continue
            for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
                if self.DIRECTA.search(linea.split("#", 1)[0]):
                    directas.append(f"{ruta.relative_to(RAIZ)}:{numero}")
        self.assertEqual(directas, [], "Conectarse con solo_lectura.conectar(), no con pyodbc.connect()")


if __name__ == "__main__":
    unittest.main()
