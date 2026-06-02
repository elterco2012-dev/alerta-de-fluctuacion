"""
snippets_v3.py  —  Würth Rotación, componentes de la propuesta v2/v3 para Streamlit.
Helpers que devuelven strings HTML con clases wz-* (ver assets/dashboard-v3.css).
"""

# ─────────────────────────────────────────────────────────────────────────────
# FORMATO  (es-AR: punto miles, coma decimal)
# ─────────────────────────────────────────────────────────────────────────────
def fmt_num(n, dec=0):
    """1234.5 -> '1.234,5'"""
    s = f"{n:,.{dec}f}"
    return s.replace(",", "·").replace(".", ",").replace("·", ".")

def fmt_pct(n, dec=0):
    return f"{fmt_num(n, dec)}%"

def fmt_pesos(n):
    return "$" + fmt_num(round(n), 0)

def fmt_pesos_corto(n):
    """$1,4 M / $980 mil"""
    if n >= 1_000_000:
        return "$" + fmt_num(n / 1_000_000, 1) + " M"
    if n >= 1_000:
        return "$" + fmt_num(round(n / 1_000), 0) + " mil"
    return fmt_pesos(n)

def fmt_meses(n):
    return fmt_num(n, 1) + " m"

def fmt_delta(n, dec=1):
    """▲ sube (peor para score), ▼ baja (mejor)."""
    if not n:
        return "="
    return ("▲ " if n > 0 else "▼ ") + fmt_num(abs(n), dec)

def fmt_antiguedad(meses):
    if meses < 12:
        return f"{meses} mes" + ("es" if meses != 1 else "")
    a, r = divmod(meses, 12)
    s = f"{a} año" + ("s" if a != 1 else "")
    if r:
        s += f" y {r} mes" + ("es" if r != 1 else "")
    return s

# ─────────────────────────────────────────────────────────────────────────────
# NIVEL DE RIESGO
# ─────────────────────────────────────────────────────────────────────────────
NIVEL_LABEL = {"critico": "Crítico", "alto": "Alto", "medio": "Medio", "bajo": "Bajo"}
NIVEL_SHAPE = {"critico": "▲", "alto": "◆", "medio": "■", "bajo": "●"}
ACCION_TXT  = {
    "critico": "Reunión esta semana",
    "alto":    "Seguimiento activo",
    "medio":   "Monitoreo mensual",
    "bajo":    "Seguimiento normal",
}

def nivel_de(score):
    if score >= 8: return "critico"
    if score >= 6: return "alto"
    if score >= 4: return "medio"
    return "bajo"

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENTES (devuelven HTML)
# ─────────────────────────────────────────────────────────────────────────────
def banner(emoji, titulo, sub="", tono="red"):
    """Banner de acción del día arriba de cada pantalla."""
    return (f'<div class="wz-banner {tono}"><span class="em">{emoji}</span>'
            f'<div><div class="ttl">{titulo}</div>'
            f'<div class="sub">{sub}</div></div></div>')

def hero_kpi(label, valor, sub="", red=False):
    """Un KPI dominante, no cinco iguales."""
    cls = "val red" if red else "val"
    return (f'<div class="wz-hero"><div class="lbl">{label}</div>'
            f'<div class="{cls}">{valor}</div><div class="sub">{sub}</div></div>')

def stat_kpi(label, valor):
    """KPI secundario (tira debajo del hero)."""
    return (f'<div class="wz-stat"><div class="val">{valor}</div>'
            f'<div class="lbl">{label}</div></div>')

def score_circle(score, nivel=None):
    nivel = nivel or nivel_de(score)
    return f'<span class="wz-score {nivel}">{score}</span>'

def badge(nivel, label=None, shape=True):
    """Badge con forma para accesibilidad (▲◆■●)."""
    shp = f'<span class="shp">{NIVEL_SHAPE.get(nivel,"")}</span>' if shape and nivel in NIVEL_SHAPE else ""
    return f'<span class="wz-badge {nivel}">{shp}{label or NIVEL_LABEL.get(nivel, nivel)}</span>'

def pill(label, color="orange"):
    return f'<span class="wz-pill {color}">{label}</span>'

def accion_tag(nivel):
    return f'<span class="wz-accion {nivel}">{ACCION_TXT[nivel]}</span>'

def score_delta(delta):
    """Δ vs mes anterior. Subir score = empeorar = rojo."""
    if not delta:
        return '<span class="wz-delta flat">=</span>'
    cls = "worse" if delta > 0 else "better"
    glyph = "▲" if delta > 0 else "▼"
    return f'<span class="wz-delta {cls}">{glyph} {abs(delta)}</span>'

def fresh(ts_str):
    """Timestamp de frescura del dato en el header."""
    return f'<span class="wz-fresh"><span class="dot"></span>Actualizado: {ts_str}</span>'

# ─────────────────────────────────────────────────────────────────────────────
# EXPLICABILIDAD DEL SCORE
# ─────────────────────────────────────────────────────────────────────────────
SIGNAL_PESO = {
    "onboarding": 2.0, "días cero↑": 2.0, "caída 3m": 2.0,
    "plan<80%": 1.5, "zona quemada": 1.5,
    "mes 4-6": 1.0, "inactivos↑": 1.0, "cobranza baja": 1.0,
    "clientes L:0": 0.5, "ticket↓": 0.5,
}

def score_breakdown_rows(senales):
    """Devuelve [(label, peso)] ordenado desc."""
    out = [("Base (todos arrancan en 1)", 1.0)]
    out += sorted([(s, SIGNAL_PESO.get(s, 0.5)) for s in senales],
                  key=lambda x: -x[1])
    return out

# ─────────────────────────────────────────────────────────────────────────────
# RECOMENDACIÓN DE ACCIÓN
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

def perfil_de(meses, riesgo_base, senales):
    if meses <= 6:
        return "onboarding_quemada" if riesgo_base > 0.45 else "onboarding_normal"
    if meses > 12 and any(s in ("caída 3m", "plan<80%") for s in senales):
        return "senior_caida"
    return "default"

def recomendar_accion(meses, riesgo_base, senales):
    p = perfil_de(meses, riesgo_base, senales)
    ranking = EFECTIVIDAD.get(p, EFECTIVIDAD["default"])
    return p, PERFIL_LABEL[p], ranking[0], ranking

# ─────────────────────────────────────────────────────────────────────────────
# MATRIZ DE CONFUSIÓN
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
    recall    = round(vp / (vp + fn) * 100) if (vp + fn) else 0
    precision = round(vp / (vp + fp) * 100) if (vp + fp) else 0
    return grid, recall, precision
