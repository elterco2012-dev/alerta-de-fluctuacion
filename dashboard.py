"""
dashboard.py
------------
Dashboard Streamlit de alertas tempranas de rotación de vendedores.
Ejecutar con: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from score_engine import calcular_scores, resumen_grupos, get_connection, obtener_sparklines

st.set_page_config(
    page_title="Wurth | Alertas de Rotación",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""<style>
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 2rem 2.5rem 3rem !important; max-width: 100% !important; }
header { display: none; }

.kpi-row { display: flex; gap: 14px; margin-bottom: 28px; }
.kpi-card {
    background: white; border-radius: 12px; padding: 18px 22px;
    flex: 1; box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border-left: 4px solid #e0e0e0;
}
.kpi-card.kc { border-left-color: #E24B4A; }
.kpi-card.ka { border-left-color: #EF9F27; }
.kpi-card.ki { border-left-color: #4A90D9; }
.kpi-value { font-size: 30px; font-weight: 800; color: #1a1a2e; line-height: 1.1; }
.kpi-label { font-size: 13px; font-weight: 700; color: #333; margin-top: 6px; }
.kpi-sub   { font-size: 11px; color: #999; margin-top: 3px; }

.sec-header {
    font-size: 15px; font-weight: 700; color: #1a1a2e;
    margin: 8px 0 14px; display: flex; align-items: center; gap: 6px;
}

.pill { display: inline-block; padding: 2px 8px; border-radius: 10px;
        font-size: 11px; font-weight: 600; margin: 1px 2px; white-space: nowrap; }
.pill-red    { background: #FDECEA; color: #B71C1C; }
.pill-orange { background: #FFF3E0; color: #E65100; }
.pill-yellow { background: #FFFDE7; color: #F57F17; }

.sc { display: inline-flex; align-items: center; justify-content: center;
      width: 36px; height: 36px; border-radius: 50%; font-weight: 800; font-size: 15px; }
.sc-critico { background: #FDECEA; color: #B71C1C; border: 2px solid #E24B4A; }
.sc-alto    { background: #FFF3E0; color: #E65100; border: 2px solid #EF9F27; }
.sc-medio   { background: #E3F2FD; color: #1565C0; border: 2px solid #4A90D9; }
.sc-bajo    { background: #F1F8E9; color: #2E7D32; border: 2px solid #639922; }

.bdg { display: inline-block; padding: 2px 8px; border-radius: 4px;
       font-size: 11px; font-weight: 600; }
.bdg-critico { background: #FDECEA; color: #B71C1C; }
.bdg-alto    { background: #FFF3E0; color: #E65100; }
.bdg-medio   { background: #E3F2FD; color: #1565C0; }
.bdg-bajo    { background: #F1F8E9; color: #2E7D32; }

.spark { display: inline-flex; align-items: flex-end; gap: 3px; height: 24px; }
.sb { width: 9px; border-radius: 2px 2px 0 0; }

.vt { width: 100%; border-collapse: collapse; }
.vt th { background: #f8f9fa; padding: 10px 12px; text-align: left;
         font-size: 12px; font-weight: 600; color: #666;
         border-bottom: 2px solid #e9ecef; }
.vt td { padding: 11px 12px; border-bottom: 1px solid #f2f2f2;
         vertical-align: middle; font-size: 13px; }
.vt tr:hover td { background: #fafafa; }
.vn  { font-weight: 700; color: #1a1a2e; font-size: 13px; }
.vsb { color: #aaa; font-size: 11px; margin-top: 2px; }

.card { background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08); }

.zc { display: flex; justify-content: space-between; align-items: center;
      padding: 13px 0; border-bottom: 1px solid #f2f2f2; }
.zc:last-child { border-bottom: none; }
.zn  { font-weight: 700; font-size: 13px; color: #1a1a2e; }
.zsb { font-size: 11px; color: #aaa; margin-top: 2px; }
.zr  { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.zpct { font-weight: 700; font-size: 13px; color: #1a1a2e; }

.ot { width: 100%; border-collapse: collapse; }
.ot th { background: #f8f9fa; padding: 10px 14px; text-align: left;
         font-size: 12px; font-weight: 600; color: #666;
         border-bottom: 2px solid #e9ecef; }
.ot td { padding: 11px 14px; border-bottom: 1px solid #f2f2f2;
         font-size: 13px; vertical-align: middle; }
</style>""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
SEÑAL_TAGS = {
    "% Plan cayendo 3 meses seguidos":    ("caída 3m",     "red"),
    "% Plan < 80% promedio últimos meses":("plan<80%",     "orange"),
    "Días sin venta > 3 en promedio":     ("días cero↑",   "red"),
    "< 60% de cartera activa":            ("inactivos↑",   "orange"),
    "Cobranza real < 90% de teórica":     ("cobranza baja","orange"),
    "En ventana crítica mes 1-3":         ("onboarding",   "red"),
    "En ventana crítica mes 4-6":         ("mes 4-6",      "orange"),
    "Grupo con alta rotación histórica":  ("zona quemada", "orange"),
    "Sin clientes nuevos últimos 2 meses":("clientes L:0", "yellow"),
}

def _pills(tags):
    if not tags:
        return '<span style="color:#ccc;font-size:12px;">Sin alertas</span>'
    return "".join(
        f'<span class="pill pill-{SEÑAL_TAGS.get(d, (d,"yellow"))[1]}">'
        f'{SEÑAL_TAGS.get(d, (d,"yellow"))[0]}</span>'
        for d in tags
    )

def _score_circle(score, nivel):
    return f'<div class="sc sc-{nivel}">{int(score)}</div>'

def _spark(vals):
    if not vals:
        return "—"
    cap = max(max(vals), 100)
    bars = []
    for v in vals:
        h = max(3, int(v / cap * 22))
        c = "#639922" if v >= 90 else ("#EF9F27" if v >= 70 else "#E24B4A")
        bars.append(f'<div class="sb" style="height:{h}px;background:{c};"></div>')
    return f'<div class="spark">{"".join(bars)}</div>'

def _bdg(nivel, label=None):
    labels = {"critico": "Crítico", "alto": "Alto", "medio": "Medio", "bajo": "Bajo"}
    return f'<span class="bdg bdg-{nivel}">{label or labels[nivel]}</span>'

def _zona_nivel(riesgo_base):
    if riesgo_base > 0.60: return "critico"
    if riesgo_base > 0.45: return "alto"
    if riesgo_base > 0.30: return "medio"
    return "bajo"

def _zona_label(riesgo_base):
    nivel = _zona_nivel(riesgo_base)
    return {"critico": "rot alta", "alto": "rot alta", "medio": "rot media", "bajo": "rot baja"}[nivel]

# ── Carga de datos ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_datos():
    scores   = calcular_scores(meses_tendencia=3)
    grupos   = resumen_grupos()
    sparks   = obtener_sparklines(meses=3)

    con = get_connection()
    grupos_risk = pd.read_sql("SELECT nombre_grupo, riesgo_base FROM grupos", con)
    ventanas = pd.read_sql("""
        SELECT mes_numero, COUNT(*) as renuncias
        FROM vendedores v
        JOIN ventas_mensual vm ON v.id_vendedor = vm.id_vendedor
        WHERE v.fecha_egreso IS NOT NULL
          AND vm.mes_numero = (
              SELECT MAX(mes_numero) FROM ventas_mensual
              WHERE id_vendedor = v.id_vendedor
          )
        GROUP BY mes_numero
        ORDER BY mes_numero
    """, con)
    con.close()

    grupos = grupos.merge(grupos_risk, on="nombre_grupo", how="left")
    return scores, grupos, sparks, ventanas

scores_df, grupos_df, sparks, ventanas_df = cargar_datos()

# ── Navegación ─────────────────────────────────────────────────────────────────
_, nav_col = st.columns([5, 1])
with nav_col:
    st.page_link("pages/Supervisor.py", label="👤 Vista por supervisor", icon="→")

# ── KPIs ───────────────────────────────────────────────────────────────────────
total          = len(scores_df)
en_critica     = len(scores_df[scores_df.nivel_riesgo.isin(["critico", "alto"])])
perm_prom      = grupos_df["permanencia_promedio_meses"].mean()
ob_critico     = len(scores_df[
    (scores_df.meses_activo <= 3) & (scores_df.nivel_riesgo.isin(["critico", "alto"]))
])

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-value">{total}</div>
    <div class="kpi-label">Vendedores activos</div>
    <div class="kpi-sub">Actualizando mensualmente</div>
  </div>
  <div class="kpi-card kc">
    <div class="kpi-value" style="color:#E24B4A">{en_critica}</div>
    <div class="kpi-label">En zona crítica</div>
    <div class="kpi-sub">Riesgo alto o crítico</div>
  </div>
  <div class="kpi-card ka">
    <div class="kpi-value">{perm_prom:.1f} m</div>
    <div class="kpi-label">Permanencia promedio</div>
    <div class="kpi-sub">Era 18m hace 10 años</div>
  </div>
  <div class="kpi-card ki">
    <div class="kpi-value" style="color:#4A90D9">{ob_critico}</div>
    <div class="kpi-label">En onboarding crítico</div>
    <div class="kpi-sub">Primeros 3 meses</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Filtro ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📋 Vendedores por score de riesgo de fuga</div>',
            unsafe_allow_html=True)

filtro = st.radio(
    "",
    ["Todos", "Crítico", "Alto", "Viajantes", "Televentas"],
    horizontal=True,
    label_visibility="collapsed",
)

df = scores_df.copy()
if filtro == "Crítico":
    df = df[df.nivel_riesgo == "critico"]
elif filtro == "Alto":
    df = df[df.nivel_riesgo == "alto"]
elif filtro == "Viajantes":
    df = df[df.tipo == "Viajante"]
elif filtro == "Televentas":
    df = df[df.tipo == "Televentas"]

# ── Tabla principal ────────────────────────────────────────────────────────────
rows = ""
for _, r in df.iterrows():
    vid   = int(r["id_vendedor"])
    nivel = r["nivel_riesgo"]
    zona_n = _zona_nivel(r["grupo_riesgo_base"])
    zona_l = _zona_label(r["grupo_riesgo_base"])
    rows += f"""
    <tr>
      <td>
        <div class="vn">ID {vid}</div>
        <div class="vsb">{r['tipo']} · {r['meses_activo']}m antigüedad</div>
      </td>
      <td>{_pills(r['señales_activas'])}</td>
      <td><b>{r['pct_plan_3m']}%</b></td>
      <td>{_spark(sparks.get(vid, []))}</td>
      <td>
        <div style="font-weight:600;font-size:13px;">{r['nombre_grupo']}</div>
        <div style="margin-top:3px;">{_bdg(zona_n, zona_l)}</div>
      </td>
      <td>{_score_circle(r['score'], nivel)}</td>
    </tr>"""

st.markdown(f"""
<div class="card" style="margin-bottom:6px;overflow-x:auto;">
<table class="vt">
<thead><tr>
  <th>Vendedor</th><th>Señales detectadas</th><th>% Plan 3m</th>
  <th>Tendencia</th><th>Zona</th><th>Score</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</div>""", unsafe_allow_html=True)
st.caption(f"Mostrando {len(df)} vendedores")

st.markdown("<br>", unsafe_allow_html=True)

# ── Zonas + Ventanas ───────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1.6])

with col1:
    st.markdown('<div class="sec-header">📍 Zonas con mayor rotación histórica</div>',
                unsafe_allow_html=True)
    zonas = grupos_df.sort_values("permanencia_promedio_meses", na_position="last")

    zona_cards = ""
    for _, g in zonas.iterrows():
        perm  = g["permanencia_promedio_meses"]
        rb    = g.get("riesgo_base", 0.5)
        nivel = _zona_nivel(rb) if pd.notna(rb) else "medio"
        perm_str = f"{perm:.1f}m" if pd.notna(perm) else "—"
        zona_cards += f"""
        <div class="zc">
          <div>
            <div class="zn">{g['nombre_grupo']}</div>
            <div class="zsb">{int(g['total_vendedores'])} vendedores históricos · perm. prom. {perm_str}</div>
          </div>
          <div class="zr">
            <div class="zpct">{g['cumplimiento_plan_promedio']:.0f}% plan</div>
            {_bdg(nivel)}
          </div>
        </div>"""

    st.markdown(f'<div class="card">{zona_cards}</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="sec-header">⏱️ Ventanas críticas de permanencia</div>',
                unsafe_allow_html=True)
    st.caption("Meses con mayor probabilidad de renuncia (histórico simulado)")

    vdf = ventanas_df.copy()
    vdf["label"] = vdf["mes_numero"].apply(lambda m: f"M{m}" if m < 19 else "M19+")

    def _color_mes(m):
        if m <= 3:  return "#E24B4A"
        if m <= 6:  return "#EF9F27"
        if m <= 12: return "#B4B2A9"
        return "#8DB56B"

    fig = go.Figure(go.Bar(
        x=vdf["label"],
        y=vdf["renuncias"],
        marker_color=[_color_mes(m) for m in vdf["mes_numero"]],
        text=vdf["renuncias"],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=290,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0", zeroline=False, title=""),
        xaxis=dict(showgrid=False, title=""),
        font=dict(size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Onboarding en curso ────────────────────────────────────────────────────────
onb = scores_df[scores_df.meses_activo <= 3].sort_values("score", ascending=False)

if not onb.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-header">👥 Onboarding en curso — primeros 90 días</div>',
                unsafe_allow_html=True)

    ob_rows = ""
    for _, r in onb.iterrows():
        rb     = r["grupo_riesgo_base"]
        z_n    = _zona_nivel(rb)
        z_l    = _zona_label(rb)
        nivel  = r["nivel_riesgo"]
        ob_rows += f"""
        <tr>
          <td><b>ID {int(r['id_vendedor'])}</b></td>
          <td>{r['tipo']}</td>
          <td>Mes {r['meses_activo']}</td>
          <td>{r['nombre_grupo']} {_bdg(z_n, z_l)}</td>
          <td><b>{r['pct_plan_3m']}%</b></td>
          <td>{_bdg(nivel)}</td>
        </tr>"""

    st.markdown(f"""
    <div class="card">
    <table class="ot">
    <thead><tr>
      <th>Vendedor</th><th>Tipo</th><th>Mes</th>
      <th>Zona asignada</th><th>% Plan</th><th>Riesgo</th>
    </tr></thead>
    <tbody>{ob_rows}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)
