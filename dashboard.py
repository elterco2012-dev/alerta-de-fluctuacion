"""
dashboard.py
------------
Dashboard Streamlit de alertas tempranas de rotación de vendedores.
Ejecutar con: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from score_engine import calcular_scores, resumen_grupos, get_connection

# ── Config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wurth | Alertas de Rotación",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORES = {
    "critico": "#E24B4A",
    "alto":    "#EF9F27",
    "medio":   "#4A90D9",
    "bajo":    "#639922",
}

# ── Carga de datos ─────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_datos():
    scores   = calcular_scores(meses_tendencia=3)
    grupos   = resumen_grupos()
    con      = get_connection()

    ventanas = pd.read_sql("""
        SELECT mes_numero,
               COUNT(*) as renuncias
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
    return scores, grupos, ventanas

scores_df, grupos_df, ventanas_df = cargar_datos()

# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.title("Filtros")
nivel_sel = st.sidebar.multiselect(
    "Nivel de riesgo",
    ["critico", "alto", "medio", "bajo"],
    default=["critico", "alto", "medio", "bajo"]
)
tipo_sel = st.sidebar.multiselect(
    "Tipo de vendedor",
    ["Viajante", "Televentas"],
    default=["Viajante", "Televentas"]
)
grupo_sel = st.sidebar.multiselect(
    "Grupo / Zona",
    sorted(scores_df["nombre_grupo"].unique()),
    default=[]
)
ventana_sel = st.sidebar.checkbox("Solo vendedores en ventana crítica (mes 1-6)", value=False)

st.sidebar.markdown("---")
st.sidebar.caption("⚠️ Datos simulados — estructura idéntica a Informix")

# ── Filtrar ────────────────────────────────────────────────────────────────
df = scores_df.copy()
if nivel_sel:
    df = df[df["nivel_riesgo"].isin(nivel_sel)]
if tipo_sel:
    df = df[df["tipo"].isin(tipo_sel)]
if grupo_sel:
    df = df[df["nombre_grupo"].isin(grupo_sel)]
if ventana_sel:
    df = df[df["en_ventana_critica"] == True]

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🔔 Alertas tempranas de rotación de vendedores")
st.caption("Wurth Argentina · Sistema de detección de riesgo de fuga · Datos simulados")

# ── KPIs ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Vendedores activos",   len(scores_df))
k2.metric("Críticos 🔴",          len(scores_df[scores_df.nivel_riesgo=="critico"]),
          delta=f"{len(scores_df[scores_df.nivel_riesgo=='critico'])} requieren acción inmediata",
          delta_color="inverse")
k3.metric("Riesgo alto 🟠",       len(scores_df[scores_df.nivel_riesgo=="alto"]))
k4.metric("En ventana crítica",   int(scores_df["en_ventana_critica"].sum()))
k5.metric("Permanencia prom.",    f"{grupos_df['permanencia_promedio_meses'].mean():.1f} m")

st.divider()

# ── Tabla principal ────────────────────────────────────────────────────────
st.subheader("📋 Vendedores por score de riesgo")

def color_nivel(val):
    c = {"critico":"#FCEBEB","alto":"#FEF3E2","medio":"#EBF3FC","bajo":"#EAF3DE"}.get(val,"")
    return f"background-color:{c}"

def format_señales(lista):
    if not lista:
        return "—"
    return " · ".join(lista)

df_display = df[[
    "id_vendedor","tipo","nombre_grupo","supervisor",
    "meses_activo","score","nivel_riesgo",
    "pct_plan_3m","tendencia_plan","dias_cero_promedio",
    "pct_clientes_activos","pct_cobranza","señales_activas"
]].copy()

df_display["señales_activas"] = df_display["señales_activas"].apply(format_señales)
df_display.columns = [
    "ID","Tipo","Grupo","Supervisor",
    "Meses","Score","Riesgo",
    "% Plan 3m","Tend. plan","Días cero",
    "% Cartera activa","% Cobranza","Señales detectadas"
]

st.dataframe(
    df_display.style.applymap(color_nivel, subset=["Riesgo"]),
    use_container_width=True,
    height=420,
)

st.caption(f"Mostrando {len(df)} vendedores")

st.divider()

