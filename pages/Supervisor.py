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
from snippets_v3 import banner, hero_kpi, stat_kpi, accion_tag, fmt_num, fmt_meses, score_delta, fresh, page_header

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

_v3_css = os.path.join(os.path.dirname(__file__), '..', 'assets', 'dashboard-v3.css')
st.markdown(f"<style>{open(_v3_css, encoding='utf-8').read()}</style>", unsafe_allow_html=True)

st.markdown("""<style>
[data-testid="stSidebar"]   { display: none; }
[data-testid="stHeader"]    { display: none; }
[data-testid="stToolbar"]   { display: none; }
.stDeployButton             { display: none; }
.block-container { padding: 2.5rem 2.5rem 4rem !important; max-width: 100% !important; }
header { display: none; }

.sec-header { font-size: 15px; font-weight: 700; color: #1a1a2e;
    margin: 8px 0 14px; display: flex; align-items: center; gap: 6px; }

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
# Mapea cada señal activa a un pill corto. Las señales deshabilitadas (peso=0:
# cartera, cobranza, llamadas, visitas) ya no llegan en señales_activas — el
# motor las filtra — así que no necesitan entrada acá.
SEÑAL_TAGS = {
    "% Plan cayendo 3 meses seguidos":                              ("caída 3m",     "red"),
    "% Plan < 80% promedio últimos meses":                          ("plan<80%",     "orange"),
    "Días sin venta > 3 en promedio":                              ("días cero↑",   "red"),
    "En ventana crítica mes 1-3":                                  ("onboarding",   "red"),
    "En ventana crítica mes 4-6":                                  ("mes 4-6",      "orange"),
    "Grupo con alta rotación histórica":                           ("zona quemada", "orange"),
    "Sin clientes nuevos últimos 2 meses":                         ("clientes L:0", "yellow"),
    "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3": ("ausencias↑",   "red"),
    "Balanza clientes negativa 2+ meses consecutivos":             ("balanza −",    "orange"),
    "Ticket promedio cae > 5% por mes":                            ("ticket↓",      "orange"),
    "Supervisor no acompañó en ventana crítica 1-6":              ("sin acomp.",   "yellow"),
}

def _pills(tags):
    if not tags:
        return '<span style="color:#ccc;font-size:12px;">Sin alertas</span>'
    return "".join(
        f'<span class="wz-pill {SEÑAL_TAGS.get(d,(d,"yellow"))[1]}">'
        f'{SEÑAL_TAGS.get(d,(d,"yellow"))[0]}</span>'
        for d in tags
    )

def _score_circle(score, nivel):
    return f'<span class="wz-score {nivel}">{int(score)}</span>'

def _spark(vals):
    if not vals: return "—"
    cap = max(max(vals), 100)
    bars = []
    for v in vals:
        h = max(3, int(v / cap * 22))
        c = "#639922" if v >= 90 else ("#EF9F27" if v >= 70 else "#E24B4A")
        bars.append(f'<div class="wz-sb" style="height:{h}px;background:{c};"></div>')
    return f'<div class="wz-spark">{"".join(bars)}</div>'

def _bdg(nivel, label=None):
    labels = {"critico":"Crítico","alto":"Alto","medio":"Medio","bajo":"Bajo"}
    return f'<span class="wz-badge {nivel}">{label or labels[nivel]}</span>'

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
    from datetime import date as _date
    scores = calcular_scores(meses_tendencia=3)
    grupos = resumen_grupos()
    sparks = obtener_sparklines(meses=3)
    con    = get_connection()
    grupos_risk = pd.read_sql("SELECT nombre_grupo, riesgo_base FROM grupos", con)

    from datetime import datetime as _dt
    _ts = _dt.now().strftime("%d/%m/%Y %H:%M")
    _hoy = _date.today()
    _pm  = _hoy.month - 1 or 12
    _py  = _hoy.year if _hoy.month > 1 else _hoy.year - 1
    try:
        _prev = pd.read_sql(
            f"SELECT id_vendedor, score AS score_prev FROM score_historico WHERE periodo = '{_py}-{_pm:02d}'",
            con,
        )
        delta_map = dict(zip(_prev["id_vendedor"], _prev["score_prev"]))
    except Exception:
        delta_map = {}

    con.close()
    grupos = grupos.merge(grupos_risk, on="nombre_grupo", how="left")
    return scores, grupos, sparks, delta_map, _ts

scores_df, grupos_df, sparks, delta_map, _ts_datos = cargar_datos()

# ── Control de acceso por rol ────────────────────────────────────────────────
# Cada usuario ve un alcance distinto: el supervisor solo su zona, el director
# las zonas de sus supervisores, RRHH/gerencia toda la empresa. Sin login con
# clave: el usuario se elige en un selector (ver src/acceso.py). La identidad
# viaja en el query param ?usuario= para sobrevivir a los reruns y deep-links.
import acceso

_clave = st.query_params.get("usuario", None) or st.session_state.get("_acc_usuario")
usuario = acceso.resolver(_clave)

if usuario is None:
    # Pantalla de identificación: elegir quién sos antes de ver nada.
    st.markdown(page_header("👤 Por supervisor — Wurth Argentina", "/Supervisor"),
                unsafe_allow_html=True)
    st.markdown("<div style='max-width:460px;margin-top:8px;'>", unsafe_allow_html=True)
    st.markdown('<div class="sec-header">¿Quién está ingresando?</div>',
                unsafe_allow_html=True)
    st.caption("Cada usuario ve solo el alcance que le corresponde: un supervisor "
               "su zona, un director sus supervisores, RRHH y gerencia toda la empresa.")
    _users = acceso.listar_usuarios()
    _opts  = {f"{u['etiqueta']}  ·  {acceso.ROL_LABEL[u['rol']]}": u["clave"]
              for u in _users}
    _sel = st.selectbox("Ingresá como…", list(_opts.keys()),
                        index=None, placeholder="Elegí tu nombre / rol")
    if st.button("Ingresar →", type="primary", disabled=_sel is None):
        st.query_params["usuario"] = _opts[_sel]
        st.query_params.pop("supervisor", None)
        st.session_state.pop("_acc_usuario", None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Sincronizar sesión y URL.
st.session_state["_acc_usuario"] = usuario["clave"]
if "usuario" not in st.query_params:
    st.query_params["usuario"] = usuario["clave"]

def _barra_usuario():
    """Chip con el usuario activo y botón para cambiar de identidad."""
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            f"<div style='font-size:12px;color:#888;margin-bottom:6px;'>Ingresaste como "
            f"<b style='color:#1a1a2e;'>{usuario['etiqueta']}</b> "
            f"· {acceso.ROL_LABEL[usuario['rol']]}</div>",
            unsafe_allow_html=True)
    with c2:
        if st.button("Cambiar usuario", key="logout"):
            st.query_params.clear()
            st.session_state.pop("_acc_usuario", None)
            st.rerun()

# ── Router ─────────────────────────────────────────────────────────────────────
supervisor_sel = st.query_params.get("supervisor", None)

# Un supervisor no tiene "landing": entra directo a su única zona.
if supervisor_sel is None and usuario["rol"] == "supervisor":
    supervisor_sel = usuario["supervisores"][0]

# Nadie puede ver una zona fuera de su alcance (deep-link manipulado, etc.).
if supervisor_sel is not None and not acceso.puede_ver(usuario, supervisor_sel):
    _barra_usuario()
    st.error(f"No tenés permiso para ver la zona de **{supervisor_sel}**.")
    if st.button("← Volver a mis zonas"):
        st.query_params.pop("supervisor", None)
        st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# LANDING
# ══════════════════════════════════════════════════════════════════════════════
if not supervisor_sel:
    _barra_usuario()
    _titulo = ("👤 Mis supervisores — Wurth Argentina"
               if usuario["rol"] == "director"
               else "👤 Por supervisor — Wurth Argentina")
    st.markdown(page_header(_titulo, "/Supervisor"), unsafe_allow_html=True)

    # Acotar a las zonas que el usuario tiene permitido ver.
    scores_scope = (scores_df if usuario["ve_todo"]
                    else scores_df[scores_df["supervisor"].isin(usuario["supervisores"])])
    if scores_scope.empty:
        st.info("No hay vendedores activos en tu alcance.")
        st.stop()

    resumen = scores_scope.groupby("supervisor").agg(
        activos  =("id_vendedor", "count"),
        criticos =("nivel_riesgo", lambda x: (x=="critico").sum()),
        altos    =("nivel_riesgo", lambda x: (x=="alto").sum()),
        score_max=("score", "max"),
        nombre_grupo=("nombre_grupo", "first"),
    ).reset_index()
    # Agregar permanencia y riesgo_base — tomar el primer grupo del supervisor
    grupos_sup = (grupos_df[["supervisor","permanencia_promedio_meses","riesgo_base"]]
                  .drop_duplicates("supervisor"))
    resumen = resumen.merge(grupos_sup, on="supervisor", how="left"
                  ).sort_values("score_max", ascending=False)

    cols = st.columns(3)
    for i, (_, row) in enumerate(resumen.iterrows()):
        rb    = row.get("riesgo_base", 0.4) or 0.4
        nivel = _zona_nivel(rb)
        cc    = _card_class(nivel)
        perm  = row["permanencia_promedio_meses"]
        perm_str = fmt_meses(round(perm, 1)) if pd.notna(perm) else "—"
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
            if st.button("Ver mis vendedores →", key=f"btn_{i}",
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
        st.query_params.pop("supervisor", None)
        st.rerun()
    st.stop()

grupo_info   = grupos_df[grupos_df["supervisor"] == supervisor_sel]
nombre_grupo = df_sup.iloc[0]["nombre_grupo"]
rb           = df_sup.iloc[0]["grupo_riesgo_base"]
nivel_zona   = _zona_nivel(rb)
perm_zona    = grupo_info["permanencia_promedio_meses"].values[0] if not grupo_info.empty else None
perm_general = grupos_df["permanencia_promedio_meses"].mean()

# Navegación. El supervisor no tiene landing (una sola zona): su botón es
# "Cambiar usuario". El director/staff vuelve al listado de zonas conservando
# su identidad.
_barra_usuario()
nav_b, _ = st.columns([1, 5])
with nav_b:
    if usuario["rol"] == "supervisor":
        if st.button("← Cambiar usuario"):
            st.query_params.clear()
            st.rerun()
    else:
        _volver = "← Mis supervisores" if usuario["rol"] == "director" else "← Todas las zonas"
        if st.button(_volver):
            st.query_params.pop("supervisor", None)
            st.rerun()
st.markdown(page_header(f"👤 {supervisor_sel}", "/Supervisor", sub=fresh(_ts_datos)),
            unsafe_allow_html=True)

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

# Umbral alineado con la señal "grupo_quemado" del motor (riesgo_base > 0.40):
# si los vendedores de esta zona reciben la señal de grupo quemado, el supervisor
# tiene que ver la advertencia. Es la hipótesis central del proyecto.
if rb > 0.40:
    st.warning(f"⚠️ **{nombre_grupo}** es una zona con alta rotación histórica "
               f"(riesgo base {rb:.0%}). Los vendedores nuevos aquí tienen mayor "
               f"probabilidad de irse antes de los 6 meses, incluso sin deterioro "
               f"individual visible. Priorizá el acompañamiento temprano.")

# KPIs
n_activos  = len(df_sup)
n_criticos = len(df_sup[df_sup.nivel_riesgo == "critico"])
n_altos    = len(df_sup[df_sup.nivel_riesgo == "alto"])
n_onb      = len(df_sup[df_sup.meses_activo <= 3])
perm_str   = fmt_meses(round(perm_zona, 1)) if perm_zona and pd.notna(perm_zona) else "—"
diff_perm  = (perm_zona - perm_general) if perm_zona and pd.notna(perm_zona) else None
diff_str   = (f"{'↑' if diff_perm > 0 else '↓'} {fmt_num(abs(diff_perm), 1)} m vs promedio"
              if diff_perm is not None else "")

col_hero, col_stats = st.columns([1, 2.2])
with col_hero:
    _hero_sub = f"{n_criticos} crítico{'s' if n_criticos!=1 else ''} · {n_altos} alto{'s' if n_altos!=1 else ''}"
    st.markdown(hero_kpi("Requieren atención", n_criticos + n_altos, _hero_sub,
                         red=(n_criticos + n_altos) > 0),
                unsafe_allow_html=True)
with col_stats:
    _s1, _s2, _s3 = st.columns(3)
    with _s1:
        st.markdown(stat_kpi("Vendedores activos", fmt_num(n_activos)), unsafe_allow_html=True)
    with _s2:
        st.markdown(stat_kpi("Permanencia prom. zona", perm_str), unsafe_allow_html=True)
    with _s3:
        st.markdown(stat_kpi("En onboarding (1-3m)", fmt_num(n_onb)), unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# Banner de acción — por RANKING, no por umbral fijo (ver dashboard principal):
# en esta población el deterioro es general, así que la guía es "empezá por el
# de mayor score y bajá según tu capacidad", no "todos los que pasen de X".
_n_riesgo = n_criticos + n_altos
if _n_riesgo > 0:
    st.markdown(banner("🔴",
        "Empezá por tus vendedores de mayor score",
        "La tabla está ordenada de mayor a menor riesgo. Trabajá de arriba hacia "
        "abajo según tu capacidad; los niveles (crítico/alto) son guía visual, no "
        "el disparador.", "red"), unsafe_allow_html=True)
else:
    st.markdown(banner("✅", "Sin vendedores en riesgo elevado en tu zona",
        "Igual conviene mirar el top de la tabla, ordenado por score.", "green"),
        unsafe_allow_html=True)

# Tabla
st.markdown('<div class="sec-header">📋 Mis vendedores por score de riesgo</div>',
            unsafe_allow_html=True)
_u_qs = f"&usuario={usuario['clave']}"
rows = ""
for _, r in df_sup.iterrows():
    vid   = int(r["id_vendedor"]); nivel = r["nivel_riesgo"]
    prev  = delta_map.get(vid)
    delta = round(r["score"] - prev, 1) if prev is not None else None
    rows += f"""<tr>
      <td><div class="wz-vn"><a href="/Vendedor?id={vid}{_u_qs}" target="_self">{r['nombre']}</a> <span style="color:#888;font-weight:400;font-size:11px;">({vid})</span></div>
          <div class="wz-vsb">{r['tipo']} · {_fmt_antiguedad(r['meses_activo'])} antigüedad</div></td>
      <td>{_pills(r['señales_activas'])}</td>
      <td><b>{fmt_num(r['pct_plan_3m'])}%</b></td>
      <td>{_spark(sparks.get(vid,[]))}</td>
      <td>{accion_tag(nivel)}</td>
      <td>{score_delta(delta)}</td>
      <td>{_score_circle(r['score'], nivel)}</td>
    </tr>"""

st.markdown(f"""
<div class="wz-card" style="margin-bottom:6px;overflow-x:auto;">
<table class="wz-table">
<thead><tr>
  <th>Vendedor</th><th>Señales detectadas</th>
  <th>% Plan 3m</th><th>Tendencia</th><th>Acción sugerida</th>
  <th title="Variación vs el mes anterior (▲ subió = empeoró, ▼ bajó = mejoró)">Δ mes ⓘ</th>
  <th>Score</th>
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
          <td>{_fmt_antiguedad(r['meses_activo'])}</td><td><b>{fmt_num(r['pct_plan_3m'])}%</b></td>
          <td>{_bdg(nivel)}</td></tr>"""
    st.markdown(f"""
    <div class="wz-card"><table class="ot">
    <thead><tr><th>Vendedor</th><th>Tipo</th><th>Mes</th><th>% Plan</th><th>Riesgo</th></tr></thead>
    <tbody>{ob_rows}</tbody></table></div>""", unsafe_allow_html=True)

st.markdown("<br>")
st.caption("Wurth Argentina · Sistema de alertas de rotación")
