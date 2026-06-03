"""
pages/Precision.py
------------------
¿El modelo hubiera detectado a los que se fueron?

Cruza score_historico (generado por scripts/backfill_scores.py) con
los vendedores que efectivamente se fueron, para medir precisión y
aprender de los falsos negativos.
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import os, sys
import html as _html
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from snippets_v3 import (
    banner, hero_kpi, stat_kpi, badge, pill,
    fmt_num, fmt_pct, fmt_meses,
)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

st.set_page_config(
    page_title="Wurth | Precisión del modelo",
    page_icon="🎯",
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
.sec-header { font-size: 15px; font-weight: 700; color: #1a1a2e; margin: 20px 0 12px; }
.card { background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.det-tbl { width: 100%; border-collapse: collapse; font-family: var(--font, sans-serif); }
.det-tbl th { background: #f8f9fa; padding: 9px 12px; text-align: left;
              font-size: 11px; font-weight: 700; color: #666;
              border-bottom: 2px solid #e9ecef; text-transform: uppercase; }
.det-tbl td { padding: 10px 12px; border-bottom: 1px solid #f2f2f2;
              font-size: 12.5px; vertical-align: middle; }
.det-tbl tr:hover td { background: #fafafa; }
.tag-det  { display:inline-block; padding:2px 7px; border-radius:4px;
            font-size:11px; font-weight:700;
            background:#D4EDDA; color:#155724; }
.tag-miss { display:inline-block; padding:2px 7px; border-radius:4px;
            font-size:11px; font-weight:700;
            background:#FFE0E0; color:#C0392B; }
.sig-bar  { display:flex; align-items:center; gap:8px; margin:3px 0; font-size:12px; }
.sig-fill { height:10px; border-radius:3px; min-width:4px; }
</style>""", unsafe_allow_html=True)

# ── Nav ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center;
            margin-bottom:20px; padding-bottom:14px; border-bottom:1px solid #eee;">
  <div style="font-size:20px; font-weight:800; color:#1a1a2e;">🎯 Precisión del modelo — Wurth Argentina</div>
  <div style="font-size:13px; display:flex; gap:20px; flex-wrap:wrap;">
    <a href="/"               target="_self" style="color:#4A90D9;text-decoration:none;">🏠 Inicio</a>
    <a href="/Supervisor"     target="_self" style="color:#4A90D9;text-decoration:none;">👤 Por supervisor</a>
    <a href="/Intervenciones" target="_self" style="color:#4A90D9;text-decoration:none;">📝 Intervenciones</a>
    <a href="/Historial"      target="_self" style="color:#4A90D9;text-decoration:none;">📈 Historial</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Chequeo de datos ───────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def hay_score_historico():
    con = sqlite3.connect(DB_PATH)
    try:
        n = pd.read_sql("SELECT COUNT(*) as n FROM score_historico", con).iloc[0]["n"]
    except Exception:
        n = 0
    con.close()
    return int(n)

n_hist = hay_score_historico()

if n_hist == 0:
    st.markdown(banner("📋",
        "Todavía no hay datos de backfill",
        "Ejecutá scripts/backfill_scores.bat para calcular el historial de scores de los últimos 18 meses. "
        "Tarda unos minutos y solo hay que hacerlo una vez.",
        "blue"), unsafe_allow_html=True)

    st.markdown("""
<div class="card" style="margin-top:16px;">
  <div style="font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:12px;">¿Qué es esto y cómo funciona?</div>
  <p style="font-size:13px;color:#555;line-height:1.7;">
    El sistema calcula el score <b>al vuelo</b> con datos del mes actual — no guarda un historial.
    Eso hace imposible saber si los vendedores que se fueron <b>tenían score alto antes de irse</b>.
  </p>
  <p style="font-size:13px;color:#555;line-height:1.7;">
    El backfill resuelve eso: retrocede mes a mes (hasta 18 meses) y recalcula el score
    como si fuera cada mes pasado, usando los datos de <code>ventas_mensual</code> que sí están guardados.
    El resultado va a la tabla <code>score_historico</code> en <code>wurth.db</code>.
  </p>
  <p style="font-size:13px;color:#555;line-height:1.7;">
    Después, esta pantalla cruza esos scores históricos con los vendedores que efectivamente se fueron
    para responder: <b>¿los hubiéramos detectado?</b> Y si no: <b>¿qué señal nos estamos perdiendo?</b>
  </p>
  <div style="background:#f8f9fa;border-radius:8px;padding:12px 16px;margin-top:12px;font-size:12px;color:#666;">
    <b>Para ejecutar:</b><br>
    1. Abrí una terminal en la carpeta del proyecto<br>
    2. Doble clic en <code>scripts/backfill_scores.bat</code><br>
    3. Esperá que termine (barra de progreso en la terminal)<br>
    4. Recargá esta pantalla
  </div>
</div>""", unsafe_allow_html=True)
    st.stop()

