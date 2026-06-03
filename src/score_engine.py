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

# Riesgo total de referencia para normalizar el score a 1-10.
# Representa un vendedor en deterioro claro: combinación realista de señales
# fuertes (ej: plan cayendo 2.5 + plan<80% 2.0 + cobranza 2.0 + ventana crítica
# 1.5 + días cero 2.5 ≈ 10.5 puntos).
# NO se divide por la suma de TODOS los pesos (~23.5): eso exigía activar >50%
# de las 15 señales a la vez para llegar a score 6, algo que ningún vendedor real
# hace, y dejaba a todos los egresados con score < 6 (0% detectado). Ver CLAUDE.md.
#
# Calibrado en 16.0 por backtest con holdout temporal (scripts/validar_pesos.py).
# Historia: con REF=10 la falsa alarma en activos era 69% (inservible para
# priorizar). Un primer ajuste a 14 se hizo con datos de cobranza incompletos
# para egresados, que inflaban la detección (cobranza faltante = pct 0 = señal
# falsa). Con la cobranza ya sincronizada y el bug de dato faltante corregido,
# la curva honesta muestra el óptimo en REF=16: ~40% de detección out-of-sample
# de egresados con ~32% de falsa alarma (máxima separación ~7.9). La separación
# real es modesta: es un sistema de alerta temprana sobre datos ruidosos de RRHH,
# no un oráculo. Si se ajusta, re-correr el backfill y actualizar CLAUDE.md.
RIESGO_REFERENCIA = 16.0


