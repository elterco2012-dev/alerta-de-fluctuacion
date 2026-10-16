"""
scripts/chequeo_integridad.py
-----------------------------
Chequeo de integridad de data/wurth.db: verifica con números reales los
problemas de datos que señaló la auditoría de octubre 2026
(docs/AUDITORIA_2026-10.md). Solo muestra CONTEOS, nunca nombres.

Solo LECTURA (la base se abre en modo read-only). No usa pandas.
    python scripts\\chequeo_integridad.py

Cada línea marcada con [!] es algo a revisar antes de confiar en el score.
"""

import argparse
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "wurth.db")
TABLAS_MENSUALES = ("ventas_mensual", "balanza_clientes", "actividad_mensual",
                    "acompanamiento_mensual", "ausencias_mensual")


def abrir_solo_lectura(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def existe(con, tabla):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                       (tabla,)).fetchone() is not None


def uno(con, sql, params=()):
    fila = con.execute(sql, params).fetchone()
    return fila[0] if fila else None


def chequear(con, hoy):
    """Devuelve lista de (alerta: bool, texto)."""
    out = []
    per_hoy = hoy.year * 100 + hoy.month

    # 1. Filas de meses futuros y del mes en curso (el modo vivo toma las 3 más recientes)
    for t in TABLAS_MENSUALES:
        if not existe(con, t):
            out.append((True, f"{t}: la tabla no existe"))
            continue
        maxp = uno(con, f"SELECT MAX(anio*100+mes) FROM {t}")
        fut = uno(con, f"SELECT COUNT(*) FROM {t} WHERE anio*100+mes > ?", (per_hoy,))
        cur = uno(con, f"SELECT COUNT(*) FROM {t} WHERE anio*100+mes = ?", (per_hoy,))
        out.append((fut > 0, f"{t}: último período {maxp}; filas de meses FUTUROS: {fut}; "
                             f"filas del mes en curso (parcial): {cur}"))

    # 2. Plan faltante por mes (un fallo de vplan deja plan=0 en todas las filas)
    if existe(con, "ventas_mensual"):
        filas = con.execute("""
            SELECT anio*100+mes, COUNT(*), SUM(CASE WHEN plan > 0 THEN 1 ELSE 0 END)
            FROM ventas_mensual GROUP BY anio*100+mes ORDER BY 1 DESC LIMIT 18""").fetchall()
        sin_plan = [f"{p}" for p, n, con_plan in filas if n and con_plan == 0]
        out.append((bool(sin_plan), "ventas_mensual: meses sin NINGÚN plan cargado: "
                                    + (", ".join(sin_plan) if sin_plan else "ninguno")))

    # 3. Vendedores
    if existe(con, "vendedores"):
        act = uno(con, "SELECT COUNT(*) FROM vendedores WHERE activo=1")
        sin_ventas = uno(con, """SELECT COUNT(*) FROM vendedores v WHERE activo=1
            AND NOT EXISTS (SELECT 1 FROM ventas_mensual vm WHERE vm.id_vendedor=v.id_vendedor)""")
        nuevos_ult_60 = uno(con, """SELECT COUNT(*) FROM vendedores
            WHERE fecha_ingreso >= date(?, '-60 days')""", (hoy.isoformat(),))
        out.append((sin_ventas > 0, f"vendedores activos: {act}; sin ninguna fila de ventas "
                                    f"(quedan FUERA del score): {sin_ventas}"))
        out.append((nuevos_ult_60 == 0,
                    f"vendedores con ingreso en los últimos 60 días: {nuevos_ult_60} "
                    "(si es 0, revisar que el paso 1 de sync_y_alertas.bat —padrón con "
                    "inicializar_db.py— esté corriendo: es el único que da de alta vendedores)"))
        inconsist = uno(con, """SELECT COUNT(*) FROM vendedores
            WHERE (activo=1 AND fecha_egreso IS NOT NULL) OR (activo=0 AND fecha_egreso IS NULL)""")
        out.append((inconsist > 0, f"vendedores con activo/fecha_egreso inconsistentes: {inconsist}"))
        basura = uno(con, "SELECT COUNT(*) FROM vendedores WHERE fecha_egreso = fecha_ingreso")
        out.append((False, f"vendedores con fecha_egreso = fecha_ingreso (se ignoran): {basura}"))
        homonimos = uno(con, """SELECT COUNT(*) FROM vendedores v
            WHERE COALESCE(v.es_supervisor,0)=0 AND v.activo=1 AND v.nombre IN
                  (SELECT DISTINCT supervisor FROM vendedores WHERE supervisor <> '')""")
        out.append((homonimos > 0, f"vendedores activos excluidos del score por llamarse igual "
                                   f"que un supervisor sin ser supervisor: {homonimos}"))
        motivo = uno(con, """SELECT COUNT(*) FROM vendedores
            WHERE activo=0 AND motivo_egreso IS NOT NULL AND motivo_egreso <> ''""")
        egr = uno(con, "SELECT COUNT(*) FROM vendedores WHERE activo=0")
        out.append((motivo == 0, f"egresados con motivo_egreso cargado: {motivo} de {egr} "
                                 "(sin motivo no se pueden separar renuncias de despidos)"))

    # 4. Cobertura de egresados recientes
    if existe(con, "vendedores") and existe(con, "score_historico"):
        egr18 = uno(con, """SELECT COUNT(*) FROM vendedores WHERE activo=0
            AND fecha_egreso >= date(?, '-18 months') AND fecha_egreso <> fecha_ingreso""",
                    (hoy.isoformat(),))
        con_score = uno(con, """SELECT COUNT(*) FROM vendedores v WHERE activo=0
            AND fecha_egreso >= date(?, '-18 months') AND fecha_egreso <> fecha_ingreso
            AND EXISTS (SELECT 1 FROM score_historico s WHERE s.id_vendedor = v.id_vendedor
                AND s.periodo >= strftime('%Y-%m', date(v.fecha_egreso, '-3 months'))
                AND s.periodo <  strftime('%Y-%m', v.fecha_egreso))""", (hoy.isoformat(),))
        out.append((egr18 and con_score < egr18,
                    f"egresados últimos 18 meses: {egr18}; con score en sus 3 meses previos "
                    f"(evaluables): {con_score}"))

    # 5. score_historico
    if existe(con, "score_historico"):
        periodos = con.execute("SELECT periodo, COUNT(*) FROM score_historico "
                               "GROUP BY periodo ORDER BY periodo").fetchall()
        if periodos:
            out.append((len(periodos) < 6, f"score_historico: {len(periodos)} períodos "
                                           f"({periodos[0][0]} a {periodos[-1][0]})"))
    else:
        out.append((True, "score_historico no existe: correr scripts/backfill_scores.py"))

    # 6. Grupos con muestra chica (riesgo_base poco confiable)
    if existe(con, "grupos"):
        filas = con.execute("""
            SELECT g.id_grupo, g.riesgo_base, COUNT(v.id_vendedor)
            FROM grupos g LEFT JOIN vendedores v ON v.id_grupo = g.id_grupo
                 AND v.fecha_ingreso IS NOT NULL
                 AND (v.fecha_egreso IS NULL OR v.fecha_egreso <> v.fecha_ingreso)
            GROUP BY g.id_grupo""").fetchall()
        quemados = [(rb, n) for _, rb, n in filas if rb is not None and rb > 0.40]
        chicos = [n for _, rb, n in filas if rb is not None and rb > 0.40 and n < 10]
        out.append((bool(chicos), f"grupos con riesgo_base > 0.40: {len(quemados)}; de ellos con "
                                  f"menos de 10 vendedores en la historia: {len(chicos)}"))

    # 7. Ausencias: filas solo en meses con ausencias → el promedio se infla
    if existe(con, "ausencias_mensual"):
        cols = [r[1] for r in con.execute("PRAGMA table_info(ausencias_mensual)")]
        if "dias_no_vac" not in cols:
            out.append((True, "ausencias_mensual sin columna dias_no_vac: la señal de ausencias "
                              "está apagada (ver sincronizar_reactor.py)"))
        else:
            ceros = uno(con, "SELECT COUNT(*) FROM ausencias_mensual WHERE dias_no_vac = 0")
            total = uno(con, "SELECT COUNT(*) FROM ausencias_mensual")
            out.append((total and ceros == 0,
                        f"ausencias_mensual: {total} filas, {ceros} con 0 días no vacacionales "
                        "(si casi no hay ceros, la tabla solo guarda meses CON ausencias y el "
                        "promedio del motor se infla)"))
    if existe(con, "acompanamiento_mensual"):
        cols = [r[1] for r in con.execute("PRAGMA table_info(acompanamiento_mensual)")]
        if "visitas_sup_realizadas" not in cols:
            out.append((True, "acompanamiento_mensual sin visitas_sup_realizadas: la señal de "
                              "acompañamiento está apagada"))

    # 8. Intervenciones
    if existe(con, "intervenciones"):
        n = uno(con, "SELECT COUNT(*) FROM intervenciones")
        huerf = uno(con, """SELECT COUNT(*) FROM intervenciones i WHERE NOT EXISTS
            (SELECT 1 FROM vendedores v WHERE v.id_vendedor = i.id_vendedor)""")
        demo = uno(con, """SELECT COUNT(*) FROM intervenciones
            WHERE id_vendedor BETWEEN 10002 AND 10015 AND fecha BETWEEN '2025-01-01' AND '2025-01-31'""")
        out.append((huerf > 0 or demo > 0,
                    f"intervenciones: {n}; con vendedor inexistente: {huerf}; con pinta de datos "
                    f"de ejemplo (ids 10002-10015, enero 2025): {demo}"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Chequeo de integridad (solo lectura)")
    ap.add_argument("--db", default=DB_PATH)
    args = ap.parse_args(argv)
    if not os.path.exists(args.db):
        print(f"No existe {args.db}")
        return 1
    con = abrir_solo_lectura(args.db)
    try:
        resultados = chequear(con, date.today())
    finally:
        con.close()
    print("=" * 78)
    print("CHEQUEO DE INTEGRIDAD — data/wurth.db (solo lectura, solo conteos)")
    print("=" * 78)
    for alerta, texto in resultados:
        print(f"  {'[!]' if alerta else '[ok]'} {texto}")
    n = sum(1 for a, _ in resultados if a)
    print("-" * 78)
    print(f"  {n} punto(s) a revisar." if n else "  Sin alertas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
