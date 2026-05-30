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

def _fmt_antiguedad(meses):
    if meses < 12:
        return f"{meses} mes{'es' if meses != 1 else ''}"
    anios = meses // 12
    resto = meses % 12
    s = f"{anios} año{'s' if anios != 1 else ''}"
    if resto:
        s += f" y {resto} mes{'es' if resto != 1 else ''}"
    return s

st.set_page_config(
    page_title="Wurth | Alertas de Rotación",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""<style>
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 2.5rem 2.5rem 3rem !important; max-width: 100% !important; }
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
        SELECT
            MAX(1, CAST((julianday(fecha_egreso) - julianday(fecha_ingreso)) / 30.44 + 1 AS INTEGER)) as mes_numero,
            COUNT(*) as renuncias
        FROM vendedores
        WHERE fecha_egreso IS NOT NULL
          AND fecha_ingreso IS NOT NULL
          AND fecha_egreso != fecha_ingreso
        GROUP BY mes_numero
        ORDER BY mes_numero
    """, con)
    # Permanencia promedio al egreso (vendedores que ya salieron)
    egresados = pd.read_sql("""
        SELECT fecha_ingreso, fecha_egreso
        FROM vendedores
        WHERE activo = 0
          AND fecha_egreso IS NOT NULL
          AND fecha_ingreso IS NOT NULL
          AND fecha_egreso != fecha_ingreso
          AND fecha_ingreso >= date('now', '-12 months')
    """, con)
    con.close()

    egresados["fecha_ingreso"] = pd.to_datetime(egresados["fecha_ingreso"], errors="coerce")
    egresados["fecha_egreso"]  = pd.to_datetime(egresados["fecha_egreso"],  errors="coerce")
    egresados["meses"] = (egresados["fecha_egreso"] - egresados["fecha_ingreso"]).dt.days / 30.44
    perm_egreso = egresados["meses"].mean() if len(egresados) else 0

    grupos = grupos.merge(grupos_risk, on="nombre_grupo", how="left")
    return scores, grupos, sparks, ventanas, perm_egreso

scores_df, grupos_df, sparks, ventanas_df, perm_egreso_prom = cargar_datos()

# ── Estadísticas de supervisores (calculadas desde scores_df) ──────────────────
_sup_stats = (
    scores_df[scores_df["supervisor"].notna() & (scores_df["supervisor"] != "")]
    .groupby("supervisor")
    .agg(
        n_vendedores=("id_vendedor", "count"),
        n_onboarding=("meses_activo", lambda x: (x <= 6).sum()),
    )
    .reset_index()
)
_n_supervisores       = len(_sup_stats)
_avg_por_sup          = _sup_stats["n_vendedores"].mean() if _n_supervisores > 0 else 0
_sup_con_muchos_nuevos = int((_sup_stats["n_onboarding"] >= 3).sum())

# ── Encabezado + Navegación ────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center;
            margin-bottom:20px; padding-bottom:14px; border-bottom:1px solid #eee;">
  <div style="font-size:20px; font-weight:800; color:#1a1a2e;">
    Wurth Argentina &mdash; Alertas de Rotación
  </div>
  <div style="font-size:13px; display:flex; gap:20px;">
    <a href="/Supervisor"     target="_self" style="color:#4A90D9;text-decoration:none;">👤 Por supervisor</a>
    <a href="/Intervenciones" target="_self" style="color:#4A90D9;text-decoration:none;">📝 Intervenciones</a>
    <a href="/Historial"      target="_self" style="color:#4A90D9;text-decoration:none;">📈 Historial</a>
    <a href="/Costo_Rotacion" target="_self" style="color:#4A90D9;text-decoration:none;">💰 Costo de rotación</a>
    <a href="/Actividad"      target="_self" style="color:#4A90D9;text-decoration:none;">📞 Actividad</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────────────
total          = len(scores_df)
en_critica     = len(scores_df[scores_df.nivel_riesgo.isin(["critico", "alto"])])
perm_prom      = scores_df["meses_activo"].mean()   # solo vendedores activos, sin supervisores
ob_critico     = len(scores_df[
    (scores_df.meses_activo <= 6) & (scores_df.nivel_riesgo.isin(["critico", "alto"]))
])
_sup_color = "kc" if _sup_con_muchos_nuevos > 0 else "ki"

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-value">{total}</div>
    <div class="kpi-label">Vendedores activos</div>
    <div class="kpi-sub">Actualizando mensualmente</div>
  </div>
  <div class="kpi-card kc">
    <div class="kpi-value" style="color:#E24B4A">{en_critica}</div>
    <div class="kpi-label">Vendedores en riesgo elevado</div>
    <div class="kpi-sub">Score ≥ 6 (alto o crítico) — ver zonas históricas en 📈 Historial</div>
  </div>
  <div class="kpi-card ka">
    <div class="kpi-value">{perm_egreso_prom:.1f} m</div>
    <div class="kpi-label">Permanencia promedio al egreso</div>
    <div class="kpi-sub">Últimos 12 meses · era 18m hace 10 años</div>
  </div>
  <div class="kpi-card ki">
    <div class="kpi-value" style="color:#4A90D9">{ob_critico}</div>
    <div class="kpi-label">Onboarding en riesgo elevado</div>
    <div class="kpi-sub">Score ≥ 6 en sus primeros 6 meses</div>
  </div>
  <div class="kpi-card {_sup_color}">
    <div class="kpi-value">{_n_supervisores}</div>
    <div class="kpi-label">Supervisores activos</div>
    <div class="kpi-sub">{_avg_por_sup:.1f} vendedores/supervisor · {_sup_con_muchos_nuevos} con 3+ onboardings activos</div>
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

# Filtro por supervisor
supervisores_disp = sorted([s for s in scores_df["supervisor"].dropna().unique() if s])
col_busq, col_sup = st.columns([3, 2])
with col_busq:
    busqueda_sc = st.text_input("", placeholder="🔍 Buscar por nombre o número de vendedor...", key="busq_score", label_visibility="collapsed")
with col_sup:
    sup_sel = st.selectbox("", ["Todos los supervisores"] + supervisores_disp, key="sup_score", label_visibility="collapsed")

if sup_sel != "Todos los supervisores":
    df = df[df["supervisor"] == sup_sel]
if busqueda_sc:
    mask = (df["nombre"].str.contains(busqueda_sc, case=False, na=False) |
            df["id_vendedor"].astype(str).str.contains(busqueda_sc, na=False))
    df_show = df[mask]
else:
    df_show = df.head(5)

# ── Tabla principal ────────────────────────────────────────────────────────────
rows = ""
for _, r in df_show.iterrows():
    vid   = int(r["id_vendedor"])
    nivel = r["nivel_riesgo"]
    zona_n = _zona_nivel(r["grupo_riesgo_base"])
    zona_l = _zona_label(r["grupo_riesgo_base"])
    rows += f"""
    <tr>
      <td>
        <div class="vn">{r['nombre']} <span style="color:#888;font-weight:400;font-size:11px;">({vid})</span></div>
        <div class="vsb">{r['tipo']} · {_fmt_antiguedad(r['meses_activo'])}</div>
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
if busqueda_sc or sup_sel != "Todos los supervisores":
    st.caption(f"{len(df_show)} vendedores encontrados")

