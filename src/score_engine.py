"""
score_engine.py
---------------
Calcula el score de riesgo de fuga (1-10) por vendedor activo.

Lógica basada en tendencia de los últimos N meses, NO en foto mensual.
Cada señal suma puntos de riesgo. El score final se normaliza a 1-10.

Cuando conectes Informix el lunes, solo cambiás get_connection().
Todo lo demás queda igual.
"""

import sqlite3
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')


def get_connection() -> sqlite3.Connection:
    """
    SIMULADO: conecta a SQLite local.

    LUNES - reemplazar por:
    ─────────────────────────────────────────────────────────
    import pyodbc
    conn_str = (
        "DRIVER={IBM INFORMIX ODBC DRIVER};"
        "SERVER=<servidor>;"
        "DATABASE=<base>;"
        "HOST=<host>;"
        "UID=<usuario>;"
        "PWD=<password>;"
    )
    return pyodbc.connect(conn_str)
    ─────────────────────────────────────────────────────────
    """
    return sqlite3.connect(DB_PATH)


@dataclass
class Señal:
    nombre: str
    peso: float
    descripcion: str
    activa: bool = False


@dataclass
class ScoreVendedor:
    id_vendedor: int
    nombre_grupo: str
    supervisor: str
    tipo: str
    meses_activo: int
    score: float                    # 1.0 - 10.0
    nivel_riesgo: str               # bajo / medio / alto / critico
    señales: list[Señal] = field(default_factory=list)
    pct_plan_3m: Optional[float] = None
    tendencia_plan: Optional[float] = None  # pendiente: negativo = cae
    dias_cero_promedio: Optional[float] = None
    pct_clientes_activos: Optional[float] = None
    en_ventana_critica: bool = False        # primeros 6 meses
    grupo_riesgo_historico: Optional[float] = None


def calcular_scores(meses_tendencia: int = 3) -> pd.DataFrame:
    """
    Retorna DataFrame con score de riesgo de todos los vendedores activos.
    meses_tendencia: cuántos meses hacia atrás mirar (mínimo 2, recomendado 3).
    """
    con = get_connection()

    # ── 1. Vendedores activos ──────────────────────────────────────────────
    vendedores = pd.read_sql("""
        SELECT v.id_vendedor, v.tipo, v.nombre_grupo, v.supervisor,
               v.fecha_ingreso, g.riesgo_base
        FROM vendedores v
        JOIN grupos g ON v.id_grupo = g.id_grupo
        WHERE v.activo = 1
    """, con)

    # ── 2. Últimos N meses de ventas por vendedor activo ───────────────────
    ventas = pd.read_sql(f"""
        SELECT vm.*
        FROM ventas_mensual vm
        JOIN vendedores v ON vm.id_vendedor = v.id_vendedor
        WHERE v.activo = 1
        ORDER BY vm.id_vendedor, vm.anio DESC, vm.mes DESC
    """, con)
    con.close()

    # Fecha de hoy aproximada al último registro disponible
    today = pd.Timestamp("2025-01-24")
    vendedores["fecha_ingreso"] = pd.to_datetime(vendedores["fecha_ingreso"])
    vendedores["meses_activo"] = (
        (today - vendedores["fecha_ingreso"]).dt.days / 30
    ).round().astype(int)

    scores = []

    for _, v in vendedores.iterrows():
        vid = v["id_vendedor"]
        hist = ventas[ventas["id_vendedor"] == vid].head(meses_tendencia)

        if hist.empty:
            continue

        señales = [
            Señal("caída_plan_3m",        peso=2.5, descripcion="% Plan cayendo 3 meses seguidos"),
            Señal("plan_bajo_80",          peso=2.0, descripcion="% Plan < 80% promedio últimos meses"),
            Señal("dias_cero_alto",        peso=1.5, descripcion="Días sin venta > 3 en promedio"),
            Señal("clientes_activos_baja", peso=1.5, descripcion="< 60% de cartera activa"),
            Señal("cobranza_baja",         peso=1.0, descripcion="Cobranza real < 90% de teórica"),
            Señal("ventana_critica_13",    peso=1.5, descripcion="En ventana crítica mes 1-3"),
            Señal("ventana_critica_46",    peso=1.0, descripcion="En ventana crítica mes 4-6"),
            Señal("grupo_quemado",         peso=1.5, descripcion="Grupo con alta rotación histórica"),
            Señal("clientes_nuevos_cero",  peso=0.5, descripcion="Sin clientes nuevos últimos 2 meses"),
        ]

        riesgo_total = 0.0
        pct_plan_vals = hist["pct_plan"].values
        dias_cero_vals = hist["dias_venta_cero"].values
        activos_pct = (hist["clientes_activos"] / hist["total_clientes"]).values
        cob_pct = hist["pct_cobranza"].values
        nuevos = hist["clientes_nuevos"].values

        # Señal 1: tendencia plan cayendo (pendiente negativa)
        if len(pct_plan_vals) >= 2:
            x = np.arange(len(pct_plan_vals))
            pendiente = np.polyfit(x[::-1], pct_plan_vals, 1)[0]  # más reciente primero
            if pendiente < -3:
                señales[0].activa = True
                riesgo_total += señales[0].peso
        else:
            pendiente = 0

        # Señal 2: plan promedio < 80%
        prom_plan = pct_plan_vals.mean()
        if prom_plan < 80:
            señales[1].activa = True
            riesgo_total += señales[1].peso

        # Señal 3: días venta cero altos
        prom_cero = dias_cero_vals.mean()
        if prom_cero > 3:
            señales[2].activa = True
            riesgo_total += señales[2].peso

        # Señal 4: baja activación de cartera
        prom_activos = activos_pct.mean() if len(activos_pct) else 0
        if prom_activos < 0.60:
            señales[3].activa = True
            riesgo_total += señales[3].peso

        # Señal 5: cobranza baja
        prom_cob = cob_pct.mean()
        if prom_cob < 90:
            señales[4].activa = True
            riesgo_total += señales[4].peso

        # Señal 6 y 7: ventanas críticas
        ma = v["meses_activo"]
        en_critica_13 = 1 <= ma <= 3
        en_critica_46 = 4 <= ma <= 6
        if en_critica_13:
            señales[5].activa = True
            riesgo_total += señales[5].peso
        if en_critica_46:
            señales[6].activa = True
            riesgo_total += señales[6].peso

        # Señal 8: grupo con rotación alta histórica
        if v["riesgo_base"] > 0.60:
            señales[7].activa = True
            riesgo_total += señales[7].peso

        # Señal 9: sin clientes nuevos
        if len(nuevos) >= 2 and nuevos[:2].sum() == 0:
            señales[8].activa = True
            riesgo_total += señales[8].peso

        # Normalizar a 1-10
        max_posible = sum(s.peso for s in señales)
        score_norm = 1 + (riesgo_total / max_posible) * 9
        score_norm = round(min(10, max(1, score_norm)), 1)

        # Nivel
        if score_norm >= 8:
            nivel = "critico"
        elif score_norm >= 6:
            nivel = "alto"
        elif score_norm >= 4:
            nivel = "medio"
        else:
            nivel = "bajo"

        scores.append({
            "id_vendedor": vid,
            "tipo": v["tipo"],
            "nombre_grupo": v["nombre_grupo"],
            "supervisor": v["supervisor"],
            "meses_activo": ma,
            "score": score_norm,
            "nivel_riesgo": nivel,
            "pct_plan_3m": round(prom_plan, 1),
            "tendencia_plan": round(float(pendiente), 2),
            "dias_cero_promedio": round(prom_cero, 1),
            "pct_clientes_activos": round(prom_activos * 100, 1),
            "pct_cobranza": round(prom_cob, 1),
            "en_ventana_critica": en_critica_13 or en_critica_46,
            "grupo_riesgo_base": v["riesgo_base"],
            "señales_activas": [s.descripcion for s in señales if s.activa],
        })

    df = pd.DataFrame(scores).sort_values("score", ascending=False).reset_index(drop=True)
    return df


