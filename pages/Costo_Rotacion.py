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
from snippets_v3 import banner, hero_kpi, stat_kpi, fmt_pesos_corto, fmt_num, page_header

# ── Parámetros de costo (ajustables) ──────────────────────────────────────────
SALARIO_INDUCCION   = 1_400_000   # Viajante/Ejecutivo mes 1-6
SALARIO_PRODUCTIVO  = 1_800_000   # Viajante/Ejecutivo mes 7+
SALARIO_TELEVENTAS  = 1_215_298   # CCT Comercio (actualizar mensualmente)

# Modelo de cobertura Wurth: televentas cubre la zona hasta que entra el nuevo
MESES_HASTA_NUEVO      = 1.5    # meses promedio hasta que ingresa el nuevo vendedor
MESES_RAMPA_NUEVO      = 2      # meses hasta que el nuevo vendedor alcanza productividad plena
PCT_PERDIDA_COBERTURA  = 0.08   # % cartera que se pierde durante cobertura por televentas
PCT_PERDIDA_RAMPA      = 0.12   # % cartera que se pierde en rampa del nuevo vendedor

# Plan mensual escalonado (igual para Viajante y Televentas en los primeros 6 meses).
# Para el cálculo de pérdida de cartera: se usa el plan del vendedor que se va,
# no un promedio de todos los vendedores del tipo.
_PLAN_VIAJANTE_VETERANO   = 20_740_007   # mes 7+ de calle
_PLAN_TELEVENTAS_VETERANO = 16_351_480   # mes 7+ de televentas
_PLAN_ESCALON = {
    (1, 2): 9_450_000,
    (3, 4): 11_550_000,
    (5, 6): 13_650_000,
}


def _plan_por_tenure(tipo: str, meses_activo: int) -> int:
    """Plan mensual del vendedor según su antigüedad al momento de calcular el costo."""
    if meses_activo >= 7:
        return _PLAN_TELEVENTAS_VETERANO if "Televentas" in tipo else _PLAN_VIAJANTE_VETERANO
    for (lo, hi), plan in _PLAN_ESCALON.items():
        if lo <= meses_activo <= hi:
            return plan
    return _PLAN_ESCALON[(5, 6)]   # fallback conservador para mes 6 exacto


@st.cache_data(ttl=600)
def _cargar_bajas_historicas() -> pd.DataFrame:
    """Bajas reales con fecha de egreso e ingreso, para costear la rotación que YA
    ocurrió (no la proyectada). Calcula la antigüedad al momento del egreso."""
    con = get_connection()
    df = pd.read_sql("""
        SELECT id_vendedor, nombre, tipo, nombre_grupo, supervisor,
               fecha_ingreso, fecha_egreso, motivo_egreso
        FROM vendedores
        WHERE activo = 0
          AND fecha_egreso  IS NOT NULL AND fecha_egreso  <> ''
          AND fecha_ingreso IS NOT NULL AND fecha_ingreso <> ''
    """, con)
    con.close()
    if df.empty:
        return df
    df["fecha_egreso"]  = pd.to_datetime(df["fecha_egreso"],  errors="coerce")
    df["fecha_ingreso"] = pd.to_datetime(df["fecha_ingreso"], errors="coerce")
    df = df.dropna(subset=["fecha_egreso", "fecha_ingreso"])
    # Antigüedad al egreso (mínimo 1 mes) → alimenta la misma fórmula de costo.
    df["meses_activo"] = (((df["fecha_egreso"] - df["fecha_ingreso"]).dt.days / 30.44)
                          .round().clip(lower=1).astype(int))
    df["periodo_egreso"] = df["fecha_egreso"].dt.to_period("M").astype(str)
    return df


def salario_mensual(tipo: str, meses_activo: int) -> int:
    if "Televentas" in tipo:
        return SALARIO_TELEVENTAS
    if meses_activo <= 6:
        return SALARIO_INDUCCION
    return SALARIO_PRODUCTIVO


def calcular_costo_rotacion(row) -> dict:
    """Calcula costo estimado de baja para un vendedor."""
    sal  = salario_mensual(row["tipo"], row["meses_activo"])
    plan = _plan_por_tenure(row["tipo"], int(row["meses_activo"]))

    # Costo directo
    costo_salario_perdido = sal * 1                        # último mes improductivo
    costo_reclutamiento   = sal * 1                        # publicación + entrevistas
    # Inducción: sueldo del reemplazo mientras YA está contratado pero todavía no
    # rinde (rampa). NO se cuenta MESES_HASTA_NUEVO: en la vacante no se paga sueldo
    # (esa pérdida ya está en perdida_cobertura). Contarla acá duplicaba el costo.
    costo_induccion_nuevo = SALARIO_INDUCCION * MESES_RAMPA_NUEVO

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
st.markdown(f"<style>{open(_v3_css, encoding='utf-8').read()}</style>", unsafe_allow_html=True)

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