# ── Grupos quemados + Ventanas críticas ────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🗺️ Grupos con mayor rotación histórica")
    fig_grupos = px.bar(
        grupos_df.sort_values("permanencia_promedio_meses"),
        x="permanencia_promedio_meses",
        y="nombre_grupo",
        orientation="h",
        color="permanencia_promedio_meses",
        color_continuous_scale=["#E24B4A","#EF9F27","#639922"],
        labels={
            "permanencia_promedio_meses": "Permanencia prom. (meses)",
            "nombre_grupo": "Grupo"
        },
        text="permanencia_promedio_meses",
        hover_data=["total_vendedores","bajas","cumplimiento_plan_promedio"]
    )
    fig_grupos.update_traces(texttemplate="%{text:.1f}m", textposition="outside")
    fig_grupos.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=20, t=20, b=0),
        height=320,
    )
    st.plotly_chart(fig_grupos, use_container_width=True)

    st.dataframe(
        grupos_df[["nombre_grupo","supervisor","total_vendedores",
                   "bajas","permanencia_promedio_meses","cumplimiento_plan_promedio"]].rename(columns={
            "nombre_grupo":"Grupo","supervisor":"Supervisor",
            "total_vendedores":"Total","bajas":"Bajas",
            "permanencia_promedio_meses":"Perm. prom (m)",
            "cumplimiento_plan_promedio":"% Plan prom"
        }),
        use_container_width=True, hide_index=True
    )

with col2:
    st.subheader("⏱️ Ventanas críticas de renuncia")
    st.caption("¿En qué mes de su carrera renuncian más los vendedores?")

    ventanas_agrupado = ventanas_df.copy()
    ventanas_agrupado["etapa"] = pd.cut(
        ventanas_agrupado["mes_numero"],
        bins=[0,3,6,12,18,100],
        labels=["Mes 1-3\n(onboarding)","Mes 4-6\n(adaptación)",
                "Mes 7-12","Mes 13-18","Mes 18+"]
    )
    etapas = ventanas_agrupado.groupby("etapa", observed=True)["renuncias"].sum().reset_index()

    fig_vent = px.bar(
        etapas,
        x="etapa", y="renuncias",
        color="etapa",
        color_discrete_sequence=["#E24B4A","#EF9F27","#B4B2A9","#B4B2A9","#639922"],
        labels={"etapa":"Etapa","renuncias":"Renuncias"},
        text="renuncias",
    )
    fig_vent.update_traces(textposition="outside", showlegend=False)
    fig_vent.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=320)
    st.plotly_chart(fig_vent, use_container_width=True)

    st.info("💡 Los primeros 6 meses concentran la mayor cantidad de bajas. "
            "Una acción temprana en este período tiene el mayor impacto.")

st.divider()

# ── Detalle de un vendedor ─────────────────────────────────────────────────
st.subheader("🔍 Detalle de vendedor")
ids_disponibles = df["id_vendedor"].tolist()
if ids_disponibles:
    id_sel = st.selectbox("Seleccioná un vendedor para ver su historial",
                          ids_disponibles,
                          format_func=lambda x: f"ID {x} — {df[df.id_vendedor==x]['nivel_riesgo'].values[0].upper()}")

    con = get_connection()
    hist = pd.read_sql(f"""
        SELECT anio, mes, pct_plan, dias_venta_cero, clientes_activos,
               total_clientes, pct_cobranza, dias_cobro
        FROM ventas_mensual
        WHERE id_vendedor = {id_sel}
        ORDER BY anio, mes
    """, con)
    con.close()

    if not hist.empty:
        hist["periodo"] = hist["anio"].astype(str) + "-" + hist["mes"].astype(str).str.zfill(2)
        hist["pct_activos"] = (hist["clientes_activos"] / hist["total_clientes"] * 100).round(1)

        fig_det = go.Figure()
        fig_det.add_trace(go.Scatter(
            x=hist["periodo"], y=hist["pct_plan"],
            name="% Plan", line=dict(color="#4A90D9", width=2),
            mode="lines+markers"
        ))
        fig_det.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
        fig_det.add_hline(y=80, line_dash="dot", line_color="#E24B4A", opacity=0.4,
                          annotation_text="80% alerta")
        fig_det.add_trace(go.Scatter(
            x=hist["periodo"], y=hist["pct_cobranza"],
            name="% Cobranza", line=dict(color="#EF9F27", width=2),
            mode="lines+markers"
        ))
        fig_det.add_trace(go.Bar(
            x=hist["periodo"], y=hist["dias_venta_cero"],
            name="Días sin venta", marker_color="#E24B4A",
            opacity=0.4, yaxis="y2"
        ))
        fig_det.update_layout(
            yaxis=dict(title="% Plan / Cobranza"),
            yaxis2=dict(title="Días sin venta", overlaying="y", side="right", range=[0,15]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(l=0,r=0,t=40,b=0),
            height=360
        )
        st.plotly_chart(fig_det, use_container_width=True)

        row = df[df.id_vendedor == id_sel].iloc[0]
        st.markdown(f"**Score:** `{row['score']}/10` — **Riesgo:** `{row['nivel_riesgo'].upper()}` — **Meses activo:** `{row['meses_activo']}`")
        if row["señales_activas"]:
            st.warning("**Señales activas:** " + " · ".join(row["señales_activas"]))
        else:
            st.success("Sin señales de riesgo detectadas en los últimos 3 meses.")
else:
    st.info("Aplicá filtros menos restrictivos para ver vendedores.")