else:
    st.caption(f"Top 10 de {len(df)} vendedores. Usá el buscador para filtrar.")

with st.expander("¿Cómo se calculan las señales, el % Plan 3m y la tendencia?"):
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("""
**% Plan 3m**
Promedio de `venta_real / objetivo * 100` de los últimos 3 meses del vendedor.
Por ejemplo: si vendió 80%, 75% y 70% en los últimos 3 meses → % Plan 3m = 75%.

**Tendencia (barras mini)**
Cada barra = % Plan de ese mes (izquierda = más antiguo, derecha = más reciente).
🟢 Verde ≥ 90% · 🟠 Naranja ≥ 70% · 🔴 Rojo < 70%

**Score (1–10)**
Suma de señales activas ponderadas, normalizada a escala 1–10.
Solo se usa la tendencia de los últimos 3 meses, no un dato puntual.
""")
    with col_e2:
        st.markdown("""
**Señales y sus umbrales**

| Señal | Se activa cuando |
|---|---|
| `caída 3m` | El % Plan cae de forma sostenida (pendiente < −3 pts/mes) |
| `plan<80%` | Promedio % Plan últimos 3 meses está por debajo del 80% |
| `días cero+` | Más de 3 días sin registrar ninguna venta en promedio |
| `cobranza baja` | Cobranza real < 90% de la cobranza teórica esperada |
| `onboarding` | Vendedor en sus primeros 3 meses (riesgo muy alto) |
| `mes 4-6` | Vendedor entre el mes 4 y 6 (riesgo alto) |
| `zona quemada` | El grupo tiene rotación histórica elevada (> 60%) |
| `clientes L:0` | Cero clientes nuevos en los últimos 2 meses |
""")

