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
from snippets_v3 import banner, hero_kpi, stat_kpi, fmt_num, fmt_pct, fmt_meses, page_header

# Grupos excluidos del análisis (grupos administrativos, catch-all, o sin actividad comercial real)
GRUPOS_EXCLUIDOS = {"Grupo 999"}

st.set_page_config(
    page_title="Wurth | Historial de Rotación",
    page_icon="📈",
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
.sec-header { font-size: 15px; font-weight: 700; color: #1a1a2e; margin: 20px 0 12px; }
</style>""", unsafe_allow_html=True)


# ── Nav ────────────────────────────────────────────────────────────────────────
st.markdown(page_header("📈 Historial de Rotación — Wurth Argentina", "/Historial"),
            unsafe_allow_html=True)


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
          AND (fecha_egreso IS NULL OR fecha_egreso != fecha_ingreso)
    """, con)

    # Supervisor y cantidad de vendedores activos por grupo (excluye supervisores)
    # sup_activo: 1 si el supervisor sigue activo, 0 si ya no trabaja
    sup_df = pd.read_sql("""
        SELECT v.nombre_grupo, v.supervisor, COUNT(*) as n_activos,
               s.id_vendedor as sup_id,
               COALESCE(s.activo, 0) as sup_activo
        FROM vendedores v
        LEFT JOIN vendedores s ON s.nombre = v.supervisor
        WHERE v.activo = 1
          AND (v.fecha_egreso IS NULL OR v.fecha_egreso != v.fecha_ingreso)
          AND v.nombre NOT IN (
              SELECT DISTINCT supervisor FROM vendedores
              WHERE supervisor IS NOT NULL AND supervisor != ''
          )
        GROUP BY v.nombre_grupo, v.supervisor, s.id_vendedor, s.activo
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

    # Excluir grupos administrativos
    df     = df[~df["nombre_grupo"].isin(GRUPOS_EXCLUIDOS)]
    sup_df = sup_df[~sup_df["nombre_grupo"].isin(GRUPOS_EXCLUIDOS)]

    # Mapa grupo → supervisor principal y cantidad activa
    sup_map = {}
    cnt_map = {}
    sup_id_map = {}
    for grp, g in sup_df.groupby("nombre_grupo"):
        cnt_map[grp] = int(g["n_activos"].sum())
        # Solo usar supervisores activos; si ya no trabaja, dejar el campo vacío
        g_act = g[g["sup_activo"] == 1] if "sup_activo" in g.columns else g
        if g_act.empty:
            sup_map[grp] = ""
            sup_id_map[grp] = None
            continue
        idx = g_act["n_activos"].idxmax()
        s = g_act.loc[idx, "supervisor"]
        sup_id = g_act.loc[idx, "sup_id"] if "sup_id" in g_act.columns else None
        sup_map[grp] = s if pd.notna(s) and s else ""
        sup_id_map[grp] = int(sup_id) if sup_id is not None and pd.notna(sup_id) else None

    return df[df["permanencia_meses"] > 0].copy(), sup_map, cnt_map, sup_id_map


@st.cache_data(ttl=600)
def cargar_rotacion_anual():
    """Bajas por año de egreso + headcount aproximado para calcular tasa."""
    con = get_connection()
    bajas = pd.read_sql("""
        SELECT CAST(strftime('%Y', fecha_egreso) AS INTEGER) as anio,
               COUNT(*) as bajas
        FROM vendedores
        WHERE fecha_egreso IS NOT NULL
          AND fecha_ingreso IS NOT NULL
          AND fecha_egreso != fecha_ingreso
        GROUP BY anio ORDER BY anio
    """, con)
    # Headcount: cuántos estuvieron activos en algún punto de ese año
    hc = pd.read_sql("""
        SELECT years.anio, COUNT(*) as headcount
        FROM (
            SELECT DISTINCT CAST(strftime('%Y', fecha_egreso) AS INTEGER) as anio
            FROM vendedores
            WHERE fecha_egreso IS NOT NULL AND fecha_egreso != fecha_ingreso
        ) years
        JOIN vendedores v ON
            CAST(strftime('%Y', v.fecha_ingreso) AS INTEGER) <= years.anio
            AND (v.fecha_egreso IS NULL
                 OR CAST(strftime('%Y', v.fecha_egreso) AS INTEGER) >= years.anio)
            AND (v.fecha_egreso IS NULL OR v.fecha_egreso != v.fecha_ingreso)
        GROUP BY years.anio ORDER BY years.anio
    """, con)
    con.close()
    merged = bajas.merge(hc, on="anio")
    merged["tasa_pct"] = (merged["bajas"] / merged["headcount"] * 100).round(1)
    return merged


with st.spinner("Cargando historial..."):
    df, sup_map, cnt_map, sup_id_map = cargar_historial()
    rotacion_anual = cargar_rotacion_anual()

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
n_en_critica = (df_activo["permanencia_meses"] < 6).sum()

col_hero, col_stats = st.columns([1, 2.2])
with col_hero:
    st.markdown(hero_kpi("Se fueron en menos de 6 meses", fmt_pct(pct_menos6),
                         "No sobrevivieron la ventana crítica de onboarding", red=True),
                unsafe_allow_html=True)
with col_stats:
    _s1, _s2, _s3, _s4 = st.columns(4)
    with _s1:
        st.markdown(stat_kpi("Historial total", fmt_num(total_hist)), unsafe_allow_html=True)
    with _s2:
        st.markdown(stat_kpi("Permanencia mediana bajas", fmt_meses(round(perm_bajas, 1))),
                    unsafe_allow_html=True)
    with _s3:
        st.markdown(stat_kpi("Se fueron en < 12m", fmt_pct(pct_menos12)),
                    unsafe_allow_html=True)
    with _s4:
        st.markdown(stat_kpi("Activos en ventana crítica", fmt_num(n_en_critica)),
                    unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# Banner
if pct_menos6 >= 50:
    st.markdown(banner("🔴",
        f"{fmt_pct(pct_menos6)} se fue antes del mes 7",
        "Más de la mitad no superó la ventana crítica de onboarding. El problema es estructural.", "red"),
        unsafe_allow_html=True)
elif pct_menos6 >= 30:
    st.markdown(banner("🟠",
        f"{fmt_pct(pct_menos6)} se fue antes del mes 7",
        "Rotación alta en la ventana de onboarding — revisá las zonas con mayor exposición.", "orange"),
        unsafe_allow_html=True)
else:
    st.markdown(banner("✅",
        f"{fmt_pct(pct_menos6)} se fue antes del mes 7",
        "Rotación por debajo del promedio histórico en la ventana crítica.", "green"),
        unsafe_allow_html=True)


# ── Gráfico 1: Tendencia de permanencia (últimos 10 años, solo dados de baja) ──
st.markdown('<div class="sec-header">📊 Tendencia de permanencia — últimos 10 años (solo vendedores dados de baja)</div>',
            unsafe_allow_html=True)
st.caption(
    "Cada punto = mediana de meses que duraron los vendedores que **entraron ese año** y luego se fueron. "
    "Ejemplo: el punto 2026 con '13 bajas' no es 'todos los que se fueron en 2026', "
    "son los 13 vendedores que entraron en 2026 y ya se fueron — por eso la mediana es 1m. "
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


# ── Gráfico 1b: Bajas por año de egreso + tasa de rotación ────────────────────
st.markdown('<div class="sec-header">📉 Bajas reales por año — ¿el problema mejora o empeora?</div>',
            unsafe_allow_html=True)
st.caption(
    "Este gráfico muestra cuántos vendedores SE FUERON cada año calendario, "
    "independientemente de cuándo entraron. "
    "Las barras = número absoluto de bajas. "
    "La línea naranja = tasa de rotación (bajas / dotación promedio del año × 100). "
    "Una tasa estable alta significa que el problema es estructural, no puntual."
)

rot = rotacion_anual[rotacion_anual["anio"] >= hoy - 10].copy()

if not rot.empty:
    import datetime
    mes_actual = datetime.date.today().month
    rot_vis = rot.copy()
    año_parcial = hoy  # siempre mostrar el año actual, con nota

    colores_barras = [
        "#E24B4A" if t >= 55 else ("#EF9F27" if t >= 40 else "#4A90D9")
        for t in rot_vis["tasa_pct"]
    ]

    fig_rot = go.Figure()

    fig_rot.add_trace(go.Bar(
        x=rot_vis["anio"],
        y=rot_vis["bajas"],
        name="Bajas (cantidad)",
        marker_color=colores_barras,
        text=rot_vis["bajas"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Bajas: %{y}<extra></extra>",
        yaxis="y1",
    ))

    fig_rot.add_trace(go.Scatter(
        x=rot_vis["anio"],
        y=rot_vis["tasa_pct"],
        name="Tasa de rotación (%)",
        mode="lines+markers+text",
        line=dict(color="#EF9F27", width=2.5),
        marker=dict(size=8, color="#EF9F27"),
        text=[f"{t:.0f}%" for t in rot_vis["tasa_pct"]],
        textposition="top center",
        textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Tasa rotación: %{y:.1f}%<extra></extra>",
        yaxis="y2",
    ))

    fig_rot.update_layout(
        height=360,
        margin=dict(l=0, r=50, t=40, b=0),
        xaxis=dict(tickmode="linear", dtick=1, tickformat=".0f", title="Año de egreso"),
        yaxis=dict(title="Bajas (cantidad)", rangemode="tozero", showgrid=True, gridcolor="#f0f0f0"),
        yaxis2=dict(
            title="Tasa de rotación (%)",
            overlaying="y", side="right",
            rangemode="tozero", showgrid=False,
            range=[0, max(rot_vis["tasa_pct"].max() * 1.4, 80)],
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        barmode="group",
    )
    st.plotly_chart(fig_rot, use_container_width=True)
    if mes_actual < 12:
        st.caption(
            f"* {hoy} es año incompleto (datos hasta {mes_actual} meses). "
            "La tasa de rotación del año actual no es comparable directamente con años completos."
        )


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

# Añadir supervisor, su ID y cantidad activa
zona_stats["supervisor_grupo"] = zona_stats["nombre_grupo"].map(sup_map).fillna("")
zona_stats["sup_id_grupo"]     = zona_stats["nombre_grupo"].map(sup_id_map)
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
    raw_id = row.get("sup_id_grupo", None)
    # pandas guarda int como float64 cuando hay NaN en la columna — convertir a int
    sup_id = int(raw_id) if raw_id is not None and not (isinstance(raw_id, float) and pd.isna(raw_id)) else None
    cnt = row["activos_hoy"]
    sup_label = f"{sup} ({sup_id})" if sup and sup_id else (sup if sup else "")
    if sup_label and cnt:
        return f"{grp}<br><span style='font-size:11px'>{sup_label} · {cnt} activos</span>"
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
