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
from snippets_v3 import banner, hero_kpi, stat_kpi, fmt_num, fmt_pct, page_header

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

# ── Acceso (solo Gerencia) ────────────────────────────────────────────────────
import acceso as _acc
_usuario = _acc.requerir_acceso(roles=["gerencia", "rrhh"])

# ── Nav ────────────────────────────────────────────────────────────────────────
st.markdown(page_header("🧠 Aprendizaje del modelo — Wurth Argentina", "/Aprendizaje"),
            unsafe_allow_html=True)

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
        f"No hay suficientes datos para comparar (egresados con datos: {n_leav}, "
        f"activos: {n_stay}). Asegurate de tener backfill suficiente y egresados "
        f"con historial de ventas."
    )
    st.stop()

# ── Cómo leer esta pantalla ────────────────────────────────────────────────────
st.markdown("""
<div class="card" style="margin-bottom:20px;border-left:4px solid #4A90D9;">
<div style="font-size:14px;font-weight:700;color:#1a1a2e;margin-bottom:10px;">
  📖 Cómo leer esta pantalla — en dos oraciones
</div>
<p style="font-size:13px;color:#444;line-height:1.7;margin:0 0 10px;">
  Comparamos <b>los que se fueron</b> vs. <b>los que se quedaron</b>:
  si una señal aparece mucho más en los que se fueron que en los activos, es una señal útil.
  Si aparece igual en los dos grupos, no sirve para predecir.
</p>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-top:12px;">
  <div style="background:#f0fff4;border-radius:8px;padding:10px 12px;">
    <div style="font-size:12px;font-weight:800;color:#639922;margin-bottom:4px;">✅ Señal útil</div>
    <div style="font-size:12px;color:#444;line-height:1.5;">Aparece mucho más en los que se fueron. Cuando se enciende, hay que prestar atención.</div>
  </div>
  <div style="background:#fffbf0;border-radius:8px;padding:10px 12px;">
    <div style="font-size:12px;font-weight:800;color:#EF9F27;margin-bottom:4px;">🟡 Señal débil</div>
    <div style="font-size:12px;color:#444;line-height:1.5;">Algo más frecuente en los que se fueron, pero la diferencia no es grande. Sirve como apoyo.</div>
  </div>
  <div style="background:#f8f8f8;border-radius:8px;padding:10px 12px;">
    <div style="font-size:12px;font-weight:800;color:#aaa;margin-bottom:4px;">⬜ Ruido</div>
    <div style="font-size:12px;color:#444;line-height:1.5;">Aparece igual en los que se fueron y en los activos. No predice nada útil.</div>
  </div>
  <div style="background:#fffdf0;border-radius:8px;padding:10px 12px;">
    <div style="font-size:12px;font-weight:800;color:#888;margin-bottom:4px;">⚠️ Trampa estadística</div>
    <div style="font-size:12px;color:#444;line-height:1.5;">Los que se van son más nuevos. Estas señales parecen útiles solo porque detectan "vendedor nuevo", no deterioro real.</div>
  </div>
</div>
<p style="font-size:12px;color:#888;margin:12px 0 0;">
  <b>El número "× veces"</b> es cuántas veces más frecuente es la señal en los que se fueron vs. los activos.
  5× = si esta señal está encendida, es 5 veces más probable que se trate de alguien en riesgo real.
</p>
</div>
""", unsafe_allow_html=True)

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
        "Señal más predictiva",
        mejor["corto"],
        f"{mejor['pct_leavers']}% de los que se fueron la tenían vs "
        f"{mejor['pct_stayers']}% de los activos — {fmt_num(mejor['lift'],1)}× más frecuente",
    ), unsafe_allow_html=True)
with col_stats:
    _s1, _s2, _s3, _s4 = st.columns(4)
    with _s1:
        st.markdown(stat_kpi("Vendedores que se fueron", fmt_num(n_leav)), unsafe_allow_html=True)
    with _s2:
        st.markdown(stat_kpi("Activos (grupo de control)", fmt_num(n_stay)), unsafe_allow_html=True)
    with _s3:
        utiles = int(((res["lift"] >= 1.5) & (~res["tenure"])).sum())
        st.markdown(stat_kpi("Señales útiles (sin trampas)", fmt_num(utiles)), unsafe_allow_html=True)
    with _s4:
        ruido = int(((res["lift"] < 1.2) & (~res["tenure"]) & (res["pct_leavers"] > 0)).sum())
        st.markdown(stat_kpi("Señales que son ruido", fmt_num(ruido)), unsafe_allow_html=True)

