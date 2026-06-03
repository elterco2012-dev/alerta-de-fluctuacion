"""
scripts/explorar_senales_nuevas.py
----------------------------------
¿Hay señales NUEVAS con más poder predictivo que las débiles que ya tenemos
(visitas bajas lift ~1.2, balanza ~1.4)? Antes de tocar score_engine.py, este
script mide el lift de varias señales candidatas SOBRE LOS DATOS CRUDOS, con la
misma metodología honesta de validar_pesos.py (holdout temporal).

POR QUÉ ES UN SCRIPT APARTE (y no validar_pesos.py):
  validar_pesos.py reconstruye el score a partir de la LISTA de señales ya
  guardada en score_historico. Sirve para re-pesar señales que YA existen, pero
  no puede inventar una señal que no esté guardada. Una señal nueva hay que
  calcularla desde los datos crudos (ventas_mensual + vendedores + grupos). Eso
  hace este script. Si una candidata resulta tener buen lift, recién ahí se
  implementa en score_engine.py y se vuelve a correr el backfill.

METODOLOGÍA (idéntica a validar_pesos.py):
  · Egresado: se mira su ventana de 3 meses PREVIOS al egreso.
  · Activo:   se miran sus 3 meses más recientes.
  · Señal "activa" para el vendedor = activa en alguno de esos 3 meses
    (salvo las que son por naturaleza de ventana, como tenure×grupo).
  · LIFT = %egresados_con_señal / %activos_con_señal.
        lift > 1.5  -> distingue bien (mejor que las débiles actuales).
        lift ~1.0   -> no sirve (no separa).
  · HOLDOUT: se parte a los egresados por mediana de fecha de egreso. El lift
    que importa es el de la mitad RECIENTE (out-of-sample): que la señal separe
    en egresados que no usamos para inventarla.

Para las señales continuas (variabilidad, caída abrupta) se barren varios
umbrales para encontrar el punto con mejor lift OOS.

Solo LECTURA sobre data/wurth.db. Corre con cualquier Python (no usa pandas):
    "C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" scripts\\explorar_senales_nuevas.py
"""

import sqlite3
import os
from statistics import mean, pstdev

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

N_VENTANA = 3   # meses de ventana (igual que el motor)


# ── Carga de datos crudos (solo lectura) ─────────────────────────────────────
def cargar(con):
    cur = con.cursor()

    # ventas_mensual por vendedor, ordenadas ascendente por período
    cur.execute("""
        SELECT id_vendedor, anio, mes, mes_numero, pct_plan, plan, venta_total,
               dias_venta_cero, total_clientes, clientes_activos,
               clientes_nuevos, pct_cobranza, cobranza_teorica
        FROM ventas_mensual
        ORDER BY id_vendedor, anio, mes
    """)
    cols = ["id_vendedor","anio","mes","mes_numero","pct_plan","plan","venta_total",
            "dias_venta_cero","total_clientes","clientes_activos","clientes_nuevos",
            "pct_cobranza","cobranza_teorica"]
    ventas = {}   # vid -> list[dict] ascendente
    for row in cur.fetchall():
        d = dict(zip(cols, row))
        d["pnum"] = d["anio"] * 100 + d["mes"]
        ventas.setdefault(d["id_vendedor"], []).append(d)

    # vendedores + riesgo_base del grupo
    cur.execute("""
        SELECT v.id_vendedor, v.activo, v.fecha_egreso, COALESCE(g.riesgo_base, 0)
        FROM vendedores v
        LEFT JOIN grupos g ON v.id_grupo = g.id_grupo
        WHERE v.id_vendedor != 9800
    """)
    egresados = {}   # vid -> pnum de egreso
    activos   = set()
    riesgo_base = {}
    for vid, activo, fegr, rb in cur.fetchall():
        riesgo_base[vid] = rb
        if activo == 0 and fegr:
            egresados[vid] = int(str(fegr)[:4]) * 100 + int(str(fegr)[5:7])
        elif activo == 1:
            activos.add(vid)

    return ventas, egresados, activos, riesgo_base


def periodos_pre_egreso(pnum_egreso, n=N_VENTANA):
    outs = []
    a, m = pnum_egreso // 100, pnum_egreso % 100
    for _ in range(n):
        m -= 1
        if m == 0:
            m = 12; a -= 1
        outs.append(a * 100 + m)
    return set(outs)


def filas_ventana(ventas, vid, pnums=None, ultimos=None):
    """Devuelve las filas (ascendente) del vendedor dentro de la ventana."""
    serie = ventas.get(vid, [])
    if pnums is not None:
        return [r for r in serie if r["pnum"] in pnums]
    if ultimos is not None:
        return serie[-ultimos:]
    return serie


# ── SEÑALES CANDIDATAS ───────────────────────────────────────────────────────
# Cada candidata es una función(filas, riesgo_base, umbral) -> bool|None.
# filas: lista de meses de la ventana (ascendente). None = sin datos suficientes.