# ── Carga de datos ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_datos():
    con = sqlite3.connect(DB_PATH)

    # Egresados en los últimos 18 meses con motivo de renuncia/abandono
    egresados = pd.read_sql("""
        SELECT id_vendedor, nombre, tipo, nombre_grupo, supervisor,
               fecha_ingreso, fecha_egreso, motivo_egreso,
               strftime('%Y-%m', fecha_egreso) as periodo_egreso,
               CAST(strftime('%Y', fecha_egreso) AS INTEGER) as anio_egreso,
               CAST(strftime('%m', fecha_egreso) AS INTEGER) as mes_egreso
        FROM vendedores
        WHERE activo = 0
          AND fecha_egreso IS NOT NULL
          AND fecha_ingreso IS NOT NULL
          AND fecha_egreso != fecha_ingreso
          AND fecha_egreso >= date('now', '-18 months')
          AND id_vendedor != 9800
    """, con)

    # Score histórico
    sh = pd.read_sql("""
        SELECT periodo, id_vendedor, score, nivel, señales,
               pct_plan_3m, tendencia_plan, dias_cero_prom, pct_cobranza, meses_activo
        FROM score_historico
    """, con)
    con.close()
    return egresados, sh


egresados_df, sh_df = cargar_datos()

if egresados_df.empty:
    st.info("No hay egresados en los últimos 18 meses para analizar.")
    st.stop()

# ── Función: obtener score del mes previo al egreso ────────────────────────────
def mes_previo_str(anio, mes):
    mes -= 1
    if mes == 0:
        mes = 12
        anio -= 1
    return f"{anio}-{mes:02d}"


def get_max_score_pre_egreso(id_vendedor, anio_egreso, mes_egreso, n_meses=3):
    """Score máximo en los N meses previos al egreso."""
    periodos = []
    a, m = anio_egreso, mes_egreso
    for _ in range(n_meses):
        a2, m2 = a, m - 1
        if m2 == 0:
            m2 = 12
            a2 -= 1
        periodos.append(f"{a2}-{m2:02d}")
        a, m = a2, m2

    sub = sh_df[(sh_df["id_vendedor"] == id_vendedor) &
                (sh_df["periodo"].isin(periodos))]
    if sub.empty:
        return None, None, None, []
    idx = sub["score"].idxmax()
    row = sub.loc[idx]
    try:
        señales = json.loads(row["señales"]) if row["señales"] else []
    except Exception:
        señales = []
    return float(row["score"]), row["nivel"], row["periodo"], señales


# ── Construir tabla de análisis ────────────────────────────────────────────────
registros = []
for _, eg in egresados_df.iterrows():
    score, nivel, periodo_score, señales = get_max_score_pre_egreso(
        eg["id_vendedor"], eg["anio_egreso"], eg["mes_egreso"]
    )
    registros.append({
        "id_vendedor":   int(eg["id_vendedor"]),
        "nombre":        eg["nombre"],
        "tipo":          eg["tipo"],
        "nombre_grupo":  eg["nombre_grupo"],
        "supervisor":    eg["supervisor"],
        "periodo_egreso":eg["periodo_egreso"],
        "motivo_egreso": eg["motivo_egreso"] or "—",
        "score_previo":  score,
        "nivel_previo":  nivel,
        "periodo_score": periodo_score,
        "señales":       señales,
        "detectado":     (score is not None and score >= 6),
        "sin_datos":     (score is None),
    })

analisis = pd.DataFrame(registros)

con_datos   = analisis[~analisis["sin_datos"]]
detectados  = con_datos[con_datos["detectado"]]
no_detectados = con_datos[~con_datos["detectado"]]
sin_datos   = analisis[analisis["sin_datos"]]

total_cd   = len(con_datos)
n_det      = len(detectados)
n_miss     = len(no_detectados)
pct_det    = round(n_det / total_cd * 100) if total_cd > 0 else 0

