"""
snippets-v3.py  —  Würth Rotación, componentes de la propuesta v2/v3 para Streamlit.
Versión 2 (incluye las correcciones del análisis: formato es-AR aplicado, badges con
forma para accesibilidad, stat_kpi, recomendación de acción y desglose de score).

Uso
---
1) Inyectá el CSS una vez al inicio de dashboard.py:
       st.markdown(f"<style>{open('assets/dashboard-v3.css').read()}</style>",
                   unsafe_allow_html=True)
2) from snippets_v3 import *   (o importá lo que uses)
3) Renderizá con st.markdown(<helper>(...), unsafe_allow_html=True).

Nada inventa datos: las funciones reciben tus valores reales.
"""

# ─────────────────────────────────────────────────────────────────────────────
# #3  FORMATO  — una sola fuente de verdad (es-AR / Rioplatense)
# ─────────────────────────────────────────────────────────────────────────────
def fmt_num(n, dec=0):
    """1234.5 -> '1.234,5'  (punto miles, coma decimal)."""
    s = f"{n:,.{dec}f}"                       # '1,234.5' (en-US)
    return s.replace(",", "·").replace(".", ",").replace("·", ".")

def fmt_pct(n, dec=0):
    return f"{fmt_num(n, dec)}%"

def fmt_pesos(n):
    return "$" + fmt_num(round(n), 0)

def fmt_pesos_corto(n):
    if n >= 1_000_000:
        return "$" + fmt_num(n / 1_000_000, 1) + " M"
    if n >= 1_000:
        return "$" + fmt_num(round(n / 1_000), 0) + " mil"
    return fmt_pesos(n)

def fmt_meses(n):
    return fmt_num(n, 1) + " m"

def fmt_delta(n, dec=1):
    """Glifo del producto: ▲ sube (peor en score) · ▼ baja (mejor)."""
    if not n:
        return "="
    return ("▲ " if n > 0 else "▼ ") + fmt_num(abs(n), dec)

def fmt_antiguedad(meses):
    if meses < 12:
        return f"{meses} mes" + ("es" if meses != 1 else "")
    a, r = divmod(int(meses), 12)
    s = f"{a} año" + ("s" if a != 1 else "")
    if r:
        s += f" y {r} mes" + ("es" if r != 1 else "")
    return s

# ─────────────────────────────────────────────────────────────────────────────
# NIVEL DE RIESGO  (umbral score 1–10 → nivel)
# ─────────────────────────────────────────────────────────────────────────────
NIVEL_LABEL = {"critico": "Crítico", "alto": "Alto", "medio": "Medio", "bajo": "Bajo"}
NIVEL_SHAPE = {"critico": "▲", "alto": "◆", "medio": "■", "bajo": "●"}   # #4 accesibilidad
ACCION_TXT  = {"critico": "Reunión esta semana", "alto": "Seguimiento activo",
               "medio": "Monitoreo mensual", "bajo": "Seguimiento normal"}

def nivel_de(score):
    if score >= 8: return "critico"
    if score >= 6: return "alto"
    if score >= 4: return "medio"
    return "bajo"

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENTES (devuelven HTML)
# ─────────────────────────────────────────────────────────────────────────────
def banner(emoji, titulo, sub="", tono="red"):
    """#4 acción — banner de 'qué hago hoy' arriba de cada pantalla."""
    return (f'<div class="wz-banner {tono}"><span class="em">{emoji}</span>'
            f'<div><div class="ttl">{titulo}</div>'
            f'<div class="sub">{sub}</div></div></div>')

def hero_kpi(label, valor, sub="", red=False):
    """#1 jerarquía — UN KPI dominante, no cinco iguales."""
    cls = "val red" if red else "val"
    return (f'<div class="wz-hero"><div class="lbl">{label}</div>'
            f'<div class="{cls}">{valor}</div><div class="sub">{sub}</div></div>')

def stat_kpi(label, valor):
    """KPI secundario, de-enfatizado — va en una tira al lado del hero."""
    return (f'<div class="wz-statcard"><div class="val">{valor}</div>'
            f'<div class="lbl">{label}</div></div>')

def score_circle(score, nivel=None, title=""):
    nivel = nivel or nivel_de(score)
    t = f' title="{title}"' if title else ""
    return f'<span class="wz-score {nivel}"{t}>{int(score)}</span>'

