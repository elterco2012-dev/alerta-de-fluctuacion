"""
scripts/evaluar_ranking.py
--------------------------
¿El RANKING anticipa bajas mejor que reglas simples? Evaluación point-in-time.

validar_pesos.py compara egresados (en sus 3 meses previos al egreso) contra
activos (en sus 3 meses más recientes) con un umbral de score. Eso no mide lo
que el dashboard pide hacer: "empezá por los de mayor score". Este script mide
justamente eso, como si estuviéramos parados en cada fin de mes del pasado:

  1. Para cada período P de score_historico (corte = último día de P), la
     población es la que el motor puntuó ese mes (activos al corte).
  2. Etiqueta: el vendedor egresó dentro de los H días posteriores al corte
     (H = 30 / 60 / 90). Períodos cuyo horizonte todavía no terminó
     (corte + H > fecha de datos) se excluyen: no se sabe aún quién se va.
  3. Se ordena a la población por cada criterio y se mide, en el top K:
        precisión@K  = % del top K que efectivamente se fue en H días
        recall@K     = % de las bajas de H días que estaban en el top K
        lift@K       = aciertos en el top K / aciertos esperados eligiendo K al
                       azar en cada período (1.0 = igual que elegir al azar)
        AUC          = probabilidad de que un egresado quede por encima de
                       un no egresado (0.5 = azar), promedio por período
     Los empates de score se resuelven por valor esperado (como si se
     desempatara al azar), sin favorecer a ningún criterio.
  4. Criterios comparados (más alto = más riesgo):
        modelo               score actual reconstruido desde las señales
        modelo_grupo_pit     modelo, pero "grupo quemado" calculado SOLO con
                             bajas anteriores al corte y sin contar al propio
                             vendedor (corrige la fuga temporal de riesgo_base)
        modelo_sin_grupo     modelo sin la señal de grupo
        antiguedad_tramos    mes 0-3 > mes 4-6 > resto (sin mirar desempeño)
        antiguedad           más nuevo primero
        plan_bajo            menor % de plan 3m primero
        caida_venta          mayor caída de venta del mes vs. los 2 anteriores
        grupo_pit            riesgo histórico del grupo, sin fuga temporal
        grupo_actual         riesgo_base de hoy (con fuga: solo de referencia)
        tramos+plan          antigüedad_tramos + 1 si plan 3m < 55%
        azar                 todos empatados (= tasa base)

LIMITACIONES (leerlas antes de sacar conclusiones):
  · score_historico se regenera con los datos de HOY (backfill y
    snapshot_mensual recalculan): no es lo que el supervisor vio en su momento.
  · El grupo de cada vendedor es el actual (no hay historial de jerarquía).
  · motivo_egreso no se carga: la etiqueta mezcla renuncias, despidos y
    acuerdos. Un despido por bajo rendimiento "confirma" la señal de plan.
  · La unidad es vendedor-período: un egresado puede contar en varios cortes.
  · Con pocas bajas por período las métricas son ruidosas: mirar n y la
    consistencia entre mitades antes de concluir.
  · El score NO es una probabilidad de renuncia.

Solo LECTURA sobre data/wurth.db (se abre en modo read-only). No usa pandas.
    python scripts\\evaluar_ranking.py
    python scripts\\evaluar_ranking.py --fecha-datos 2026-10-01 --csv metricas.csv
"""

import argparse
import calendar
import csv
import json
import os
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path
from statistics import median

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validar_pesos import PESOS_ACTUAL, RIESGO_REFERENCIA  # noqa: E402

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "wurth.db")

HORIZONTES = (30, 60, 90)
KS_GLOBAL = (5, 10, 20, 30)
KS_ZONA = (1, 2, 3)
K_REFERENCIA = 20            # ≈ FOCO_SEMANA del dashboard
SEÑAL_GRUPO = "Grupo con alta rotación histórica"
UMBRAL_GRUPO = 0.40          # mismo umbral que score_engine
DIAS_BAJA_RAPIDA = 180       # misma definición que riesgo_base (< 6 meses)
UMBRAL_PLAN = 55             # mismo umbral que score_engine


