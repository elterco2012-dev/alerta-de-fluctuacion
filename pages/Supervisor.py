"""
pages/Supervisor.py
-------------------
Vista individual por supervisor (multi-page Streamlit).
Se accede desde el dashboard principal o directo con ?supervisor=Nombre.
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
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
    page_title="Wurth | Vista Supervisor",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""<style>
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 2rem 2.5rem 3rem !important; max-width: 100% !important; }
header { display: none; }

.kpi-row { display: flex; gap: 14px; margin-bottom: 24px; }
.kpi-card { background: white; border-radius: 12px; padding: 18px 22px;
    flex: 1; box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 4px solid #e0e0e0; }
.kpi-card.kc { border-left-color: #E24B4A; }
.kpi-card.ka { border-left-color: #EF9F27; }
.kpi-card.ki { border-left-color: #4A90D9; }
.kpi-value { font-size: 30px; font-weight: 800; color: #1a1a2e; line-height: 1.1; }
.kpi-label { font-size: 13px; font-weight: 700; color: #333; margin-top: 6px; }
.kpi-sub   { font-size: 11px; color: #999; margin-top: 3px; }

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
         font-size: 12px; font-weight: 600; color: #666; border-bottom: 2px solid #e9ecef; }
.vt td { padding: 11px 12px; border-bottom: 1px solid #f2f2f2;
         vertical-align: middle; font-size: 13px; }
.vt tr:hover td { background: #fafafa; }
.vn  { font-weight: 700; color: #1a1a2e; font-size: 13px; }
.vsb { color: #aaa; font-size: 11px; margin-top: 2px; }

.sec-header { font-size: 15px; font-weight: 700; color: #1a1a2e;
    margin: 8px 0 14px; display: flex; align-items: center; gap: 6px; }

.card { background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08); }

.sup-card { background: white; border-radius: 12px; padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 4px;
    border-left: 4px solid #e0e0e0; }
.sup-card.rc { border-left-color: #E24B4A; }
.sup-card.ra { border-left-color: #EF9F27; }
.sup-card.rm { border-left-color: #4A90D9; }
.sup-card.rb { border-left-color: #639922; }
.sup-name  { font-size: 15px; font-weight: 800; color: #1a1a2e; }
.sup-grupo { font-size: 12px; color: #888; margin-top: 2px; }

.ot { width: 100%; border-collapse: collapse; }
.ot th { background: #f8f9fa; padding: 10px 14px; text-align: left;
         font-size: 12px; font-weight: 600; color: #666; border-bottom: 2px solid #e9ecef; }
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
        f'<span class="pill pill-{SEÑAL_TAGS.get(d,(d,"yellow"))[1]}">'
        f'{SEÑAL_TAGS.get(d,(d,"yellow"))[0]}</span>'
        for d in tags
    )

def _score_circle(score, nivel):
    return f'<div class="sc sc-{nivel}">{int(score)}</div>'

def _spark(vals):
    if not vals: return "—"
    cap = max(max(vals), 100)
    bars = []
    for v in vals:
        h = max(3, int(v / cap * 22))
        c = "#639922" if v >= 90 else ("#EF9F27" if v >= 70 else "#E24B4A")
        bars.append(f'<div class="sb" style="height:{h}px;background:{c};"></div>')
    return f'<div class="spark">{"".join(bars)}</div>'

def _bdg(nivel, label=None):
    labels = {"critico":"Crítico","alto":"Alto","medio":"Medio","bajo":"Bajo"}
    return f'<span class="bdg bdg-{nivel}">{label or labels[nivel]}</span>'

def _zona_nivel(rb):
    if rb > 0.60: return "critico"
    if rb > 0.45: return "alto"
    if rb > 0.30: return "medio"
    return "bajo"

def _zona_label(rb):
    return {"critico":"rot alta","alto":"rot alta",
            "medio":"rot media","bajo":"rot baja"}[_zona_nivel(rb)]

def _card_class(nivel):
    return {"critico":"rc","alto":"ra","medio":"rm","bajo":"rb"}.get(nivel,"rb")

# ── Datos ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_datos():
    scores = calcular_scores(meses_tendencia=3)
    grupos = resumen_grupos()
    sparks = obtener_sparklines(meses=3)
    con    = get_connection()
    grupos_risk = pd.read_sql("SELECT nombre_grupo, riesgo_base FROM grupos", con)
    con.close()
    grupos = grupos.merge(grupos_risk, on="nombre_grupo", how="left")
    return scores, grupos, sparks

scores_df, grupos_df, sparks = cargar_datos()

# ── Router ─────────────────────────────────────────────────────────────────────
supervisor_sel = st.query_params.get("supervisor", None)

# ══════════════════════════════════════════════════════════════════════════════
# LANDING
# ══════════════════════════════════════════════════════════════════════════════
if not supervisor_sel:
    nav_col, _ = st.columns([1, 4])
    with nav_col:
        st.page_link("dashboard.py", label="← Dashboard principal", icon="📊")

    st.markdown("""
    <div style="margin-bottom:28px;margin-top:12px;">
      <div style="font-size:22px;font-weight:800;color:#1a1a2e;">👤 Vista por supervisor</div>
      <div style="font-size:14px;color:#888;margin-top:4px;">
        Seleccioná tu zona para ver tus vendedores y alertas activas
      </div>
    </div>
    """, unsafe_allow_html=True)

    resumen = scores_df.groupby("supervisor").agg(
        activos  =("id_vendedor", "count"),
        criticos =("nivel_riesgo", lambda x: (x=="critico").sum()),
        altos    =("nivel_riesgo", lambda x: (x=="alto").sum()),
        score_max=("score", "max"),
    ).reset_index()
    resumen = resumen.merge(
        grupos_df[["supervisor","nombre_grupo","permanencia_promedio_meses","riesgo_base"]],
        on="supervisor", how="left"
    ).sort_values("score_max", ascending=False)

    cols = st.columns(3)
    for i, (_, row) in enumerate(resumen.iterrows()):
        rb    = row.get("riesgo_base", 0.4) or 0.4
        nivel = _zona_nivel(rb)
        cc    = _card_class(nivel)
        perm  = row["permanencia_promedio_meses"]
        perm_str = f"{perm:.1f}m" if pd.notna(perm) else "—"
        c = int(row["criticos"]); a = int(row["altos"])
        if c > 0:
            alerta = f'<span style="color:#E24B4A;font-weight:700;">{c} crítico{"s" if c>1 else ""}</span>'
            if a: alerta += f' · <span style="color:#E65100;">{a} alto{"s" if a>1 else ""}</span>'
        elif a:
            alerta = f'<span style="color:#E65100;">{a} alto{"s" if a>1 else ""}</span>'
        else:
            alerta = '<span style="color:#2E7D32;">Sin alertas activas</span>'

        with cols[i % 3]:
            st.markdown(f"""
            <div class="sup-card {cc}">
              <div class="sup-name">{row['supervisor']}</div>
              <div class="sup-grupo">{row['nombre_grupo']}</div>
              <div style="display:flex;gap:20px;margin-top:12px;">
                <div><div style="font-size:20px;font-weight:800;">{int(row['activos'])}</div>
                     <div style="font-size:11px;color:#aaa;">activos</div></div>
                <div><div style="font-size:20px;font-weight:800;">{perm_str}</div>
                     <div style="font-size:11px;color:#aaa;">perm. prom.</div></div>
                <div style="margin-left:auto;align-self:center;">{_bdg(nivel)}</div>
              </div>
              <div style="font-size:12px;margin-top:10px;">{alerta}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Ver mis vendedores →", key=f"btn_{row['supervisor']}",
                         use_container_width=True):
                st.query_params["supervisor"] = row["supervisor"]
                st.rerun()

    st.markdown("---")
    st.caption("Wurth Argentina · Sistema de alertas de rotación")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# VISTA DEL SUPERVISOR
