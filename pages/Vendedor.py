"""
pages/Vendedor.py
-----------------
Detalle individual de un vendedor.
Acceso: /Vendedor?id=1234  (desde el dashboard o tabla de supervisor)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from score_engine import calcular_scores, get_connection
from snippets_v3 import (
    banner, hero_kpi, stat_kpi, accion_tag,
    badge, pill, fmt_num, fmt_pct, fmt_meses, fmt_antiguedad,
    score_breakdown_rows, recomendar_accion,
    NIVEL_LABEL,
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _zona_nivel(rb):
    if rb > 0.60: return "critico"
    if rb > 0.45: return "alto"
    if rb > 0.30: return "medio"
    return "bajo"

def _zona_label(rb):
    n = _zona_nivel(rb)
    return {"critico": "rot. alta", "alto": "rot. alta",
            "medio": "rot. media", "bajo": "rot. baja"}[n]

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

def _señal_short(desc):
    """Devuelve (etiqueta_corta, color) para una descripción de señal."""
    return SEÑAL_TAGS.get(desc, (desc[:20], "yellow"))

def _pct_plan_color(v):
    if v >= 90:
        return "#2E7D32"
    if v >= 70:
        return "#E65100"
    return "#B71C1C"

def _fmt_periodo(anio, mes):
    return f"{anio}-{int(mes):02d}"

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wurth | Detalle vendedor",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_v3_css = os.path.join(os.path.dirname(__file__), '..', 'assets', 'dashboard-v3.css')
st.markdown(f"<style>{open(_v3_css).read()}</style>", unsafe_allow_html=True)

st.markdown("""<style>
[data-testid="stSidebar"]   { display: none; }
[data-testid="stHeader"]    { display: none; }
[data-testid="stToolbar"]   { display: none; }
.stDeployButton             { display: none; }
header                      { display: none; }
.block-container { padding: 2.5rem 2.5rem 4rem !important; max-width: 100% !important; }

