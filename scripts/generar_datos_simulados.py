"""
generar_datos_simulados.py
--------------------------
Genera datos ficticios con la misma estructura exacta que va a tener
el ERP Informix de Wurth cuando conectemos el lunes.

Tablas generadas:
  - vendedores       → legajo completo
  - ventas_mensual   → métricas del Talata por mes
  - cobranza_mensual → cobranza real vs teórica por mes
"""

import sqlite3
import random
import numpy as np
from datetime import date, timedelta
import os

random.seed(42)
np.random.seed(42)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ── Configuración de grupos (reemplazará "zonas") ──────────────────────────
GRUPOS = [
    {"id": 10, "nombre": "GBA Norte",    "supervisor": "Zerbatto Jose Luis",   "riesgo_base": 0.72},
    {"id": 20, "nombre": "GBA Sur",      "supervisor": "Kalpokas Gustavo",      "riesgo_base": 0.68},
    {"id": 30, "nombre": "GBA Oeste",    "supervisor": "Galla Gabriel Isaac",   "riesgo_base": 0.55},
    {"id": 40, "nombre": "GBA Este",     "supervisor": "Pérez Roberto",         "riesgo_base": 0.40},
    {"id": 50, "nombre": "Córdoba",      "supervisor": "Martínez Sandra",       "riesgo_base": 0.30},
    {"id": 60, "nombre": "Rosario",      "supervisor": "Vega Claudia",          "riesgo_base": 0.25},
    {"id": 70, "nombre": "Interior NOA", "supervisor": "Torres Miguel",         "riesgo_base": 0.60},
]

TIPOS = ["Viajante", "Televentas"]
MOTIVOS_EGRESO = ["Renuncia voluntaria", "Despido", "Acuerdo mutuo", "Abandono"]

def fecha_aleatoria(inicio: date, fin: date) -> date:
    delta = (fin - inicio).days
    return inicio + timedelta(days=random.randint(0, delta))

def duracion_meses(grupo_riesgo: float) -> int:
    """Simula permanencia: grupos de alto riesgo duran menos."""
    if grupo_riesgo > 0.65:
        return max(1, int(np.random.exponential(4)))
    elif grupo_riesgo > 0.45:
        return max(1, int(np.random.exponential(7)))
    else:
        return max(2, int(np.random.exponential(14)))

def generar_vendedores(n=1100):
    vendedores = []
    ids_usados = set()
    fecha_inicio_historico = date(2014, 1, 1)
    fecha_hoy = date(2025, 1, 24)

    for _ in range(n):
        # ID único tipo Wurth
        while True:
            vid = random.randint(1000, 9999)
            if vid not in ids_usados:
                ids_usados.add(vid)
                break

        grupo = random.choice(GRUPOS)
        tipo  = random.choices(TIPOS, weights=[0.65, 0.35])[0]

        fecha_ingreso = fecha_aleatoria(fecha_inicio_historico, date(2024, 10, 1))
        meses_duracion = duracion_meses(grupo["riesgo_base"])
        fecha_egreso_tentativa = fecha_ingreso + timedelta(days=meses_duracion * 30)

        if fecha_egreso_tentativa < fecha_hoy:
            fecha_egreso = fecha_egreso_tentativa
            # Motivo correlacionado con velocidad de salida
            if meses_duracion <= 3:
                motivo = random.choices(MOTIVOS_EGRESO, weights=[0.3, 0.2, 0.1, 0.4])[0]
            else:
                motivo = random.choices(MOTIVOS_EGRESO, weights=[0.6, 0.2, 0.15, 0.05])[0]
            activo = 0
        else:
            fecha_egreso = None
            motivo = None
            activo = 1

        vendedores.append({
            "id_vendedor": vid,
            "tipo": tipo,
            "id_grupo": grupo["id"],
            "nombre_grupo": grupo["nombre"],
            "supervisor": grupo["supervisor"],
            "fecha_ingreso": fecha_ingreso.isoformat(),
            "fecha_egreso": fecha_egreso.isoformat() if fecha_egreso else None,
            "motivo_egreso": motivo,
            "activo": activo,
        })

    return vendedores

