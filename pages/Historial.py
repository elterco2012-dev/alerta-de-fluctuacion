"""
pages/Historial.py
------------------
Análisis histórico de permanencia y zonas críticas.
Usa TODOS los vendedores (activos + bajas) de la tabla vendedores.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from score_engine import get_connection

st.set_page_config(
    page_title="Wurth | Historial de Rotación",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
.kpi-card.kr { border-left-color: #E24B4A; }
.kpi-card.ko { border-left-color: #EF9F27; }
.kpi-card.kb { border-left-color: #4A90D9; }
.kpi-card.kg { border-left-color: #27AE60; }
.kpi-value { font-size: 28px; font-weight: 800; color: #1a1a2e; line-height: 1.1; }
.kpi-label { font-size: 13px; font-weight: 700; color: #333; margin-top: 6px; }
.kpi-sub   { font-size: 11px; color: #999; margin-top: 3px; }
.sec-header { font-size: 15px; font-weight: 700; color: #1a1a2e; margin: 20px 0 12px; }
</style>""", unsafe_allow_html=True)


# ── Nav ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center;
            margin-bottom:20px; padding-bottom:14px; border-bottom:1px solid #eee;">
  <div style="font-size:20px; font-weight:800; color:#1a1a2e;">
    📈 Historial de Rotación — Wurth Argentina
  </div>
  <div style="font-size:13px; display:flex; gap:20px;">
    <a href="/"               target="_self" style="color:#4A90D9;text-decoration:none;">🏠 Inicio</a>
    <a href="/Supervisor"     target="_self" style="color:#4A90D9;text-decoration:none;">👤 Por supervisor</a>
    <a href="/Costo_Rotacion" target="_self" style="color:#4A90D9;text-decoration:none;">💰 Costo de rotación</a>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Datos ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def cargar_historial():
    con = get_connection()
    df = pd.read_sql("""
        SELECT id_vendedor, nombre, tipo, nombre_grupo, supervisor,
               fecha_ingreso, fecha_egreso, activo
        FROM vendedores
        WHERE fecha_ingreso IS NOT NULL
    """, con)
    con.close()

    today = pd.Timestamp(date.today())
    df["fecha_ingreso"] = pd.to_datetime(df["fecha_ingreso"], errors="coerce")
    df["fecha_egreso"]  = pd.to_datetime(df["fecha_egreso"],  errors="coerce")

    df["fecha_fin"] = df["fecha_egreso"].fillna(today)
    df["permanencia_meses"] = (
        (df["fecha_fin"] - df["fecha_ingreso"]).dt.days / 30.44
    ).round(1)

    df["año_ingreso"] = df["fecha_ingreso"].dt.year
    df["completado"]  = df["activo"] == 0   # True = ya se fue, False = aún activo

    return df[df["permanencia_meses"] > 0].copy()


with st.spinner("Cargando historial..."):
    df = cargar_historial()

if df.empty:
    st.warning("No hay datos históricos disponibles.")
    st.stop()

hoy = date.today().year
df_bajas  = df[df["completado"]]
df_activo = df[~df["completado"]]

# ── KPIs ───────────────────────────────────────────────────────────────────────
total_hist  = len(df)
total_bajas = len(df_bajas)
perm_bajas  = df_bajas["permanencia_meses"].median()
pct_menos6  = (df_bajas["permanencia_meses"] < 6).mean() * 100

st.markdown(f"""<div class="kpi-row">
  <div class="kpi-card kb">
    <div class="kpi-value">{total_hist}</div>
    <div class="kpi-label">Vendedores en historial total</div>
    <div class="kpi-sub">{len(df_activo)} activos · {total_bajas} con baja</div>
  </div>
  <div class="kpi-card ko">
    <div class="kpi-value">{perm_bajas:.0f} m</div>
    <div class="kpi-label">Permanencia mediana (dados de baja)</div>
    <div class="kpi-sub">La mitad se fue antes de este número</div>
  </div>
  <div class="kpi-card kr">
    <div class="kpi-value">{pct_menos6:.0f}%</div>
    <div class="kpi-label">Se fueron en menos de 6 meses</div>
    <div class="kpi-sub">De todos los vendedores con baja</div>
  </div>
  <div class="kpi-card kg">
    <div class="kpi-value">{len(df_activo)}</div>
    <div class="kpi-label">Vendedores activos hoy</div>
    <div class="kpi-sub">Antigüedad promedio: {df_activo['permanencia_meses'].mean():.0f} m</div>
  </div>
</div>""", unsafe_allow_html=True)


# ── Gráfico 1: Permanencia por año de ingreso ─────────────────────────────────
st.markdown('<div class="sec-header">📊 Permanencia promedio por año de ingreso (cohorte)</div>',
            unsafe_allow_html=True)
st.caption("Cada barra = promedio de meses que duraron los vendedores que entraron ese año. "
           "Los activos cuentan su antigüedad actual (mínimo, aún no cerraron su ciclo).")

año_min = max(hoy - 12, int(df["año_ingreso"].min()))
df_rango = df[df["año_ingreso"] >= año_min]

cohorte = (
    df_rango.groupby(["año_ingreso", "completado"])["permanencia_meses"]
    .agg(["mean", "count"])
    .reset_index()
    .rename(columns={"mean": "prom", "count": "n"})
)

años = sorted(df_rango["año_ingreso"].unique())

bars_bajas  = []
bars_activo = []
labels_b    = []
labels_a    = []

