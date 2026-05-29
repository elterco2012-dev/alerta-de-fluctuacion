"""
pages/Actividad.py
------------------
Resumen de actividad Televentas (llamadas) y Viajantes (visitas):
Target oficial vs Plan real vs Ejecutado vs Cumplimiento.
"""

import streamlit as st
import pandas as pd
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

TARGET_TELEVENTAS   = 80   # llamadas planificadas por empresa / día
TARGET_VIAJANTES    = 15   # visitas planificadas por empresa / día
DIAS_HABILES_MES    = 20

st.set_page_config(
    page_title="Wurth | Actividad Comercial",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center;
            margin-bottom:20px; padding-bottom:14px; border-bottom:1px solid #eee;">
  <div style="font-size:20px; font-weight:800; color:#1a1a2e;">
    Wurth Argentina &mdash; Actividad Comercial
  </div>
  <div style="font-size:13px; display:flex; gap:20px;">
    <a href="/"              target="_self" style="color:#4A90D9;text-decoration:none;">🏠 Inicio</a>
    <a href="/Supervisor"    target="_self" style="color:#4A90D9;text-decoration:none;">👤 Por supervisor</a>
    <a href="/Intervenciones" target="_self" style="color:#4A90D9;text-decoration:none;">📝 Intervenciones</a>
    <a href="/Historial"     target="_self" style="color:#4A90D9;text-decoration:none;">📈 Historial</a>
    <a href="/Costo_Rotacion" target="_self" style="color:#4A90D9;text-decoration:none;">💰 Costo de rotación</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_actividad():
    con = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("""
            SELECT am.id_vendedor, am.anio, am.mes,
                   am.llamadas, am.gestionadas_llamadas, am.planificadas_llamadas,
                   am.visitas, am.visitadas_schedule, am.planificadas_visitas,
                   v.tipo, v.nombre, v.nombre_grupo, v.supervisor
            FROM actividad_mensual am
            JOIN vendedores v ON am.id_vendedor = v.id_vendedor
            WHERE v.activo = 1
              AND v.nombre NOT IN (
                  SELECT DISTINCT supervisor FROM vendedores
                  WHERE supervisor IS NOT NULL AND supervisor != ''
              )
            ORDER BY am.anio DESC, am.mes DESC
        """, con)
    except Exception:
        df = pd.DataFrame()
    con.close()
    return df

df_all = cargar_actividad()

if df_all.empty:
    st.warning("No hay datos en actividad_mensual. Ejecutá `sincronizar_reactor.py` primero.")
    st.stop()

df_all["periodo"] = df_all["anio"].astype(str) + "-" + df_all["mes"].astype(str).str.zfill(2)

periodos_disp = sorted(df_all["periodo"].unique(), reverse=True)

# ── Selector de período ───────────────────────────────────────────────────────
col_sel, _ = st.columns([2, 6])
with col_sel:
    periodo_sel = st.selectbox("Período", periodos_disp)

df = df_all[df_all["periodo"] == periodo_sel].copy()

df_tel = df[df["tipo"] == "Televentas"].copy()
df_via = df[df["tipo"] == "Viajante"].copy()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _safe_mean(series):
    return series.mean() if len(series) else 0.0

def _pct(num, den):
    return round(num / den * 100) if den > 0 else 0


# ── KPIs globales del período ─────────────────────────────────────────────────
st.markdown("### Resumen del período")

# Televentas
tel_vendedores    = df_tel["id_vendedor"].nunique()
tel_plan_dia      = _safe_mean(df_tel["planificadas_llamadas"]) / DIAS_HABILES_MES
tel_ejec_plan_dia = _safe_mean(df_tel["gestionadas_llamadas"])  / DIAS_HABILES_MES
tel_ejec_tot_dia  = _safe_mean(df_tel["llamadas"])              / DIAS_HABILES_MES
tel_cumpl_plan    = _pct(
    df_tel["llamadas"].sum(),          # total real (plan + espontáneas)
    df_tel["planificadas_llamadas"].sum()
)

# Viajantes
via_vendedores    = df_via["id_vendedor"].nunique()
via_plan_dia      = _safe_mean(df_via["planificadas_visitas"])  / DIAS_HABILES_MES
via_ejec_plan_dia = _safe_mean(df_via["visitadas_schedule"])    / DIAS_HABILES_MES
via_ejec_tot_dia  = _safe_mean(df_via["visitas"])               / DIAS_HABILES_MES
via_cumpl_plan    = _pct(
    df_via["visitas"].sum(),           # total real (plan + espontáneas)
    df_via["planificadas_visitas"].sum()
)

resumen_data = {
    "Tipo": ["📞 Televentas", "🚗 Viajantes"],
    "Vendedores con datos": [tel_vendedores, via_vendedores],
    "Target empresa / día": [TARGET_TELEVENTAS, TARGET_VIAJANTES],
    "Plan real / día (prom)": [round(tel_plan_dia), round(via_plan_dia)],
    "Ejecutadas del plan / día": [round(tel_ejec_plan_dia), round(via_ejec_plan_dia)],
    "Espontáneas / día": [round(tel_ejec_tot_dia - tel_ejec_plan_dia), round(via_ejec_tot_dia - via_ejec_plan_dia)],
    "Total / día": [round(tel_ejec_tot_dia), round(via_ejec_tot_dia)],
    "Cumplimiento (%)": [tel_cumpl_plan, via_cumpl_plan],
}

df_resumen = pd.DataFrame(resumen_data).set_index("Tipo")

def colorear_cumplimiento(val):
    if isinstance(val, float) and val < 30:
        return "background-color:#ffe0e0; color:#c0392b; font-weight:bold"
    elif isinstance(val, float) and val < 50:
        return "background-color:#fff3cd; color:#856404"
    return ""

st.dataframe(
    df_resumen.style.map(colorear_cumplimiento, subset=["Cumplimiento (%)"]),
    use_container_width=True,
)

st.caption(
    f"Target empresa: {TARGET_TELEVENTAS} llamadas/día (Televentas) · "
    f"{TARGET_VIAJANTES} visitas/día (Viajantes). "
    f"Base: {DIAS_HABILES_MES} días hábiles/mes. "
    "Espontáneas = gestiones/visitas realizadas sin una planificación previa en Reactor. "
    "Cumplimiento incluye espontáneas porque el objetivo es hablar con el cliente, no solo ejecutar el plan."
)

# ── Tendencia mes a mes ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Tendencia mensual")

def tendencia_tipo(df_tipo, col_plan, col_ejec, col_total, label):
    grp = (
        df_tipo.groupby("periodo")
        .agg(
            plan=(col_plan, "sum"),
            ejec=(col_ejec, "sum"),
            total=(col_total, "sum"),
            n=("id_vendedor", "nunique"),
        )
        .reset_index()
        .sort_values("periodo")
    )
    grp["cumpl_%"] = grp.apply(
        lambda r: round(r["total"] / r["plan"] * 100) if r["plan"] > 0 else 0, axis=1
    )
    grp["espontaneas"] = grp["total"] - grp["ejec"]
    return grp

t_tel = tendencia_tipo(df_tel, "planificadas_llamadas", "gestionadas_llamadas", "llamadas", "Televentas")
t_via = tendencia_tipo(df_via, "planificadas_visitas",  "visitadas_schedule",   "visitas",  "Viajantes")

c1, c2 = st.columns(2)
with c1:
    st.markdown("**📞 Televentas — Llamadas**")
    if not t_tel.empty:
        st.dataframe(
            t_tel[["periodo","n","plan","ejec","espontaneas","total","cumpl_%"]]
            .rename(columns={
                "periodo":"Período","n":"Vendedores",
                "plan":"Planificadas","ejec":"Del plan",
                "espontaneas":"Espontáneas","total":"Total","cumpl_%":"Cumpl. %"
            }),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Sin datos Televentas.")

with c2:
    st.markdown("**🚗 Viajantes — Visitas**")
    if not t_via.empty:
        st.dataframe(
            t_via[["periodo","n","plan","ejec","espontaneas","total","cumpl_%"]]
            .rename(columns={
                "periodo":"Período","n":"Vendedores",
                "plan":"Planificadas","ejec":"Del plan",
                "espontaneas":"Espontáneas","total":"Total","cumpl_%":"Cumpl. %"
            }),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Sin datos Viajantes.")

# ── Ranking por vendedor ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Ranking por vendedor — período seleccionado")

tab1, tab2 = st.tabs(["📞 Televentas", "🚗 Viajantes"])

def ranking_df(df_tipo, col_plan, col_ejec, col_total):
    if df_tipo.empty:
        return pd.DataFrame()
    df_r = df_tipo.copy()
    df_r["cumpl_%"] = df_r.apply(
        lambda r: round(r[col_total] / r[col_plan] * 100) if r[col_plan] > 0 else None,
        axis=1,
    )
    df_r["espontaneas"] = df_r[col_total] - df_r[col_ejec]
    return (
        df_r[["nombre", "supervisor", "nombre_grupo", col_plan, col_ejec, "espontaneas", col_total, "cumpl_%"]]
        .sort_values("cumpl_%", ascending=True)
        .rename(columns={
            "nombre": "Vendedor",
            "supervisor": "Supervisor",
            "nombre_grupo": "Grupo",
            col_plan: "Planificadas",
            col_ejec: "Del plan",
            "espontaneas": "Espontáneas",
            col_total: "Total",
            "cumpl_%": "Cumpl. %",
        })
    )

def _color_cumpl(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if val < 25:
        return "background-color:#ffe0e0; color:#c0392b; font-weight:bold"
    elif val < 50:
        return "background-color:#fff3cd"
    elif val >= 70:
        return "background-color:#d4edda; color:#155724"
    return ""

with tab1:
    df_rank_tel = ranking_df(df_tel, "planificadas_llamadas", "gestionadas_llamadas", "llamadas")
    if df_rank_tel.empty:
        st.info("Sin datos Televentas para el período.")
    else:
        st.dataframe(
            df_rank_tel.style.map(_color_cumpl, subset=["Cumpl. %"]),
            use_container_width=True, hide_index=True,
        )
        st.caption("Rojo = < 25% del plan (señal de alerta en score). Verde = ≥ 70%.")

with tab2:
    df_rank_via = ranking_df(df_via, "planificadas_visitas", "visitadas_schedule", "visitas")
    if df_rank_via.empty:
        st.info("Sin datos Viajantes para el período.")
    else:
        st.dataframe(
            df_rank_via.style.map(_color_cumpl, subset=["Cumpl. %"]),
            use_container_width=True, hide_index=True,
        )
        st.caption("Rojo = < 25% del plan (señal de alerta en score). Verde = ≥ 70%.")
