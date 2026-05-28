"""
pages/Historial.py
------------------
Análisis histórico de permanencia y zonas críticas.
Usa TODOS los vendedores (activos + bajas) de la tabla vendedores.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
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


# ── Helpers ────────────────────────────────────────────────────────────────────
def _remap_grupo(nombre):
    """Traduce IDs de grupos Televentas de Informix a nombres legibles."""
    n = str(nombre)
    if "971" in n: return "Televentas Auto"
    if "972" in n: return "Televentas Metal"
    if "973" in n: return "Televentas Cargo"
    return nombre


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

    # Supervisor y cantidad de vendedores activos por grupo (excluye supervisores)
    sup_df = pd.read_sql("""
        SELECT nombre_grupo, supervisor, COUNT(*) as n_activos
        FROM vendedores
        WHERE activo = 1
          AND nombre NOT IN (
              SELECT DISTINCT supervisor FROM vendedores
              WHERE supervisor IS NOT NULL AND supervisor != ''
          )
        GROUP BY nombre_grupo, supervisor
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
    df["completado"]  = df["activo"] == 0

    # Remap televentas
    df["nombre_grupo"]     = df["nombre_grupo"].apply(_remap_grupo)
    sup_df["nombre_grupo"] = sup_df["nombre_grupo"].apply(_remap_grupo)

    # Mapa grupo → supervisor principal y cantidad activa
    sup_map = {}
    cnt_map = {}
    for grp, g in sup_df.groupby("nombre_grupo"):
        idx = g["n_activos"].idxmax()
        s = g.loc[idx, "supervisor"]
        sup_map[grp] = s if pd.notna(s) and s else ""
        cnt_map[grp] = int(g["n_activos"].sum())

    return df[df["permanencia_meses"] > 0].copy(), sup_map, cnt_map


with st.spinner("Cargando historial..."):
    df, sup_map, cnt_map = cargar_historial()

if df.empty:
    st.warning("No hay datos históricos disponibles.")
    st.stop()

hoy = date.today().year
df_bajas  = df[df["completado"]]
df_activo = df[~df["completado"]]

# ── KPIs ───────────────────────────────────────────────────────────────────────
total_hist   = len(df)
total_bajas  = len(df_bajas)
perm_bajas   = df_bajas["permanencia_meses"].median()
pct_menos6   = (df_bajas["permanencia_meses"] < 6).mean()  * 100
pct_menos12  = (df_bajas["permanencia_meses"] < 12).mean() * 100

st.markdown(f"""<div class="kpi-row">
  <div class="kpi-card kb">
    <div class="kpi-value">{total_hist}</div>
    <div class="kpi-label">Vendedores en historial total</div>
    <div class="kpi-sub">{len(df_activo)} activos · {total_bajas} con baja</div>
  </div>
  <div class="kpi-card ko">
    <div class="kpi-value">{perm_bajas:.0f} m</div>
    <div class="kpi-label">Permanencia mediana (dados de baja)</div>
    <div class="kpi-sub">La mitad se fue antes de este número. Era 18m hace 10 años.</div>
  </div>
  <div class="kpi-card kr">
    <div class="kpi-value">{pct_menos6:.0f}%</div>
    <div class="kpi-label">Se fueron en menos de 6 meses</div>
    <div class="kpi-sub">No sobrevivió la ventana crítica de onboarding</div>
  </div>
  <div class="kpi-card kr" style="border-left-color:#C0392B;">
    <div class="kpi-value" style="color:#C0392B;">{pct_menos12:.0f}%</div>
    <div class="kpi-label">Se fueron en menos de 12 meses</div>
    <div class="kpi-sub">No completó ni un año — incluye los &lt;6m anteriores</div>
  </div>
  <div class="kpi-card kg">
    <div class="kpi-value">{len(df_activo)}</div>
    <div class="kpi-label">Vendedores activos hoy</div>
    <div class="kpi-sub">Antigüedad promedio: {df_activo['permanencia_meses'].mean():.0f} m</div>
  </div>
</div>""", unsafe_allow_html=True)


# ── Gráfico 1: Tendencia de permanencia (últimos 10 años, solo dados de baja) ──
st.markdown('<div class="sec-header">📊 Tendencia de permanencia — últimos 10 años (solo vendedores dados de baja)</div>',
            unsafe_allow_html=True)
st.caption(
    "Cada punto = mediana de meses que duraron los vendedores que entraron ese año y luego se fueron. "
    "Los activos no se incluyen porque su ciclo todavía no cerró. "
    "La línea roja punteada muestra la tendencia: si baja, el problema se está profundizando."
)

año_min = hoy - 10
df_rango = df_bajas[df_bajas["año_ingreso"] >= año_min].copy()

if df_rango.empty:
    st.info("No hay suficientes datos de bajas en los últimos 10 años.")