with st.expander("¿Cómo se calculan las señales, el % Plan 3m y la tendencia?"):
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("""
**% Plan 3m**
Promedio de `venta_real / objetivo * 100` de los últimos 3 meses del vendedor.
Por ejemplo: si vendió 80%, 75% y 70% en los últimos 3 meses → % Plan 3m = 75%.

**Tendencia (barras mini)**
Cada barra = % Plan de ese mes (izquierda = más antiguo, derecha = más reciente).
🟢 Verde ≥ 90% · 🟠 Naranja ≥ 70% · 🔴 Rojo < 70%

**Score (1–10)**
Suma de señales activas ponderadas, normalizada a escala 1–10.
Solo se usa la tendencia de los últimos 3 meses, no un dato puntual.
""")
    with col_e2:
        st.markdown("""
**Señales y sus umbrales**

| Señal | Se activa cuando |
|---|---|
| `caída 3m` | El % Plan cae de forma sostenida (pendiente < −3 pts/mes) |
| `plan<80%` | Promedio % Plan últimos 3 meses está por debajo del 80% |
| `días cero+` | Más de 3 días sin registrar ninguna venta en promedio |
| `cobranza baja` | Cobranza real < 90% de la cobranza teórica esperada |
| `onboarding` | Vendedor en sus primeros 3 meses (riesgo muy alto) |
| `mes 4-6` | Vendedor entre el mes 4 y 6 (riesgo alto) |
| `zona quemada` | El grupo tiene rotación histórica elevada (> 60%) |
| `clientes L:0` | Cero clientes nuevos en los últimos 2 meses |
""")

st.markdown("<br>", unsafe_allow_html=True)

# ── Zonas + Ventanas ───────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1.6])

