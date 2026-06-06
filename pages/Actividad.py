"""
pages/Actividad.py
------------------
Resumen de actividad Televentas (llamadas) y Viajantes (visitas):
Target oficial vs Plan real vs Ejecutado vs Cumplimiento.
"""

import streamlit as st
import pandas as pd
import sqlite3
import os, sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from snippets_v3 import banner, fmt_num, hero_kpi, stat_kpi, fmt_pct, page_header, HIDE_CHROME_CSS

TARGET_TELEVENTAS   = 80   # llamadas planificadas por empresa / día
TARGET_VIAJANTES    = 15   # visitas planificadas por empresa / día
DIAS_HABILES_MES    = 20

st.set_page_config(
    page_title="Wurth | Actividad Comercial",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_v3_css = os.path.join(os.path.dirname(__file__), '..', 'assets', 'dashboard-v3.css')
st.markdown(f"<style>{open(_v3_css, encoding='utf-8').read()}</style>", unsafe_allow_html=True)
st.markdown(HIDE_CHROME_CSS, unsafe_allow_html=True)

st.markdown(page_header("Wurth Argentina &mdash; Actividad Comercial", "/Actividad"),
            unsafe_allow_html=True)

# ── Acceso ────────────────────────────────────────────────────────────────────
import acceso as _acc
_usuario = _acc.requerir_acceso()

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
              AND (am.anio * 100 + am.mes) <= CAST(strftime('%Y%m', 'now') AS INTEGER)
              AND (v.fecha_ingreso IS NULL OR v.fecha_ingreso <= date('now'))
              AND am.id_vendedor != 9800
            ORDER BY am.anio DESC, am.mes DESC
        """, con)
    except Exception:
        df = pd.DataFrame()
    con.close()
    return df

df_all = cargar_actividad()

# Filtrar al alcance del usuario.
if not _usuario["ve_todo"] and _usuario["supervisores"]:
    df_all = df_all[df_all["supervisor"].isin(set(_usuario["supervisores"]))]

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


# ── KPIs y Banner ──────────────────────────────────────────────────────────────
tel_plan_tot = df_tel["planificadas_llamadas"].sum()
tel_ejec_tot = df_tel["llamadas"].sum()
via_plan_tot = df_via["planificadas_visitas"].sum()
via_ejec_tot = df_via["visitas"].sum()
tel_cumpl    = _pct(tel_ejec_tot, tel_plan_tot)
via_cumpl    = _pct(via_ejec_tot, via_plan_tot)
min_cumpl    = min(tel_cumpl, via_cumpl) if tel_plan_tot > 0 and via_plan_tot > 0 else (tel_cumpl or via_cumpl)

col_hero, col_stats = st.columns([1, 2.2])
with col_hero:
    st.markdown(hero_kpi(
        "Cumplimiento del plan",
        fmt_pct(min_cumpl),
        f"Peor entre Televentas y Viajantes — período {periodo_sel}",
        red=(min_cumpl < 50),
    ), unsafe_allow_html=True)
with col_stats:
    _s1, _s2, _s3, _s4 = st.columns(4)
    with _s1:
        st.markdown(stat_kpi("Televentas activos", fmt_num(df_tel["id_vendedor"].nunique())),
                    unsafe_allow_html=True)
    with _s2:
        st.markdown(stat_kpi("Viajantes activos", fmt_num(df_via["id_vendedor"].nunique())),
                    unsafe_allow_html=True)
    with _s3:
        st.markdown(stat_kpi("Cumpl. Televentas", fmt_pct(tel_cumpl)), unsafe_allow_html=True)
    with _s4:
        st.markdown(stat_kpi("Cumpl. Viajantes", fmt_pct(via_cumpl)), unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

if min_cumpl < 50:
    st.markdown(banner("📞",
        f"Cumplimiento bajo: {fmt_num(min_cumpl)}% del plan de actividad",
        f"Televentas {fmt_num(tel_cumpl)}% · Viajantes {fmt_num(via_cumpl)}% — período {periodo_sel}",
        "red"), unsafe_allow_html=True)
elif min_cumpl < 75:
    st.markdown(banner("🟠",
        f"Actividad comercial {fmt_num(min_cumpl)}% del plan",
        f"Televentas {fmt_num(tel_cumpl)}% · Viajantes {fmt_num(via_cumpl)}% — período {periodo_sel}",
        "orange"), unsafe_allow_html=True)
else:
    st.markdown(banner("✅",
        f"Actividad en plan: {fmt_num(min_cumpl)}%",
        f"Televentas {fmt_num(tel_cumpl)}% · Viajantes {fmt_num(via_cumpl)}% — período {periodo_sel}",
        "green"), unsafe_allow_html=True)

# ── Resumen del período ───────────────────────────────────────────────────────

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
        _t = t_tel[["periodo","n","plan","ejec","espontaneas","total","cumpl_%"]].copy()
        for _c in ["plan","ejec","espontaneas","total"]:
            _t[_c] = _t[_c].apply(lambda x: fmt_num(int(x), 0))
        st.dataframe(
            _t.rename(columns={
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
        _t = t_via[["periodo","n","plan","ejec","espontaneas","total","cumpl_%"]].copy()
        for _c in ["plan","ejec","espontaneas","total"]:
            _t[_c] = _t[_c].apply(lambda x: fmt_num(int(x), 0))
        st.dataframe(
            _t.rename(columns={
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
        lambda r: int(round(r[col_total] / r[col_plan] * 100)) if r[col_plan] > 0 else 0,
        axis=1,
    )
    df_r["espontaneas"] = df_r[col_total] - df_r[col_ejec]
    df_r["Vendedor"] = df_r["nombre"] + " (" + df_r["id_vendedor"].astype(int).astype(str) + ")"
    return (
        df_r[["Vendedor", "supervisor", "nombre_grupo", col_plan, col_ejec, "espontaneas", col_total, "cumpl_%"]]
        .sort_values("cumpl_%", ascending=True)
        .rename(columns={
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
        _r = df_rank_tel.copy()
        for _c in ["Planificadas", "Del plan", "Espontáneas", "Total"]:
            _r[_c] = _r[_c].apply(lambda x: fmt_num(int(x), 0))
        st.dataframe(
            _r.style.map(_color_cumpl, subset=["Cumpl. %"]),
            use_container_width=True, hide_index=True,
        )
        st.caption("Rojo = < 25% del plan (señal de alerta en score). Verde = ≥ 70%.")

with tab2:
    df_rank_via = ranking_df(df_via, "planificadas_visitas", "visitadas_schedule", "visitas")
    if df_rank_via.empty:
        st.info("Sin datos Viajantes para el período.")
    else:
        _r = df_rank_via.copy()
        for _c in ["Planificadas", "Del plan", "Espontáneas", "Total"]:
            _r[_c] = _r[_c].apply(lambda x: fmt_num(int(x), 0))
        st.dataframe(
            _r.style.map(_color_cumpl, subset=["Cumpl. %"]),
            use_container_width=True, hide_index=True,
        )
        st.caption("Rojo = < 25% del plan (señal de alerta en score). Verde = ≥ 70%.")