else:
    cohorte = (
        df_rango.groupby("año_ingreso")["permanencia_meses"]
        .agg(mediana="median", n="count")
        .reset_index()
        .sort_values("año_ingreso")
    )

    años     = cohorte["año_ingreso"].values.astype(float)
    medianas = cohorte["mediana"].values

    fig1 = go.Figure()

    # Datos reales
    fig1.add_trace(go.Scatter(
        x=años,
        y=medianas,
        mode="lines+markers+text",
        name="Permanencia mediana (bajas)",
        line=dict(color="#4A90D9", width=2.5),
        marker=dict(size=10, color="#4A90D9", line=dict(color="white", width=2)),
        text=[f"{v:.0f}m<br>({int(n)} bajas)"
              for v, n in zip(medianas, cohorte["n"].values)],
        textposition="top center",
        textfont=dict(size=11, color="#333"),
        hovertemplate="<b>%{x:.0f}</b><br>Permanencia mediana: %{y:.0f} meses<extra></extra>",
    ))

    # Línea de tendencia (regresión lineal)
    if len(años) >= 3:
        z = np.polyfit(años, medianas, 1)
        p = np.poly1d(z)
        x_line = np.linspace(años[0], años[-1], 100)
        fig1.add_trace(go.Scatter(
            x=x_line,
            y=p(x_line),
            mode="lines",
            name=f"Tendencia ({z[0]:+.1f} m/año)",
            line=dict(color="#E24B4A", width=2, dash="dash"),
            hoverinfo="skip",
        ))

    # Referencia histórica 18 meses
    fig1.add_hline(
        y=18, line_dash="dot", line_color="#27AE60", line_width=1.5,
        annotation_text="18 m (benchmark histórico)",
        annotation_position="top left",
        annotation_font_size=11,
        annotation_font_color="#27AE60",
    )

    fig1.update_layout(
        height=380,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(
            tickmode="linear", dtick=1, title="Año de ingreso",
            tickformat=".0f",
        ),
        yaxis=dict(title="Permanencia mediana (meses)", rangemode="tozero"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
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

# Añadir supervisor y cantidad activa
zona_stats["supervisor_grupo"] = zona_stats["nombre_grupo"].map(sup_map).fillna("")
zona_stats["activos_hoy"]      = zona_stats["nombre_grupo"].map(cnt_map).fillna(0).astype(int)

# Solo mostrar grupos con al menos un vendedor activo hoy
zona_stats = zona_stats[zona_stats["activos_hoy"] > 0]

if top_n != "Todos":
    zona_stats_vis = zona_stats.head(int(top_n))
else:
    zona_stats_vis = zona_stats

# Construir etiquetas Y con supervisor y cantidad
def _y_label(row):
    grp = row["nombre_grupo"]
    sup = row["supervisor_grupo"]
    cnt = row["activos_hoy"]
    if sup and cnt:
        return f"{grp}<br><span style='font-size:11px'>{sup} ({cnt})</span>"
    if cnt:
        return f"{grp}<br>({cnt} activos)"
    return grp

y_labels = [_y_label(row) for _, row in zona_stats_vis.iterrows()]

fig2 = go.Figure()

colores = [
    "#E24B4A" if p >= 50 else ("#EF9F27" if p >= 30 else "#4A90D9")
    for p in zona_stats_vis["pct_rotacion_rapida"]
]

hover_texts = [
    (f"<b>{row['nombre_grupo']}</b><br>"
     f"Supervisor: {row['supervisor_grupo'] or '—'}<br>"
     f"Activos hoy: {row['activos_hoy']}<br>"
     f"Rotación rápida (&lt;6m): {row['pct_rotacion_rapida']:.1f}%<br>"
     f"Bajas rápidas: {int(row['bajas_rapidas'])}/{int(row['total'])}")
    for _, row in zona_stats_vis.iterrows()
]

fig2.add_trace(go.Bar(
    x=zona_stats_vis["pct_rotacion_rapida"],
    y=y_labels,
    orientation="h",
    marker_color=colores,
    text=[f"{p:.0f}% ({int(b)}/{int(t)})"
          for p, b, t in zip(
              zona_stats_vis["pct_rotacion_rapida"],
              zona_stats_vis["bajas_rapidas"],
              zona_stats_vis["total"],
          )],
    textposition="outside",
    hovertext=hover_texts,
    hoverinfo="text",
))

fig2.add_vline(x=50, line_dash="dash", line_color="#E24B4A", line_width=1,
               annotation_text="50% umbral crítico", annotation_position="top",
               annotation_font_size=10)

fig2.update_layout(
    height=max(380, len(zona_stats_vis) * 38),
    margin=dict(l=0, r=150, t=20, b=0),
    xaxis=dict(title="% vendedores que se fueron en < 6 meses", range=[0, 120]),
    yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
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
    tabla["supervisor_grupo"] = tabla["supervisor_grupo"].replace("", "—")
    st.dataframe(
        tabla[[
            "nombre_grupo", "supervisor_grupo", "activos_hoy",
            "total", "bajas", "bajas_rapidas",
            "pct_rotacion_rapida", "perm_mediana"
        ]].rename(columns={
            "nombre_grupo":         "Zona",
            "supervisor_grupo":     "Supervisor",
            "activos_hoy":          "Activos hoy",
            "total":                "Total hist.",
            "bajas":                "Bajas",
            "bajas_rapidas":        "Bajas < 6m",
            "pct_rotacion_rapida":  "% rot. rápida",
            "perm_mediana":         "Perm. mediana bajas",
        }),
        use_container_width=True,
        hide_index=True,
    )