# ── KPIs ───────────────────────────────────────────────────────────────────────
col_hero, col_stats = st.columns([1, 2.2])
with col_hero:
    st.markdown(hero_kpi(
        "Detectados antes de irse",
        fmt_pct(pct_det),
        f"{n_det} de {total_cd} vendedores que se fueron tenían score ≥ 6",
        red=(pct_det < 50),
    ), unsafe_allow_html=True)
with col_stats:
    _s1, _s2, _s3, _s4 = st.columns(4)
    with _s1:
        st.markdown(stat_kpi("Egresados analizados", fmt_num(total_cd)), unsafe_allow_html=True)
    with _s2:
        st.markdown(stat_kpi("No detectados (miss)", fmt_num(n_miss)), unsafe_allow_html=True)
    with _s3:
        st.markdown(stat_kpi("Sin datos de score", fmt_num(len(sin_datos))), unsafe_allow_html=True)
    with _s4:
        score_prom_det  = round(detectados["score_previo"].mean(), 1) if n_det > 0 else 0
        score_prom_miss = round(no_detectados["score_previo"].mean(), 1) if n_miss > 0 else 0
        st.markdown(stat_kpi("Score prom. no detectados", fmt_num(score_prom_miss, 1)),
                    unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# Banner
if pct_det >= 70:
    st.markdown(banner("✅",
        f"El modelo detectó al {fmt_pct(pct_det)} de los que se fueron",
        f"{n_miss} no detectados — revisá la tabla de abajo para ver qué señales les faltaban.",
        "green"), unsafe_allow_html=True)
elif pct_det >= 40:
    st.markdown(banner("🟠",
        f"El modelo detectó al {fmt_pct(pct_det)} de los que se fueron",
        f"{n_miss} falsos negativos — las señales de abajo muestran qué está pasando por alto.",
        "orange"), unsafe_allow_html=True)
else:
    st.markdown(banner("🔴",
        f"El modelo solo detectó al {fmt_pct(pct_det)} de los que se fueron",
        f"{n_miss} falsos negativos — hay un problema estructural en las señales. Revisá el análisis de abajo.",
        "red"), unsafe_allow_html=True)

# ── Análisis de señales: qué diferencia detectados de no detectados ────────────
st.markdown('<div class="sec-header">🔬 ¿Qué señales separaron a los detectados de los no detectados?</div>',
            unsafe_allow_html=True)
st.caption(
    "Las barras muestran qué % de cada grupo tenía activa cada señal. "
    "Si una señal aparece MUCHO en detectados y POCO en no detectados → el modelo la está viendo bien. "
    "Si una señal aparece MUCHO en no detectados (y no en detectados) → hay un patrón que el modelo no captura."
)

# Recolectar todas las señales
all_señales = set()
for s_list in analisis["señales"]:
    all_señales.update(s_list)
all_señales = sorted(all_señales)

if all_señales and total_cd > 0:
    sig_data = []
    for s in all_señales:
        pct_d = round(detectados["señales"].apply(lambda x: s in x).mean() * 100) if n_det > 0 else 0
        pct_m = round(no_detectados["señales"].apply(lambda x: s in x).mean() * 100) if n_miss > 0 else 0
        sig_data.append({"señal": s, "pct_det": pct_d, "pct_miss": pct_m,
                          "diff": pct_d - pct_m})

    sig_df = pd.DataFrame(sig_data).sort_values("pct_det", ascending=False)

    col_sig1, col_sig2 = st.columns(2)

    with col_sig1:
        st.markdown("**Señales más frecuentes en detectados** (el modelo las ve bien)")
        top_det = sig_df.nlargest(8, "pct_det")
        bars_html = ""
        for _, r in top_det.iterrows():
            w_det  = max(4, r["pct_det"])
            w_miss = max(4, r["pct_miss"])
            bars_html += f"""
            <div class="sig-bar">
              <div style="width:120px;font-size:11px;color:#555;flex-shrink:0;
                          overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                   title="{r['señal']}">{r['señal']}</div>
              <div style="flex:1;display:flex;flex-direction:column;gap:2px;">
                <div style="display:flex;align-items:center;gap:4px;">
                  <div class="sig-fill" style="width:{w_det}%;background:#639922;opacity:.85;"></div>
                  <span style="font-size:10px;color:#639922;font-weight:700;">{r['pct_det']}%</span>
                </div>
                <div style="display:flex;align-items:center;gap:4px;">
                  <div class="sig-fill" style="width:{w_miss}%;background:#ccc;opacity:.7;"></div>
                  <span style="font-size:10px;color:#999;">{r['pct_miss']}%</span>
                </div>
              </div>
            </div>"""
        st.markdown(f'<div class="card">{bars_html}'
                    '<div style="font-size:10px;color:#aaa;margin-top:8px;">'
                    '🟢 detectados &nbsp; ⬜ no detectados</div></div>',
                    unsafe_allow_html=True)

    with col_sig2:
        st.markdown("**Señales ausentes en no detectados** (brechas del modelo)")
        # Señales que detectados TIENEN pero no-detectados NO → brecha clara
        top_miss = sig_df.nlargest(8, "diff")
        if top_miss["diff"].max() <= 0:
            st.info("No hay señales con diferencia clara entre grupos aún. "
                    "Con más datos históricos esto se va a definir mejor.")
        else:
            gaps_html = ""
            for _, r in top_miss.iterrows():
                diff_color = "#E24B4A" if r["diff"] > 20 else ("#EF9F27" if r["diff"] > 10 else "#888")
                gaps_html += f"""
                <div class="sig-bar">
                  <div style="width:120px;font-size:11px;color:#555;flex-shrink:0;
                              overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                               title="{r['señal']}">{r['señal']}</div>
                  <div style="flex:1;display:flex;align-items:center;gap:6px;">
                    <div class="sig-fill"
                         style="width:{max(4,r['diff'])}%;background:{diff_color};"></div>
                    <span style="font-size:10px;color:{diff_color};font-weight:700;">
                      +{r['diff']}pp más en detectados</span>
                  </div>
                </div>"""
            st.markdown(f'<div class="card">{gaps_html}'
                        '<div style="font-size:10px;color:#aaa;margin-top:8px;">'
                        'Diferencia en puntos porcentuales (detectados − no detectados)</div>'
                        '</div>', unsafe_allow_html=True)
        st.caption(
            "Si muchos no detectados no tenían ninguna señal activa, el modelo puede estar "
            "faltando señales de factores externos (zona quemada + ventana crítica no capturas todo). "
            "Considerá agregar la señal de supervisor o antigüedad del grupo."
        )

# ── Tabla detalle ──────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📋 Detalle por vendedor egresado</div>',
            unsafe_allow_html=True)