def generar_ventas_mensual(vendedores):
    """
    Para cada vendedor activo en cada mes genera métricas del Talata.
    Simula deterioro progresivo en vendedores que terminan yéndose.
    """
    registros = []
    fecha_hoy = date(2025, 1, 24)

    for v in vendedores:
        ingreso  = date.fromisoformat(v["fecha_ingreso"])
        egreso   = date.fromisoformat(v["fecha_egreso"]) if v["fecha_egreso"] else fecha_hoy
        grupo    = next(g for g in GRUPOS if g["id"] == v["id_grupo"])
        se_fue   = v["activo"] == 0
        meses_total = max(1, round((egreso - ingreso).days / 30))

        plan_base = random.randint(8_000_000, 18_000_000)

        cur = date(ingreso.year, ingreso.month, 1)
        mes_num = 0

        while cur <= egreso and cur <= fecha_hoy:
            mes_num += 1
            progreso = mes_num / max(meses_total, 1)  # 0→1 a lo largo de su vida

            # Si se va, los últimos 3 meses muestran deterioro
            en_deterioro = se_fue and progreso > 0.70

            # % plan: arranca dudoso, se estabiliza, luego cae si deteriora
            if mes_num <= 3:
                pct_plan = random.gauss(85, 15)
            elif en_deterioro:
                caida = (progreso - 0.70) / 0.30  # 0→1
                pct_plan = random.gauss(100 - caida * 35, 10)
            else:
                pct_plan = random.gauss(105, 12)

            pct_plan = max(30, min(200, pct_plan))
            venta_total = plan_base * (pct_plan / 100) * random.gauss(1, 0.05)

            # Días venta cero — sube en deterioro
            if en_deterioro:
                dias_cero = random.randint(3, 8)
            elif mes_num <= 2:
                dias_cero = random.randint(1, 4)
            else:
                dias_cero = random.randint(0, 2)

            # Clientes activos — caen en deterioro
            total_clientes = random.randint(180, 260)
            if en_deterioro:
                activos = int(total_clientes * random.uniform(0.45, 0.60))
            else:
                activos = int(total_clientes * random.uniform(0.62, 0.75))

            inactivos = total_clientes - activos
            clientes_nuevos = 0 if en_deterioro else random.randint(0, 4)

            # Cobranza
            cob_teorica = venta_total * random.uniform(0.90, 1.10)
            if en_deterioro:
                pct_cob = random.gauss(88, 8)
            else:
                pct_cob = random.gauss(102, 6)
            cob_real = cob_teorica * (pct_cob / 100)
            dias_cobro = random.gauss(55 if en_deterioro else 47, 5)
            cheques_rechazados = random.randint(1, 4) if en_deterioro else random.randint(0, 1)

            registros.append({
                "id_vendedor": v["id_vendedor"],
                "anio": cur.year,
                "mes": cur.month,
                "mes_numero": mes_num,
                "dias_trabajados": random.randint(18, 23),
                "dias_venta_cero": dias_cero,
                "venta_total": round(venta_total),
                "plan": round(plan_base),
                "pct_plan": round(pct_plan, 2),
                "venta_anio_anterior": round(venta_total * random.uniform(0.7, 1.3)),
                "crecimiento_pct": round(random.gauss(10 if not en_deterioro else -8, 15), 2),
                "pedidos_por_dia": round(random.gauss(2.8 if not en_deterioro else 1.9, 0.5), 2),
                "cant_pedidos": random.randint(40, 90),
                "total_clientes": total_clientes,
                "clientes_activos": activos,
                "clientes_inactivos": inactivos,
                "clientes_nuevos": clientes_nuevos,
                "cobranza_teorica": round(cob_teorica),
                "cobranza_real": round(cob_real),
                "pct_cobranza": round(pct_cob, 2),
                "dias_cobro": round(dias_cobro, 1),
                "cheques_rechazados": cheques_rechazados,
                "en_deterioro": int(en_deterioro),  # solo para validar el modelo luego
            })

            # avanzar un mes
            if cur.month == 12:
                cur = date(cur.year + 1, 1, 1)
            else:
                cur = date(cur.year, cur.month + 1, 1)

    return registros

