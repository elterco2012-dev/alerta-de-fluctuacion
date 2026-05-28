"""
pages/Costo_Rotacion.py
-----------------------
Estimación de costo de rotación por vendedor y total.

Metodología:
- Costo directo: salario de los meses perdidos + reemplazo (reclutamiento + inducción)
- Costo indirecto: pérdida estimada de cartera (clientes sin atención)
- Salarios según estructura Wurth Argentina 2025:
    Viajante/Ejecutivo < 6m  → mínimo garantizado inducción $1,400,000/mes
    Viajante/Ejecutivo ≥ 6m  → mínimo garantizado productividad $1,800,000/mes
    Televentas               → básico CCT ~$800,000/mes
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from score_engine import calcular_scores, get_connection

# ── Parámetros de costo (ajustables) ──────────────────────────────────────────
SALARIO_INDUCCION   = 1_400_000   # Viajante/Ejecutivo mes 1-6
SALARIO_PRODUCTIVO  = 1_800_000   # Viajante/Ejecutivo mes 7+
SALARIO_TELEVENTAS  = 800_000     # CCT Comercio (estimado)

MESES_REEMPLAZO     = 3           # tiempo promedio hasta nuevo vendedor operativo
PCT_CARTERA_PERDIDA = 0.15        # 15% de la cartera estimada que no regresa

# Plan mensual promedio por tipo (de datos históricos Wurth)
PLAN_MENSUAL_VIAJANTE   = 17_000_000
PLAN_MENSUAL_TELEVENTAS = 6_000_000


def salario_mensual(tipo: str, meses_activo: int) -> int:
    if "Televentas" in tipo:
        return SALARIO_TELEVENTAS
    if meses_activo <= 6:
        return SALARIO_INDUCCION
    return SALARIO_PRODUCTIVO


def plan_mensual(tipo: str) -> int:
    return PLAN_MENSUAL_TELEVENTAS if "Televentas" in tipo else PLAN_MENSUAL_VIAJANTE


def calcular_costo_rotacion(row) -> dict:
    """Calcula costo estimado de baja para un vendedor."""
    sal = salario_mensual(row["tipo"], row["meses_activo"])
    plan = plan_mensual(row["tipo"])

    # Costo directo: salario ya pagado en período improductivo + reclutamiento (1 mes)
    # + salario del nuevo en inducción (3 meses sin venta efectiva)
    costo_salario_perdido = sal * 1               # último mes improductivo
    costo_reclutamiento   = sal * 1               # publicación + entrevistas + trámites
    costo_induccion_nuevo = SALARIO_INDUCCION * MESES_REEMPLAZO  # siempre inducción

    # Costo indirecto: pérdida de cartera durante vacante + primeros meses del nuevo
    meses_sin_atencion = MESES_REEMPLAZO + 2      # vacante + rampa del nuevo
    perdida_venta = plan * meses_sin_atencion * PCT_CARTERA_PERDIDA

    total_directo   = costo_salario_perdido + costo_reclutamiento + costo_induccion_nuevo
    total_indirecto = perdida_venta
    total           = total_directo + total_indirecto

    return {
        "salario_mensual":         sal,
        "costo_salario_perdido":   costo_salario_perdido,
        "costo_reclutamiento":     costo_reclutamiento,
        "costo_induccion_nuevo":   costo_induccion_nuevo,
        "total_directo":           total_directo,
        "perdida_venta_estimada":  total_indirecto,
        "costo_total":             total,
    }


def _fmt_antiguedad(meses):
    if meses < 12:
        return f"{meses} mes{'es' if meses != 1 else ''}"
    anios = meses // 12
    resto = meses % 12
    s = f"{anios} año{'s' if anios != 1 else ''}"
    if resto:
        s += f" y {resto} mes{'es' if resto != 1 else ''}"
    return s


def _fmt_pesos(n):
    return f"${n:,.0f}".replace(",", ".")


# ── Config página ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wurth | Costo de Rotación",
    page_icon="💰",
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

.sec-header {
    font-size: 15px; font-weight: 700; color: #1a1a2e;
    margin: 8px 0 14px; display: flex; align-items: center; gap: 6px;
}
.vendor-card {
    background: white; border-radius: 10px; padding: 16px 20px;
    margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    border-left: 4px solid #E24B4A;
}
.vendor-card.alto { border-left-color: #EF9F27; }
.vendor-card.medio { border-left-color: #4A90D9; }

.nota { font-size: 11px; color: #999; font-style: italic; margin-top: 4px; }
</style>""", unsafe_allow_html=True)