# ══════════════════════════════════════════════════════════════════════════════
df_sup = scores_df[scores_df["supervisor"] == supervisor_sel]

if df_sup.empty:
    st.error(f"No se encontró el supervisor: **{supervisor_sel}**")
    if st.button("← Volver"):
        st.query_params.clear()
        st.rerun()
    st.stop()

grupo_info   = grupos_df[grupos_df["supervisor"] == supervisor_sel]
nombre_grupo = df_sup.iloc[0]["nombre_grupo"]
rb           = df_sup.iloc[0]["grupo_riesgo_base"]
nivel_zona   = _zona_nivel(rb)
perm_zona    = grupo_info["permanencia_promedio_meses"].values[0] if not grupo_info.empty else None
perm_general = grupos_df["permanencia_promedio_meses"].mean()

# Navegación
nav1, nav2, nav3, _ = st.columns([1, 1, 1, 3])
with nav1:
    st.page_link("dashboard.py", label="← Dashboard", icon="📊")
with nav2:
    if st.button("← Todas las zonas"):
        st.query_params.clear()
        st.rerun()
with nav3:
    st.page_link("pages/Intervenciones.py", label="📝 Intervenciones")

# Header
st.markdown(f"""
<div style="margin-bottom:24px;margin-top:12px;">
  <div style="font-size:22px;font-weight:800;color:#1a1a2e;">👤 {supervisor_sel}</div>
  <div style="font-size:14px;color:#888;margin-top:4px;">
    Zona: <b style="color:#1a1a2e;">{nombre_grupo}</b>
    &nbsp;·&nbsp; {_bdg(nivel_zona, _zona_label(rb))}
  </div>
</div>
""", unsafe_allow_html=True)