def sig_variabilidad_plan(filas, rb, umbral):
    """Variabilidad (desvío) del % plan en la ventana. Mucha oscilación mes a
    mes puede indicar inestabilidad antes de la fuga."""
    vals = [r["pct_plan"] for r in filas if r["plan"] and r["plan"] > 0]
    if len(vals) < 2:
        return None
    return pstdev(vals) > umbral

def sig_coefvar_venta(filas, rb, umbral):
    """Coeficiente de variación de la venta total (desvío/promedio). Normaliza
    por tamaño: capta inestabilidad relativa, no el volumen."""
    vals = [r["venta_total"] for r in filas if r["venta_total"] is not None]
    vals = [v for v in vals if v > 0]
    if len(vals) < 2:
        return None
    m = mean(vals)
    if m <= 0:
        return None
    return (pstdev(vals) / m) > umbral

def sig_caida_abrupta(filas, rb, umbral):
    """Mayor caída mes-a-mes de venta_total dentro de la ventana, como fracción
    del mes anterior. Capta un derrumbe puntual (cliente grande perdido, etc.)."""
    vals = [r["venta_total"] for r in filas if r["venta_total"] is not None]
    if len(vals) < 2:
        return None
    peor = 0.0
    for a, b in zip(vals[:-1], vals[1:]):
        if a > 0:
            caida = (a - b) / a
            peor = max(peor, caida)
    return peor > umbral

def sig_dias_cero_creciente(filas, rb, umbral):
    """Días sin venta con tendencia CRECIENTE (pendiente positiva). No el nivel
    (eso ya lo capta la señal actual), sino que esté empeorando."""
    vals = [r["dias_venta_cero"] for r in filas]
    if len(vals) < 2:
        return None
    # pendiente simple por mínimos cuadrados
    n = len(vals); xs = list(range(n))
    mx = mean(xs); my = mean(vals)
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    pend = sum((x - mx) * (y - my) for x, y in zip(xs, vals)) / den
    return pend > umbral

def sig_tenure_grupo(filas, rb, umbral):
    """INTERACCIÓN tenure×grupo: vendedor nuevo (mes 1-3) Y en grupo quemado
    (riesgo_base > umbral). La hipótesis central del proyecto: ser nuevo en un
    grupo malo compone el riesgo más que cada factor por separado."""
    if not filas:
        return None
    mes_num = filas[-1].get("mes_numero")
    if mes_num is None:
        return None
    return (1 <= mes_num <= 3) and (rb > umbral)

def sig_tenure_grupo_amplio(filas, rb, umbral):
    """Variante: ventana 1-6 (no solo 1-3) en grupo quemado."""
    if not filas:
        return None
    mes_num = filas[-1].get("mes_numero")
    if mes_num is None:
        return None
    return (1 <= mes_num <= 6) and (rb > umbral)

def sig_cobranza_empeorando(filas, rb, umbral):
    """% cobranza con tendencia a la baja (pendiente negativa fuerte). Distinto
    del nivel: capta el deterioro de cobranza, no que ya esté baja."""
    vals = [(r["pct_cobranza"]) for r in filas if r["cobranza_teorica"] and r["cobranza_teorica"] > 0]
    if len(vals) < 2:
        return None
    n = len(vals); xs = list(range(n))
    mx = mean(xs); my = mean(vals)
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    pend = sum((x - mx) * (y - my) for x, y in zip(xs, vals)) / den
    return pend < -umbral


# (función, etiqueta, lista de umbrales a barrer)
CANDIDATAS = [
    (sig_variabilidad_plan,    "Variabilidad %plan (desvío > U)",       [10, 15, 20, 25, 30]),
    (sig_coefvar_venta,        "Coef.var venta (desvío/prom > U)",      [0.2, 0.3, 0.4, 0.5]),
    (sig_caida_abrupta,        "Caída abrupta venta MoM > U",           [0.3, 0.4, 0.5, 0.6]),
    (sig_dias_cero_creciente,  "Días venta cero creciendo (pend > U)",  [0.5, 1.0, 1.5, 2.0]),
    (sig_cobranza_empeorando,  "Cobranza empeorando (pend < -U)",       [2, 4, 6, 8]),
    (sig_tenure_grupo,         "Tenure 1-3 × grupo quemado (rb > U)",   [0.30, 0.40, 0.50]),
    (sig_tenure_grupo_amplio,  "Tenure 1-6 × grupo quemado (rb > U)",   [0.30, 0.40, 0.50]),
]