tab_det, tab_miss, tab_sin = st.tabs([
    f"✅ Detectados ({n_det})",
    f"❌ No detectados ({n_miss})",
    f"⬜ Sin datos ({len(sin_datos)})",
])

def _nivel_badge(nivel):
    if not nivel:
        return '<span style="color:#aaa;font-size:11px;">—</span>'
    colors = {"critico": ("#FDECEA","#B71C1C"), "alto": ("#FFF3E0","#E65100"),
              "medio": ("#E3F2FD","#1565C0"), "bajo": ("#F1F8E9","#2E7D32")}
    bg, tx = colors.get(nivel, ("#f8f9fa","#666"))
    return f'<span style="background:{bg};color:{tx};padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700;">{nivel.upper()}</span>'

def _señales_pills(lista):
    if not lista:
        return '<span style="color:#ccc;font-size:11px;">Sin señales</span>'
    pill_colors = {
        "% Plan cayendo 3 meses seguidos":       ("caída 3m",     "#FDECEA","#B71C1C"),
        "% Plan < 80% promedio últimos meses":    ("plan &lt;80%", "#FFF3E0","#E65100"),
        "Días sin venta > 3 en promedio":         ("días cero↑",   "#FDECEA","#B71C1C"),
        "< 60% de cartera activa":                ("inactivos↑",   "#FFF3E0","#E65100"),
        "Cobranza real < 90% de teórica":         ("cobranza baja","#FFF3E0","#E65100"),
        "En ventana crítica mes 1-3":             ("inducción",    "#FDECEA","#B71C1C"),
        "En ventana crítica mes 4-6":             ("mes 4-6",      "#FFF3E0","#E65100"),
        "Grupo con alta rotación histórica":      ("zona quemada", "#FFF3E0","#E65100"),
        "Sin clientes nuevos últimos 2 meses":    ("cl. L:0",      "#FFFDE7","#F57F17"),
    }
    parts = []
    for s in lista:
        lbl, bg, tx = pill_colors.get(s, (_html.escape(s[:12]), "#f0f0f0", "#666"))
        parts.append(f'<span style="background:{bg};color:{tx};padding:1px 6px;'
                     f'border-radius:8px;font-size:10px;font-weight:600;margin:1px 2px;'
                     f'display:inline-block;white-space:nowrap;">{lbl}</span>')
    return "".join(parts)