.vd-card {
    background: white; border-radius: 14px; padding: 24px 28px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.09); margin-bottom: 18px;
}
.vd-name  { font-size: 24px; font-weight: 800; color: #1a1a2e; display: inline; }
.vd-id    { font-size: 13px; color: #aaa; margin-left: 10px; }
.vd-meta  { font-size: 13px; color: #666; margin-top: 8px; display: flex; gap: 18px; flex-wrap: wrap; }
.vd-meta b { color: #1a1a2e; }

.wz-table { width: 100%; border-collapse: collapse; }
.wz-table th {
    background: #f8f9fa; padding: 10px 12px; text-align: left;
    font-size: 12px; font-weight: 600; color: #666; border-bottom: 2px solid #e9ecef;
}
.wz-table td {
    padding: 11px 12px; border-bottom: 1px solid #f2f2f2;
    font-size: 13px; vertical-align: middle;
}
.wz-table tr:hover td { background: #fafafa; }

.sec-header {
    font-size: 15px; font-weight: 700; color: #1a1a2e;
    margin: 20px 0 12px; display: flex; align-items: center; gap: 6px;
}

.bd-row   { display: flex; justify-content: space-between; padding: 5px 0;
            border-bottom: 1px solid #f5f5f5; font-size: 13px; }
.bd-label { color: #444; }
.bd-peso  { font-weight: 700; color: #1a1a2e; }

.rec-card {
    background: #f8f9fa; border-radius: 10px; padding: 16px 20px;
    font-size: 13px; color: #333;
}
.rec-title  { font-size: 14px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }
.rec-action { font-weight: 700; color: #E24B4A; font-size: 15px; margin-bottom: 10px; }
.rec-list li { margin-bottom: 4px; }
</style>""", unsafe_allow_html=True)

# ── Nav header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center;
            margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid #eee;">
  <div style="font-size:18px; font-weight:800; color:#1a1a2e;">👤 Detalle de vendedor — Wurth Argentina</div>
  <div style="font-size:13px; display:flex; gap:18px; flex-wrap:wrap;">
    <a href="/"               target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">🏠 Inicio</a>
    <a href="/Supervisor"     target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">👤 Por supervisor</a>
    <a href="/Intervenciones" target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">📝 Intervenciones</a>
    <a href="/Historial"      target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">📈 Historial</a>
    <a href="/Precision"      target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">🎯 Precisión</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Query param ───────────────────────────────────────────────────────────────
id_param = st.query_params.get("id", None)

if not id_param:
    st.markdown("""
    <div style="padding: 48px 0; text-align: center; color: #888;">
      <div style="font-size: 48px; margin-bottom: 16px;">👤</div>
      <div style="font-size: 18px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px;">
        Seleccioná un vendedor desde el dashboard
      </div>
      <div style="font-size: 14px;">
        Abrí esta pantalla desde el dashboard haciendo clic en el nombre de un vendedor.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

try:
    id_vendedor = int(id_param)
except ValueError:
    st.error(f"ID de vendedor inválido: **{id_param}**")
    st.stop()

# ── Back button ───────────────────────────────────────────────────────────────
if st.button("← Volver al inicio"):
    st.switch_page("dashboard.py")

# ── Datos (cacheados) ─────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _cargar_vendedor(vid: int):
    scores = calcular_scores(meses_tendencia=3)
    con = get_connection()

    v_info = pd.read_sql(f"""
        SELECT v.*, g.riesgo_base
        FROM vendedores v
        LEFT JOIN grupos g ON v.id_grupo = g.id_grupo
        WHERE v.id_vendedor = {vid}
    """, con)

    ventas = pd.read_sql(f"""
        SELECT *
        FROM ventas_mensual
        WHERE id_vendedor = {vid}
        ORDER BY anio DESC, mes DESC
        LIMIT 6
    """, con)

    try:
        score_hist = pd.read_sql(f"""
            SELECT periodo, score, nivel, señales, pct_plan_3m, meses_activo
            FROM score_historico
            WHERE id_vendedor = {vid}
            ORDER BY periodo ASC
        """, con)
    except Exception:
        score_hist = pd.DataFrame()

    con.close()
    return scores, v_info, ventas, score_hist


scores_df, v_info_df, ventas_df, score_hist_df = _cargar_vendedor(id_vendedor)

# ── Validar existencia ────────────────────────────────────────────────────────
row_score = scores_df[scores_df["id_vendedor"] == id_vendedor]
if row_score.empty:
    st.error(f"No se encontró el vendedor con ID **{id_vendedor}** en los scores activos. "
             f"Puede que ya no esté activo o no tenga datos de ventas recientes.")
    st.stop()

r = row_score.iloc[0]
score_val   = r["score"]
score_int   = int(round(score_val))
nivel       = r["nivel_riesgo"]
nivel_label = NIVEL_LABEL.get(nivel, nivel)
señales_activas = r["señales_activas"]  # lista Python
meses_activo = int(r["meses_activo"])

# Info del vendedor de la tabla vendedores
if v_info_df.empty:
    v_nombre    = r["nombre"]
    v_tipo      = r["tipo"]
    v_supervisor = r["supervisor"]
    v_grupo     = r["nombre_grupo"]
    v_fecha_ingreso = None
    v_riesgo_base   = float(r.get("grupo_riesgo_base", 0.4) or 0.4)
    v_fecha_egreso  = None
    v_motivo_egreso = None
else:
    vi = v_info_df.iloc[0]
    v_nombre    = r["nombre"]
    v_tipo      = str(vi.get("tipo", r["tipo"]) or r["tipo"])
    v_supervisor = str(vi.get("supervisor", r["supervisor"]) or r["supervisor"])
    v_grupo     = str(vi.get("nombre_grupo", r["nombre_grupo"]) or r["nombre_grupo"])
    v_fecha_ingreso = vi.get("fecha_ingreso")
    v_riesgo_base   = float(vi.get("riesgo_base", r.get("grupo_riesgo_base", 0.4)) or 0.4)
    v_fecha_egreso  = vi.get("fecha_egreso")
    v_motivo_egreso = vi.get("motivo_egreso")

zona_nivel = _zona_nivel(v_riesgo_base)
zona_label = _zona_label(v_riesgo_base)

# Fecha ingreso formateada
if v_fecha_ingreso:
    try:
        fi = pd.to_datetime(v_fecha_ingreso).strftime("%d/%m/%Y")
    except Exception:
        fi = str(v_fecha_ingreso)
else:
    fi = "—"

# ── Tarjeta info vendedor ─────────────────────────────────────────────────────
tipo_badge = badge("tipo", v_tipo, shape=False)
zona_badge = badge(zona_nivel, zona_label, shape=False)

st.markdown(f"""
<div class="vd-card">
  <div>
    <span class="vd-name">{v_nombre}</span>
    <span class="vd-id">#{id_vendedor}</span>
    &nbsp; {tipo_badge}
  </div>
  <div class="vd-meta">
    <span>📍 <b>{v_grupo}</b> &nbsp;{zona_badge}</span>
    <span>👤 Supervisor: <b>{v_supervisor}</b></span>
    <span>📅 Ingreso: <b>{fi}</b> · {fmt_antiguedad(meses_activo)} de antigüedad</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Score + señales ───────────────────────────────────────────────────────────
col_score, col_señales = st.columns([1, 2])

with col_score:
    st.markdown(hero_kpi("Score de riesgo actual", score_int, nivel_label,
                         red=(nivel == "critico")),
                unsafe_allow_html=True)
    st.markdown(accion_tag(nivel), unsafe_allow_html=True)

with col_señales:
    # Pills
    if señales_activas:
        pills_html = " ".join(
            pill(_señal_short(s)[0], _señal_short(s)[1])
            for s in señales_activas
        )
    else:
        pills_html = '<span style="color:#ccc;font-size:12px;">Sin señales de alerta activas</span>'

    # Breakdown table
    breakdown = score_breakdown_rows(
        [_señal_short(s)[0] for s in señales_activas]
    )
    rows_bd = "".join(
        f'<div class="bd-row"><span class="bd-label">{lbl}</span>'
        f'<span class="bd-peso">+{peso:.1f}</span></div>'
        for lbl, peso in breakdown
    )

    st.markdown(f"""
<div style="margin-bottom:12px;">{pills_html}</div>
<div style="font-size:13px;font-weight:700;color:#666;margin-bottom:6px;">Desglose del score</div>
<div style="background:#fafafa;border-radius:8px;padding:10px 14px;">
  {rows_bd}
  <div class="bd-row" style="border-bottom:none;margin-top:4px;">
    <span style="font-weight:700;color:#1a1a2e;">Total</span>
    <span style="font-weight:800;color:#1a1a2e;">{score_val}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Historial de score ────────────────────────────────────────────────────────
if not score_hist_df.empty:
    periodos = score_hist_df["periodo"].tolist()
    scores_h = score_hist_df["score"].tolist()
    n_periodos = len(periodos)

    fig = go.Figure()

    # Bandas de color
    fig.add_hrect(y0=8, y1=10,  fillcolor="#FDECEA", opacity=0.4, line_width=0,
                  annotation_text="Crítico", annotation_position="right",
                  annotation_font_size=11, annotation_font_color="#B71C1C")
    fig.add_hrect(y0=6, y1=8,   fillcolor="#FFF3E0", opacity=0.4, line_width=0,
                  annotation_text="Alto",    annotation_position="right",
                  annotation_font_size=11, annotation_font_color="#E65100")
    fig.add_hrect(y0=4, y1=6,   fillcolor="#E3F2FD", opacity=0.35, line_width=0,
                  annotation_text="Medio",   annotation_position="right",
                  annotation_font_size=11, annotation_font_color="#1565C0")
    fig.add_hrect(y0=1, y1=4,   fillcolor="#F1F8E9", opacity=0.4, line_width=0,
                  annotation_text="Bajo",    annotation_position="right",
                  annotation_font_size=11, annotation_font_color="#2E7D32")

    fig.add_trace(go.Scatter(
        x=periodos, y=scores_h,
        mode="lines+markers",
        line=dict(color="#E24B4A", width=2.5),
        marker=dict(size=7, color="#E24B4A", line=dict(width=1.5, color="white")),
        name="Score",
        hovertemplate="<b>%{x}</b><br>Score: %{y}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=f"Evolución del score (últimos {n_periodos} períodos)",
                   font=dict(size=14, color="#1a1a2e"), x=0),
        height=260,
        margin=dict(l=0, r=60, t=40, b=30),
        yaxis=dict(range=[1, 10.2], tickfont=dict(size=11), gridcolor="#f0f0f0"),
        xaxis=dict(tickfont=dict(size=11), tickangle=-30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )

    st.markdown('<div class="sec-header">📈 Evolución del score</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)

# ── Tabla ventas recientes ────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📊 Ventas mensuales — últimos 6 meses</div>',
            unsafe_allow_html=True)

if ventas_df.empty:
    st.info("No hay datos de ventas disponibles para este vendedor.")
else:
    ventas_rows = ""
    for _, vr in ventas_df.iterrows():
        periodo_str = _fmt_periodo(vr["anio"], vr["mes"])
        pct_plan    = float(vr.get("pct_plan", 0) or 0)
        venta_total = float(vr.get("venta_total", 0) or 0)
        dias_cero   = int(vr.get("dias_venta_cero", 0) or 0)
        pct_cob     = float(vr.get("pct_cobranza", 0) or 0)
        cli_activos = int(vr.get("clientes_activos", 0) or 0)
        cli_nuevos  = int(vr.get("clientes_nuevos", 0) or 0)

        color_plan = _pct_plan_color(pct_plan)

        ventas_rows += f"""<tr>
          <td><b>{periodo_str}</b></td>
          <td><b style="color:{color_plan};">{fmt_pct(pct_plan)}</b></td>
          <td>${fmt_num(venta_total)}</td>
          <td style="color:{'#B71C1C' if dias_cero > 3 else '#1a1a2e'};font-weight:{'700' if dias_cero > 3 else '400'};">{dias_cero}</td>
          <td style="color:{'#B71C1C' if pct_cob < 90 else '#2E7D32'};">{fmt_pct(pct_cob)}</td>
          <td>{fmt_num(cli_activos)}</td>
          <td style="color:{'#aaa' if cli_nuevos == 0 else '#1a1a2e'};">{fmt_num(cli_nuevos)}</td>
        </tr>"""

    st.markdown(f"""
<div style="background:white;border-radius:12px;padding:16px 18px;
            box-shadow:0 1px 4px rgba(0,0,0,0.08);overflow-x:auto;">
  <table class="wz-table">
    <thead><tr>
      <th>Período</th>
      <th>% Plan</th>
      <th>Venta total</th>
      <th>Días cero</th>
      <th>Cobranza %</th>
      <th>Clientes activos</th>
      <th>Clientes nuevos</th>
    </tr></thead>
    <tbody>{ventas_rows}</tbody>
  </table>
</div>
""", unsafe_allow_html=True)

# ── Recomendación de acción ───────────────────────────────────────────────────
perfil_key, perfil_label, top_accion, ranking = recomendar_accion(
    meses_activo, v_riesgo_base,
    [_señal_short(s)[0] for s in señales_activas]
)

st.markdown('<div class="sec-header">🎯 Acción recomendada</div>', unsafe_allow_html=True)

ranking_items = "".join(
    f'<li style="margin-bottom:4px;">'
    f'<b>{a[0]}</b>'
    f'<span style="color:#aaa;font-size:11px;margin-left:8px;">'
    f'efectividad {a[1]:.1f} · {a[2]} días promedio</span>'
    f'</li>'
    for a in ranking[:4]
)

st.markdown(f"""
<div class="rec-card">
  <div class="rec-title">Perfil: {perfil_label}</div>
  <div class="rec-action">→ {top_accion[0]}</div>
  <ul class="rec-list" style="margin:0;padding-left:18px;color:#444;">
    {ranking_items}
  </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>")
st.caption(f"Wurth Argentina · Detalle vendedor #{id_vendedor} · Sistema de alertas de rotación")