def resumen_grupos() -> pd.DataFrame:
    """Ranking de grupos por rotación histórica."""
    con = get_connection()
    df = pd.read_sql("""
        SELECT
            v.nombre_grupo,
            v.supervisor,
            COUNT(*) as total_vendedores,
            ROUND(AVG(
                CASE WHEN v.fecha_egreso IS NOT NULL
                THEN CAST((julianday(v.fecha_egreso) - julianday(v.fecha_ingreso)) / 30 AS REAL)
                ELSE NULL END
            ), 1) as permanencia_promedio_meses,
            SUM(CASE WHEN v.activo = 0 THEN 1 ELSE 0 END) as bajas,
            SUM(CASE WHEN v.activo = 1 THEN 1 ELSE 0 END) as activos_hoy
        FROM vendedores v
        GROUP BY v.nombre_grupo, v.supervisor
        ORDER BY permanencia_promedio_meses ASC
    """, con)

    ventas_grupo = pd.read_sql("""
        SELECT v.nombre_grupo,
               ROUND(AVG(vm.pct_plan), 1) as cumplimiento_plan_promedio
        FROM ventas_mensual vm
        JOIN vendedores v ON vm.id_vendedor = v.id_vendedor
        GROUP BY v.nombre_grupo
    """, con)
    con.close()

    return df.merge(ventas_grupo, on="nombre_grupo")


if __name__ == "__main__":
    df = calcular_scores()
    print(f"\nVendedores activos evaluados: {len(df)}")
    print(f"Críticos: {len(df[df.nivel_riesgo=='critico'])}")
    print(f"Altos:    {len(df[df.nivel_riesgo=='alto'])}")
    print(f"\nTop 5 mayor riesgo:")
    print(df[["id_vendedor","tipo","nombre_grupo","meses_activo","score","nivel_riesgo","pct_plan_3m"]].head())

    print("\nRanking de grupos:")
    print(resumen_grupos().to_string(index=False))