# ── Acceso (solo Gerencia) ────────────────────────────────────────────────────
import acceso as _acc
_usuario = _acc.requerir_acceso(roles=["gerencia", "rrhh"])

st.markdown(page_header("💰 Costo de Rotación — Wurth Argentina", "/Costo_Rotacion"),
            unsafe_allow_html=True)


# ── Datos ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _get_scores():
    return calcular_scores()

with st.spinner("Calculando..."):
    df = _get_scores()

if df.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# COSTO HISTÓRICO — cuánto YA costó la rotación (bajas reales)
# ══════════════════════════════════════════════════════════════════════════════
bajas = _cargar_bajas_historicas()
if not bajas.empty:
    costos_h = bajas.apply(calcular_costo_rotacion, axis=1, result_type="expand")
    bajas = pd.concat([bajas, costos_h], axis=1)

    # Ventana relativa a la baja más reciente de los datos (robusto a datos no-live)
    _max_eg = bajas["fecha_egreso"].max()
    cap_v1, cap_v2 = st.columns([1, 3])
    with cap_v1:
        _ventana = st.selectbox("Período histórico",
                                ["Últimos 12 meses", "Últimos 24 meses", "Todo el historial"],
                                index=0)
    meses_v = {"Últimos 12 meses": 12, "Últimos 24 meses": 24, "Todo el historial": None}[_ventana]
    if meses_v:
        desde = _max_eg - pd.DateOffset(months=meses_v)
        bajas_v = bajas[bajas["fecha_egreso"] >= desde]
    else:
        bajas_v = bajas

    n_bajas      = len(bajas_v)
    costo_hist   = bajas_v["costo_total"].sum()
    costo_prom_h = bajas_v["costo_total"].mean() if n_bajas else 0
    tenure_prom  = bajas_v["meses_activo"].mean() if n_bajas else 0
    _rango = (f"{bajas_v['fecha_egreso'].min():%m/%Y} – {bajas_v['fecha_egreso'].max():%m/%Y}"
              if n_bajas else "—")

    col_h, col_hs = st.columns([1, 2.2])
    with col_h:
        st.markdown(hero_kpi("Costo de la rotación ya ocurrida", fmt_pesos_corto(costo_hist),
                             f"{n_bajas} baja{'s' if n_bajas!=1 else ''} · {_rango}", red=True),
                    unsafe_allow_html=True)
    with col_hs:
        _h1, _h2, _h3 = st.columns(3)
        with _h1:
            st.markdown(stat_kpi("Costo promedio por baja", fmt_pesos_corto(costo_prom_h)),
                        unsafe_allow_html=True)
        with _h2:
            st.markdown(stat_kpi("Antigüedad prom. al irse", f"{tenure_prom:.1f} meses"),
                        unsafe_allow_html=True)
        with _h3:
            _voluntarias = bajas_v["motivo_egreso"].isin(["Renuncia voluntaria", "Abandono"]).sum()
            _pct_vol = (_voluntarias / n_bajas * 100) if n_bajas else 0
            st.markdown(stat_kpi("Salidas voluntarias", f"{_pct_vol:.0f}%"), unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    if n_bajas:
        g1, g2 = st.columns(2)
        # Tendencia mensual del costo
        with g1:
            st.markdown('<div class="sec-header">📉 Costo de rotación por mes</div>',
                        unsafe_allow_html=True)
            por_mes = (bajas_v.groupby("periodo_egreso")
                       .agg(costo=("costo_total", "sum"), n=("id_vendedor", "count"))
                       .reset_index().sort_values("periodo_egreso"))
            fig_m = go.Figure(go.Bar(
                x=por_mes["periodo_egreso"], y=por_mes["costo"],
                marker_color="#E24B4A",
                customdata=por_mes["n"],
                hovertemplate="<b>%{x}</b><br>Costo: $%{y:,.0f}<br>Bajas: %{customdata}<extra></extra>",
            ))
            fig_m.update_layout(height=300, margin=dict(l=0, r=10, t=10, b=10),
                                plot_bgcolor="white", paper_bgcolor="white",
                                yaxis=dict(showgrid=True, gridcolor="#f0f0f0"))
            st.plotly_chart(fig_m, use_container_width=True)
        # Costo por motivo de egreso
        with g2:
            st.markdown('<div class="sec-header">🧭 Costo por motivo de egreso</div>',
                        unsafe_allow_html=True)
            por_motivo = (bajas_v.groupby("motivo_egreso")
                          .agg(costo=("costo_total", "sum"), n=("id_vendedor", "count"))
                          .reset_index().sort_values("costo"))
            fig_mo = go.Figure(go.Bar(
                x=por_motivo["costo"], y=por_motivo["motivo_egreso"], orientation="h",
                marker_color="#EF9F27",
                customdata=por_motivo["n"],
                text=[_fmt_pesos(v) for v in por_motivo["costo"]], textposition="outside",
                hovertemplate="<b>%{y}</b><br>Costo: $%{x:,.0f}<br>Bajas: %{customdata}<extra></extra>",
            ))
            fig_mo.update_layout(height=300, margin=dict(l=0, r=110, t=10, b=10),
                                 plot_bgcolor="white", paper_bgcolor="white",
                                 xaxis=dict(showticklabels=False, showgrid=False))
            st.plotly_chart(fig_mo, use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="sec-header">🔮 Exposición futura — activos en riesgo hoy</div>',
                unsafe_allow_html=True)
    st.caption("Lo de arriba ya pasó. Lo de abajo es lo que podés evitar: cuánto costaría "
               "si se van los vendedores activos en riesgo.")

# Calcular costo por vendedor usando plan real del período actual
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
# Ejemplo: Televentas veterano (mes 7+) y Viajante nuevo (mes 1-2)
_plan_tv_vet = _PLAN_TELEVENTAS_VETERANO
_plan_v_nuevo = _PLAN_ESCALON[(1, 2)]
_meses_ind  = MESES_RAMPA_NUEVO
_tot_dir_tv = SALARIO_TELEVENTAS * 2 + SALARIO_INDUCCION * _meses_ind
_perd_cob   = _plan_tv_vet * MESES_HASTA_NUEVO * PCT_PERDIDA_COBERTURA
_perd_rampa = _plan_tv_vet * MESES_RAMPA_NUEVO  * PCT_PERDIDA_RAMPA

st.markdown("---")
with st.expander("Metodología de cálculo — ¿de dónde salen los números?"):
    st.caption(
        "Los salarios se actualizan mensualmente en pages/Costo_Rotacion.py. "
        "El plan se asigna por antigüedad del vendedor (escalón real, no promedio del tipo). "
        "El modelo de cobertura refleja que televentas actúa de cobertura mientras se contrata el reemplazo."
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
**Costos directos — ejemplo Televentas veterano (7+ meses):**

| Concepto | Cálculo | Total |
|---|---|---|
| Último mes improductivo | {_fmt_pesos(SALARIO_TELEVENTAS)} × 1 mes | {_fmt_pesos(SALARIO_TELEVENTAS)} |
| Reclutamiento | {_fmt_pesos(SALARIO_TELEVENTAS)} × 1 mes | {_fmt_pesos(SALARIO_TELEVENTAS)} |
| Inducción nuevo | {_fmt_pesos(SALARIO_INDUCCION)} × {_meses_ind} meses | {_fmt_pesos(SALARIO_INDUCCION * _meses_ind)} |
| **Total directo** | | **{_fmt_pesos(_tot_dir_tv)}** |

**Salarios base:**
- Viajante / Televentas meses 1-2: {_fmt_pesos(_PLAN_ESCALON[(1,2)])} plan
- Viajante / Televentas meses 3-4: {_fmt_pesos(_PLAN_ESCALON[(3,4)])} plan
- Viajante / Televentas meses 5-6: {_fmt_pesos(_PLAN_ESCALON[(5,6)])} plan
- Viajante veterano (7+m): {_fmt_pesos(_PLAN_VIAJANTE_VETERANO)} plan
- Televentas veterano (7+m): {_fmt_pesos(_PLAN_TELEVENTAS_VETERANO)} plan
""")
    with col2:
        st.markdown(f"""
**Costo indirecto — pérdida parcial de cartera (modelo con cobertura Wurth):**

Cuando un vendedor se va, **televentas cubre la zona** hasta que ingresa el reemplazo.
La pérdida se calcula sobre el **plan del vendedor que se fue** (no un promedio del tipo):

| Período | Duración | Pérdida estimada | Ejemplo Televentas vet. |
|---|---|---|---|
| Cobertura televentas | {MESES_HASTA_NUEVO:.1f} m | {int(PCT_PERDIDA_COBERTURA*100)}% del plan/mes | {_fmt_pesos(_perd_cob)} |
| Rampa nuevo vendedor | {MESES_RAMPA_NUEVO:.0f} m | {int(PCT_PERDIDA_RAMPA*100)}% del plan/mes | {_fmt_pesos(_perd_rampa)} |
| **Pérdida total** | | | **{_fmt_pesos(_perd_cob + _perd_rampa)}** |

*Ajustar PCT\\_PERDIDA\\_COBERTURA y PCT\\_PERDIDA\\_RAMPA según experiencia histórica.*
""")