def main():
    con = sqlite3.connect(DB_PATH)
    ventas, egresados, activos, riesgo_base = cargar(con)
    con.close()

    # Egresados evaluables (con al menos 1 mes en su ventana pre-egreso) y holdout
    def tiene_ventana_egr(vid):
        return len(filas_ventana(ventas, vid, pnums=periodos_pre_egreso(egresados[vid]))) > 0

    egr_eval = [v for v in egresados if v in ventas and tiene_ventana_egr(v)]
    egr_eval.sort(key=lambda v: egresados[v])
    mitad = len(egr_eval) // 2
    egr_recientes = egr_eval[mitad:]          # out-of-sample
    act_eval = [v for v in activos if v in ventas and len(ventas[v]) >= 1]

    print("=" * 74)
    print("EXPLORACIÓN DE SEÑALES NUEVAS — ¿superan a las débiles (lift ~1.2-1.4)?")
    print("=" * 74)
    print(f"\n  Egresados evaluables: {len(egr_eval)}  (OOS recientes: {len(egr_recientes)})")
    print(f"  Activos evaluables:   {len(act_eval)}")
    print(f"  Ventana: {N_VENTANA} meses pre-egreso (egr) / {N_VENTANA} más recientes (act)")
    print("\n  Referencia: una señal NUEVA vale la pena si su lift OOS supera con")
    print("  holgura a las débiles actuales (visitas ~1.2, balanza ~1.4). Apuntar")
    print("  a lift >= 1.8-2.0 para que aporte de verdad.\n")

    def freq(grupo, fn, umbral, es_egr):
        activos_n = 0; total = 0
        for vid in grupo:
            if es_egr:
                filas = filas_ventana(ventas, vid, pnums=periodos_pre_egreso(egresados[vid]))
            else:
                filas = filas_ventana(ventas, vid, ultimos=N_VENTANA)
            r = fn(filas, riesgo_base.get(vid, 0), umbral)
            if r is None:
                continue
            total += 1
            if r:
                activos_n += 1
        return (activos_n / total * 100 if total else 0.0), total

    for fn, etiqueta, umbrales in CANDIDATAS:
        print("-" * 74)
        print(f"  {etiqueta}")
        print(f"    {'umbral':>8} {'%egr OOS':>9} {'%act':>7} {'lift OOS':>9} {'veredicto':>14}")
        mejor = None
        for u in umbrales:
            fe, _ = freq(egr_recientes, fn, u, True)
            fa, _ = freq(act_eval, fn, u, False)
            lift = (fe / fa) if fa > 0 else (float("inf") if fe > 0 else 0.0)
            if mejor is None or (lift != float("inf") and (mejor[2] == float("inf") or lift > mejor[2])):
                mejor = (u, fe, lift, fa)
            lift_s = " inf" if lift == float("inf") else f"{lift:5.2f}"
            if lift == float("inf") or lift >= 1.8:
                vd = "FUERTE"
            elif lift >= 1.4:
                vd = "ok (~débil)"
            else:
                vd = "no separa"
            u_s = f"{u:.2f}" if isinstance(u, float) else str(u)
            print(f"    {u_s:>8} {fe:>8.1f}% {fa:>6.1f}% {lift_s:>9} {vd:>14}")
        if mejor:
            u, fe, lift, fa = mejor
            lift_s = "inf" if lift == float("inf") else f"{lift:.2f}"
            print(f"    -> mejor umbral: {u}  (lift OOS {lift_s}, marca {fe:.0f}% egr / {fa:.0f}% act)")

    print("\n" + "=" * 74)
    print("CAVEAT DE LECTURA:")
    print("  · 'inf' o lifts enormes con %act=0 son POCO confiables: el pool de")
    print("    activos es chico y un 0% es ruido de muestra, no señal. Preferí")
    print("    candidatas donde TANTO %egr como %act estén poblados (ej: tenure 1-6")
    print("    × grupo, cobranza empeorando): su lift es estadísticamente sólido.")
    print("  · OJO doble conteo: 'tenure × grupo' se solapa con las señales que ya")
    print("    existen ('ventana crítica' + 'grupo quemado'). Solo aporta si el")
    print("    combo separa MÁS que la suma de las dos por separado -> validar el")
    print("    Δseparación en validar_pesos.py tras el backfill, no solo el lift.")
    print("\n" + "-" * 74)
    print("CÓMO SEGUIR:")
    print("  1. Tomá las candidatas con lift OOS >= ~1.8 (las 'FUERTE').")
    print("  2. Implementala como nueva Señal(...) en src/score_engine.py con un")
    print("     peso inicial proporcional a su lift (las fuertes actuales pesan 2.0-2.5).")
    print("  3. Re-corré el backfill para que score_historico la incluya.")
    print("  4. Validala en validar_pesos.py (auditoría por señal + barrido REF):")
    print("     que suba la separación detección-vs-falsa-alarma out-of-sample.")
    print("  Si ninguna candidata supera a las débiles, mejor podar las débiles")
    print("  (bajarles peso) que agregar ruido nuevo.")
    print("=" * 74)


if __name__ == "__main__":
    main()
