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
# NAVEGACIÓN — única fuente de verdad para los links del header.
# Todas las páginas usan page_header()/nav_links() para que el menú sea
# idéntico en todas y no se omita ninguna sección.
# ─────────────────────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("/",               "🏠 Inicio"),
    ("/Supervisor",     "👤 Por supervisor"),
    ("/Intervenciones", "📝 Intervenciones"),
    ("/Historial",      "📈 Historial"),
    ("/Costo_Rotacion", "💰 Costo de rotación"),
    ("/Actividad",      "📞 Actividad"),
    ("/Precision",      "🎯 Precisión"),
    ("/Aprendizaje",    "🧠 Aprendizaje"),
]

def nav_links(current=""):
    """Devuelve el bloque HTML de navegación filtrado por rol del usuario activo.
    - Gerencia/RRHH: ve todo.
    - Director: no ve Precisión, Aprendizaje, Costo de rotación.
    - Supervisor: igual que Director + no ve Inicio ni Historial (ambos lo
      redirigen a /Supervisor, mostrarlo es confuso).
    - Sin usuario aún: muestra todo (flash breve antes del selector).
    Propaga ?usuario= en todos los links para no romper la sesión al navegar."""
    import streamlit as _st
    from acceso import resolver as _resolver

    _u = _st.query_params.get("usuario", "")
    _uq = f"?usuario={_u}" if _u else ""

    _rol = (_resolver(_u) or {}).get("rol")
    if _rol in ("gerencia", "rrhh"):
        _ocultas: set = set()
    elif _rol == "director":
        _ocultas = {"/Precision", "/Aprendizaje", "/Costo_Rotacion"}
    elif _rol == "supervisor":
        _ocultas = {"/Precision", "/Aprendizaje", "/Costo_Rotacion", "/", "/Historial"}
    else:
        _ocultas = set()  # usuario desconocido → no ocultar nada

    out = []
    for href, label in NAV_ITEMS:
        if href in _ocultas:
            continue
        if href == current:
            out.append(f'<span style="color:#1a1a2e;font-weight:700;white-space:nowrap;">{label}</span>')
        else:
            out.append(f'<a href="{href}{_uq}" target="_self" '
                        f'style="color:#4A90D9;text-decoration:none;white-space:nowrap;">{label}</a>')
    return ('<div style="font-size:13px; display:flex; gap:16px; flex-wrap:wrap; '
            'justify-content:flex-end;">' + "".join(out) + '</div>')

def page_header(titulo, current="", sub=""):
    """Encabezado estándar: título a la izquierda, navegación completa a la
    derecha. sub = HTML opcional bajo el título (ej. fresh(...))."""
    sub_html = f'<div style="margin-top:4px;">{sub}</div>' if sub else ""
    return (f'<div style="display:flex; justify-content:space-between; align-items:center; '
            f'margin-bottom:20px; padding-bottom:14px; border-bottom:1px solid #eee; gap:20px; '
            f'flex-wrap:wrap;"><div><div style="font-size:20px; font-weight:800; color:#1a1a2e;">'
            f'{titulo}</div>{sub_html}</div>{nav_links(current)}</div>')

# CSS que oculta el sidebar nativo de Streamlit y la barra superior.
# Todas las páginas deben inyectarlo para que no aparezca el menú lateral
# automático con la lista de páginas.
HIDE_CHROME_CSS = (
    '<style>'
    '[data-testid="stSidebar"]   { display: none; }'
    '[data-testid="stHeader"]    { display: none; }'
    '[data-testid="stToolbar"]   { display: none; }'
    '.stDeployButton             { display: none; }'
    'header                      { display: none; }'
    '</style>'
)

# ─────────────────────────────────────────────────────────────────────────────
# EXPLICABILIDAD DEL SCORE
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# EXPLICABILIDAD DEL SCORE
# SIGNAL_PESO mapea etiqueta_corta (de SEÑAL_TAGS) → peso del motor.
# Mantener sincronizado con los peso= de las Señal() en score_engine.calcular_scores.
# El motor ya excluye señales deshabilitadas (peso=0) de señales_activas, así que
# el fallback nunca se usa para ellas — se declaran a 0 por claridad.
# ─────────────────────────────────────────────────────────────────────────────
SIGNAL_PESO = {
    # — 9 señales activas (peso > 0 en score_engine) ——————————————————————————
    "plan<80%":     2.0,   # plan_bajo_80       → Señal peso=2.0
    "ausencias↑":   2.0,   # ausencias_tempranas → Señal peso=2.0
    "onboarding":   1.5,   # ventana_critica_13  → Señal peso=1.5  (era 2.0 ← bug)
    "zona quemada": 1.5,   # grupo_quemado       → Señal peso=1.5
    "balanza↓":     1.5,   # balanza_negativa    → Señal peso=1.5  (faltaba ← bug)
    "mes 4-6":      1.0,   # ventana_critica_46  → Señal peso=1.0
    "ticket↓":      1.0,   # ticket_cayendo      → Señal peso=1.0  (era 0.5 ← bug)
    "acomp. bajo":  1.0,   # acomp_bajo          → Señal peso=1.0  (faltaba ← bug)
    "clientes L:0": 0.5,   # clientes_nuevos_cero → Señal peso=0.5
    # — 6 señales deshabilitadas (peso=0, nunca aparecen en señales_activas) ——
    "caída 3m":     0.0,   # caída_plan_3m        → Señal peso=0.0
    "días cero↑":   0.0,   # dias_cero_alto       → Señal peso=0.0
    "inactivos↑":   0.0,   # clientes_activos_baja → Señal peso=0.0
    "cobranza baja":0.0,   # cobranza_baja        → Señal peso=0.0
    "llamadas↓":    0.0,   # llamadas_bajas       → Señal peso=0.0
    "visitas↓":     0.0,   # visitas_bajas        → Señal peso=0.0
}