def badge(nivel, label=None, shape=True, title="", kind=None):
    """#4 accesibilidad — la forma (▲◆■●) hace que el nivel no dependa solo del color.
       `title` preserva tu tooltip; `kind='tipo'` para badges categóricos (morado)."""
    key = kind or nivel
    shp = (f'<span class="shp">{NIVEL_SHAPE.get(key,"")}</span>'
           if shape and key in NIVEL_SHAPE else "")
    t = f' title="{title}"' if title else ""
    return f'<span class="wz-badge {key}"{t}>{shp}{label or NIVEL_LABEL.get(nivel, nivel)}</span>'

def pill(label, color="orange", title=""):
    t = f' title="{title}"' if title else ""
    return f'<span class="wz-pill {color}"{t}>{label}</span>'

def accion_tag(nivel):
    """#4 acción — pop para crítico/alto; recede para medio/bajo (menos ruido)."""
    if nivel == "bajo":
        return '<span class="wz-accion bajo">—</span>'
    return f'<span class="wz-accion {nivel}">{ACCION_TXT[nivel]}</span>'

def score_delta(delta):
    """#2 trayectoria — Δ vs mes anterior. Subir score = empeorar = rojo.
       Requiere score_snapshot (ver queries-v3.sql). Si no hay dato previo, pasá None."""
    if delta is None:
        return '<span class="wz-delta flat" title="Sin histórico todavía">·</span>'
    if not delta:
        return '<span class="wz-delta flat">=</span>'
    cls, g = ("worse", "▲") if delta > 0 else ("better", "▼")
    return f'<span class="wz-delta {cls}">{g} {abs(delta)}</span>'

def fresh(ts_str):
    """#5 frescura del dato — arriba a la derecha del header."""
    return (f'<span class="wz-fresh"><span class="dot"></span>'
            f'Actualizado: {ts_str}</span>')

# ─────────────────────────────────────────────────────────────────────────────
# #1 EXPLICABILIDAD DEL SCORE — desglose ponderado "por qué este score"
#    Ajustá SIGNAL_PESO a los pesos reales de src/score_engine.py.
# ─────────────────────────────────────────────────────────────────────────────
SIGNAL_PESO = {
    "inducción": 2.0, "días cero↑": 2.0, "caída 3m": 2.0, "ausencias↑": 2.0,
    "plan<80%": 1.5, "zona quemada": 1.5, "cobranza baja": 1.0,
    "mes 4-6": 1.0, "inactivos↑": 1.0, "balanza neg.": 1.0, "sin acomp.": 1.0,
    "< 70% llamadas": 1.0, "< 70% visitas": 1.0,
    "clientes L:0": 0.5, "ticket↓": 0.5,
}

def score_breakdown_html(senales_labels):
    """senales_labels = lista de etiquetas cortas ya mapeadas (caída 3m, etc.)."""
    filas = [("Base (todos arrancan en 1)", 1.0)]
    filas += sorted(((s, SIGNAL_PESO.get(s, 0.5)) for s in senales_labels),
                    key=lambda x: -x[1])
    maxp = 2.0
    out = '<div class="wz-breakdown">'
    for label, peso in filas:
        color = ("var(--red-accent)" if peso >= 2 else
                 "var(--orange-accent)" if peso >= 1.5 else
                 "var(--ink-200)" if peso <= 1.0 and label.startswith("Base") else
                 "#F57F17")
        w = int(peso / maxp * 100)
        out += (f'<div class="row"><span class="lbl">{label}</span>'
                f'<span class="bar"><span style="width:{w}%;background:{color}"></span></span>'
                f'<span class="num">+{fmt_num(peso,1)}</span></div>')
    out += '</div>'
    return out