with col1:
    st.markdown('<div class="sec-header">📍 Zonas con mayor rotación histórica</div>',
                unsafe_allow_html=True)
    zonas = grupos_df.sort_values("permanencia_promedio_meses", na_position="last")

    # Search
    busqueda_z = st.text_input("", placeholder="🔍 Buscar supervisor o grupo...", key="busq_zona", label_visibility="collapsed")
    if busqueda_z:
        zonas_fil = zonas[zonas.apply(lambda r:
            busqueda_z.lower() in str(r["nombre_grupo"]).lower() or
            busqueda_z.lower() in str(r.get("supervisor","")).lower(), axis=1)]
    else:
        zonas_fil = zonas

    def _zona_cards_html(subset):
        cards = ""
        for _, g in subset.iterrows():
            perm  = g["permanencia_promedio_meses"]
            rb    = g.get("riesgo_base", 0.5)
            nivel = _zona_nivel(rb) if pd.notna(rb) else "medio"
            perm_str = f"{perm:.1f}m" if pd.notna(perm) else "—"
            sup_str = f" · {g['supervisor']}" if pd.notna(g.get('supervisor','')) and g.get('supervisor','') else ""
            cards += f"""
            <div class="zc">
              <div>
                <div class="zn">{g['nombre_grupo']}{sup_str}</div>
                <div class="zsb">{int(g['total_vendedores'])} vendedores históricos · perm. prom. {perm_str}</div>
              </div>
              <div class="zr">
                <div class="zpct">{g['cumplimiento_plan_promedio']:.0f}% plan</div>
                {_bdg(nivel)}
              </div>
            </div>"""
        return cards

    top5_zonas = zonas_fil.head(5)
    resto_zonas = zonas_fil.iloc[5:]
    st.markdown(f'<div class="card">{_zona_cards_html(top5_zonas)}</div>', unsafe_allow_html=True)
    if not resto_zonas.empty:
        with st.expander(f"Ver {len(resto_zonas)} grupos más"):
            st.markdown(f'<div class="card">{_zona_cards_html(resto_zonas)}</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="sec-header">⏱️ Ventanas críticas de permanencia</div>',
                unsafe_allow_html=True)

    vdf = ventanas_df.copy()
    # Separar M19+ para no aplastarlo escala del gráfico
    m19_total = int(vdf[vdf["mes_numero"] >= 19]["renuncias"].sum())
    vdf = vdf[vdf["mes_numero"] < 19].copy()  # solo M1-M18 en el gráfico

    def _color_mes(m):
        if m <= 3:  return "#E24B4A"
        if m <= 6:  return "#EF9F27"
        if m <= 12: return "#B4B2A9"
        return "#8DB56B"

    fig = go.Figure(go.Bar(
        x=[f"M{m}" for m in vdf["mes_numero"]],
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
        xaxis=dict(showgrid=False, title="Mes de carrera del vendedor"),
        font=dict(size=11),
    )
    st.caption(
        "🔴 Mes 1-3 (onboarding) · 🟠 Mes 4-6 (adaptación) · ⬜ Mes 7-12 · "
        f"Vendedores que renunciaron con más de 18 meses: {m19_total} (no se muestran para preservar escala)"
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Onboarding en curso ────────────────────────────────────────────────────────
# Onboarding = meses 1-6 (ventana crítica completa según histórico Wurth)
# Mes 1-3: riesgo muy alto (57% de bajas de toda la carrera ocurren acá)
# Mes 4-6: riesgo alto (se requiere seguimiento activo del supervisor)
# A partir del mes 7 el riesgo cae significativamente.
onb = scores_df[scores_df.meses_activo <= 6].sort_values("score", ascending=False)

if not onb.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    n_onb_13 = len(onb[onb.meses_activo <= 3])
    n_onb_46 = len(onb[(onb.meses_activo >= 4) & (onb.meses_activo <= 6)])
    st.markdown(
        f'<div class="sec-header">👥 Onboarding activo — meses 1 a 6 '
        f'<span style="font-weight:400;color:#888;font-size:13px;">'
        f'{len(onb)} vendedores · {n_onb_13} en mes 1-3 (riesgo muy alto) · {n_onb_46} en mes 4-6 (riesgo alto)'
        f'</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Onboarding = los primeros 6 meses. "
        "Históricamente, más de la mitad de las renuncias ocurren antes del mes 7. "
        "Mes 1-3: período de adaptación inicial donde el supervisor debe reunirse semanalmente. "
        "Mes 4-6: el vendedor ya tiene cartera asignada pero aún no alcanzó velocidad de crucero."
    )

    busqueda_onb = st.text_input("", placeholder="🔍 Buscar vendedor en onboarding...", key="busq_onb", label_visibility="collapsed")
    if busqueda_onb:
        onb_show = onb[onb["nombre"].str.contains(busqueda_onb, case=False, na=False) |
                       onb["id_vendedor"].astype(str).str.contains(busqueda_onb, na=False)]
    else:
        onb_show = onb

    def _onb_rows_html(subset):
        rows = ""
        for _, r in subset.iterrows():
            rb    = r["grupo_riesgo_base"]
            z_n   = _zona_nivel(rb)
            z_l   = _zona_label(rb)
            nivel = r["nivel_riesgo"]
            rows += f"""
            <tr>
              <td><b>{r['nombre']}</b><br><span style="color:#888;font-size:11px;">({int(r['id_vendedor'])})</span></td>
              <td>{r['tipo']}</td>
              <td>{_fmt_antiguedad(r['meses_activo'])}</td>
              <td>{r['nombre_grupo']} {_bdg(z_n, z_l)}</td>
              <td><b>{r['pct_plan_3m']}%</b></td>
              <td>{_bdg(nivel)}</td>
            </tr>"""
        return rows

    top5_onb = onb_show.head(5)
    resto_onb = onb_show.iloc[5:]

    st.markdown(f"""
    <div class="card">
    <table class="ot">
    <thead><tr>
      <th>Vendedor</th><th>Tipo</th><th>Mes en empresa</th>
      <th>Zona asignada</th><th>% Plan 3m</th><th>Riesgo</th>
    </tr></thead>
    <tbody>{_onb_rows_html(top5_onb)}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)

    if not resto_onb.empty:
        with st.expander(f"Ver {len(resto_onb)} vendedores más en onboarding"):
            st.markdown(f"""
    <div class="card">
    <table class="ot">
    <thead><tr>
      <th>Vendedor</th><th>Tipo</th><th>Mes en empresa</th>
      <th>Zona asignada</th><th>% Plan 3m</th><th>Riesgo</th>
    </tr></thead>
    <tbody>{_onb_rows_html(resto_onb)}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)