# ── Nav ────────────────────────────────────────────────────────────────────────
cols_nav = st.columns([2, 1, 1, 1])
with cols_nav[0]:
    st.markdown("### 💰 Costo de Rotación")
with cols_nav[1]:
    if st.button("← Volver al inicio"):
        st.switch_page("dashboard.py")
with cols_nav[2]:
    if st.button("👤 Por Supervisor"):
        st.switch_page("pages/Supervisor.py")
with cols_nav[3]:
    pass

st.markdown("---")


# ── Datos ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _get_scores():
    return calcular_scores()

with st.spinner("Calculando..."):
    df = _get_scores()

if df.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

# Calcular costo por vendedor
costos = df.apply(calcular_costo_rotacion, axis=1, result_type="expand")
df = pd.concat([df, costos], axis=1)

# ── Filtros ────────────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
with col_f1:
    niveles = st.multiselect(
        "Nivel de riesgo",
        ["critico", "alto", "medio", "bajo"],
        default=["critico", "alto"],
    )
with col_f2:
    tipos = st.multiselect(
        "Tipo",
        ["Viajante", "Televentas"],
        default=["Viajante", "Televentas"],
    )
with col_f3:
    grupos = df["nombre_grupo"].unique().tolist()
    grupos_sel = st.multiselect("Grupo / Zona", grupos, default=[])

df_fil = df[df["nivel_riesgo"].isin(niveles) & df["tipo"].isin(tipos)]
if grupos_sel:
    df_fil = df_fil[df_fil["nombre_grupo"].isin(grupos_sel)]


# ── KPIs ───────────────────────────────────────────────────────────────────────
n_criticos = len(df[df.nivel_riesgo == "critico"])
n_altos    = len(df[df.nivel_riesgo == "alto"])

costo_criticos = df[df.nivel_riesgo == "critico"]["costo_total"].sum()
costo_todos    = df[df.nivel_riesgo.isin(["critico", "alto"])]["costo_total"].sum()
costo_promedio = df[df.nivel_riesgo.isin(["critico", "alto"])]["costo_total"].mean() if (n_criticos + n_altos) > 0 else 0

st.markdown(f"""<div class="kpi-row">
  <div class="kpi-card kr">
    <div class="kpi-value">{_fmt_pesos(costo_criticos)}</div>
    <div class="kpi-label">Exposición nivel crítico</div>
    <div class="kpi-sub">{n_criticos} vendedores en riesgo inmediato</div>
  </div>
  <div class="kpi-card ko">
    <div class="kpi-value">{_fmt_pesos(costo_todos)}</div>
    <div class="kpi-label">Exposición total (crítico + alto)</div>
    <div class="kpi-sub">{n_criticos + n_altos} vendedores en riesgo elevado</div>
  </div>
  <div class="kpi-card kb">
    <div class="kpi-value">{_fmt_pesos(costo_promedio)}</div>
    <div class="kpi-label">Costo promedio por baja</div>
    <div class="kpi-sub">Directo + pérdida de cartera estimada</div>
  </div>
  <div class="kpi-card kg">
    <div class="kpi-value">{len(df_fil)}</div>
    <div class="kpi-label">Vendedores en vista actual</div>
    <div class="kpi-sub">Costo total: {_fmt_pesos(df_fil['costo_total'].sum())}</div>
  </div>
</div>""", unsafe_allow_html=True)


# ── Gráfico por grupo ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📊 Exposición por zona</div>', unsafe_allow_html=True)

por_grupo = (
    df[df.nivel_riesgo.isin(["critico", "alto"])]
    .groupby("nombre_grupo")
    .agg(
        n_riesgo=("id_vendedor", "count"),
        costo_total=("costo_total", "sum"),
        score_max=("score", "max"),
    )
    .sort_values("costo_total", ascending=True)
    .tail(15)
)