# ─────────────────────────────────────────────────────────────────────────────
# #2 RECOMENDACIÓN DE ACCIÓN — qué intervención funcionó para perfiles similares
#    Reemplazá EFECTIVIDAD con el resultado real de queries-v3.sql (bloque #3).
#    Tipos = los REALES de src/intervenciones.py.
# ─────────────────────────────────────────────────────────────────────────────
EFECTIVIDAD = {
    "onboarding_quemada": [("Reunión 1:1", 1.8, 7), ("Acompañamiento en campo", 1.3, 5),
                           ("Cambio de zona", 1.1, 3), ("Capacitación técnica", 0.4, 4)],
    "onboarding_normal":  [("Acompañamiento en campo", 1.6, 6), ("Reunión 1:1", 1.2, 8),
                           ("Capacitación técnica", 0.9, 5)],
    "senior_caida":       [("Revisión de cartera", 1.5, 4), ("Reunión 1:1", 1.1, 9),
                           ("Ajuste de objetivos", 0.7, 6)],
    "default":            [("Reunión 1:1", 1.3, 12), ("Acompañamiento en campo", 1.0, 8),
                           ("Conversación motivacional", 0.6, 7)],
}
PERFIL_LABEL = {
    "onboarding_quemada": "nuevos en zona de alta rotación",
    "onboarding_normal": "nuevos en zona normal",
    "senior_caida": "veteranos con caída de plan",
    "default": "vendedores en riesgo",
}

def perfil_de(meses, riesgo_base, senales_labels):
    if meses <= 6:
        return "onboarding_quemada" if riesgo_base > 0.45 else "onboarding_normal"
    if meses > 12 and any(s in ("caída 3m", "plan<80%") for s in senales_labels):
        return "senior_caida"
    return "default"

def recomendar_accion(meses, riesgo_base, senales_labels):
    p = perfil_de(meses, riesgo_base, senales_labels)
    ranking = EFECTIVIDAD.get(p, EFECTIVIDAD["default"])
    return p, PERFIL_LABEL[p], ranking[0], ranking

def recomendacion_html(meses, riesgo_base, senales_labels, nivel):
    """Bloque para el detalle del vendedor (#2). Solo tiene sentido en crítico/alto."""
    p, plabel, mejor, ranking = recomendar_accion(meses, riesgo_base, senales_labels)
    tono = "red" if nivel == "critico" else "orange"
    chips = "".join(
        f'<span class="alt">{t} · ↓{fmt_num(a,1)}</span>' for t, a, _ in ranking[1:]
    )
    return (
        f'<div class="wz-recom {tono}">'
        f'<div class="cap">Acción recomendada</div>'
        f'<div class="main"><b>{mejor[0]}</b> '
        f'<span class="imp">↓ {fmt_num(mejor[1],1)} de score en promedio</span></div>'
        f'<div class="sub">Es lo que mejor funcionó para <b>{plabel}</b> '
        f'({mejor[2]} casos).</div>'
        f'<div class="alts">{chips}</div>'
        f'</div>'
    )

# ─────────────────────────────────────────────────────────────────────────────
# #1 MATRIZ DE CONFUSIÓN — ¿el score predijo las fugas?  (ver queries-v3.sql)
# ─────────────────────────────────────────────────────────────────────────────
def matriz_confusion_html(vp, fn, fp, vn, fp_intervenidos=0):
    def cell(n, tono, txt):
        return f'<div class="wz-cm {tono}"><div class="n">{n}</div><div class="d">{txt}</div></div>'
    grid = (
        '<div style="display:grid;grid-template-columns:120px 1fr 1fr;gap:12px;align-items:stretch">'
        '<div></div>'
        '<div style="text-align:center;font-size:12px;font-weight:700;color:var(--ink-500)">Se fue ✓</div>'
        '<div style="text-align:center;font-size:12px;font-weight:700;color:var(--ink-500)">Se quedó</div>'
        '<div style="display:flex;align-items:center;justify-content:flex-end;font-size:12px;font-weight:700;color:var(--ink-500)">Marcado en riesgo ▲</div>'
        + cell(vp, "good", "Acertado — lo vimos venir y pudimos actuar")
        + cell(fp, "warn", f"Marcado pero retenido — {fp_intervenidos} salvados por intervención")
        + '<div style="display:flex;align-items:center;justify-content:flex-end;font-size:12px;font-weight:700;color:var(--ink-500)">No marcado</div>'
        + cell(fn, "bad", "Fuga sorpresa — el modelo NO la anticipó")
        + cell(vn, "neutral", "Correcto — sin alerta y se quedó")
        + '</div>'
    )
    recall = round(vp / (vp + fn) * 100) if (vp + fn) else 0
    precision = round(vp / (vp + fp) * 100) if (vp + fp) else 0
    return grid, recall, precision
