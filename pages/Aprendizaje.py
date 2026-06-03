"""
pages/Aprendizaje.py
--------------------
¿Qué señales separan a los que SE FUERON de los que SE QUEDARON?

La pantalla de Precisión solo mira egresados. Por sí sola no puede decir si una
señal predice una fuga: para eso hay que compararla contra el grupo de control
(los que siguen activos). Si una señal aparece tanto en los que se fueron como
en los que se quedaron, no discrimina nada.

Esta pantalla cruza score_historico de:
  - LEAVERS  : egresados (18 meses) → señales en los 3 meses previos al egreso
  - STAYERS  : activos → señales en el último período del histórico (sobrevivieron)

y calcula, por señal, el "lift" = %leavers / %stayers. Lift alto → discrimina.
Lift ≈ 1 → ruido de fondo.
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import os, sys
import html as _html

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from snippets_v3 import banner, hero_kpi, stat_kpi, fmt_num, fmt_pct

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

# Pesos actuales del score_engine (descripción → peso). Para mostrar junto al lift.
PESOS = {
    "% Plan cayendo 3 meses seguidos":       2.5,
    "% Plan < 80% promedio últimos meses":    2.0,
    "Días sin venta > 3 en promedio":         1.5,
    "< 60% de cartera activa":                1.5,
    "Cobranza real < 90% de teórica":         1.0,
    "En ventana crítica mes 1-3":             1.5,
    "En ventana crítica mes 4-6":             1.0,
    "Grupo con alta rotación histórica":      1.5,
    "Sin clientes nuevos últimos 2 meses":    0.5,
    "< 70% de llamadas planificadas gestionadas (Televentas)": 1.5,
    "< 70% de visitas planificadas realizadas (Viajante)":     1.5,
    "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3": 2.0,
    "Balanza clientes negativa 2+ meses consecutivos":         1.5,
    "Ticket promedio cae > 5% por mes":                        1.0,
    "Supervisor no acompañó en ventana crítica 1-6":           1.0,
}
# Etiqueta corta para mostrar
CORTO = {
    "% Plan cayendo 3 meses seguidos":       "Plan cayendo 3m",
    "% Plan < 80% promedio últimos meses":    "Plan < 80%",
    "Días sin venta > 3 en promedio":         "Días venta cero ↑",
    "< 60% de cartera activa":                "Cartera activa baja",
    "Cobranza real < 90% de teórica":         "Cobranza baja",
    "En ventana crítica mes 1-3":             "Ventana mes 1-3",
    "En ventana crítica mes 4-6":             "Ventana mes 4-6",
    "Grupo con alta rotación histórica":      "Grupo quemado",
    "Sin clientes nuevos últimos 2 meses":    "Sin clientes nuevos",
    "< 70% de llamadas planificadas gestionadas (Televentas)": "Llamadas bajas",
    "< 70% de visitas planificadas realizadas (Viajante)":     "Visitas bajas",
    "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3": "Ausencias tempranas",
    "Balanza clientes negativa 2+ meses consecutivos":         "Balanza negativa",
    "Ticket promedio cae > 5% por mes":                        "Ticket cayendo",
    "Supervisor no acompañó en ventana crítica 1-6":           "Sin acompañamiento",
}
# Señales confundidas con antigüedad (los que se van son más nuevos)
CONFUNDIDAS_TENURE = {
    "En ventana crítica mes 1-3", "En ventana crítica mes 4-6",
    "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3",
    "Supervisor no acompañó en ventana crítica 1-6",
}

st.set_page_config(
    page_title="Wurth | Aprendizaje del modelo",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_v3_css = os.path.join(os.path.dirname(__file__), '..', 'assets', 'dashboard-v3.css')
st.markdown(f"<style>{open(_v3_css, encoding='utf-8').read()}</style>", unsafe_allow_html=True)

st.markdown("""<style>
[data-testid="stSidebar"] { display: none; }
[data-testid="stHeader"]  { display: none; }
.block-container { padding: 2.5rem 2.5rem 4rem !important; max-width: 100% !important; }
header { display: none; }
.sec-header { font-size: 15px; font-weight: 700; color: #1a1a2e; margin: 24px 0 12px; }
.card { background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.lift-tbl { width: 100%; border-collapse: collapse; font-family: var(--font, sans-serif); }
.lift-tbl th { background: #f8f9fa; padding: 9px 12px; text-align: left;
               font-size: 11px; font-weight: 700; color: #666;
               border-bottom: 2px solid #e9ecef; text-transform: uppercase; }
.lift-tbl td { padding: 10px 12px; border-bottom: 1px solid #f2f2f2;
               font-size: 12.5px; vertical-align: middle; }
.lift-tbl tr:hover td { background: #fafafa; }
.cmp-row { display:flex; align-items:center; gap:10px; margin:7px 0; }
.cmp-lbl { width:160px; font-size:12px; color:#444; flex-shrink:0; font-weight:600;
           overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.cmp-bars { flex:1; display:flex; flex-direction:column; gap:3px; }
.cmp-bar  { height:11px; border-radius:3px; min-width:3px; }
</style>""", unsafe_allow_html=True)

# ── Nav ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center;
            margin-bottom:20px; padding-bottom:14px; border-bottom:1px solid #eee;">
  <div style="font-size:20px; font-weight:800; color:#1a1a2e;">🧠 Aprendizaje del modelo — Wurth Argentina</div>
  <div style="font-size:13px; display:flex; gap:20px; flex-wrap:wrap;">
    <a href="/"               target="_self" style="color:#4A90D9;text-decoration:none;">🏠 Inicio</a>
    <a href="/Precision"      target="_self" style="color:#4A90D9;text-decoration:none;">🎯 Precisión</a>
    <a href="/Supervisor"     target="_self" style="color:#4A90D9;text-decoration:none;">👤 Por supervisor</a>
    <a href="/Historial"      target="_self" style="color:#4A90D9;text-decoration:none;">📈 Historial</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Chequeo de datos ───────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def hay_historico():
    con = sqlite3.connect(DB_PATH)
    try:
        n = pd.read_sql("SELECT COUNT(*) n FROM score_historico", con).iloc[0]["n"]
    except Exception:
        n = 0
    con.close()
    return int(n)

if hay_historico() == 0:
    st.markdown(banner("📋",
        "Todavía no hay datos de backfill",
        "Ejecutá scripts/backfill_scores.bat para calcular el historial de scores. "
        "Esta pantalla lo necesita para comparar a los que se fueron contra los que se quedaron.",
        "blue"), unsafe_allow_html=True)
    st.stop()

# ── Carga ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar():
    con = sqlite3.connect(DB_PATH)
    sh = pd.read_sql("SELECT periodo, id_vendedor, señales FROM score_historico", con)
    vend = pd.read_sql("""
        SELECT id_vendedor, nombre, tipo, activo, fecha_egreso,
               CAST(strftime('%Y', fecha_egreso) AS INTEGER) ae,
               CAST(strftime('%m', fecha_egreso) AS INTEGER) me
        FROM vendedores
        WHERE id_vendedor != 9800
    """, con)
    con.close()
    sh["sig"] = sh["señales"].apply(lambda x: json.loads(x) if x else [])
    return sh, vend

sh, vend = cargar()

# Filtro por tipo (para comparación justa)
tipo_sel = st.radio("Comparar dentro de:", ["Todos", "Viajante", "Televentas"],
                    horizontal=True, index=0)
if tipo_sel != "Todos":
    ids_tipo = set(vend[vend["tipo"] == tipo_sel]["id_vendedor"])
    vend = vend[vend["tipo"] == tipo_sel]
    sh = sh[sh["id_vendedor"].isin(ids_tipo)]

# ── Construir grupos ───────────────────────────────────────────────────────────
def _idx(a, m):       # índice de mes absoluto
    return a * 12 + (m - 1)
def _periodo(a, m, n):  # n meses hacia atrás de (a,m)
    i = _idx(a, m) - n
    return f"{i // 12}-{i % 12 + 1:02d}"

anchor = sh["periodo"].max()
ay, am = map(int, anchor.split("-"))

# STAYERS: activos con señales en el período anchor
act_ids = set(vend[vend["activo"] == 1]["id_vendedor"])
stay = sh[(sh["periodo"] == anchor) & (sh["id_vendedor"].isin(act_ids))]
stayer_sets = [set(s) for s in stay["sig"].tolist()]

# LEAVERS: egresados dentro de 18 meses del anchor, señales en 3 meses pre-egreso
lim = _idx(ay, am) - 18
leav = vend[(vend["activo"] == 0) & (vend["fecha_egreso"].notna()) & (vend["ae"].notna())].copy()
leav = leav[leav.apply(lambda r: lim <= _idx(int(r["ae"]), int(r["me"])) <= _idx(ay, am), axis=1)]

leaver_sets = []
for _, r in leav.iterrows():
    pers = [_periodo(int(r["ae"]), int(r["me"]), k) for k in (1, 2, 3)]
    sub = sh[(sh["id_vendedor"] == r["id_vendedor"]) & (sh["periodo"].isin(pers))]
    if sub.empty:
        continue
    s = set()
    for lst in sub["sig"]:
        s.update(lst)
    leaver_sets.append(s)

n_leav, n_stay = len(leaver_sets), len(stayer_sets)

if n_leav == 0 or n_stay == 0:
    st.warning(
        f"No hay suficientes datos para comparar (leavers con datos: {n_leav}, "
        f"stayers: {n_stay}). Asegurate de tener backfill suficiente y egresados "
        f"con historial de ventas."
    )
    st.stop()

# ── Calcular lift por señal ────────────────────────────────────────────────────
filas = []
for sig, peso in PESOS.items():
    pl = sum(1 for s in leaver_sets if sig in s) / n_leav * 100
    ps = sum(1 for s in stayer_sets if sig in s) / n_stay * 100
    if ps > 0:
        lift = pl / ps
    elif pl > 0:
        lift = 99.0
    else:
        lift = 0.0
    filas.append({
        "señal": sig, "corto": CORTO.get(sig, sig[:18]), "peso": peso,
        "pct_leavers": round(pl), "pct_stayers": round(ps),
        "lift": round(lift, 1), "diff": round(pl - ps),
        "tenure": sig in CONFUNDIDAS_TENURE,
    })
res = pd.DataFrame(filas).sort_values("lift", ascending=False).reset_index(drop=True)

# ── KPIs ───────────────────────────────────────────────────────────────────────
total_egresados = len(leav)
mejor = res.iloc[0]
col_hero, col_stats = st.columns([1, 2.2])
with col_hero:
    st.markdown(hero_kpi(
        "Señal que más discrimina",
        mejor["corto"],
        f"Aparece en {mejor['pct_leavers']}% de los que se fueron vs {mejor['pct_stayers']}% "
        f"de los que se quedaron (lift {fmt_num(mejor['lift'],1)}×)",
    ), unsafe_allow_html=True)
with col_stats:
    _s1, _s2, _s3, _s4 = st.columns(4)
    with _s1:
        st.markdown(stat_kpi("Se fueron (con datos)", fmt_num(n_leav)), unsafe_allow_html=True)
    with _s2:
        st.markdown(stat_kpi("Se quedaron (control)", fmt_num(n_stay)), unsafe_allow_html=True)
    with _s3:
        utiles = int((res["lift"] >= 1.5).sum())
        st.markdown(stat_kpi("Señales que discriminan", fmt_num(utiles)), unsafe_allow_html=True)
    with _s4:
        ruido = int(((res["lift"] < 1.2) & (res["pct_leavers"] > 0)).sum())
        st.markdown(stat_kpi("Señales tipo ruido", fmt_num(ruido)), unsafe_allow_html=True)

st.markdown(f"<div style='font-size:12px;color:#888;margin:6px 0 4px;'>"
            f"Período de referencia: {anchor} · comparación: {tipo_sel}</div>",
            unsafe_allow_html=True)

# ── Gráfico comparativo ────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📊 Prevalencia de cada señal: se fueron vs. se quedaron</div>',
            unsafe_allow_html=True)
st.caption("Barra roja = % de los que se fueron con la señal activa. Barra gris = % de los "
           "que se quedaron. Cuanto más larga la roja respecto a la gris, más discrimina la señal.")

bars = ""
for _, r in res.iterrows():
    wl = max(2, r["pct_leavers"])
    ws = max(2, r["pct_stayers"])
    lbl = _html.escape(r["corto"]) + (" ⚠️" if r["tenure"] else "")
    bars += (
        '<div class="cmp-row">'
        f'<div class="cmp-lbl" title="{_html.escape(r["señal"])}">{lbl}</div>'
        '<div class="cmp-bars">'
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'<div class="cmp-bar" style="width:{wl}%;background:#E24B4A;"></div>'
        f'<span style="font-size:10px;color:#E24B4A;font-weight:700;">{r["pct_leavers"]}%</span></div>'
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'<div class="cmp-bar" style="width:{ws}%;background:#bbb;"></div>'
        f'<span style="font-size:10px;color:#999;">{r["pct_stayers"]}%</span></div>'
        '</div>'
        f'<div style="width:70px;text-align:right;font-size:13px;font-weight:800;'
        f'color:{"#639922" if r["lift"]>=2 else "#EF9F27" if r["lift"]>=1.2 else "#aaa"};">'
        f'{fmt_num(r["lift"],1)}×</div>'
        '</div>'
    )
st.markdown(f'<div class="card">{bars}'
            '<div style="font-size:10px;color:#aaa;margin-top:10px;">'
            '🟥 se fueron &nbsp; ⬜ se quedaron &nbsp;·&nbsp; ⚠️ = confundida con antigüedad '
            '(los que se van son más nuevos, así que estas señales exageran su poder)</div></div>',
            unsafe_allow_html=True)

# ── Tabla detalle ──────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📋 Detalle y lectura por señal</div>', unsafe_allow_html=True)

def _lectura(r):
    if r["tenure"]:
        return ('<span style="color:#888;">Confundida con antigüedad — interpretá con cuidado</span>')
    if r["lift"] >= 2:
        return '<span style="color:#639922;font-weight:700;">Discrimina fuerte ✓</span>'
    if r["lift"] >= 1.2:
        return '<span style="color:#EF9F27;font-weight:700;">Discrimina algo</span>'
    if r["pct_leavers"] == 0 and r["pct_stayers"] == 0:
        return '<span style="color:#ccc;">Sin casos en este corte</span>'
    return '<span style="color:#aaa;">Ruido — no separa los grupos</span>'

rows = ""
for _, r in res.iterrows():
    rows += (
        "<tr>"
        f'<td style="font-weight:600;">{_html.escape(r["corto"])}'
        f'{" ⚠️" if r["tenure"] else ""}</td>'
        f'<td>{fmt_num(r["peso"],1)}</td>'
        f'<td style="color:#E24B4A;font-weight:700;">{r["pct_leavers"]}%</td>'
        f'<td style="color:#888;">{r["pct_stayers"]}%</td>'
        f'<td style="font-weight:800;">{fmt_num(r["lift"],1)}×</td>'
        f'<td>{_lectura(r)}</td>'
        "</tr>"
    )
st.markdown(
    '<div class="card" style="overflow-x:auto;"><table class="lift-tbl"><thead><tr>'
    '<th>Señal</th><th>Peso actual</th><th>% se fueron</th><th>% se quedaron</th>'
    '<th>Lift</th><th>Lectura</th></tr></thead>'
    f'<tbody>{rows}</tbody></table></div>',
    unsafe_allow_html=True)

# ── Sugerencias de re-peso ─────────────────────────────────────────────────────
st.markdown('<div class="sec-header">💡 Qué sugiere la evidencia (no aplicado automáticamente)</div>',
            unsafe_allow_html=True)

no_tenure = res[~res["tenure"]]
subir = no_tenure[(no_tenure["lift"] >= 2.5) & (no_tenure["peso"] <= 1.5)]
bajar = no_tenure[(no_tenure["lift"] < 1.2) & (no_tenure["peso"] >= 1.5) &
                  (no_tenure["pct_leavers"] > 0)]

sug = []
for _, r in subir.iterrows():
    sug.append(f'⬆️ <b>{_html.escape(r["corto"])}</b>: discrimina fuerte (lift '
               f'{fmt_num(r["lift"],1)}×) pero pesa solo {fmt_num(r["peso"],1)}. '
               f'Candidata a <b>subir peso</b>.')
for _, r in bajar.iterrows():
    sug.append(f'⬇️ <b>{_html.escape(r["corto"])}</b>: pesa {fmt_num(r["peso"],1)} pero '
               f'casi no separa los grupos (lift {fmt_num(r["lift"],1)}×). '
               f'Candidata a <b>bajar peso</b>.')

if sug:
    items = "".join(f'<li style="margin:8px 0;line-height:1.5;">{s}</li>' for s in sug)
    st.markdown(f'<div class="card"><ul style="margin:0;padding-left:20px;font-size:13px;color:#444;">'
                f'{items}</ul></div>', unsafe_allow_html=True)
else:
    st.info("Con los datos actuales no hay candidatos claros de re-peso. "
            "Con más meses de backfill esto se va a definir mejor.")

with st.expander("⚠️ Cómo leer esto sin engañarse (importante)"):
    st.markdown("""
**El lift es evidencia, no prueba.** Antes de cambiar pesos, tené en cuenta:

- **Confusión con antigüedad (⚠️):** los que se van son, en promedio, más nuevos. Las
  señales de ventana crítica y de inducción van a parecer muy discriminantes solo porque
  los leavers son más jóvenes en la empresa, no porque la señal capture deterioro real.
  Por eso están marcadas y excluidas de las sugerencias de re-peso.

- **Tamaño de muestra:** con pocos egresados con datos, un lift alto puede ser azar.
  Mirá los conteos arriba antes de sacar conclusiones.

- **El control se mide en un punto, los leavers antes de irse:** los stayers se evalúan
  en el último período; los leavers en sus 3 meses previos al egreso. No es un experimento
  perfecto, es la mejor aproximación con los datos que hay.

- **Correlación ≠ causa:** que una señal discrimine no significa que mejorarla evite la
  fuga. Sirve para *detectar*, no necesariamente para *intervenir*.

- **Validación real (próximo paso):** entrenar pesos con datos viejos y testear sobre
  egresados recientes. Si predice ahí, es real; si no, era sobreajuste.
""")

st.caption(
    f"Comparación basada en score_historico. Leavers: egresados ≤18 meses del período "
    f"{anchor} con señales en sus 3 meses previos. Stayers: activos en {anchor}. "
    "Para actualizar, recalculá el backfill y recargá."
)