for a in años:
    sub = cohorte[cohorte["año_ingreso"] == a]
    baja   = sub[sub["completado"] == True]
    activo = sub[sub["completado"] == False]

    b_val = baja["prom"].values[0]   if not baja.empty   else None
    b_n   = int(baja["n"].values[0]) if not baja.empty   else 0
    a_val = activo["prom"].values[0] if not activo.empty else None
    a_n   = int(activo["n"].values[0]) if not activo.empty else 0

    bars_bajas.append(b_val)
    bars_activo.append(a_val)
    labels_b.append(f"{b_val:.0f} m ({b_n} bajas)" if b_val else "")
    labels_a.append(f"{a_val:.0f} m ({a_n} activos)" if a_val else "")

fig1 = go.Figure()

fig1.add_trace(go.Bar(
    name="Dados de baja (permanencia final)",
    x=años,
    y=bars_bajas,
    marker_color="#E24B4A",
    text=[f"{v:.0f}m" if v else "" for v in bars_bajas],
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Permanencia promedio bajas: %{y:.0f} meses<extra></extra>",
))

fig1.add_trace(go.Bar(
    name="Aún activos (antigüedad mínima)",
    x=años,
    y=bars_activo,
    marker_color="#4A90D9",
    opacity=0.6,
    text=[f"{v:.0f}m" if v else "" for v in bars_activo],
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Antigüedad promedio activos: %{y:.0f} meses<extra></extra>",
))

# Línea de referencia: 18 meses (benchmark histórico)
fig1.add_hline(
    y=18, line_dash="dash", line_color="#27AE60", line_width=1.5,
    annotation_text="18 m (benchmark 2015)", annotation_position="top left",
    annotation_font_size=11,
)

fig1.update_layout(
    barmode="group",
    height=380,
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(tickmode="linear", dtick=1, title="Año de ingreso"),
    yaxis=dict(title="Meses promedio", rangemode="tozero"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig1, use_container_width=True)


# ── Gráfico 2: Zonas críticas ─────────────────────────────────────────────────
st.markdown('<div class="sec-header">🔥 Zonas críticas — rotación histórica por grupo</div>',
            unsafe_allow_html=True)
st.caption("Basado en todos los vendedores (activos + bajas) de cada grupo. "
           "Riesgo alto = más del 50% de los que pasaron por ese grupo se fueron en < 6 meses.")

col_f1, col_f2 = st.columns([1, 3])
with col_f1:
    top_n = st.selectbox("Mostrar top", [10, 20, 30, "Todos"], index=1)

zona_stats = (
    df.groupby("nombre_grupo")
    .apply(lambda g: pd.Series({
        "total":         len(g),
        "bajas":         (g["completado"]).sum(),
        "bajas_rapidas": ((g["completado"]) & (g["permanencia_meses"] < 6)).sum(),
        "activos":       (~g["completado"]).sum(),
        "perm_mediana":  g.loc[g["completado"], "permanencia_meses"].median()
                         if g["completado"].any() else None,
    }))
    .reset_index()
)
zona_stats["pct_rotacion_rapida"] = (
    zona_stats["bajas_rapidas"] / zona_stats["total"] * 100
).round(1)
zona_stats = zona_stats[zona_stats["total"] >= 2].sort_values("pct_rotacion_rapida", ascending=False)

if top_n != "Todos":
    zona_stats_vis = zona_stats.head(int(top_n))
else:
    zona_stats_vis = zona_stats

fig2 = go.Figure()

colores = [
    "#E24B4A" if p >= 50 else ("#EF9F27" if p >= 30 else "#4A90D9")
    for p in zona_stats_vis["pct_rotacion_rapida"]
]

fig2.add_trace(go.Bar(
    x=zona_stats_vis["pct_rotacion_rapida"],
    y=zona_stats_vis["nombre_grupo"],
    orientation="h",
    marker_color=colores,
    text=[f"{p:.0f}% ({int(b)}/{int(t)} bajas rápidas)"
          for p, b, t in zip(
              zona_stats_vis["pct_rotacion_rapida"],
              zona_stats_vis["bajas_rapidas"],
              zona_stats_vis["total"],
          )],
    textposition="outside",
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Rotación rápida (<6m): %{x:.1f}%<br>"
        "<extra></extra>"
    ),
))

fig2.add_vline(x=50, line_dash="dash", line_color="#E24B4A", line_width=1,
               annotation_text="50% umbral crítico", annotation_position="top",
               annotation_font_size=10)

fig2.update_layout(
    height=max(350, len(zona_stats_vis) * 32),
    margin=dict(l=0, r=150, t=20, b=0),
    xaxis=dict(title="% vendedores que se fueron en < 6 meses", range=[0, 115]),
    yaxis=dict(autorange="reversed"),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
st.plotly_chart(fig2, use_container_width=True)


# ── Tabla detalle zonas ────────────────────────────────────────────────────────
with st.expander("Ver tabla completa de zonas"):
    tabla = zona_stats.copy()
    tabla["perm_mediana"] = tabla["perm_mediana"].apply(
        lambda x: f"{x:.0f} m" if pd.notna(x) else "—"
    )
    tabla["pct_rotacion_rapida"] = tabla["pct_rotacion_rapida"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(
        tabla[[
            "nombre_grupo", "total", "activos", "bajas",
            "bajas_rapidas", "pct_rotacion_rapida", "perm_mediana"
        ]].rename(columns={
            "nombre_grupo":         "Zona",
            "total":                "Total hist.",
            "activos":              "Activos",
            "bajas":                "Bajas",
            "bajas_rapidas":        "Bajas < 6m",
            "pct_rotacion_rapida":  "% rot. rápida",
            "perm_mediana":         "Perm. mediana bajas",
        }),
        use_container_width=True,
        hide_index=True,
    )