def crear_db(vendedores, ventas):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS vendedores;
        DROP TABLE IF EXISTS ventas_mensual;
        DROP TABLE IF EXISTS grupos;

        CREATE TABLE grupos (
            id_grupo     INTEGER PRIMARY KEY,
            nombre_grupo TEXT,
            supervisor   TEXT,
            riesgo_base  REAL
        );

        CREATE TABLE vendedores (
            id_vendedor  INTEGER PRIMARY KEY,
            tipo         TEXT,
            id_grupo     INTEGER,
            nombre_grupo TEXT,
            supervisor   TEXT,
            fecha_ingreso TEXT,
            fecha_egreso  TEXT,
            motivo_egreso TEXT,
            activo        INTEGER,
            FOREIGN KEY (id_grupo) REFERENCES grupos(id_grupo)
        );

        CREATE TABLE ventas_mensual (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            id_vendedor     INTEGER,
            anio            INTEGER,
            mes             INTEGER,
            mes_numero      INTEGER,
            dias_trabajados INTEGER,
            dias_venta_cero INTEGER,
            venta_total     REAL,
            plan            REAL,
            pct_plan        REAL,
            venta_anio_anterior REAL,
            crecimiento_pct REAL,
            pedidos_por_dia REAL,
            cant_pedidos    INTEGER,
            total_clientes  INTEGER,
            clientes_activos INTEGER,
            clientes_inactivos INTEGER,
            clientes_nuevos INTEGER,
            cobranza_teorica REAL,
            cobranza_real    REAL,
            pct_cobranza     REAL,
            dias_cobro       REAL,
            cheques_rechazados INTEGER,
            en_deterioro    INTEGER,
            FOREIGN KEY (id_vendedor) REFERENCES vendedores(id_vendedor)
        );

        CREATE INDEX IF NOT EXISTS idx_ventas_vendedor ON ventas_mensual(id_vendedor);
        CREATE INDEX IF NOT EXISTS idx_ventas_periodo  ON ventas_mensual(anio, mes);
    """)

    for g in GRUPOS:
        cur.execute("INSERT INTO grupos VALUES (?,?,?,?)",
                    (g["id"], g["nombre"], g["supervisor"], g["riesgo_base"]))

    cur.executemany("""INSERT INTO vendedores VALUES
        (:id_vendedor,:tipo,:id_grupo,:nombre_grupo,:supervisor,
         :fecha_ingreso,:fecha_egreso,:motivo_egreso,:activo)""", vendedores)

    cur.executemany("""INSERT INTO ventas_mensual
        (id_vendedor,anio,mes,mes_numero,dias_trabajados,dias_venta_cero,
         venta_total,plan,pct_plan,venta_anio_anterior,crecimiento_pct,
         pedidos_por_dia,cant_pedidos,total_clientes,clientes_activos,
         clientes_inactivos,clientes_nuevos,cobranza_teorica,cobranza_real,
         pct_cobranza,dias_cobro,cheques_rechazados,en_deterioro)
        VALUES
        (:id_vendedor,:anio,:mes,:mes_numero,:dias_trabajados,:dias_venta_cero,
         :venta_total,:plan,:pct_plan,:venta_anio_anterior,:crecimiento_pct,
         :pedidos_por_dia,:cant_pedidos,:total_clientes,:clientes_activos,
         :clientes_inactivos,:clientes_nuevos,:cobranza_teorica,:cobranza_real,
         :pct_cobranza,:dias_cobro,:cheques_rechazados,:en_deterioro)""", ventas)

    con.commit()
    con.close()
    print(f"✓ DB creada en {DB_PATH}")
    print(f"  Vendedores: {len(vendedores)}")
    print(f"  Registros mensuales: {len(ventas)}")

def generar_vendedores_en_riesgo():
    """
    Genera ~20 vendedores activos que muestran señales de deterioro temprano.
    Son los casos que el sistema DEBE detectar: aún no renunciaron pero las métricas caen.
    """
    vendedores = []
    fecha_hoy = date(2025, 1, 24)

    escenarios = [
        # (id, tipo, grupo_idx, meses_activo, perfil_riesgo)
        # perfil: "caida_plan", "onboarding_alto_riesgo", "deterioro_cobranza", "zona_quemada"
        (10001, "Viajante",   0, 5,  "caida_plan"),
        (10002, "Televentas", 1, 3,  "onboarding_alto_riesgo"),
        (10003, "Viajante",   0, 8,  "deterioro_cobranza"),
        (10004, "Viajante",   1, 2,  "onboarding_alto_riesgo"),
        (10005, "Televentas", 6, 6,  "caida_plan"),
        (10006, "Viajante",   0, 4,  "caida_plan"),
        (10007, "Viajante",   1, 7,  "deterioro_cobranza"),
        (10008, "Televentas", 0, 3,  "onboarding_alto_riesgo"),
        (10009, "Viajante",   6, 5,  "caida_plan"),
        (10010, "Televentas", 2, 9,  "deterioro_cobranza"),
        (10011, "Viajante",   0, 4,  "caida_plan"),
        (10012, "Viajante",   1, 2,  "onboarding_alto_riesgo"),
        (10013, "Televentas", 6, 6,  "caida_plan"),
        (10014, "Viajante",   0, 11, "deterioro_cobranza"),
        (10015, "Viajante",   2, 5,  "caida_plan"),
    ]

    for vid, tipo, gidx, meses, perfil in escenarios:
        grupo = GRUPOS[gidx]
        fecha_ingreso = fecha_hoy - timedelta(days=meses * 30)
        vendedores.append({
            "id_vendedor": vid,
            "tipo": tipo,
            "id_grupo": grupo["id"],
            "nombre_grupo": grupo["nombre"],
            "supervisor": grupo["supervisor"],
            "fecha_ingreso": fecha_ingreso.isoformat(),
            "fecha_egreso": None,
            "motivo_egreso": None,
            "activo": 1,
            "_perfil": perfil,
            "_meses": meses,
        })

    return vendedores


def generar_ventas_en_riesgo(vendedores_riesgo):
    """Genera métricas mensuales con señales de deterioro para vendedores en riesgo."""
    registros = []
    fecha_hoy = date(2025, 1, 24)

    for v in vendedores_riesgo:
        perfil = v.pop("_perfil")
        meses  = v.pop("_meses")
        ingreso = date.fromisoformat(v["fecha_ingreso"])
        plan_base = random.randint(8_000_000, 15_000_000)

        cur = date(ingreso.year, ingreso.month, 1)
        mes_num = 0

        while cur <= fecha_hoy:
            mes_num += 1
            es_reciente = mes_num >= max(1, meses - 2)

            if perfil == "caida_plan":
                if es_reciente:
                    caida = (mes_num - (meses - 3)) / 3
                    pct_plan = random.gauss(95 - caida * 18, 6)
                    dias_cero = random.randint(3, 7)
                    activos_pct = random.uniform(0.50, 0.62)
                    pct_cob = random.gauss(91, 6)
                else:
                    pct_plan = random.gauss(100, 10)
                    dias_cero = random.randint(0, 2)
                    activos_pct = random.uniform(0.62, 0.75)
                    pct_cob = random.gauss(102, 5)

            elif perfil == "onboarding_alto_riesgo":
                pct_plan = random.gauss(78 - mes_num * 3, 12)
                dias_cero = random.randint(2, 6)
                activos_pct = random.uniform(0.45, 0.60)
                pct_cob = random.gauss(88, 8)

            elif perfil == "deterioro_cobranza":
                pct_plan = random.gauss(90, 10)
                dias_cero = random.randint(2, 5) if es_reciente else random.randint(0, 2)
                activos_pct = random.uniform(0.55, 0.65)
                pct_cob = random.gauss(82 if es_reciente else 98, 6)

            else:
                pct_plan = random.gauss(100, 12)
                dias_cero = random.randint(0, 2)
                activos_pct = random.uniform(0.62, 0.75)
                pct_cob = random.gauss(100, 5)

            pct_plan = max(30, min(180, pct_plan))
            total_clientes = random.randint(180, 250)
            activos = int(total_clientes * activos_pct)
            venta = plan_base * (pct_plan / 100)
            cob_teorica = venta * random.uniform(0.95, 1.05)
            cob_real = cob_teorica * (pct_cob / 100)

            registros.append({
                "id_vendedor": v["id_vendedor"],
                "anio": cur.year,
                "mes": cur.month,
                "mes_numero": mes_num,
                "dias_trabajados": random.randint(18, 23),
                "dias_venta_cero": dias_cero,
                "venta_total": round(venta),
                "plan": round(plan_base),
                "pct_plan": round(pct_plan, 2),
                "venta_anio_anterior": round(venta * random.uniform(0.8, 1.2)),
                "crecimiento_pct": round(random.gauss(0, 15), 2),
                "pedidos_por_dia": round(random.gauss(2.0, 0.5), 2),
                "cant_pedidos": random.randint(30, 80),
                "total_clientes": total_clientes,
                "clientes_activos": activos,
                "clientes_inactivos": total_clientes - activos,
                "clientes_nuevos": 0 if es_reciente else random.randint(0, 3),
                "cobranza_teorica": round(cob_teorica),
                "cobranza_real": round(cob_real),
                "pct_cobranza": round(pct_cob, 2),
                "dias_cobro": round(random.gauss(58, 6), 1),
                "cheques_rechazados": random.randint(1, 3) if es_reciente else 0,
                "en_deterioro": 1,
            })

            if cur.month == 12:
                cur = date(cur.year + 1, 1, 1)
            else:
                cur = date(cur.year, cur.month + 1, 1)

    return registros


if __name__ == "__main__":
    print("Generando datos simulados Wurth...")
    v  = generar_vendedores(1100)
    vm = generar_ventas_mensual(v)

    vr  = generar_vendedores_en_riesgo()
    vmr = generar_ventas_en_riesgo(vr)

    crear_db(v + vr, vm + vmr)
    print("Listo.")