# ── Utilidades ────────────────────────────────────────────────────────────────

def abrir_solo_lectura(path):
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def fin_de_mes(periodo):
    a, m = int(periodo[:4]), int(periodo[5:7])
    return date(a, m, calendar.monthrange(a, m)[1])


def a_fecha(valor):
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def score_desde_riesgo(riesgo, ref=RIESGO_REFERENCIA):
    return round(min(10.0, max(1.0, 1 + min(riesgo / ref, 1.0) * 9)), 1)


def riesgo_de(senales, pesos=PESOS_ACTUAL, excluir=()):
    return sum(pesos.get(s, 0.0) for s in senales if s not in excluir)


# ── Métricas ──────────────────────────────────────────────────────────────────

def tp_esperado_top_k(valores, etiquetas, k):
    """(positivos esperados en el top k, k efectivo). Empates por valor esperado."""
    pares = sorted(zip(valores, etiquetas), key=lambda x: -x[0])
    k = min(k, len(pares))
    tp, usados, i = 0.0, 0, 0
    while usados < k and i < len(pares):
        j = i
        while j < len(pares) and pares[j][0] == pares[i][0]:
            j += 1
        bloque = pares[i:j]
        pos = sum(e for _, e in bloque)
        lugar = k - usados
        if len(bloque) <= lugar:
            tp += pos
            usados += len(bloque)
        else:
            tp += pos * lugar / len(bloque)
            usados = k
        i = j
    return tp, k