st.markdown(f"<div style='font-size:12px;color:#888;margin:6px 0 4px;'>"
            f"Período analizado: {anchor} · filtro: {tipo_sel}</div>",
            unsafe_allow_html=True)

# ── Gráfico comparativo ────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📊 ¿Qué tan seguido tenía cada señal encendida antes de irse?</div>',
            unsafe_allow_html=True)
st.caption(
    "Cada señal tiene dos barras: 🟥 cuántos de los que SE FUERON la tenían encendida "
    "· ⬜ cuántos de los que SE QUEDARON la tienen encendida. "
    "Una señal útil tiene barra roja larga y gris corta. "
    "Si las dos barras son del mismo tamaño, la señal no sirve para predecir."
)

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
            '🟥 se fueron &nbsp;·&nbsp; ⬜ se quedaron &nbsp;·&nbsp; '
            '⚠️ = trampa estadística (vendedor nuevo, no deterioro)</div></div>',
            unsafe_allow_html=True)

# ── Tabla detalle ──────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📋 Tabla completa por señal</div>', unsafe_allow_html=True)

def _lectura(r):
    if r["tenure"]:
        return ('<span style="color:#888;">⚠️ Trampa — los que se van son más nuevos, '
                'esta señal detecta eso, no deterioro real</span>')
    if r["pct_leavers"] == 0 and r["pct_stayers"] == 0:
        return '<span style="color:#ccc;">Sin casos — esta señal no se enciende en nadie</span>'
    # Señal casi ausente en los que se fueron pero presente en activos →
    # casi seguro falta el dato en los egresados, no es un hallazgo real.
    if r["pct_leavers"] < 5 and r["pct_stayers"] >= 20:
        return ('<span style="color:#C0392B;">🔧 Revisar datos — casi no aparece en los que '
                'se fueron pero sí en los activos. Probablemente falta el dato en los egresados.</span>')
    if r["lift"] >= 2:
        return '<span style="color:#639922;font-weight:700;">✅ Señal útil — cuando se enciende, prestar atención</span>'
    if r["lift"] >= 1.2:
        return '<span style="color:#EF9F27;font-weight:700;">🟡 Señal débil — sirve como apoyo</span>'
    return '<span style="color:#aaa;">⬜ Ruido — aparece parecido en los dos grupos, no predice nada</span>'

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
    '<th>Señal</th><th>Peso actual</th>'
    '<th>Se fueron (tenían esta señal)</th><th>Se quedaron (la tienen)</th>'
    '<th>Cuántas veces más frecuente en los que se fueron</th><th>¿Vale la pena?</th>'
    '</tr></thead>'
    f'<tbody>{rows}</tbody></table></div>',
    unsafe_allow_html=True)

# ── Sugerencias de re-peso ─────────────────────────────────────────────────────
st.markdown('<div class="sec-header">💡 Qué sugiere la evidencia sobre los pesos del score</div>',
            unsafe_allow_html=True)

no_tenure = res[~res["tenure"]]
# Señales con datos confiables: se encienden de forma plausible en los que se
# fueron (>= 20%). Si una señal casi no aparece en egresados, probablemente
# falta el dato y NO se puede concluir nada — se excluye de las sugerencias.
confiables = no_tenure[no_tenure["pct_leavers"] >= 20]
subir = confiables[(confiables["lift"] >= 2.5) & (confiables["peso"] <= 1.5)]
# "Ruido honesto": aparece parecido en ambos grupos (no invertido por falta de dato).
bajar = confiables[(confiables["lift"] >= 0.8) & (confiables["lift"] < 1.2) &
                   (confiables["peso"] >= 1.5)]
# Señales sospechosas de falta de datos (no son sugerencias, son alertas de calidad).
falta_datos = no_tenure[(no_tenure["pct_leavers"] < 5) & (no_tenure["pct_stayers"] >= 20)]

