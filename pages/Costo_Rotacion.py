"""
pages/Costo_Rotacion.py
-----------------------
Estimación de costo de rotación por vendedor y total.

Metodología:
- Costo directo: último mes improductivo + reclutamiento + inducción del nuevo
- Costo indirecto: pérdida parcial de cartera durante cobertura y rampa del nuevo
  * Cuando un vendedor de zona se va, televentas actúa de cobertura mientras se
    contrata el reemplazo (1-2 meses). El reemplazo tarda ~2 meses en ser productivo.
  * La pérdida de cartera es menor que en modelos sin cobertura, porque los clientes
    siguen siendo contactados por televentas.
- Salarios según estructura Wurth Argentina 2025.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from score_engine import calcular_scores, get_connection
from snippets_v3 import banner, hero_kpi, stat_kpi, fmt_pesos_corto, fmt_num

# ── Parámetros de costo (ajustables) ──────────────────────────────────────────
SALARIO_INDUCCION   = 1_400_000   # Viajante/Ejecutivo mes 1-6
SALARIO_PRODUCTIVO  = 1_800_000   # Viajante/Ejecutivo mes 7+
SALARIO_TELEVENTAS  = 1_215_298   # CCT Comercio (actualizar mensualmente)

# Modelo de cobertura Wurth: televentas cubre la zona hasta que entra el nuevo
MESES_HASTA_NUEVO      = 1.5    # meses promedio hasta que ingresa el nuevo vendedor
MESES_RAMPA_NUEVO      = 2      # meses hasta que el nuevo vendedor alcanza productividad plena
PCT_PERDIDA_COBERTURA  = 0.08   # % cartera que se pierde durante cobertura por televentas
PCT_PERDIDA_RAMPA      = 0.12   # % cartera que se pierde en rampa del nuevo vendedor

# Fallbacks si no hay datos reales de plan
_PLAN_FALLBACK_VIAJANTE   = 17_000_000
_PLAN_FALLBACK_TELEVENTAS =  6_000_000


@st.cache_data(ttl=600)
def _cargar_plan_promedio() -> dict:
    """Calcula el plan mensual promedio por tipo desde los últimos 3 meses con datos."""
    con = get_connection()
    df = pd.read_sql("""
        SELECT v.tipo, AVG(vm.plan) as plan_prom
        FROM ventas_mensual vm
        JOIN vendedores v ON vm.id_vendedor = v.id_vendedor
        WHERE vm.plan > 0
          AND vm.anio * 12 + vm.mes >= (
              SELECT MAX(anio * 12 + mes) - 2 FROM ventas_mensual
          )
        GROUP BY v.tipo
    """, con)
    con.close()
    result = {}
    for _, row in df.iterrows():
        result[row["tipo"]] = int(row["plan_prom"])
    return result


def salario_mensual(tipo: str, meses_activo: int) -> int:
    if "Televentas" in tipo:
        return SALARIO_TELEVENTAS
    if meses_activo <= 6:
        return SALARIO_INDUCCION
    return SALARIO_PRODUCTIVO


def calcular_costo_rotacion(row, planes: dict | None = None) -> dict:
    """Calcula costo estimado de baja para un vendedor."""
    sal = salario_mensual(row["tipo"], row["meses_activo"])

    # Plan real del período o fallback
    if planes:
        plan = planes.get(row["tipo"]) or (
            _PLAN_FALLBACK_TELEVENTAS if "Televentas" in row["tipo"] else _PLAN_FALLBACK_VIAJANTE
        )
    else:
        plan = _PLAN_FALLBACK_TELEVENTAS if "Televentas" in row["tipo"] else _PLAN_FALLBACK_VIAJANTE

    # Costo directo
    costo_salario_perdido = sal * 1                        # último mes improductivo
    costo_reclutamiento   = sal * 1                        # publicación + entrevistas
    costo_induccion_nuevo = SALARIO_INDUCCION * int(round(MESES_HASTA_NUEVO + MESES_RAMPA_NUEVO))

    # Costo indirecto: cobertura televentas + rampa nuevo (con modelo de cobertura Wurth)
    perdida_cobertura = plan * MESES_HASTA_NUEVO * PCT_PERDIDA_COBERTURA
    perdida_rampa     = plan * MESES_RAMPA_NUEVO  * PCT_PERDIDA_RAMPA
    perdida_venta     = perdida_cobertura + perdida_rampa

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

_v3_css = os.path.join(os.path.dirname(__file__), '..', 'assets', 'dashboard-v3.css')
st.markdown(f"<style>{open(_v3_css).read()}</style>", unsafe_allow_html=True)

st.markdown("""<style>
[data-testid="stSidebar"]   { display: none; }
[data-testid="stHeader"]    { display: none; }
[data-testid="stToolbar"]   { display: none; }
.stDeployButton             { display: none; }
.block-container { padding: 2.5rem 2.5rem 4rem !important; max-width: 100% !important; }
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


st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center;
            margin-bottom:20px; padding-bottom:14px; border-bottom:1px solid #eee;">
  <div style="font-size:20px; font-weight:800; color:#1a1a2e;">💰 Costo de Rotación — Wurth Argentina</div>
  <div style="font-size:13px; display:flex; gap:20px; flex-wrap:wrap;">
    <a href="/"               target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">🏠 Inicio</a>
    <a href="/Supervisor"     target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">👤 Por supervisor</a>
    <a href="/Intervenciones" target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">📝 Intervenciones</a>
    <a href="/Historial"      target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">📈 Historial</a>
    <a href="/Actividad"      target="_self" style="color:#4A90D9;text-decoration:none;white-space:nowrap;">📞 Actividad</a>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Datos ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _get_scores():
    return calcular_scores()