def get_connection():
    """
    Conecta a la fuente de datos activa.

    Si las variables de entorno INFORMIX_SERVER / INFORMIX_DATABASE / INFORMIX_HOST /
    INFORMIX_UID / INFORMIX_PWD están configuradas (en .env o el entorno del sistema),
    conecta a Informix via pyodbc (requiere Python 32-bit con ODBC driver instalado).
    Si no están configuradas, usa SQLite local (data/wurth.db).

    Para activar Informix: copiá .env.example → .env y completá las variables.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    except ImportError:
        pass

    server = os.getenv("INFORMIX_SERVER", "").strip()
    if server:
        import pyodbc
        conn_str = (
            f"DRIVER={{IBM INFORMIX ODBC DRIVER}};"
            f"SERVER={server};"
            f"DATABASE={os.getenv('INFORMIX_DATABASE', '')};"
            f"HOST={os.getenv('INFORMIX_HOST', '')};"
            f"UID={os.getenv('INFORMIX_UID', '')};"
            f"PWD={os.getenv('INFORMIX_PWD', '')};"
        )
        return pyodbc.connect(conn_str)

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


def calcular_scores(meses_tendencia: int = 3,
                    hasta_anio: int = None,
                    hasta_mes: int = None) -> pd.DataFrame:
    """
    Retorna DataFrame con score de riesgo de todos los vendedores activos.
    meses_tendencia: cuántos meses hacia atrás mirar (mínimo 2, recomendado 3).

    hasta_anio / hasta_mes: si se especifican, simula el score como si fuera
    el fin de ese mes. Incluye vendedores que estaban activos en esa fecha
    (aunque hoy ya se hayan ido). Útil para backfill histórico.
    """
    import datetime, calendar
    con = get_connection()

    if hasta_anio and hasta_mes:
        ultimo_dia   = calendar.monthrange(hasta_anio, hasta_mes)[1]
        fecha_corte  = datetime.date(hasta_anio, hasta_mes, ultimo_dia)
        periodo_num  = hasta_anio * 100 + hasta_mes
        fc_str       = fecha_corte.isoformat()
        today        = pd.Timestamp(fecha_corte)

        vendedores = pd.read_sql(f"""
            SELECT v.id_vendedor,
                   COALESCE(v.nombre, 'ID ' || v.id_vendedor) as nombre,
                   v.tipo, v.nombre_grupo, v.supervisor,
                   v.fecha_ingreso, g.riesgo_base
            FROM vendedores v
            JOIN grupos g ON v.id_grupo = g.id_grupo
            WHERE v.fecha_ingreso IS NOT NULL
              AND v.fecha_ingreso <= '{fc_str}'
              AND (v.fecha_egreso IS NULL
                   OR v.fecha_egreso > '{fc_str}'
                   OR v.fecha_egreso = v.fecha_ingreso)
              AND v.id_vendedor != 9800
              AND v.nombre NOT IN (
                  SELECT DISTINCT supervisor FROM vendedores
                  WHERE supervisor IS NOT NULL AND supervisor != ''
              )
        """, con)

        ventas = pd.read_sql(f"""
            SELECT vm.*
            FROM ventas_mensual vm
            WHERE (vm.anio * 100 + vm.mes) <= {periodo_num}
            ORDER BY vm.id_vendedor, vm.anio DESC, vm.mes DESC
        """, con)

        try:
            actividad = pd.read_sql(f"""
                SELECT am.*
                FROM actividad_mensual am
                WHERE (am.anio * 100 + am.mes) <= {periodo_num}
                ORDER BY am.id_vendedor, am.anio DESC, am.mes DESC
            """, con)
        except Exception:
            actividad = pd.DataFrame()

        try:
            ausencias = pd.read_sql(f"""
                SELECT au.*
                FROM ausencias_mensual au
                WHERE (au.anio * 100 + au.mes) <= {periodo_num}
                ORDER BY au.id_vendedor, au.anio DESC, au.mes DESC
            """, con)
        except Exception:
            ausencias = pd.DataFrame()

        try:
            balanza = pd.read_sql(f"""
                SELECT bc.*
                FROM balanza_clientes bc
                WHERE (bc.anio * 100 + bc.mes) <= {periodo_num}
                ORDER BY bc.id_vendedor, bc.anio DESC, bc.mes DESC
            """, con)
        except Exception:
            balanza = pd.DataFrame()

        try:
            acompanamiento = pd.read_sql(f"""
                SELECT ac.*
                FROM acompanamiento_mensual ac
                WHERE (ac.anio * 100 + ac.mes) <= {periodo_num}
                ORDER BY ac.id_vendedor, ac.anio DESC, ac.mes DESC
            """, con)
        except Exception:
            acompanamiento = pd.DataFrame()

    else:
        today = pd.Timestamp(datetime.date.today())

        vendedores = pd.read_sql("""
            SELECT v.id_vendedor,
                   COALESCE(v.nombre, 'ID ' || v.id_vendedor) as nombre,
                   v.tipo, v.nombre_grupo, v.supervisor,
                   v.fecha_ingreso, g.riesgo_base
            FROM vendedores v
            JOIN grupos g ON v.id_grupo = g.id_grupo
            WHERE v.activo = 1
              AND (v.fecha_egreso IS NULL OR v.fecha_egreso != v.fecha_ingreso)
              AND v.id_vendedor != 9800
              AND v.nombre NOT IN (
                  SELECT DISTINCT supervisor FROM vendedores
                  WHERE supervisor IS NOT NULL AND supervisor != ''
              )
        """, con)

        ventas = pd.read_sql("""
            SELECT vm.*
            FROM ventas_mensual vm
            JOIN vendedores v ON vm.id_vendedor = v.id_vendedor
            WHERE v.activo = 1
            ORDER BY vm.id_vendedor, vm.anio DESC, vm.mes DESC
        """, con)

        try:
            actividad = pd.read_sql("""
                SELECT am.*
                FROM actividad_mensual am
                JOIN vendedores v ON am.id_vendedor = v.id_vendedor
                WHERE v.activo = 1
                ORDER BY am.id_vendedor, am.anio DESC, am.mes DESC
            """, con)
        except Exception:
            actividad = pd.DataFrame()

        try:
            ausencias = pd.read_sql("""
                SELECT au.*
                FROM ausencias_mensual au
                JOIN vendedores v ON au.id_vendedor = v.id_vendedor
                WHERE v.activo = 1
                ORDER BY au.id_vendedor, au.anio DESC, au.mes DESC
            """, con)
        except Exception:
            ausencias = pd.DataFrame()

        try:
            balanza = pd.read_sql("""
                SELECT bc.*
                FROM balanza_clientes bc
                JOIN vendedores v ON bc.id_vendedor = v.id_vendedor
                WHERE v.activo = 1
                ORDER BY bc.id_vendedor, bc.anio DESC, bc.mes DESC
            """, con)
        except Exception:
            balanza = pd.DataFrame()

        try:
            acompanamiento = pd.read_sql("""
                SELECT ac.*
                FROM acompanamiento_mensual ac
                JOIN vendedores v ON ac.id_vendedor = v.id_vendedor
                WHERE v.activo = 1
                ORDER BY ac.id_vendedor, ac.anio DESC, ac.mes DESC
            """, con)
        except Exception:
            acompanamiento = pd.DataFrame()

    con.close()

    vendedores["fecha_ingreso"] = pd.to_datetime(vendedores["fecha_ingreso"])
    vendedores["meses_activo"] = (
        (today - vendedores["fecha_ingreso"]).dt.days / 30
    ).round().fillna(0).astype(int)

    scores = []

    for _, v in vendedores.iterrows():
        vid = v["id_vendedor"]
        hist = ventas[ventas["id_vendedor"] == vid].head(meses_tendencia)

        if hist.empty:
            continue

        # Actividad Reactor de este vendedor (últimos N meses)
        act_vid   = actividad[actividad["id_vendedor"] == vid].head(meses_tendencia)   if not actividad.empty   else pd.DataFrame()
        aus_vid   = ausencias[ausencias["id_vendedor"] == vid].head(meses_tendencia)   if not ausencias.empty   else pd.DataFrame()
        bal_vid   = balanza[balanza["id_vendedor"] == vid].head(meses_tendencia)       if not balanza.empty     else pd.DataFrame()
        acomp_vid = acompanamiento[acompanamiento["id_vendedor"] == vid].head(meses_tendencia) if not acompanamiento.empty else pd.DataFrame()

        señales = [
            Señal("caída_plan_3m",        peso=2.5, descripcion="% Plan cayendo 3 meses seguidos"),
            Señal("plan_bajo_80",          peso=2.0, descripcion="% Plan < 80% promedio últimos meses"),
            Señal("dias_cero_alto",        peso=2.5, descripcion="Días sin venta > 3 en promedio"),
            # DESHABILITADA (peso 0): cuando el vendedor se va, Informix reasigna sus clientes
            # al nuevo vendedor y el histórico queda con total_clientes=0. El fix de dato
            # faltante la apaga para egresados pero no para activos → lift 0.01, Δsep +13.4.
            Señal("clientes_activos_baja", peso=0.0, descripcion="< 60% de cartera activa"),
            Señal("cobranza_baja",         peso=2.0, descripcion="Cobranza real < 90% de teórica"),
            Señal("ventana_critica_13",    peso=1.5, descripcion="En ventana crítica mes 1-3"),
            Señal("ventana_critica_46",    peso=1.0, descripcion="En ventana crítica mes 4-6"),
            Señal("grupo_quemado",         peso=1.5, descripcion="Grupo con alta rotación histórica"),
            Señal("clientes_nuevos_cero",  peso=0.5, descripcion="Sin clientes nuevos últimos 2 meses"),
            # DESHABILITADAS (peso 0): los egresados raramente tienen datos de Reactor en sus
            # últimos meses activos → la señal dispara más en activos (tienen Reactor al día)
            # que en egresados → invertida (lift < 1, Δsep positivo al sacarlas).
            Señal("llamadas_bajas",        peso=0.0, descripcion="< 70% de llamadas planificadas gestionadas (Televentas)"),
            Señal("visitas_bajas",         peso=0.0, descripcion="< 70% de visitas planificadas realizadas (Viajante)"),
            Señal("ausencias_tempranas",   peso=2.0, descripcion="Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3"),
            Señal("balanza_negativa",      peso=1.5, descripcion="Balanza clientes negativa 2+ meses consecutivos"),
            Señal("ticket_cayendo",        peso=1.0, descripcion="Ticket promedio cae > 5% por mes"),
            Señal("acomp_bajo",            peso=1.0, descripcion="Supervisor no acompañó en ventana crítica 1-6"),
            # NUEVA: interacción tenure × grupo quemado (hipótesis central del proyecto).
            # Umbral rb>0.30 (más amplio que grupo_quemado solo, 0.40): el combo "vendedor
            # nuevo en grupo históricamente malo" tiene lift OOS 2.04 bien poblado (22% egr /
            # 11% act). Se solapa con ventana_critica + grupo_quemado, pero captura el riesgo
            # compuesto extra. Validar Δsep en validar_pesos.py tras el backfill.
            Señal("tenure_x_grupo",        peso=1.0, descripcion="Nuevo en grupo quemado (tenure 1-6 × riesgo_base > 0.30)"),
        ]

        riesgo_total = 0.0
        pct_plan_vals  = hist["pct_plan"].values
        plan_vals      = hist["plan"].values
        dias_cero_vals = hist["dias_venta_cero"].values
        total_cli_vals = hist["total_clientes"].values
        activos_cli    = hist["clientes_activos"].values
        cob_pct        = hist["pct_cobranza"].values
        cob_teorica    = hist["cobranza_teorica"].values
        nuevos         = hist["clientes_nuevos"].values

        # Un dato faltante en ventas_mensual queda en 0; si lo tomáramos como
        # valor real, encendería señales de riesgo FALSAMENTE (ej: cobranza
        # ausente = pct_cobranza 0 = "cobranza < 90"). Para evitarlo, cada señal
        # usa solo los meses donde existe la BASE del dato:
        #   plan      → meses con plan > 0
        #   cobranza  → meses con cobranza_teorica > 0
        #   cartera   → meses con total_clientes > 0
        # Si no hay ningún mes con base, la señal NO se enciende (dato desconocido).
        pct_plan_validos = pct_plan_vals[plan_vals > 0]
        cob_validos      = cob_pct[cob_teorica > 0]
        _mask_cli        = total_cli_vals > 0
        activos_pct      = (activos_cli[_mask_cli] / total_cli_vals[_mask_cli])

        # Señal 1: tendencia plan cayendo (pendiente negativa) — solo meses con plan
        if len(pct_plan_validos) >= 2:
            x = np.arange(len(pct_plan_validos))
            pendiente = np.polyfit(x[::-1], pct_plan_validos, 1)[0]  # más reciente primero
            if pendiente < -3:
                señales[0].activa = True
                riesgo_total += señales[0].peso
        else:
            pendiente = 0

        # Señal 2: plan promedio < 80% — solo si hay plan cargado
        prom_plan = pct_plan_validos.mean() if len(pct_plan_validos) else 0
        if len(pct_plan_validos) and prom_plan < 80:
            señales[1].activa = True
            riesgo_total += señales[1].peso

        # Señal 3: días venta cero altos (si falta el dato queda en 0 y no enciende)
        prom_cero = dias_cero_vals.mean()
        if prom_cero > 3:
            señales[2].activa = True
            riesgo_total += señales[2].peso

        # Señal 4: baja activación de cartera — solo meses con cartera conocida
        prom_activos = activos_pct.mean() if len(activos_pct) else 0
        if len(activos_pct) and prom_activos < 0.60:
            señales[3].activa = True
            riesgo_total += señales[3].peso

        # Señal 5: cobranza baja — solo si hay cobranza teórica (base) cargada
        prom_cob = cob_validos.mean() if len(cob_validos) else 0
        if len(cob_validos) and prom_cob < 90:
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
        # Umbral 0.40 (antes 0.60): el grupo MÁS quemado tiene riesgo_base 0.51,
        # así que con 0.60 la señal nunca disparaba (estaba muerta). El
        # diagnóstico (scripts/diagnostico_grupos_quemados.py) mostró que a 0.40
        # los egresados están 2.1x más seguido en grupos quemados que los activos
        # (la hipótesis central del proyecto). Ver CLAUDE.md.
        if v["riesgo_base"] > 0.40:
            señales[7].activa = True
            riesgo_total += señales[7].peso

        # Señal 9: sin clientes nuevos (fuente: adrchr + kund de Informix)
        if len(nuevos) >= 2 and nuevos[:2].sum() == 0:
            señales[8].activa = True
            riesgo_total += señales[8].peso

        # Señales 10 y 11: actividad Reactor (solo si hay datos)
        tipo_v = v["tipo"]
        if not act_vid.empty:
            tiene_plan_ll = "planificadas_llamadas" in act_vid.columns
            tiene_plan_vi = "planificadas_visitas"  in act_vid.columns

            if tipo_v == "Televentas":
                if tiene_plan_ll and act_vid["planificadas_llamadas"].sum() > 0:
                    # Promedio real del sistema: ~40% de completitud.
                    # Señal activa si el vendedor está sostenidamente por debajo del 25%
                    # (la mitad del promedio — indica desenganche claro).
                    ratio = (act_vid["gestionadas_llamadas"] /
                             act_vid["planificadas_llamadas"].replace(0, float("nan"))).mean()
                    if ratio < 0.25:
                        señales[9].activa = True
                        riesgo_total += señales[9].peso
                elif "llamadas" in act_vid.columns:
                    if act_vid["llamadas"].mean() < 500:
                        señales[9].activa = True
                        riesgo_total += señales[9].peso

            elif tipo_v == "Viajante":
                if tiene_plan_vi and act_vid["planificadas_visitas"].sum() > 0:
                    # Mismo criterio: promedio real ~40%, señal si < 25%
                    ratio = (act_vid["visitadas_schedule"] /
                             act_vid["planificadas_visitas"].replace(0, float("nan"))).mean()
                    if ratio < 0.25:
                        señales[10].activa = True
                        riesgo_total += señales[10].peso
                elif "visitas" in act_vid.columns:
                    if act_vid["visitas"].mean() < 300:
                        señales[10].activa = True
                        riesgo_total += señales[10].peso

        # Señal 12: ausencias no-vacacionales en ventana crítica mes 1-3
        if not aus_vid.empty and en_critica_13 and "dias_no_vac" in aus_vid.columns:
            prom_no_vac = aus_vid["dias_no_vac"].mean()
            if prom_no_vac > 2:
                señales[11].activa = True
                riesgo_total += señales[11].peso

        # Señal 13: balanza negativa los últimos 2 meses Y pérdida neta > 3 clientes
        # Umbral más estricto para evitar falsos positivos (70% de meses son negativos)
        if not bal_vid.empty and "balanza" in bal_vid.columns and len(bal_vid) >= 2:
            ultimos_2 = bal_vid["balanza"].values[:2]  # más recientes primero (orden DESC)
            if all(b < 0 for b in ultimos_2) and ultimos_2.sum() < -3:
                señales[12].activa = True
                riesgo_total += señales[12].peso

        # Señal 14: ticket promedio con tendencia bajista (> 5% del promedio por mes)
        if not bal_vid.empty and "ticket_promedio" in bal_vid.columns and len(bal_vid) >= 2:
            tickets = bal_vid["ticket_promedio"].replace(0, float("nan")).dropna().values
            if len(tickets) >= 2:
                x_t = np.arange(len(tickets))
                pend_ticket = np.polyfit(x_t[::-1], tickets, 1)[0]
                mean_ticket = tickets.mean()
                if mean_ticket > 0 and (-pend_ticket / mean_ticket) > 0.05:
                    señales[13].activa = True
                    riesgo_total += señales[13].peso

        # Señal 15: acompañamiento del supervisor bajo en ventana crítica 1-6
        en_critica_16 = 1 <= ma <= 6
        if not acomp_vid.empty and en_critica_16 and "visitas_sup_realizadas" in acomp_vid.columns:
            prom_acomp = acomp_vid["visitas_sup_realizadas"].mean()
            if prom_acomp < 1:
                señales[14].activa = True
                riesgo_total += señales[14].peso

        # Señal 16: interacción tenure × grupo quemado (hipótesis central del proyecto)
        # Umbral rb > 0.30 (más amplio que grupo_quemado solo, 0.40): captura el riesgo
        # COMPUESTO de ser nuevo en un grupo con mala historia de retención.
        # Lift OOS 2.04, bien poblado (22% egresados / 11% activos). Ver explorar_senales_nuevas.py.
        if en_critica_16 and v["riesgo_base"] > 0.30:
            señales[15].activa = True
            riesgo_total += señales[15].peso

        # Normalizar a 1-10 contra un riesgo de referencia realista.
        # Las señales no aplicables por tipo/datos (visitas para Televentas,
        # ventanas fuera de rango, etc.) simplemente no se activan, así que
        # aportan 0 a riesgo_total: no hace falta excluirlas del denominador.
        score_norm = 1 + min(riesgo_total / RIESGO_REFERENCIA, 1.0) * 9
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
            "nombre": v["nombre"],
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

    if not scores:
        return pd.DataFrame(columns=[
            "id_vendedor","nombre","tipo","nombre_grupo","supervisor",
            "meses_activo","score","nivel_riesgo",
            "pct_plan_3m","tendencia_plan","dias_cero_promedio",
            "pct_clientes_activos","pct_cobranza","en_ventana_critica",
            "grupo_riesgo_base","señales_activas",
        ])
    df = pd.DataFrame(scores).sort_values("score", ascending=False).reset_index(drop=True)
    return df


def resumen_grupos() -> pd.DataFrame:
    """Ranking de grupos por rotación histórica."""
    import datetime
    con = get_connection()
    vend_df = pd.read_sql("""
        SELECT v.nombre_grupo, v.supervisor, v.activo,
               v.fecha_ingreso, v.fecha_egreso
        FROM vendedores v
        WHERE fecha_ingreso IS NOT NULL
          AND (fecha_egreso IS NULL OR fecha_egreso != fecha_ingreso)
    """, con)

    ventas_grupo = pd.read_sql("""
        SELECT v.nombre_grupo,
               ROUND(AVG(vm.pct_plan), 1) as cumplimiento_plan_promedio
        FROM ventas_mensual vm
        JOIN vendedores v ON vm.id_vendedor = v.id_vendedor
        GROUP BY v.nombre_grupo
    """, con)
    con.close()

    # Calcular permanencia en Python (evita julianday que es SQLite-specific)
    vend_df["fecha_ingreso"] = pd.to_datetime(vend_df["fecha_ingreso"], errors="coerce")
    vend_df["fecha_egreso"]  = pd.to_datetime(vend_df["fecha_egreso"],  errors="coerce")
    today = pd.Timestamp(datetime.date.today())
    vend_df["meses"] = (
        (vend_df["fecha_egreso"].fillna(today) - vend_df["fecha_ingreso"]).dt.days / 30
    )

    # meses_egreso: solo para los que ya se fueron (activo=0)
    # Excluye activos para que los veteranos de muchos años no inflen el promedio
    vend_df["meses_egreso"] = vend_df["meses"].where(vend_df["activo"] == 0)

    df = (
        vend_df
        .groupby(["nombre_grupo", "supervisor"])
        .agg(
            total_vendedores=("activo", "count"),
            bajas=("activo", lambda x: (x == 0).sum()),
            activos_hoy=("activo", lambda x: (x == 1).sum()),
            permanencia_promedio_meses=("meses_egreso", "mean"),
        )
        .reset_index()
    )
    df["permanencia_promedio_meses"] = df["permanencia_promedio_meses"].round(1)

    return df.merge(ventas_grupo, on="nombre_grupo", how="left").sort_values(
        "permanencia_promedio_meses"
    )


def obtener_sparklines(meses: int = 3) -> dict:
    """Retorna {id_vendedor: [pct_plan_mes_viejo, ..., pct_plan_mes_reciente]} para activos."""
    con = get_connection()
    df = pd.read_sql("""
        SELECT vm.id_vendedor, vm.pct_plan
        FROM ventas_mensual vm
        JOIN vendedores v ON vm.id_vendedor = v.id_vendedor
        WHERE v.activo = 1
        ORDER BY vm.id_vendedor, vm.anio DESC, vm.mes DESC
    """, con)
    con.close()

    result = {}
    for vid, group in df.groupby("id_vendedor"):
        vals = group["pct_plan"].head(meses).values[::-1].tolist()
        result[int(vid)] = [round(v, 1) for v in vals]
    return result


if __name__ == "__main__":
    df = calcular_scores()
    print(f"\nVendedores activos evaluados: {len(df)}")
    print(f"Críticos: {len(df[df.nivel_riesgo=='critico'])}")
    print(f"Altos:    {len(df[df.nivel_riesgo=='alto'])}")
    print(f"\nTop 5 mayor riesgo:")
    print(df[["id_vendedor","tipo","nombre_grupo","meses_activo","score","nivel_riesgo","pct_plan_3m"]].head())

    print("\nRanking de grupos:")
    print(resumen_grupos().to_string(index=False))