sug = []
for _, r in subir.iterrows():
    sug.append(
        f'⬆️ <b>{_html.escape(r["corto"])}</b>: aparece en el {r["pct_leavers"]}% de los que '
        f'se fueron pero solo en el {r["pct_stayers"]}% de los activos '
        f'({fmt_num(r["lift"],1)}× más frecuente en fugas). Hoy pesa solo {fmt_num(r["peso"],1)} '
        f'— la evidencia sugiere que debería pesar más.'
    )
for _, r in bajar.iterrows():
    sug.append(
        f'⬇️ <b>{_html.escape(r["corto"])}</b>: aparece parecido en los que se fueron '
        f'({r["pct_leavers"]}%) y en los activos ({r["pct_stayers"]}%). '
        f'Hoy pesa {fmt_num(r["peso"],1)} pero no separa los grupos — candidata a bajar peso.'
    )

# Alerta de calidad de datos (antes que las sugerencias)
if len(falta_datos) > 0:
    nombres = ", ".join(f'<b>{_html.escape(x)}</b>' for x in falta_datos["corto"])
    st.markdown(
        f'<div class="card" style="border-left:4px solid #C0392B;margin-bottom:14px;">'
        f'<div style="font-size:14px;font-weight:700;color:#C0392B;margin-bottom:8px;">'
        f'🔧 Antes de leer las sugerencias: hay un problema de datos</div>'
        f'<p style="font-size:13px;color:#444;line-height:1.6;margin:0;">'
        f'Estas señales casi no aparecen en los que se fueron pero sí en los activos: {nombres}. '
        f'Eso casi nunca es una conducta real — lo más probable es que <b>a los egresados les '
        f'falte ese dato</b> en la base (se sincronizaron sus ventas pero no las tablas '
        f'secundarias). Mientras esto no se arregle, esas señales no se pueden comparar y '
        f'quedan fuera de las sugerencias de abajo.</p></div>',
        unsafe_allow_html=True)

if sug:
    items = "".join(f'<li style="margin:8px 0;line-height:1.6;">{s}</li>' for s in sug)
    st.markdown(
        '<div class="card">'
        '<p style="font-size:13px;color:#555;margin:0 0 12px;">Estas son sugerencias basadas '
        'en los datos históricos. <b>No se aplican solas</b> — requieren validación antes '
        'de cambiar el score (ver nota abajo).</p>'
        f'<ul style="margin:0;padding-left:20px;font-size:13px;color:#444;">{items}</ul>'
        '</div>', unsafe_allow_html=True)
else:
    st.info("Con los datos actuales no hay candidatos claros de re-peso. "
            "Con más meses de backfill esto se va a definir mejor.")

with st.expander("⚠️ Antes de cambiar pesos — leé esto"):
    st.markdown("""
**Estas sugerencias son indicios, no certezas.** Tres cosas que podés estar viendo sin querer:

- **La trampa de la antigüedad:** los que se van son más nuevos en promedio. Las señales
  marcadas con ⚠️ parecen útiles solo porque detectan "vendedor nuevo", no porque capturen
  deterioro real. Por eso están excluidas de las sugerencias de arriba.

- **Pocos casos:** con 172 egresados, un porcentaje alto puede ser solo 10-15 personas.
  Mirá siempre los números absolutos antes de sacar conclusiones.

- **Detección ≠ prevención:** que una señal aparezca mucho antes de que alguien se vaya
  no significa que si "arreglamos" esa señal el vendedor se quede. La cobranza baja, por
  ejemplo, puede ser consecuencia de que el vendedor ya decidió irse, no la causa.

**El paso siguiente correcto** es validar: tomar los pesos sugeridos, probarlos solo con
datos viejos (por ejemplo 2022-2023) y ver si hubieran predicho mejor los egresos de
2024. Si sí → tiene sentido cambiarlos. Si no → era sobreajuste.
""")

st.caption(
    f"Comparación basada en score_historico. Leavers: egresados ≤18 meses del período "
    f"{anchor} con señales en sus 3 meses previos. Stayers: activos en {anchor}. "
    "Para actualizar, recalculá el backfill y recargá."
)