def _tabla(subset, mostrar_tag):
    if subset.empty:
        return '<div style="color:#aaa;padding:20px;font-size:13px;">No hay registros en este grupo.</div>'
    rows = ""
    for _, r in subset.sort_values("periodo_egreso", ascending=False).iterrows():
        tag = ('<span class="tag-det">✅ Detectado</span>' if r["detectado"]
               else '<span class="tag-miss">❌ No detectado</span>')
        score_str = (f'<b style="font-size:15px">{r["score_previo"]}</b> '
                     f'{_nivel_badge(r["nivel_previo"])}') if pd.notna(r.get("score_previo")) else "—"
        nombre        = _html.escape(str(r['nombre'] or ''))
        tipo          = _html.escape(str(r['tipo'] or ''))
        nombre_grupo  = _html.escape(str(r['nombre_grupo'] or '—'))
        periodo_egreso= _html.escape(str(r['periodo_egreso'] or '—'))
        motivo_egreso = _html.escape(str(r['motivo_egreso'] or '—'))
        periodo_score = _html.escape(str(r.get('periodo_score') or '—'))
        rows += f"""<tr>
          <td>
            <div style="font-weight:700;font-size:12px;">{nombre}</div>
            <div style="color:#aaa;font-size:11px;">{tipo} · ID {int(r['id_vendedor'])}</div>
          </td>
          <td style="font-size:12px;">{nombre_grupo}</td>
          <td style="font-size:12px;color:#666;">{periodo_egreso}</td>
          <td style="font-size:12px;color:#888;">{motivo_egreso}</td>
          <td>{score_str}</td>
          <td style="font-size:11px;color:#777;">{periodo_score}</td>
          <td>{_señales_pills(r['señales'])}</td>
          {'<td>' + tag + '</td>' if mostrar_tag else ''}
        </tr>"""
    th_tag = "<th>Estado</th>" if mostrar_tag else ""
    return f"""
<div class="card" style="overflow-x:auto;">
<table class="det-tbl">
<thead><tr>
  <th>Vendedor</th><th>Zona</th><th>Período egreso</th>
  <th>Motivo</th><th>Score previo</th><th>Período score</th>
  <th>Señales activas antes de irse</th>{th_tag}
</tr></thead>
<tbody>{rows}</tbody>
</table></div>"""

with tab_det:
    st.caption(f"Vendedores que el modelo hubiera marcado como riesgo alto o crítico "
               f"en los 3 meses previos a irse (score ≥ 6).")
    st.markdown(_tabla(detectados, False), unsafe_allow_html=True)

with tab_miss:
    st.caption(f"Vendedores que se fueron SIN haber tenido score ≥ 6 en los 3 meses previos. "
               f"Estas son las fugas que el modelo NO hubiera anticipado.")
    if n_miss == 0:
        st.success("¡Sin falsos negativos! El modelo hubiera marcado a todos los que se fueron.")
    else:
        st.markdown(_tabla(no_detectados, False), unsafe_allow_html=True)
        with st.expander("¿Qué hacer con esto?"):
            st.markdown("""
**Interpretá los falsos negativos así:**

- Si tienen pocas o ninguna señal → el problema puede ser externo (conflicto con supervisor,
  oferta de otro trabajo, motivo personal). El modelo de ventas no puede capturar eso.
- Si tienen señales pero score bajo → los pesos actuales subestiman esas señales.
  Considerá aumentar el peso de las que más aparecen en este grupo.
- Si todos son del mismo tipo (ej. Televentas) → puede haber un sesgo por tipo.
  Los datos de actividad Reactor son clave para Televentas y puede que estén incompletos.

**Lo más accionable:** si hay un patrón en las señales de los no detectados
(ej. siempre tienen "plan<80%" pero no "caída 3m"), el score_engine podría ajustar
el umbral de la señal 2 o agregar una señal nueva de "plan bajo sostenido sin tendencia".
""")

with tab_sin:
    st.caption(
        "Vendedores egresados en el período de análisis para los que no había datos de ventas "
        "en score_historico (probablemente no tenían historial en ventas_mensual)."
    )
    st.markdown(_tabla(sin_datos.assign(score_previo=None, nivel_previo=None,
                                         periodo_score=None, señales=[[]]*len(sin_datos),
                                         detectado=False), False),
                unsafe_allow_html=True)

# ── Nota ───────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.caption(
    f"Datos de score_historico: {n_hist} registros de backfill. "
    f"Período analizado: últimos 18 meses de egresados. "
    "Para actualizar, ejecutá scripts/backfill_scores.bat y recargá la página."
)