def auc(valores, etiquetas):
    """AUC (Mann-Whitney con rangos promedio para empates). None si falta una clase."""
    n_pos = sum(etiquetas)
    n_neg = len(etiquetas) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    orden = sorted(range(len(valores)), key=lambda i: valores[i])
    rangos = [0.0] * len(valores)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and valores[orden[j + 1]] == valores[orden[i]]:
            j += 1
        r = (i + j) / 2 + 1
        for t in range(i, j + 1):
            rangos[orden[t]] = r
        i = j + 1
    suma = sum(r for r, e in zip(rangos, etiquetas) if e)
    return (suma - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def imputar_mediana(valores):
    """None → mediana del período (neutral: ni premia ni castiga el dato faltante)."""
    conocidos = [v for v in valores if v is not None]
    med = median(conocidos) if conocidos else 0.0
    return [med if v is None else v for v in valores]


# ── Riesgo de grupo point-in-time ─────────────────────────────────────────────

def riesgo_base_pit(miembros, corte, excluir_vid=None):
    """Réplica de la fórmula de sincronizar_informix.py (bajas < 6 meses / total
    del grupo) usando SOLO lo que se sabía al corte y sin contar al vendedor
    evaluado. miembros: lista de (vid, fecha_ingreso, fecha_egreso)."""
    total = rapidas = 0
    for vid, ing, egr in miembros:
        if vid == excluir_vid or ing is None or ing > corte:
            continue
        if egr is not None and egr == ing:
            continue
        total += 1
        if egr is not None and egr <= corte and (egr - ing).days < DIAS_BAJA_RAPIDA:
            rapidas += 1
    return rapidas / total if total else None


# ── Carga ─────────────────────────────────────────────────────────────────────

def cargar(con):
    cur = con.cursor()
    cur.execute("""SELECT periodo, id_vendedor, señales, meses_activo, pct_plan_3m, score
                   FROM score_historico""")
    filas = []
    for periodo, vid, sen_json, meses, pct_plan, score in cur.fetchall():
        try:
            senales = json.loads(sen_json) if sen_json else []
        except ValueError:
            senales = []
        filas.append({"periodo": periodo, "id": vid, "senales": senales,
                      "meses": meses, "pct_plan": pct_plan, "score_guardado": score})

    cur.execute("SELECT id_vendedor, id_grupo, fecha_ingreso, fecha_egreso FROM vendedores")
    vendedores = {vid: {"grupo": g, "ingreso": a_fecha(fi), "egreso": a_fecha(fe)}
                  for vid, g, fi, fe in cur.fetchall()}

    cur.execute("SELECT id_grupo, riesgo_base FROM grupos")
    rb_actual = dict(cur.fetchall())

    ventas = {}
    try:
        cur.execute("SELECT id_vendedor, anio, mes, venta_total FROM ventas_mensual")
        for vid, a, m, v in cur.fetchall():
            ventas[(vid, a * 12 + m - 1)] = v or 0.0
    except sqlite3.Error:
        pass
    return filas, vendedores, rb_actual, ventas


# ── Criterios de priorización ─────────────────────────────────────────────────

def caida_venta(ventas, vid, periodo):
    idx = int(periodo[:4]) * 12 + int(periodo[5:7]) - 1
    v0 = ventas.get((vid, idx))
    previos = [ventas.get((vid, idx - 1)), ventas.get((vid, idx - 2))]
    if v0 is None or any(p is None for p in previos):
        return None
    base = sum(previos) / 2
    return (base - v0) / base if base > 0 else None


def tramo_antiguedad(meses):
    if meses is None:
        return None
    return 2 if meses <= 3 else 1 if meses <= 6 else 0


def construir_criterios(fila, ctx):
    """Valores de cada criterio para una fila (más alto = más riesgo; None = sin dato)."""
    sen = fila["senales"]
    peso_g = PESOS_ACTUAL.get(SEÑAL_GRUPO, 0.0)
    rb_pit = ctx["rb_pit"]
    riesgo_sin_g = riesgo_de(sen, excluir=(SEÑAL_GRUPO,))
    plan = fila["pct_plan"] if fila["pct_plan"] else None   # 0 = sin dato de plan
    tramo = tramo_antiguedad(fila["meses"])
    return {
        "modelo": score_desde_riesgo(riesgo_de(sen)),
        "modelo_grupo_pit": score_desde_riesgo(
            riesgo_sin_g + (peso_g if rb_pit is not None and rb_pit > UMBRAL_GRUPO else 0.0)),
        "modelo_sin_grupo": score_desde_riesgo(riesgo_sin_g),
        "antiguedad_tramos": tramo,
        "antiguedad": -fila["meses"] if fila["meses"] is not None else None,
        "plan_bajo": -plan if plan is not None else None,
        "caida_venta": ctx["caida"],
        "grupo_pit": rb_pit,
        "grupo_actual": ctx["rb_actual"],
        "tramos+plan": None if tramo is None else
            tramo + (1 if plan is not None and plan < UMBRAL_PLAN else 0),
        "azar": 0.0,
    }


CRITERIOS = ("modelo", "modelo_grupo_pit", "modelo_sin_grupo", "antiguedad_tramos",
             "antiguedad", "plan_bajo", "caida_venta", "grupo_pit", "grupo_actual",
             "tramos+plan", "azar")


def preparar_periodos(filas, vendedores, rb_actual, ventas):
    """{periodo: [registro]} con criterios y datos de egreso por vendedor."""
    miembros = {}
    for vid, d in vendedores.items():
        miembros.setdefault(d["grupo"], []).append((vid, d["ingreso"], d["egreso"]))

    periodos = {}
    for f in filas:
        v = vendedores.get(f["id"])
        if v is None:
            continue
        corte = fin_de_mes(f["periodo"])
        ctx = {
            "rb_pit": riesgo_base_pit(miembros.get(v["grupo"], []), corte, excluir_vid=f["id"]),
            "rb_actual": rb_actual.get(v["grupo"]),
            "caida": caida_venta(ventas, f["id"], f["periodo"]),
        }
        periodos.setdefault(f["periodo"], []).append({
            "id": f["id"], "grupo": v["grupo"], "egreso": v["egreso"], "corte": corte,
            "criterios": construir_criterios(f, ctx), "senales": f["senales"],
            "score_guardado": f["score_guardado"],
        })
    return periodos


# ── Evaluación ────────────────────────────────────────────────────────────────

def etiqueta(reg, h):
    e = reg["egreso"]
    return int(e is not None and reg["corte"] < e <= reg["corte"] + timedelta(days=h))


def periodos_evaluables(periodos, h, fecha_datos):
    return sorted(p for p in periodos if fin_de_mes(p) + timedelta(days=h) <= fecha_datos)


def evaluar_criterio(periodos, lista, criterio, h, ks=KS_GLOBAL, ks_zona=KS_ZONA):
    """Métricas agregadas de un criterio sobre los períodos de `lista`."""
    tp = {k: 0.0 for k in ks}
    usados = {k: 0 for k in ks}
    azar = {k: 0.0 for k in ks}      # positivos esperados en el top k eligiendo al azar
    tpz = {k: 0.0 for k in ks_zona}
    usadosz = {k: 0 for k in ks_zona}
    n_tot = pos_tot = 0
    aucs = []
    for p in lista:
        regs = periodos[p]
        valores = imputar_mediana([r["criterios"][criterio] for r in regs])
        etiq = [etiqueta(r, h) for r in regs]
        n_tot += len(regs)
        pos_tot += sum(etiq)
        a = auc(valores, etiq)
        if a is not None:
            aucs.append(a)
        for k in ks:
            t, ke = tp_esperado_top_k(valores, etiq, k)
            tp[k] += t
            usados[k] += ke
            azar[k] += ke * sum(etiq) / len(etiq) if etiq else 0.0
        por_zona = {}
        for r, v, e in zip(regs, valores, etiq):
            por_zona.setdefault(r["grupo"], ([], []))
            por_zona[r["grupo"]][0].append(v)
            por_zona[r["grupo"]][1].append(e)
        for vals, ets in por_zona.values():
            for k in ks_zona:
                t, ke = tp_esperado_top_k(vals, ets, k)
                tpz[k] += t
                usadosz[k] += ke
    base = pos_tot / n_tot if n_tot else 0.0
    res = {"criterio": criterio, "h": h, "periodos": len(lista), "n": n_tot,
           "bajas": pos_tot, "tasa_base": base,
           "auc": sum(aucs) / len(aucs) if aucs else None}
    for k in ks:
        prec = tp[k] / usados[k] if usados[k] else 0.0
        res[f"prec@{k}"] = prec
        res[f"recall@{k}"] = tp[k] / pos_tot if pos_tot else 0.0
        # lift contra el azar de CADA período (la tasa base varía mes a mes)
        res[f"lift@{k}"] = tp[k] / azar[k] if azar[k] else None
    for k in ks_zona:
        prec = tpz[k] / usadosz[k] if usadosz[k] else 0.0
        res[f"zona_prec@{k}"] = prec
        res[f"zona_recall@{k}"] = tpz[k] / pos_tot if pos_tot else 0.0
    return res


def top_k_con_empates(regs, criterio, k):
    valores = imputar_mediana([r["criterios"][criterio] for r in regs])
    if not valores:
        return set()
    corte_v = sorted(valores, reverse=True)[min(k, len(valores)) - 1]
    return {r["id"] for r, v in zip(regs, valores) if v >= corte_v}


def estabilidad_top_k(periodos, criterio="modelo", k=K_REFERENCIA):
    """Jaccard promedio del top K (empates incluidos) entre meses consecutivos,
    entre vendedores presentes en ambos meses."""
    ps = sorted(periodos)
    jac = []
    for p1, p2 in zip(ps, ps[1:]):
        comunes = {r["id"] for r in periodos[p1]} & {r["id"] for r in periodos[p2]}
        a = top_k_con_empates([r for r in periodos[p1] if r["id"] in comunes], criterio, k)
        b = top_k_con_empates([r for r in periodos[p2] if r["id"] in comunes], criterio, k)
        if a | b:
            jac.append(len(a & b) / len(a | b))
    return sum(jac) / len(jac) if jac else None


def anticipacion(periodos, vendedores, criterio="modelo", k=K_REFERENCIA, ventana_dias=180):
    """Para egresados cubiertos por score_historico: ¿estuvieron en el top K en
    algún corte de los `ventana_dias` previos al egreso? ¿Con cuánta anticipación?"""
    tops = {p: top_k_con_empates(regs, criterio, k) for p, regs in periodos.items()}
    primer_corte = min((fin_de_mes(p) for p in periodos), default=None)
    ultimo_corte = max((fin_de_mes(p) for p in periodos), default=None)
    detectados, no_detectados, sin_score, dias = 0, 0, 0, []
    for vid, d in vendedores.items():
        e = d["egreso"]
        if e is None or primer_corte is None or not (primer_corte < e <= ultimo_corte + timedelta(days=31)):
            continue
        if d["ingreso"] is not None and e == d["ingreso"]:
            continue
        cortes = [p for p in periodos
                  if fin_de_mes(p) < e <= fin_de_mes(p) + timedelta(days=ventana_dias)
                  and any(r["id"] == vid for r in periodos[p])]
        if not cortes:
            sin_score += 1
            continue
        en_top = sorted(p for p in cortes if vid in tops[p])
        if en_top:
            detectados += 1
            dias.append((e - fin_de_mes(en_top[0])).days)
        else:
            no_detectados += 1
    return {"detectados": detectados, "no_detectados": no_detectados,
            "sin_score": sin_score, "mediana_dias": median(dias) if dias else None}


# ── Salida ────────────────────────────────────────────────────────────────────

def _pct(x):
    return "   —  " if x is None else f"{x * 100:5.1f}%"


def _num(x, fmt="{:5.2f}"):
    return "  —  " if x is None else fmt.format(x)


def imprimir_tabla(resultados, h):
    print(f"\n  Horizonte {h} días — top K global y top k por zona (grupo)")
    filas = [r for r in resultados if r["h"] == h]
    if not filas or not filas[0]["n"]:
        print("    (sin períodos evaluables para este horizonte)")
        return
    r0 = filas[0]
    print(f"    períodos={r0['periodos']}  vendedor-períodos={r0['n']}  "
          f"bajas={r0['bajas']}  tasa base={_pct(r0['tasa_base'])}")
    cab = (f"    {'criterio':18} {'AUC':>5}" + "".join(f" {'P@'+str(k):>6}" for k in KS_GLOBAL)
           + f" {'R@'+str(K_REFERENCIA):>6} {'lift@'+str(K_REFERENCIA):>8}"
           + "".join(f" {'zP@'+str(k):>6}" for k in KS_ZONA))
    print(cab)
    print("    " + "-" * (len(cab) - 4))
    for r in filas:
        print(f"    {r['criterio']:18} {_num(r['auc'])}"
              + "".join(f" {_pct(r[f'prec@{k}'])}" for k in KS_GLOBAL)
              + f" {_pct(r[f'recall@{K_REFERENCIA}'])} {_num(r[f'lift@{K_REFERENCIA}'], '{:7.2f}x')}"
              + "".join(f" {_pct(r[f'zona_prec@{k}'])}" for k in KS_ZONA))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--fecha-datos", default=None,
                    help="fecha hasta la que los egresos están sincronizados (AAAA-MM-DD). "
                         "Default: hoy. Si la base no se sincroniza hace días, pasá la fecha real.")
    ap.add_argument("--csv", default=None, help="guardar todas las métricas en un CSV")
    args = ap.parse_args(argv)

    fecha_datos = date.fromisoformat(args.fecha_datos) if args.fecha_datos else date.today()
    con = abrir_solo_lectura(args.db)
    try:
        filas, vendedores, rb_actual, ventas = cargar(con)
    finally:
        con.close()
    if not filas:
        print("score_historico está vacío: correr scripts/backfill_scores.py primero.")
        return 1

    periodos = preparar_periodos(filas, vendedores, rb_actual, ventas)

    print("=" * 78)
    print("EVALUACIÓN POINT-IN-TIME DEL RANKING — ¿el orden anticipa bajas?")
    print("=" * 78)
    print(f"  Períodos en score_historico: {len(periodos)} "
          f"({min(periodos)} a {max(periodos)})   fecha de datos: {fecha_datos}")
    difs = [abs(r["criterios"]["modelo"] - (r["score_guardado"] or 0))
            for regs in periodos.values() for r in regs]
    print(f"  [chequeo] máx. diferencia score reconstruido vs guardado: {max(difs):.2f}"
          + ("" if max(difs) < 0.15 else "  <-- OJO: score_historico desincronizado con los pesos"))
    print("  AVISO: motivo_egreso vacío → la etiqueta mezcla renuncias, despidos y acuerdos.")
    print("  AVISO: el score no es una probabilidad; leer lift y AUC, no el valor absoluto.")

    resultados = []
    for h in HORIZONTES:
        lista = periodos_evaluables(periodos, h, fecha_datos)
        for c in CRITERIOS:
            resultados.append(evaluar_criterio(periodos, lista, c, h))
        imprimir_tabla(resultados, h)

    # Consistencia temporal: mitad vieja vs. mitad reciente (horizonte 90 días)
    lista90 = periodos_evaluables(periodos, 90, fecha_datos)
    if len(lista90) >= 4:
        mitad = len(lista90) // 2
        print(f"\n  Consistencia temporal (90 días): {lista90[0]}..{lista90[mitad-1]} vs "
              f"{lista90[mitad]}..{lista90[-1]}")
        print(f"    {'criterio':18} {'AUC vieja':>10} {'AUC reciente':>13} "
              f"{'P@'+str(K_REFERENCIA)+' vieja':>12} {'P@'+str(K_REFERENCIA)+' rec.':>11}")
        for c in CRITERIOS:
            a = evaluar_criterio(periodos, lista90[:mitad], c, 90)
            b = evaluar_criterio(periodos, lista90[mitad:], c, 90)
            print(f"    {c:18} {_num(a['auc']):>10} {_num(b['auc']):>13} "
                  f"{_pct(a[f'prec@{K_REFERENCIA}']):>12} {_pct(b[f'prec@{K_REFERENCIA}']):>11}")

    est = estabilidad_top_k(periodos)
    print(f"\n  Estabilidad del top {K_REFERENCIA} del modelo entre meses consecutivos "
          f"(Jaccard, empates incluidos): {_pct(est)}")
    ant = anticipacion(periodos, vendedores)
    print(f"  Anticipación (top {K_REFERENCIA} con empates, que puede superar K; ventana 180 días): "
          f"{ant['detectados']} egresados estuvieron en el top antes de irse, "
          f"{ant['no_detectados']} no; {ant['sin_score']} sin score previo (no evaluables). "
          f"Mediana de anticipación: "
          f"{ant['mediana_dias'] if ant['mediana_dias'] is not None else '—'} días.")

    print("\n  CÓMO LEERLO:")
    print("   · lift@K ~1 = el criterio no es mejor que elegir al azar.")
    print("   · Si 'antiguedad_tramos' o 'tramos+plan' rinden igual que 'modelo', el resto")
    print("     de las señales no está agregando información sobre el orden.")
    print("   · La diferencia 'modelo' vs 'modelo_grupo_pit' es cuánto de la performance")
    print("     histórica venía de la fuga temporal de riesgo_base.")
    print("   · Si las mitades vieja y reciente difieren mucho, no hay evidencia estable.")
    print("=" * 78)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(resultados[0].keys()))
            w.writeheader()
            w.writerows(resultados)
        print(f"Métricas guardadas en {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
