"""
scripts/validar_pesos.py
------------------------
¿Los pesos sugeridos por la pantalla de Aprendizaje predicen MEJOR, o solo se
ajustan a lo que ya pasó? Esta es la prueba honesta antes de cambiar el score.

CÓMO FUNCIONA (sin tocar ninguna base externa, solo lee SQLite):
  1. score_historico ya guarda, por vendedor/período, la LISTA de señales que
     estaban activas. Cada señal tiene un peso. El score se reconstruye como:
         riesgo = suma de pesos de las señales activas
         score  = 1 + min(riesgo / RIESGO_REFERENCIA, 1) * 9
     => podemos recalcular el score con CUALQUIER set de pesos sin re-correr el
        motor ni consultar Informix/Reactor/SUN.

  2. Comparamos dos sets de pesos:
        ACTUAL    = los que usa hoy score_engine.py
        PROPUESTO = ACTUAL con los cambios que sugiere Aprendizaje

  3. HOLDOUT TEMPORAL: partimos a los egresados en dos mitades por fecha de
     egreso (vieja / reciente). Los pesos se "inspiraron" mirando todo el
     histórico, así que la prueba justa es si MEJORAN la detección en la mitad
     RECIENTE (out-of-sample), no solo en la vieja.

  4. Métricas por set de pesos:
        DETECCIÓN (recall): % de egresados con score >= 6 en sus 3 meses
                            previos al egreso. Más alto = mejor (los vemos
                            antes de que se vayan).
        FALSA ALARMA:       % de activos con score >= 6 en sus últimos 3 meses.
                            Más alto = peor (molestamos a quien no se va).

     Subir pesos SIEMPRE sube ambas. Lo que importa es si la detección sube
     MÁS que la falsa alarma. Si no, es sobreajuste.

Solo LECTURA sobre data/wurth.db. Corre con cualquier Python (no usa pandas):
    "C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312\\python.exe" scripts\\validar_pesos.py
"""

import sqlite3
import os
import json
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

RIESGO_REFERENCIA = 8.0    # coincide con score_engine.py (calibrado por backtest)
UMBRAL_RIESGO     = 6.0   # score >= 6 = alto/crítico = "el modelo lo marca"

# ── Pesos ACTUALES (deben coincidir con score_engine.py) ─────────────────────
PESOS_ACTUAL = {
    # Deshabilitada: con umbral <-50 pp/mes dispara en solo 1.1% de egresados
    # y 0% de activos — muestra insignificante, Δsep=0. El %plan en Würth 2026
    # es tan volátil que la pendiente no discrimina a ningún umbral razonable.
    "% Plan cayendo 3 meses seguidos":                              0.0,
    "% Plan < 80% promedio últimos meses":                         2.0,
    "Días sin venta > 3 en promedio":                              2.5,
    # Deshabilitada: Informix reasigna clientes al egreso → histórico queda en 0
    # → dato faltante la apaga en egresados pero no en activos → lift 0.01, Δsep +13.4.
    "< 60% de cartera activa":                                     0.0,
    # Deshabilitada: lift 1.07 (cobranza baja generalizada ~48% egr vs ~46% act),
    # Δsep +3.2 al sacarla. No diferencia; re-evaluar si el dato mejora.
    "Cobranza real < 90% de teórica":                              0.0,
    "En ventana crítica mes 1-3":                                  1.5,
    "En ventana crítica mes 4-6":                                  1.0,
    "Grupo con alta rotación histórica":                           1.5,
    "Sin clientes nuevos últimos 2 meses":                         0.5,
    # Deshabilitadas: egresados raramente tienen datos Reactor en sus últimos meses
    # → señal dispara más en activos que en egresados → invertida (lift < 1, Δsep > 0).
    "< 70% de llamadas planificadas gestionadas (Televentas)":     0.0,
    "< 70% de visitas planificadas realizadas (Viajante)":         0.0,
    "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3": 2.0,
    "Balanza clientes negativa 2+ meses consecutivos":             1.5,
    "Ticket promedio cae > 5% por mes":                            1.0,
    "Supervisor no acompañó en ventana crítica 1-6":               1.0,
    # tenure × grupo probada y descartada (Δsep +1.7, doble conteo). No se agregó.
}