if rb > 0.60:
    st.warning(f"⚠️ **{nombre_grupo}** es una zona con alta rotación histórica. "
               f"Los vendedores nuevos aquí tienen mayor probabilidad de irse antes de los 6 meses.")

# KPIs
n_activos  = len(df_sup)
n_criticos = len(df_sup[df_sup.nivel_riesgo == "critico"])
n_altos    = len(df_sup[df_sup.nivel_riesgo == "alto"])
n_onb      = len(df_sup[df_sup.meses_activo <= 3])
perm_str   = f"{perm_zona:.1f}m" if perm_zona and pd.notna(perm_zona) else "—"
diff_perm  = (perm_zona - perm_general) if perm_zona and pd.notna(perm_zona) else None
diff_str   = (f"{'↑' if diff_perm > 0 else '↓'} {abs(diff_perm):.1f}m vs promedio"
              if diff_perm is not None else "")
diff_color = "#2E7D32" if diff_perm and diff_perm > 0 else "#E24B4A"

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-value">{n_activos}</div>
    <div class="kpi-label">Vendedores activos</div>
    <div class="kpi-sub">En tu zona</div>
  </div>
  <div class="kpi-card kc">
    <div class="kpi-value" style="color:#E24B4A">{n_criticos + n_altos}</div>
    <div class="kpi-label">Requieren atención</div>
    <div class="kpi-sub">{n_criticos} crítico{"s" if n_criticos!=1 else ""} · {n_altos} alto{"s" if n_altos!=1 else ""}</div>
  </div>
  <div class="kpi-card ka">
    <div class="kpi-value">{perm_str}</div>
    <div class="kpi-label">Permanencia prom. zona</div>
    <div class="kpi-sub" style="color:{diff_color};">{diff_str}</div>
  </div>
  <div class="kpi-card ki">
    <div class="kpi-value" style="color:#4A90D9">{n_onb}</div>
    <div class="kpi-label">En onboarding</div>
    <div class="kpi-sub">Primeros 3 meses</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Tabla
st.markdown('<div class="sec-header">📋 Mis vendedores por score de riesgo</div>',
            unsafe_allow_html=True)
rows = ""
for _, r in df_sup.iterrows():
    vid = int(r["id_vendedor"]); nivel = r["nivel_riesgo"]
    rows += f"""<tr>
      <td><div class="vn">{r['nombre']} <span style="color:#888;font-weight:400;font-size:11px;">({vid})</span></div>
          <div class="vsb">{r['tipo']} · {_fmt_antiguedad(r['meses_activo'])} antigüedad</div></td>
      <td>{_pills(r['señales_activas'])}</td>
      <td><b>{r['pct_plan_3m']}%</b></td>
      <td>{_spark(sparks.get(vid,[]))}</td>
      <td>{_score_circle(r['score'], nivel)}</td>
    </tr>"""

st.markdown(f"""
<div class="card" style="margin-bottom:6px;overflow-x:auto;">
<table class="vt">
<thead><tr>
  <th>Vendedor</th><th>Señales detectadas</th>
  <th>% Plan 3m</th><th>Tendencia</th><th>Score</th>
</tr></thead>
<tbody>{rows}</tbody>
</table></div>""", unsafe_allow_html=True)
st.caption(f"{n_activos} vendedores en {nombre_grupo}")

# Onboarding
onb = df_sup[df_sup.meses_activo <= 3].sort_values("score", ascending=False)
if not onb.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-header">👥 Onboarding en curso — primeros 90 días</div>',
                unsafe_allow_html=True)
    ob_rows = ""
    for _, r in onb.iterrows():
        nivel = r["nivel_riesgo"]
        ob_rows += f"""<tr>
          <td><b>{r['nombre']}</b> <span style="color:#888;font-size:11px;">({int(r['id_vendedor'])})</span></td>
          <td>{r['tipo']}</td>
          <td>{_fmt_antiguedad(r['meses_activo'])}</td><td><b>{r['pct_plan_3m']}%</b></td>
          <td>{_bdg(nivel)}</td></tr>"""
    st.markdown(f"""
    <div class="card"><table class="ot">
    <thead><tr><th>Vendedor</th><th>Tipo</th><th>Mes</th><th>% Plan</th><th>Riesgo</th></tr></thead>
    <tbody>{ob_rows}</tbody></table></div>""", unsafe_allow_html=True)

st.markdown("<br>")
st.caption("Wurth Argentina · Sistema de alertas de rotación")