def score_breakdown_rows(senales):
    """
    [(label, peso)] con Base primero, luego señales ordenadas por peso desc.
    El fallback es 0.0 (no 0.5): una señal sin peso conocido no inventa
    contribución — indica que hay que actualizar SIGNAL_PESO.
    """
    out = [("Base (todos arrancan en 1)", 1.0)]
    out += sorted(
        [(s, SIGNAL_PESO.get(s, 0.0)) for s in senales],
        key=lambda x: -x[1],
    )
    return out

# ─────────────────────────────────────────────────────────────────────────────
# MAPEO DE SEÑALES — descripción larga (clave del motor) → etiqueta corta.
# Fuente ÚNICA: la usan Vendedor.py (pills + desglose) e intervenciones.py
# (para clasificar el perfil de cada vendedor intervenido). Las claves DEBEN
# coincidir exactas con los descripcion= de score_engine.py.
# ─────────────────────────────────────────────────────────────────────────────
SEÑAL_TAGS = {
    "% Plan cayendo 3 meses seguidos":                ("caída 3m",   "red"),
    "% Plan < 80% promedio últimos meses":             ("plan<80%",   "orange"),
    "Días sin venta > 3 en promedio":                  ("días cero↑", "red"),
    "< 60% de cartera activa":                         ("inactivos↑", "orange"),
    "Cobranza real < 90% de teórica":                  ("cobranza baja", "orange"),
    "En ventana crítica mes 1-3":                      ("onboarding", "red"),
    "En ventana crítica mes 4-6":                      ("mes 4-6",    "orange"),
    "Grupo con alta rotación histórica":               ("zona quemada", "orange"),
    "Sin clientes nuevos últimos 2 meses":             ("clientes L:0", "yellow"),
    "< 70% de llamadas planificadas gestionadas (Televentas)": ("llamadas↓", "red"),
    "< 70% de visitas planificadas realizadas (Viajante)":     ("visitas↓",  "red"),
    "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3": ("ausencias↑", "red"),
    "Balanza clientes negativa 2+ meses consecutivos": ("balanza↓",   "orange"),
    "Ticket promedio cae > 5% por mes":                ("ticket↓",    "orange"),
    "Supervisor no acompañó en ventana crítica 1-6":   ("acomp. bajo","yellow"),
}

def senal_corta(desc):
    """(etiqueta_corta, color) para una descripción de señal. Fallback seguro."""
    return SEÑAL_TAGS.get(desc, (desc[:20], "yellow"))

# ─────────────────────────────────────────────────────────────────────────────
# RECOMENDACIÓN DE ACCIÓN
# El ranking de efectividad sale de DATOS REALES (intervenciones.efectividad_por_perfil),
# NO de números inventados. Si un perfil no tiene suficientes intervenciones medidas,
# `recomendar_accion` devuelve ranking vacío y la UI muestra un estado "sin datos"
# en vez de fabricar una recomendación.
# ─────────────────────────────────────────────────────────────────────────────
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

def recomendar_accion(meses, riesgo_base, senales, efectividad=None):
    """
    (perfil_key, perfil_label, top_accion|None, ranking).
    `efectividad` = dict real {perfil: [(tipo, impacto_prom, n_casos), ...]}
    calculado por intervenciones.efectividad_por_perfil(). Si no se pasa, o el
    perfil no tiene datos, top_accion = None y ranking = [] → la UI NO debe
    inventar una recomendación: muestra "sin datos suficientes".
    """
    p = perfil_de(meses, riesgo_base, senales)
    ranking = (efectividad or {}).get(p, [])
    top = ranking[0] if ranking else None
    return p, PERFIL_LABEL[p], top, ranking

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