# ── Pesos PROPUESTOS ──────────────────────────────────────────────────────────
# Las subidas de días venta cero (1.5->2.5) y cobranza (1.0->2.0) YA se aplicaron
# a producción (score_engine.py) tras validarse acá. PESOS_PROPUESTO arranca
# igual a PESOS_ACTUAL; para probar un cambio NUEVO, modificá una línea abajo y
# volvé a correr el script (sigue sirviendo como banco de pruebas + monitoreo).
PESOS_PROPUESTO = dict(PESOS_ACTUAL)
# Ejemplo de cambio a probar (descomentar y ajustar):
# PESOS_PROPUESTO["Sin clientes nuevos últimos 2 meses"] = 1.5


def periodo_a_num(periodo):
    """'2025-03' -> 202503"""
    a, m = periodo.split("-")
    return int(a) * 100 + int(m)


def fecha_a_periodo_num(fecha_iso):
    """'2025-03-15' -> 202503"""
    a = int(fecha_iso[:4]); m = int(fecha_iso[5:7])
    return a * 100 + m


def score_de(senales, pesos, ref=RIESGO_REFERENCIA):
    """Reconstruye el score 1-10 a partir de la lista de señales activas.
    ref = RIESGO_REFERENCIA: subirlo baja todos los scores (calibración)."""
    riesgo = sum(pesos.get(s, 0.0) for s in senales)
    return 1 + min(riesgo / ref, 1.0) * 9


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # ── Cargar score_historico: por vendedor, lista de (periodo_num, señales) ─
    cur.execute("SELECT periodo, id_vendedor, score, señales FROM score_historico")
    hist = {}        # id_vendedor -> list[(periodo_num, [señales])]
    score_guardado = {}  # (periodo_num, id_vendedor) -> score guardado (sanity check)
    for periodo, vid, score, senales_json in cur.fetchall():
        try:
            senales = json.loads(senales_json) if senales_json else []
        except Exception:
            senales = []
        pnum = periodo_a_num(periodo)
        hist.setdefault(vid, []).append((pnum, senales))
        score_guardado[(pnum, vid)] = score

    # ── Sanity check: ¿mi reconstrucción con pesos ACTUALES = score guardado? ─
    difs = []
    senales_desconocidas = set()
    for vid, filas in hist.items():
        for pnum, senales in filas:
            for s in senales:
                if s not in PESOS_ACTUAL:
                    senales_desconocidas.add(s)
            recon = round(min(10, max(1, score_de(senales, PESOS_ACTUAL))), 1)
            difs.append(abs(recon - score_guardado[(pnum, vid)]))
    max_dif = max(difs) if difs else 0
    print("=" * 70)
    print("VALIDACIÓN DE PESOS — ¿predicen mejor o sobreajustan?")
    print("=" * 70)
    print(f"\n[chequeo] Reconstrucción del score con pesos actuales:")
    print(f"          máxima diferencia vs score guardado = {max_dif:.2f}", end="")
    print("  (debe ser ~0)" if max_dif < 0.15 else "  <-- OJO: no coincide, revisar pesos")
    if senales_desconocidas:
        print(f"          AVISO: señales sin peso mapeado: {senales_desconocidas}")

    # ── Clasificar egresados (con fecha) y activos ───────────────────────────
    cur.execute("""
        SELECT id_vendedor, activo, fecha_egreso
        FROM vendedores
        WHERE id_vendedor != 9800
    """)
    egresados = {}   # vid -> periodo_num del egreso
    activos   = set()
    for vid, activo, fegr in cur.fetchall():
        if activo == 0 and fegr:
            egresados[vid] = fecha_a_periodo_num(str(fegr))
        elif activo == 1:
            activos.add(vid)

    # ── Ventana pre-egreso: 3 períodos antes del egreso ──────────────────────
    def periodos_pre_egreso(pnum_egreso, n=3):
        outs = []
        a, m = pnum_egreso // 100, pnum_egreso % 100
        for _ in range(n):
            m -= 1
            if m == 0:
                m = 12; a -= 1
            outs.append(a * 100 + m)
        return set(outs)

    # ── Detección de un egresado bajo un set de pesos ────────────────────────
    # detectado = en ALGUNO de sus 3 meses previos tuvo score >= UMBRAL
    def egresado_detectado(vid, pesos, ref=RIESGO_REFERENCIA, umbral=UMBRAL_RIESGO):
        if vid not in hist or vid not in egresados:
            return None  # sin datos para evaluar
        ventana = periodos_pre_egreso(egresados[vid])
        scores_ventana = [score_de(sen, pesos, ref) for (pnum, sen) in hist[vid] if pnum in ventana]
        if not scores_ventana:
            return None
        return max(scores_ventana) >= umbral

    # ── Falsa alarma de un activo bajo un set de pesos ───────────────────────
    # falsa alarma = en sus 3 períodos más recientes tuvo score >= UMBRAL
    def activo_falsa_alarma(vid, pesos, ref=RIESGO_REFERENCIA, umbral=UMBRAL_RIESGO):
        if vid not in hist:
            return None
        ult = sorted(hist[vid], key=lambda x: x[0])[-3:]
        if not ult:
            return None
        return max(score_de(sen, pesos, ref) for (_, sen) in ult) >= umbral

    # ── Holdout temporal: partir egresados por mediana de fecha de egreso ─────
    egr_evaluables = [vid for vid in egresados if egresado_detectado(vid, PESOS_ACTUAL) is not None]
    egr_evaluables.sort(key=lambda v: egresados[v])
    mitad = len(egr_evaluables) // 2
    egr_viejos    = set(egr_evaluables[:mitad])
    egr_recientes = set(egr_evaluables[mitad:])
    corte = egresados[egr_evaluables[mitad]] if egr_evaluables else 0

    def tasa_deteccion(grupo, pesos, ref=RIESGO_REFERENCIA):
        det = [egresado_detectado(v, pesos, ref) for v in grupo]
        det = [d for d in det if d is not None]
        return (sum(det) / len(det) * 100 if det else 0.0), len(det)

    def tasa_falsa_alarma(pesos, ref=RIESGO_REFERENCIA, umbral=UMBRAL_RIESGO):
        fa = [activo_falsa_alarma(v, pesos, ref, umbral) for v in activos]
        fa = [f for f in fa if f is not None]
        return (sum(fa) / len(fa) * 100 if fa else 0.0), len(fa)

    def tasa_deteccion_u(grupo, pesos, ref, umbral):
        det = [egresado_detectado(v, pesos, ref, umbral) for v in grupo]
        det = [d for d in det if d is not None]
        return (sum(det) / len(det) * 100 if det else 0.0)

    print(f"\nEgresados evaluables: {len(egr_evaluables)}  "
          f"(viejos: {len(egr_viejos)}, recientes: {len(egr_recientes)})")
    print(f"Activos evaluables:   {len(activos)}")
    print(f"Corte temporal (holdout) en período: {corte//100}-{corte%100:02d}")

    # ── Tabla comparativa ────────────────────────────────────────────────────
    def fila(label, val_act, val_prop, n, mejor_alto=True):
        delta = val_prop - val_act
        flecha = "▲" if delta > 0.05 else ("▼" if delta < -0.05 else "=")
        print(f"  {label:42} {val_act:6.1f}%  {val_prop:6.1f}%   {flecha} {delta:+5.1f}  (n={n})")

    print("\n" + "-" * 70)
    print(f"  {'MÉTRICA':42} {'ACTUAL':>7} {'PROPU.':>8}   {'CAMBIO':>8}")
    print("-" * 70)
    print("  DETECCIÓN de egresados (más alto = mejor):")
    d_v_a, n_v = tasa_deteccion(egr_viejos, PESOS_ACTUAL)
    d_v_p, _   = tasa_deteccion(egr_viejos, PESOS_PROPUESTO)
    fila("  · mitad vieja (in-sample)", d_v_a, d_v_p, n_v)
    d_r_a, n_r = tasa_deteccion(egr_recientes, PESOS_ACTUAL)
    d_r_p, _   = tasa_deteccion(egr_recientes, PESOS_PROPUESTO)
    fila("  · mitad reciente (OUT-OF-SAMPLE) ***", d_r_a, d_r_p, n_r)
    d_t_a, n_t = tasa_deteccion(set(egr_evaluables), PESOS_ACTUAL)
    d_t_p, _   = tasa_deteccion(set(egr_evaluables), PESOS_PROPUESTO)
    fila("  · total", d_t_a, d_t_p, n_t)

    print("\n  FALSA ALARMA en activos (más alto = peor):")
    fa_a, n_fa = tasa_falsa_alarma(PESOS_ACTUAL)
    fa_p, _    = tasa_falsa_alarma(PESOS_PROPUESTO)
    fila("  · activos marcados score>=6", fa_a, fa_p, n_fa)

    # ── Veredicto ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("CÓMO LEERLO:")
    ganancia_oos = d_r_p - d_r_a       # cuánto sube detección out-of-sample
    costo_fa     = fa_p - fa_a         # cuánto sube falsa alarma
    print(f"  Detección out-of-sample:  {d_r_a:.1f}% -> {d_r_p:.1f}%  ({ganancia_oos:+.1f} pts)")
    print(f"  Falsa alarma:             {fa_a:.1f}% -> {fa_p:.1f}%  ({costo_fa:+.1f} pts)")
    print()
    if PESOS_PROPUESTO == PESOS_ACTUAL:
        print("  (PESOS_PROPUESTO == PESOS_ACTUAL: no hay cambio de pesos que probar.")
        print("   El script corre como monitoreo. Para evaluar un cambio nuevo,")
        print("   editá PESOS_PROPUESTO arriba. Usá el barrido de abajo para calibrar.)")
    elif ganancia_oos <= 0.1:
        print("  VEREDICTO: los pesos propuestos NO mejoran la detección de los")
        print("  egresados que el análisis no usó. Probablemente sea sobreajuste.")
        print("  -> NO conviene cambiar los pesos.")
    elif ganancia_oos > costo_fa:
        print("  VEREDICTO: la detección out-of-sample sube MÁS que la falsa alarma.")
        print("  La evidencia respalda el cambio de pesos. Conviene aplicarlo y")
        print("  monitorear la falsa alarma real en producción.")
    else:
        print("  VEREDICTO: la detección sube, pero la falsa alarma sube IGUAL o MÁS.")
        print("  El cambio es discutible: ganás detección a costa de más ruido.")
        print("  Decisión de negocio: ¿cuánto molesta una falsa alarma vs perder a")
        print("  alguien sin verlo venir?")
    print("=" * 70)

    # ── BARRIDO de RIESGO_REFERENCIA (curva detección vs falsa alarma) ───────
    # Con los pesos PROPUESTOS, ¿qué pasa si subimos la referencia? Subirla baja
    # todos los scores → menos gente cae en score>=6 → menos detección PERO
    # menos falsa alarma. Buscamos el punto donde la falsa alarma se vuelve
    # manejable sin perder demasiada detección de egresados.
    print("\n" + "=" * 70)
    print("BARRIDO DE CALIBRACIÓN — RIESGO_REFERENCIA (pesos PROPUESTOS)")
    print("=" * 70)
    print("  Subir la referencia = score más exigente = menos alertas.")
    print("  'separación' = detección_OOS - falsa_alarma (más alto = mejor filtro)\n")
    print(f"  {'REF':>5} {'Det.OOS':>9} {'Det.total':>10} {'FalsaAlarma':>12} {'Separación':>11}")
    print("  " + "-" * 52)
    mejor_ref, mejor_sep = None, -999
    referencias = [8, 10, 11, 12, 13, 14, 15, 16, 18, 20, 22]
    for ref in referencias:
        det_oos, _ = tasa_deteccion(egr_recientes, PESOS_PROPUESTO, ref)
        det_tot, _ = tasa_deteccion(set(egr_evaluables), PESOS_PROPUESTO, ref)
        fa, _      = tasa_falsa_alarma(PESOS_PROPUESTO, ref)
        sep        = det_oos - fa
        marca = ""
        if sep > mejor_sep:
            mejor_sep, mejor_ref = sep, ref
        actual = f"  <- actual ({int(RIESGO_REFERENCIA)})" if ref == int(RIESGO_REFERENCIA) else ""
        print(f"  {ref:>5} {det_oos:>8.1f}% {det_tot:>9.1f}% {fa:>11.1f}% {sep:>10.1f}{actual}")

    # Recomendación: mayor separación, y además falsa alarma 'manejable' (<=40%)
    print("  " + "-" * 52)
    print(f"\n  Mejor SEPARACIÓN detección-falsa alarma: REF = {mejor_ref}")

    # Buscar el primer REF donde falsa alarma <= 40% (objetivo manejable)
    objetivo_fa = 40.0
    ref_objetivo = None
    for ref in referencias:
        fa, _ = tasa_falsa_alarma(PESOS_PROPUESTO, ref)
        if fa <= objetivo_fa:
            ref_objetivo = ref
            det_oos, _ = tasa_deteccion(egr_recientes, PESOS_PROPUESTO, ref)
            det_tot, _ = tasa_deteccion(set(egr_evaluables), PESOS_PROPUESTO, ref)
            break
    if ref_objetivo:
        print(f"  Para bajar la falsa alarma a <= {objetivo_fa:.0f}%: REF = {ref_objetivo}")
        print(f"    -> ahí la detección OOS queda en {det_oos:.1f}% y total {det_tot:.1f}%")
    else:
        print(f"  Ningún REF probado baja la falsa alarma a <= {objetivo_fa:.0f}%.")
    print("\n  CÓMO DECIDIR: elegí el REF más alto que todavía detecte a una")
    print("  proporción aceptable de egresados. Más arriba = menos ruido para el")
    print("  supervisor, pero más egresados que se escapan sin alerta.")
    print("=" * 70)

    # ── Barrido del nivel CRÍTICO (>=8), que es la alerta accionable ─────────
    # El barrido de arriba usa el umbral >=6. Pero el supervisor actúa sobre
    # >=8 ('reunión esta semana'). Acá vemos, por cada REF, cómo se comporta esa
    # alerta accionable. Buscamos un REF donde >=8 detecte a una porción real de
    # egresados con poca falsa alarma (que cada reunión convocada valga la pena).
    print("\n" + "=" * 70)
    print("BARRIDO DEL NIVEL CRÍTICO (>=8, 'reunión esta semana')")
    print("=" * 70)
    print("  A REF alto, score>=8 es casi inalcanzable -> la alerta no dispara.")
    print("  A REF bajo, dispara más pero con más falsa alarma.\n")
    print(f"  {'REF':>5} {'Det>=8':>8} {'F.alarma>=8':>12} {'Separación':>11}")
    print("  " + "-" * 40)
    mejor_ref8, mejor_sep8 = None, -999
    for ref in referencias:
        det8 = tasa_deteccion_u(set(egr_evaluables), PESOS_PROPUESTO, ref, 8.0)
        fa8, _ = tasa_falsa_alarma(PESOS_PROPUESTO, ref, 8.0)
        sep8 = det8 - fa8
        if sep8 > mejor_sep8:
            mejor_sep8, mejor_ref8 = sep8, ref
        actual = f"  <- actual ({int(RIESGO_REFERENCIA)})" if ref == int(RIESGO_REFERENCIA) else ""
        print(f"  {ref:>5} {det8:>7.1f}% {fa8:>11.1f}% {sep8:>10.1f}{actual}")
    print("  " + "-" * 40)
    print(f"\n  Mejor separación del nivel crítico (>=8): REF = {mejor_ref8}")
    print("  Si incluso ahí la detección >=8 es muy baja, significa que el nivel")
    print("  'crítico' no puede ser la única alerta accionable: conviene actuar")
    print("  sobre el TOP del ranking de score, no sobre un umbral fijo.")
    print("=" * 70)

    # ── Niveles de alerta operativos (a la REF de producción) ────────────────
    # El supervisor NO actúa sobre todo score >= 6. La acción real es:
    #   score >= 8  -> crítico -> "reunión esta semana"
    #   score >= 6  -> alto    -> "seguimiento activo"
    # Medimos cada nivel por separado para saber cuán precisa es CADA alerta.
    print("\n" + "=" * 70)
    print(f"NIVELES DE ALERTA OPERATIVOS (REF de producción = {int(RIESGO_REFERENCIA)})")
    print("=" * 70)
    print("  Qué tan seguido cae cada grupo en cada nivel de alerta:\n")
    print(f"  {'NIVEL':28} {'egresados (det.)':>17} {'activos (f.alarma)':>20}")
    print("  " + "-" * 64)
    for umbral, etiqueta in ((8.0, "crítico (>=8) reunión"),
                             (6.0, "alto+crit (>=6) seguim.")):
        det = [egresado_detectado(v, PESOS_ACTUAL, RIESGO_REFERENCIA, umbral)
               for v in egr_evaluables]
        det = [d for d in det if d is not None]
        fa  = [activo_falsa_alarma(v, PESOS_ACTUAL, RIESGO_REFERENCIA, umbral)
               for v in activos]
        fa  = [f for f in fa if f is not None]
        det_pct = sum(det) / len(det) * 100 if det else 0
        fa_pct  = sum(fa) / len(fa) * 100 if fa else 0
        print(f"  {etiqueta:28} {det_pct:>15.1f}% {fa_pct:>19.1f}%")
    print("\n  CÓMO LEERLO: la fila 'crítico (>=8)' es la alerta sobre la que el")
    print("  supervisor realmente actúa. Si su falsa alarma es baja, cada reunión")
    print("  convocada está bien justificada (poca molestia). La fila '>=6' es el")
    print("  seguimiento más amplio, tolera más ruido porque la acción es liviana.")
    print("=" * 70)

    # ── AUDITORÍA POR SEÑAL — ¿cuáles aportan y cuáles son ruido? ─────────────
    # Para cada señal calculamos dos cosas:
    #   1) LIFT: cada cuánto está activa en egresados (ventana pre-egreso) vs en
    #      activos (ventana reciente). lift > 1 = aparece más en los que se van.
    #      lift ~1 = no distingue (la señal no separa). Es el mismo número que
    #      muestra la pantalla de Aprendizaje, recalculado acá para auditar.
    #   2) CONTRIBUCIÓN MARGINAL: cuánto cae la separación (detección_OOS -
    #      falsa_alarma) si a esa señal le ponemos peso 0. Positivo = la señal
    #      ayuda; ~0 o negativo = sacarla no empeora (o mejora). Es la prueba
    #      definitiva de si vale la pena tenerla pesando en el score.
    print("\n" + "=" * 70)
    print("AUDITORÍA POR SEÑAL — lift y contribución marginal a la separación")
    print("=" * 70)

    # Frecuencia de cada señal en un grupo de vendedores dentro de su ventana.
    def freq_senal_en(grupo, ventana_de):
        # ventana_de(vid) -> set de periodos a mirar para ese vendedor
        cont = {s: 0 for s in PESOS_ACTUAL}
        total = 0
        for vid in grupo:
            if vid not in hist:
                continue
            ventana = ventana_de(vid)
            filas = [sen for (pnum, sen) in hist[vid] if pnum in ventana]
            if not filas:
                continue
            total += 1
            # señal "activa para el vendedor" = activa en alguno de sus meses de ventana
            activas = set()
            for sen in filas:
                activas.update(sen)
            for s in PESOS_ACTUAL:
                if s in activas:
                    cont[s] += 1
        return cont, total

    def ventana_egr(vid):
        return periodos_pre_egreso(egresados[vid])

    def ventana_act(vid):
        return {pnum for (pnum, _) in sorted(hist[vid], key=lambda x: x[0])[-3:]}

    cont_egr, n_egr = freq_senal_en(egr_recientes, ventana_egr)   # OOS
    cont_act, n_act = freq_senal_en(activos, ventana_act)

    # Separación base con todos los pesos actuales (a REF de producción).
    def separacion(pesos, ref=RIESGO_REFERENCIA):
        det_oos, _ = tasa_deteccion(egr_recientes, pesos, ref)
        fa, _      = tasa_falsa_alarma(pesos, ref)
        return det_oos - fa

    sep_base = separacion(PESOS_ACTUAL)

    print(f"\n  Egresados OOS evaluados: {n_egr}   Activos evaluados: {n_act}")
    print(f"  Separación base (todos los pesos, REF={int(RIESGO_REFERENCIA)}): {sep_base:.1f}\n")
    print(f"  {'SEÑAL':44} {'peso':>5} {'%egr':>6} {'%act':>6} {'lift':>6} {'Δsep si=0':>10}")
    print("  " + "-" * 80)

    filas_audit = []
    for s in PESOS_ACTUAL:
        fe = cont_egr.get(s, 0) / n_egr * 100 if n_egr else 0
        fa_ = cont_act.get(s, 0) / n_act * 100 if n_act else 0
        lift = (fe / fa_) if fa_ > 0 else float("inf") if fe > 0 else 0.0
        pesos_sin = dict(PESOS_ACTUAL); pesos_sin[s] = 0.0
        delta_sep = separacion(pesos_sin) - sep_base   # negativo = sacarla empeora
        filas_audit.append((s, PESOS_ACTUAL[s], fe, fa_, lift, delta_sep))

    # Ordenar por lift descendente para ver arriba las que más separan.
    filas_audit.sort(key=lambda r: (r[4] if r[4] != float("inf") else 999), reverse=True)
    for s, peso, fe, fa_, lift, delta_sep in filas_audit:
        lift_str = "  inf" if lift == float("inf") else f"{lift:5.2f}"
        nombre = (s[:42] + "..") if len(s) > 44 else s
        print(f"  {nombre:44} {peso:>5.1f} {fe:>5.1f}% {fa_:>5.1f}% {lift_str:>6} {delta_sep:>+9.1f}")

    print("  " + "-" * 80)
    print("  CÓMO LEERLO:")
    print("   · lift ~1.0  -> la señal NO distingue egresados de activos (ruido).")
    print("   · Δsep si=0  -> cambio en la separación al anular la señal.")
    print("        negativo = la señal aporta (sacarla empeora el filtro)")
    print("        ~0 / positivo = sacarla NO empeora (o mejora): candidata a")
    print("        bajarle el peso o quitarla.")
    print("   Señales con lift bajo Y Δsep>=0 son las que conviene podar primero.")
    print("=" * 70)

    con.close()


if __name__ == "__main__":
    main()