with st.spinner("Calculando..."):
    df     = _get_scores()
    planes = _cargar_plan_promedio()

if df.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

# Calcular costo por vendedor usando plan real del período actual
costos = df.apply(lambda row: calcular_costo_rotacion(row, planes), axis=1, result_type="expand")
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

col_hero, col_stats = st.columns([1, 2.2])
with col_hero:
    st.markdown(hero_kpi("Exposición nivel crítico", fmt_pesos_corto(costo_criticos),
                         f"{n_criticos} vendedor{'es' if n_criticos!=1 else ''} en riesgo inmediato",
                         red=True),
                unsafe_allow_html=True)
with col_stats:
    _s1, _s2, _s3 = st.columns(3)
    with _s1:
        st.markdown(stat_kpi("Exposición crítico + alto",
                             fmt_pesos_corto(costo_todos)), unsafe_allow_html=True)
    with _s2:
        st.markdown(stat_kpi("Costo promedio por baja",
                             fmt_pesos_corto(costo_promedio)), unsafe_allow_html=True)
    with _s3:
        st.markdown(stat_kpi("Vendedores en vista",
                             f"{fmt_num(len(df_fil))} · {fmt_pesos_corto(df_fil['costo_total'].sum())}"),
                    unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# Banner
if n_criticos > 0:
    st.markdown(banner("💰",
        f"Exposición inmediata: {fmt_pesos_corto(costo_criticos)}",
        f"{n_criticos} vendedor{'es críticos' if n_criticos!=1 else ' crítico'} representan este costo si se van. "
        "Cada reunión esta semana puede evitarlo.", "red"),
        unsafe_allow_html=True)
elif n_altos > 0:
    st.markdown(banner("🟠",
        f"Exposición total: {fmt_pesos_corto(costo_todos)}",
        f"{n_altos} vendedor{'es en nivel alto' if n_altos!=1 else ' en nivel alto'} con seguimiento activo pueden reducir esta cifra.", "orange"),
        unsafe_allow_html=True)
else:
    st.markdown(banner("✅", "Sin exposición crítica en este momento",
        "No hay vendedores en nivel crítico o alto según el filtro actual.", "green"),
        unsafe_allow_html=True)


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
_plan_v  = planes.get("Viajante",   _PLAN_FALLBACK_VIAJANTE)
_plan_tv = planes.get("Televentas", _PLAN_FALLBACK_TELEVENTAS)
_meses_ind = int(round(MESES_HASTA_NUEVO + MESES_RAMPA_NUEVO))
_tot_dir_tv = SALARIO_TELEVENTAS * 2 + SALARIO_INDUCCION * _meses_ind
_perd_cob   = _plan_tv * MESES_HASTA_NUEVO * PCT_PERDIDA_COBERTURA
_perd_rampa = _plan_tv * MESES_RAMPA_NUEVO  * PCT_PERDIDA_RAMPA

st.markdown("---")
with st.expander("Metodología de cálculo — ¿de dónde salen los números?"):
    st.caption(
        "Los salarios se actualizan mensualmente en pages/Costo_Rotacion.py. "
        "El plan mensual se calcula automáticamente del promedio real de los últimos 3 meses en Informix. "
        "El modelo de cobertura refleja que televentas actúa de cobertura mientras se contrata el reemplazo."
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
**Costos directos — ejemplo Televentas:**

| Concepto | Cálculo | Total |
|---|---|---|
| Último mes improductivo | {_fmt_pesos(SALARIO_TELEVENTAS)} × 1 mes | {_fmt_pesos(SALARIO_TELEVENTAS)} |
| Reclutamiento | {_fmt_pesos(SALARIO_TELEVENTAS)} × 1 mes | {_fmt_pesos(SALARIO_TELEVENTAS)} |
| Inducción nuevo | {_fmt_pesos(SALARIO_INDUCCION)} × {_meses_ind} meses | {_fmt_pesos(SALARIO_INDUCCION * _meses_ind)} |
| **Total directo** | | **{_fmt_pesos(_tot_dir_tv)}** |

**Salarios base:**
- Viajante en inducción (0-6m): {_fmt_pesos(SALARIO_INDUCCION)}/mes
- Viajante productivo (7+m): {_fmt_pesos(SALARIO_PRODUCTIVO)}/mes
- Televentas CCT: {_fmt_pesos(SALARIO_TELEVENTAS)}/mes
""")
    with col2:
        st.markdown(f"""
**Costo indirecto — pérdida parcial de cartera (modelo con cobertura Wurth):**

Cuando un vendedor se va, **televentas cubre la zona** hasta que ingresa el reemplazo.
La pérdida es menor que en modelos sin cobertura, pero no es cero:

| Período | Duración | Pérdida estimada | Total |
|---|---|---|---|
| Cobertura televentas | {MESES_HASTA_NUEVO:.1f} m | {int(PCT_PERDIDA_COBERTURA*100)}% del plan/mes | {_fmt_pesos(_perd_cob)} |
| Rampa nuevo vendedor | {MESES_RAMPA_NUEVO:.0f} m | {int(PCT_PERDIDA_RAMPA*100)}% del plan/mes | {_fmt_pesos(_perd_rampa)} |
| **Pérdida total** | | | **{_fmt_pesos(_perd_cob + _perd_rampa)}** |

**Plan promedio actual (últimos 3 meses):**
- Viajante: {_fmt_pesos(_plan_v)}/mes
- Televentas: {_fmt_pesos(_plan_tv)}/mes

*Ajustar PCT\\_PERDIDA\\_COBERTURA y PCT\\_PERDIDA\\_RAMPA según experiencia histórica.*
""")