if not por_grupo.empty:
    fig = go.Figure(go.Bar(
        x=por_grupo["costo_total"],
        y=por_grupo.index,
        orientation="h",
        marker_color=["#E24B4A" if s >= 8 else "#EF9F27" for s in por_grupo["score_max"]],
        text=[f"{_fmt_pesos(v)}" for v in por_grupo["costo_total"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Exposición: $%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        height=max(300, len(por_grupo) * 38),
        margin=dict(l=0, r=120, t=10, b=10),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(tickfont=dict(size=12)),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Tabla de vendedores ────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">🧾 Detalle por vendedor</div>', unsafe_allow_html=True)

if df_fil.empty:
    st.info("No hay vendedores con los filtros seleccionados.")
else:
    tabla = df_fil[[
        "nombre", "id_vendedor", "tipo", "nombre_grupo", "supervisor",
        "meses_activo", "score", "nivel_riesgo",
        "salario_mensual", "costo_induccion_nuevo", "perdida_venta_estimada", "costo_total"
    ]].copy()

    tabla["antigüedad"]       = tabla["meses_activo"].apply(_fmt_antiguedad)
    tabla["salario_mensual"]  = tabla["salario_mensual"].apply(_fmt_pesos)
    tabla["reemplazo"]        = tabla["costo_induccion_nuevo"].apply(_fmt_pesos)
    tabla["pérdida cartera"]  = tabla["perdida_venta_estimada"].apply(_fmt_pesos)
    tabla["COSTO TOTAL"]      = tabla["costo_total"].apply(_fmt_pesos)
    tabla["nivel"]            = tabla["nivel_riesgo"].str.upper()

    st.dataframe(
        tabla[[
            "nombre", "id_vendedor", "tipo", "nombre_grupo", "supervisor",
            "antigüedad", "score", "nivel",
            "salario_mensual", "reemplazo", "pérdida cartera", "COSTO TOTAL"
        ]].rename(columns={
            "nombre": "Vendedor",
            "id_vendedor": "ID",
            "tipo": "Tipo",
            "nombre_grupo": "Zona",
            "supervisor": "Supervisor",
            "antigüedad": "Antigüedad",
            "score": "Score",
            "nivel": "Nivel",
            "salario_mensual": "Salario/mes",
            "reemplazo": "Reemplazo",
            "pérdida cartera": "Pérd. cartera",
            "COSTO TOTAL": "Costo total",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Exportar CSV
    csv = tabla.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇ Exportar CSV",
        csv,
        file_name=f"costo_rotacion_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


# ── Nota metodológica ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("Metodología de cálculo"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
**Costos directos incluidos:**
- Último mes improductivo del vendedor saliente
- Reclutamiento (publicación, entrevistas, trámites): 1 mes salario
- Inducción del nuevo vendedor: {MESES_REEMPLAZO} meses a salario mínimo garantizado

**Salarios base:**
- Viajante/Ejecutivo en inducción (0-6 meses): {_fmt_pesos(SALARIO_INDUCCION)}/mes
- Viajante/Ejecutivo productivo (7+ meses): {_fmt_pesos(SALARIO_PRODUCTIVO)}/mes
- Televentas (CCT Comercio estimado): {_fmt_pesos(SALARIO_TELEVENTAS)}/mes
""")
    with col2:
        st.markdown(f"""
**Costo indirecto — pérdida de cartera:**
- Período sin atención: {MESES_REEMPLAZO + 2} meses (vacante + rampa del nuevo)
- % de la cartera estimado que no regresa: {int(PCT_CARTERA_PERDIDA * 100)}%
- Plan mensual Viajante referencia: {_fmt_pesos(PLAN_MENSUAL_VIAJANTE)}
- Plan mensual Televentas referencia: {_fmt_pesos(PLAN_MENSUAL_TELEVENTAS)}

*Los valores de pérdida de cartera son estimaciones conservadoras.*
*El porcentaje real puede variar según el perfil de clientes de cada zona.*
""")
