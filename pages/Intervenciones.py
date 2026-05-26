"""
pages/Intervenciones.py
-----------------------
Registro y seguimiento de intervenciones sobre vendedores en riesgo.
"""

import streamlit as st
import pandas as pd
from datetime import date
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from score_engine import calcular_scores, resumen_grupos, get_connection
from intervenciones import (
    TIPOS, registrar, obtener_todas, calcular_impacto,
    hay_datos_demo, cargar_demo,
)

st.set_page_config(
    page_title="Wurth | Intervenciones",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""<style>
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 2rem 2.5rem 3rem !important; max-width: 100% !important; }
header { display: none; }

.sc { display: inline-flex; align-items: center; justify-content: center;
      width: 32px; height: 32px; border-radius: 50%; font-weight: 800; font-size: 13px; }
.sc-critico { background: #FDECEA; color: #B71C1C; border: 2px solid #E24B4A; }
.sc-alto    { background: #FFF3E0; color: #E65100; border: 2px solid #EF9F27; }
.sc-medio   { background: #E3F2FD; color: #1565C0; border: 2px solid #4A90D9; }
.sc-bajo    { background: #F1F8E9; color: #2E7D32; border: 2px solid #639922; }
.sc-baja    { background: #f0f0f0; color: #999; border: 2px solid #ccc; }

.bdg { display: inline-block; padding: 2px 8px; border-radius: 4px;
       font-size: 11px; font-weight: 600; }
.bdg-critico { background: #FDECEA; color: #B71C1C; }
.bdg-alto    { background: #FFF3E0; color: #E65100; }
.bdg-medio   { background: #E3F2FD; color: #1565C0; }
.bdg-bajo    { background: #F1F8E9; color: #2E7D32; }
.bdg-baja    { background: #f0f0f0; color: #888; }
.bdg-tipo    { background: #F3E8FF; color: #6B21A8; }

.card { background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08); }

.it { width: 100%; border-collapse: collapse; }
.it th { background: #f8f9fa; padding: 10px 12px; text-align: left;
         font-size: 12px; font-weight: 600; color: #666; border-bottom: 2px solid #e9ecef; }
.it td { padding: 11px 12px; border-bottom: 1px solid #f2f2f2;
         vertical-align: middle; font-size: 13px; }
.it tr:hover td { background: #fafafa; }

.imp-pos { color: #2E7D32; font-weight: 700; font-size: 14px; }
.imp-neg { color: #B71C1C; font-weight: 700; font-size: 14px; }
.imp-neu { color: #888; font-size: 13px; }

.sec-header { font-size: 15px; font-weight: 700; color: #1a1a2e;
    margin: 8px 0 14px; }

.kpi-row { display: flex; gap: 14px; margin-bottom: 24px; }
.kpi-card { background: white; border-radius: 12px; padding: 16px 20px;
    flex: 1; box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 4px solid #e0e0e0; }
.kpi-card.kg { border-left-color: #639922; }
.kpi-card.kc { border-left-color: #E24B4A; }
.kpi-card.ka { border-left-color: #4A90D9; }
.kpi-value { font-size: 26px; font-weight: 800; color: #1a1a2e; }
.kpi-label { font-size: 12px; font-weight: 700; color: #555; margin-top: 4px; }
.kpi-sub   { font-size: 11px; color: #aaa; margin-top: 2px; }
</style>""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def _sc(score, nivel):
    return f'<div class="sc sc-{nivel}">{int(score) if score else "—"}</div>'

def _bdg(nivel, label=None):
    labels = {"critico":"Crítico","alto":"Alto","medio":"Medio","bajo":"Bajo","baja":"Baja"}
    return f'<span class="bdg bdg-{nivel}">{label or labels.get(nivel, nivel)}</span>'

def _impacto_html(impacto, estado):
    if estado == "Baja":
        return '<span class="imp-neu">— Baja</span>'
    if impacto is None:
        return '<span class="imp-neu">—</span>'
    if impacto > 0.4:
        return f'<span class="imp-pos">↓ {impacto} mejora</span>'
    if impacto < -0.4:
        return f'<span class="imp-neg">↑ {abs(impacto)} empeora</span>'
    return f'<span class="imp-neu">= sin cambio</span>'

# ── Datos ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def cargar_scores():
    return calcular_scores()

scores_df = cargar_scores()

# Demo data si la tabla está vacía
if not hay_datos_demo():
    cargar_demo(scores_df)
    st.cache_data.clear()

# ── Navegación ─────────────────────────────────────────────────────────────────
nav1, nav2, _ = st.columns([1, 1, 5])
with nav1:
    st.page_link("dashboard.py", label="← Dashboard", icon="📊")
with nav2:
    st.page_link("pages/Supervisor.py", label="👤 Supervisores")

st.markdown("""
<div style="margin-bottom:24px;margin-top:12px;">
  <div style="font-size:22px;font-weight:800;color:#1a1a2e;">📝 Registro de intervenciones</div>
  <div style="font-size:14px;color:#888;margin-top:4px;">
    Documentá qué acción se tomó sobre cada vendedor en riesgo y medí el impacto real
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs de impacto ────────────────────────────────────────────────────────────
todas = obtener_todas()
if not todas.empty:
    con_impacto = calcular_impacto(todas, scores_df)
    mejoraron = len(con_impacto[con_impacto["impacto"].fillna(0) > 0.4])
    empeoraron = len(con_impacto[con_impacto["impacto"].fillna(0) < -0.4])
    total_int  = len(con_impacto)
    bajas      = len(con_impacto[con_impacto["estado"] == "Baja"])

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-value">{total_int}</div>
        <div class="kpi-label">Intervenciones registradas</div>
      </div>
      <div class="kpi-card kg">
        <div class="kpi-value" style="color:#2E7D32">{mejoraron}</div>
        <div class="kpi-label">Con mejora de score</div>
        <div class="kpi-sub">Score bajó ≥ 0.5 después</div>
      </div>
      <div class="kpi-card kc">
        <div class="kpi-value" style="color:#E24B4A">{empeoraron}</div>
        <div class="kpi-label">Sin mejora</div>
        <div class="kpi-sub">Score igual o subió</div>
      </div>
      <div class="kpi-card ka">
        <div class="kpi-value" style="color:#888">{bajas}</div>
        <div class="kpi-label">Vendedor dio de baja</div>
        <div class="kpi-sub">A pesar de la intervención</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Formulario de registro ─────────────────────────────────────────────────────
st.markdown('<div class="sec-header">➕ Registrar nueva intervención</div>',
            unsafe_allow_html=True)

en_riesgo = scores_df[scores_df.nivel_riesgo.isin(["critico","alto"])].sort_values("score", ascending=False)

if en_riesgo.empty:
    st.info("No hay vendedores en nivel crítico o alto en este momento.")
else:
    supervisores = sorted(scores_df["supervisor"].unique().tolist())

    with st.form("form_intervencion", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            opciones_vendedor = {
                f"ID {int(r['id_vendedor'])} — {r['nombre_grupo']} — Score {r['score']} ({r['nivel_riesgo'].upper()})": {
                    "id": int(r["id_vendedor"]),
                    "score": r["score"],
                    "nivel": r["nivel_riesgo"],
                    "supervisor": r["supervisor"],
                }
                for _, r in en_riesgo.iterrows()
            }
            vendedor_label = st.selectbox("Vendedor en riesgo", list(opciones_vendedor.keys()))
            tipo = st.selectbox("Tipo de intervención", TIPOS)
            fecha = st.date_input("Fecha", value=date(2025, 1, 24))

        with col2:
            supervisor = st.selectbox("Supervisor que intervino", supervisores,
                index=supervisores.index(opciones_vendedor[vendedor_label]["supervisor"])
                if opciones_vendedor[vendedor_label]["supervisor"] in supervisores else 0)
            observaciones = st.text_area(
                "Observaciones",
                placeholder="¿Qué se habló? ¿Qué se acordó? ¿Cómo reaccionó el vendedor?",
                height=120,
            )

        submitted = st.form_submit_button("💾 Guardar intervención", use_container_width=True,
                                           type="primary")

        if submitted:
            v = opciones_vendedor[vendedor_label]
            registrar(
                id_vendedor   = v["id"],
                tipo          = tipo,
                supervisor    = supervisor,
                score_inicial = v["score"],
                nivel_inicial = v["nivel"],
                observaciones = observaciones,
                fecha         = fecha.isoformat(),
            )
            st.success(f"✓ Intervención registrada para ID {v['id']} — {tipo}")
            st.cache_data.clear()
            st.rerun()

st.divider()

# ── Historial con impacto ──────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📊 Historial de intervenciones e impacto</div>',
            unsafe_allow_html=True)
st.caption("El impacto se mide comparando el score al momento de intervenir con el score actual.")

todas = obtener_todas()
if todas.empty:
    st.info("Todavía no hay intervenciones registradas.")
else:
    con_impacto = calcular_impacto(todas, scores_df)

    # Filtro por tipo
    tipos_usados = ["Todos"] + sorted(con_impacto["tipo"].unique().tolist())
    filtro_tipo = st.selectbox("Filtrar por tipo", tipos_usados, label_visibility="collapsed")
    if filtro_tipo != "Todos":
        con_impacto = con_impacto[con_impacto["tipo"] == filtro_tipo]

    rows = ""
    for _, r in con_impacto.iterrows():
        nivel_i = r["nivel_inicial"]
        nivel_a = r.get("nivel_actual") or "baja"
        score_a = r.get("score_actual")
        obs = (r["observaciones"] or "")[:80] + ("…" if len(r["observaciones"] or "") > 80 else "")

        rows += f"""<tr>
          <td style="color:#aaa;font-size:12px;">{r['fecha']}</td>
          <td>
            <div style="font-weight:700;">ID {int(r['id_vendedor'])}</div>
            <div style="color:#aaa;font-size:11px;">{r['tipo_vendedor']} · {r['nombre_grupo']}</div>
          </td>
          <td><span class="bdg bdg-tipo">{r['tipo']}</span></td>
          <td>{r['supervisor']}</td>
          <td style="text-align:center;">{_sc(r['score_inicial'], nivel_i)}</td>
          <td style="text-align:center;">{_sc(score_a, nivel_a) if score_a else _bdg('baja', r['estado'].capitalize())}</td>
          <td>{_impacto_html(r.get('impacto'), r.get('estado',''))}</td>
          <td style="color:#888;font-size:12px;max-width:200px;">{obs}</td>
        </tr>"""

    st.markdown(f"""
    <div class="card" style="overflow-x:auto;">
    <table class="it">
    <thead><tr>
      <th>Fecha</th><th>Vendedor</th><th>Tipo</th><th>Supervisor</th>
      <th style="text-align:center;">Score inicial</th>
      <th style="text-align:center;">Score actual</th>
      <th>Impacto</th><th>Observaciones</th>
    </tr></thead>
    <tbody>{rows}</tbody>
    </table></div>
    """, unsafe_allow_html=True)

    # Resumen por tipo
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-header">📈 Efectividad por tipo de intervención</div>',
                unsafe_allow_html=True)

    todas_imp = calcular_impacto(obtener_todas(), scores_df)
    activas   = todas_imp[todas_imp["estado"] == "activo"]
    if not activas.empty:
        resumen = activas.groupby("tipo").agg(
            cantidad =("id","count"),
            impacto_promedio=("impacto","mean"),
            mejoraron=("impacto", lambda x: (x > 0.4).sum()),
        ).reset_index().sort_values("impacto_promedio", ascending=False)

        res_rows = ""
        for _, r in resumen.iterrows():
            imp = r["impacto_promedio"]
            color = "#2E7D32" if imp > 0.2 else ("#B71C1C" if imp < -0.2 else "#888")
            bar_w = min(100, max(0, int(abs(imp) / 3 * 100)))
            bar_color = "#639922" if imp > 0 else "#E24B4A"
            res_rows += f"""<tr>
              <td><span class="bdg bdg-tipo">{r['tipo']}</span></td>
              <td style="text-align:center;">{int(r['cantidad'])}</td>
              <td style="text-align:center;">{int(r['mejoraron'])}</td>
              <td>
                <div style="display:flex;align-items:center;gap:8px;">
                  <div style="width:{bar_w}px;height:8px;background:{bar_color};
                              border-radius:4px;min-width:4px;"></div>
                  <span style="color:{color};font-weight:700;">{imp:+.1f}</span>
                </div>
              </td>
            </tr>"""

        st.markdown(f"""
        <div class="card">
        <table class="it">
        <thead><tr>
          <th>Tipo de intervención</th>
          <th style="text-align:center;">Cantidad</th>
          <th style="text-align:center;">Mejoraron</th>
          <th>Impacto promedio en score</th>
        </tr></thead>
        <tbody>{res_rows}</tbody>
        </table></div>
        """, unsafe_allow_html=True)
        st.caption("Impacto = score_inicial − score_actual. Positivo = riesgo bajó = intervención efectiva.")

st.markdown("<br>")
st.caption("Wurth Argentina · Sistema de alertas de rotación · Datos simulados")
