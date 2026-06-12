/* @ds-bundle: {"format":3,"namespace":"WRthRotaciNDesignSystem_0064d7","components":[],"sourceHashes":{"ui_kits/dashboard/ActividadViews.jsx":"d125d3e72597","ui_kits/dashboard/App.jsx":"2d020c85debe","ui_kits/dashboard/CompareApp.jsx":"b4870803809c","ui_kits/dashboard/CostV2.jsx":"9d253c712582","ui_kits/dashboard/CostView.jsx":"e7e84a91f0e8","ui_kits/dashboard/FeatureViews.jsx":"9bd28813b87e","ui_kits/dashboard/HistorialViews.jsx":"eaf3e934676b","ui_kits/dashboard/InicioV2.jsx":"7449297d2514","ui_kits/dashboard/InicioView.jsx":"53d44396d8de","ui_kits/dashboard/InterventionsV2.jsx":"10c0119b70db","ui_kits/dashboard/InterventionsView.jsx":"97ad5a56c3af","ui_kits/dashboard/PrecisionView.jsx":"d778d6fee87a","ui_kits/dashboard/SupervisorV2.jsx":"87a043c084d9","ui_kits/dashboard/SupervisorView.jsx":"104a9acee243","ui_kits/dashboard/data.js":"801bb257a7a7","ui_kits/dashboard/ios-frame.jsx":"be3343be4b51","ui_kits/dashboard/model.js":"cf3143427dad","ui_kits/dashboard/primitives.jsx":"9c667435c289","ui_kits/dashboard/v2common.jsx":"f38bff0e1bdc"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.WRthRotaciNDesignSystem_0064d7 = window.WRthRotaciNDesignSystem_0064d7 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// ui_kits/dashboard/ActividadViews.jsx
try { (() => {
/* Actividad comercial — Televentas (llamadas) + Viajantes (visitas) vs plan.
   actual = faithful conditional-format table; v2 = leads with cumplimiento,
   splits the two channels, ranks reps, ties low activity back to risk. */

function cumplColor(v) {
  if (v >= 90) return ["var(--green-pos-bg)", "var(--green-pos-tx)"];
  if (v >= 70) return ["var(--cell-warn-bg)", "var(--cell-warn-tx)"];
  return ["var(--cell-bad-bg)", "var(--cell-bad-tx)"];
}
function ActividadV2({
  data,
  onOpenVendedor
}) {
  const A = data.ACTIVIDAD;
  const tel = A.filter(a => a.tipo === "Televentas");
  const via = A.filter(a => a.tipo === "Viajante");
  const [canal, setCanal] = React.useState("Televentas");
  const rows = (canal === "Televentas" ? tel : via).slice().sort((a, b) => a.cumpl - b.cumpl);
  const avg = arr => Math.round(arr.reduce((s, a) => s + a.cumpl, 0) / arr.length);
  const bajoPlan = A.filter(a => a.cumpl < 70);
  const unidad = canal === "Televentas" ? "llamadas/día" : "visitas/semana";
  const verbo = canal === "Televentas" ? "llamó" : "visitó";
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(V2Banner, {
    emoji: bajoPlan.length ? "⚠️" : "📞",
    tone: bajoPlan.length > 2 ? "orange" : "blue",
    title: `${bajoPlan.length} vendedores están por debajo del 70% del plan de actividad`,
    sub: "La baja actividad suele anticipar la ca\xEDda de plan. Revisalos antes de que el score escale."
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement(HeroStat, {
    label: `Cumplimiento ${canal}`,
    value: `${avg(canal === "Televentas" ? tel : via)}%`,
    accent: avg(canal === "Televentas" ? tel : via) >= 80 ? "var(--green-accent)" : "var(--orange-accent)",
    valueColor: avg(canal === "Televentas" ? tel : via) >= 80 ? "var(--green-text)" : "var(--orange-text)"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-500)"
    }
  }, "Promedio del canal vs. plan de ", unidad)), /*#__PURE__*/React.createElement(V2Card, {
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 10
    }
  }, [["Televentas", "📞", tel], ["Viajante", "🚗", via]].map(([k, ico, arr]) => /*#__PURE__*/React.createElement("button", {
    key: k,
    onClick: () => setCanal(k),
    style: {
      flex: 1,
      textAlign: "left",
      padding: "14px 16px",
      borderRadius: 10,
      cursor: "pointer",
      border: "1px solid",
      borderColor: canal === k ? "var(--blue-accent)" : "var(--line-strong)",
      background: canal === k ? "var(--blue-bg)" : "#fff"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 700,
      color: "var(--ink-700)"
    }
  }, ico, " ", k === "Viajante" ? "Viajantes" : k), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: 6,
      marginTop: 4
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 800,
      fontSize: 26,
      color: avg(arr) >= 80 ? "var(--green-text)" : "var(--orange-text)"
    }
  }, avg(arr), "%"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)"
    }
  }, arr.length, " reps"))))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      lineHeight: 1.5
    }
  }, "Eleg\xED un canal para ver el ranking de actividad. Los de menor cumplimiento aparecen primero."))), /*#__PURE__*/React.createElement(StatStrip, null, /*#__PURE__*/React.createElement(StatItem, {
    value: A.length,
    label: "Vendedores con actividad"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: `${avg(A)}%`,
    label: "Cumplimiento general"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: bajoPlan.length,
    label: "Por debajo del 70%"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: A.filter(a => a.clientesL === 0).length,
    label: "Sin altas de clientes"
  })), /*#__PURE__*/React.createElement(V2Section, {
    title: `${canal === "Televentas" ? "📞" : "🚗"} Ranking de actividad — ${canal === "Viajante" ? "Viajantes" : canal}`,
    right: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        color: "var(--ink-400)"
      }
    }, "Ordenado por menor cumplimiento")
  }), /*#__PURE__*/React.createElement(V2Card, {
    pad: false,
    style: {
      overflow: "hidden",
      padding: "8px 8px 0"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Vendedor"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Plan"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Real"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Cumplimiento"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Contactos efectivos"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Riesgo"))), /*#__PURE__*/React.createElement("tbody", null, rows.map(a => {
    const [bg, tx] = cumplColor(a.cumpl);
    return /*#__PURE__*/React.createElement("tr", {
      key: a.id,
      className: "vrow"
    }, /*#__PURE__*/React.createElement("td", {
      style: v2td
    }, /*#__PURE__*/React.createElement("b", null, a.nombre), " ", /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--ink-400)",
        fontSize: 11
      }
    }, "(", a.id, ")"), /*#__PURE__*/React.createElement("div", {
      style: {
        color: "var(--ink-250)",
        fontSize: 11
      }
    }, a.grupo)), /*#__PURE__*/React.createElement("td", {
      style: v2td
    }, a.plan, " ", /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--ink-400)",
        fontSize: 11
      }
    }, unidad.split("/")[1] ? "/" + unidad.split("/")[1] : "")), /*#__PURE__*/React.createElement("td", {
      style: v2td
    }, /*#__PURE__*/React.createElement("b", null, a.real)), /*#__PURE__*/React.createElement("td", {
      style: v2td
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: "inline-block",
        minWidth: 52,
        textAlign: "center",
        padding: "4px 0",
        borderRadius: 6,
        background: bg,
        color: tx,
        fontWeight: 700,
        fontSize: 12
      }
    }, a.cumpl, "%")), /*#__PURE__*/React.createElement("td", {
      style: v2td
    }, a.contactos), /*#__PURE__*/React.createElement("td", {
      style: v2td
    }, /*#__PURE__*/React.createElement(Badge, {
      nivel: a.nivel
    })));
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 10
    }
  }, verbo.charAt(0).toUpperCase() + verbo.slice(1), ": real vs. plan de ", unidad, ". Datos simulados."));
}
function ActividadActual({
  data
}) {
  const A = data.ACTIVIDAD.slice().sort((a, b) => a.cumpl - b.cumpl);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 22,
      color: "var(--ink-900)",
      marginBottom: 4
    }
  }, "\uD83D\uDCDE Actividad comercial"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: "var(--ink-400)",
      marginBottom: 22
    }
  }, "Televentas (llamadas) y Viajantes (visitas): target vs. ejecutado."), /*#__PURE__*/React.createElement(Card, {
    pad: false,
    style: {
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, ["Vendedor", "Tipo", "Zona", "Plan", "Real", "Cumplimiento", "Contactos"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: {
      background: "var(--table-head-bg)",
      padding: "10px 12px",
      textAlign: "left",
      fontSize: 12,
      fontWeight: 600,
      color: "var(--ink-500)",
      borderBottom: "2px solid var(--line-strong)"
    }
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, A.map(a => {
    const [bg, tx] = cumplColor(a.cumpl);
    return /*#__PURE__*/React.createElement("tr", {
      key: a.id
    }, /*#__PURE__*/React.createElement("td", {
      style: {
        padding: "11px 12px",
        borderBottom: "1px solid var(--line-faint)",
        fontSize: 13,
        fontWeight: 700
      }
    }, a.nombre), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: "11px 12px",
        borderBottom: "1px solid var(--line-faint)",
        fontSize: 13
      }
    }, a.tipo), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: "11px 12px",
        borderBottom: "1px solid var(--line-faint)",
        fontSize: 13
      }
    }, a.grupo), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: "11px 12px",
        borderBottom: "1px solid var(--line-faint)",
        fontSize: 13
      }
    }, a.plan), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: "11px 12px",
        borderBottom: "1px solid var(--line-faint)",
        fontSize: 13
      }
    }, a.real), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: "8px 12px",
        borderBottom: "1px solid var(--line-faint)",
        fontSize: 13
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: "inline-block",
        padding: "3px 10px",
        borderRadius: 4,
        background: bg,
        color: tx,
        fontWeight: 600
      }
    }, a.cumpl, "%")), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: "11px 12px",
        borderBottom: "1px solid var(--line-faint)",
        fontSize: 13
      }
    }, a.contactos));
  })))));
}
Object.assign(window, {
  ActividadV2,
  ActividadActual
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/ActividadViews.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/App.jsx
try { (() => {
/* App shell — top nav + screen router + vendedor detail modal. */

function Placeholder({
  emoji,
  title,
  blurb
}) {
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      font: "var(--w-black) 22px var(--font-sans)",
      color: "var(--ink-900)",
      marginBottom: 4
    }
  }, emoji, " ", title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: "var(--ink-400)",
      marginBottom: 22
    }
  }, blurb), /*#__PURE__*/React.createElement(Card, {
    style: {
      padding: "40px 22px",
      textAlign: "center",
      color: "var(--ink-400)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 34,
      marginBottom: 10
    }
  }, emoji), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600,
      color: "var(--ink-600)"
    }
  }, "Pantalla presente en el producto real"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      marginTop: 6,
      maxWidth: 460,
      marginLeft: "auto",
      marginRight: "auto",
      lineHeight: 1.5
    }
  }, "Este UI kit recrea Inicio, Por supervisor, Intervenciones y Costo de rotaci\xF3n.", /*#__PURE__*/React.createElement("b", null, " ", title), " existe en la app pero no se reconstruy\xF3 aqu\xED \u2014 us\xE1 los mismos componentes (tabla, KPIs, badges, charts) para armarla.")));
}
function App() {
  const data = window.DASH_DATA;
  const [screen, setScreen] = React.useState("inicio");
  const [modal, setModal] = React.useState(null);
  let view;
  if (screen === "inicio") view = /*#__PURE__*/React.createElement(InicioView, {
    data: data,
    onOpenVendedor: setModal
  });else if (screen === "supervisor") view = /*#__PURE__*/React.createElement(SupervisorView, {
    data: data,
    onOpenVendedor: setModal
  });else if (screen === "intervenciones") view = /*#__PURE__*/React.createElement(InterventionsView, {
    data: data
  });else if (screen === "costo") view = /*#__PURE__*/React.createElement(CostView, {
    data: data
  });else if (screen === "historial") view = /*#__PURE__*/React.createElement(HistorialView, {
    data: data
  });else if (screen === "actividad") view = /*#__PURE__*/React.createElement(ActividadView, {
    data: data
  });
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "2.5rem",
      maxWidth: 1280,
      margin: "0 auto"
    }
  }, /*#__PURE__*/React.createElement(TopNav, {
    current: screen,
    onNav: k => {
      setScreen(k);
      setModal(null);
    }
  }), view, /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 36,
      paddingTop: 16,
      borderTop: "1px solid var(--line)",
      fontSize: 12,
      color: "var(--ink-300)"
    }
  }, "W\xFCrth Argentina \xB7 Sistema de alertas de rotaci\xF3n \xB7 Datos simulados \xB7 Recreaci\xF3n UI kit"), /*#__PURE__*/React.createElement(VendedorModal, {
    r: modal,
    onClose: () => setModal(null)
  }));
}
ReactDOM.createRoot(document.getElementById("root")).render(/*#__PURE__*/React.createElement(App, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/App.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/CompareApp.jsx
try { (() => {
/* Comparison shell — pick a screen, flip current vs v2. Feature screens
   (digest / mobile / estados) are v2-only and hide the toggle. */

const SCREENS = [{
  id: "inicio",
  label: "🏠 Inicio"
}, {
  id: "supervisor",
  label: "👤 Por supervisor"
}, {
  id: "intervenciones",
  label: "📝 Intervenciones"
}, {
  id: "costo",
  label: "💰 Costo"
}, {
  id: "historial",
  label: "📈 Historial"
}, {
  id: "actividad",
  label: "📞 Actividad"
}, {
  id: "precision",
  label: "🎯 Precisión"
}];
const FEATURES = [{
  id: "digest",
  label: "✉️ Resumen semanal"
}, {
  id: "mobile",
  label: "📱 Móvil"
}, {
  id: "estados",
  label: "🧩 Estados"
}];
const FEATURE_IDS = FEATURES.map(f => f.id);
// v2-only screens (no "actual" counterpart → hide the toggle)
const V2_ONLY = [...FEATURE_IDS, "precision"];
const NUEVA_NOTA = {
  digest: "Resumen semanal que se envía por mail a cada supervisor para empujar la acción (#6).",
  mobile: "Vista móvil para viajantes en la ruta (#7).",
  estados: "Estados de carga, error de conexión y vacío (#5).",
  precision: "Valida que el score realmente predice las fugas — matriz predicción vs. resultado (#1)."
};
const V2_NOTES = {
  inicio: "① KPI dominante de riesgo · ② más aire · ③ permanencia 18→5m como estrella · ④ banner + columna “acción sugerida” · ⑤ chart sin ruido · ⑥ estado vacío.",
  supervisor: "Supervisores ordenados por urgencia · el nº de “requieren acción” es el héroe de cada tarjeta · banner de la peor zona · detalle con acción sugerida.",
  intervenciones: "Arranca con la tasa de efectividad · gráfico “qué tipo mueve más el score” · formulario plegable · impacto en lenguaje claro.",
  costo: "Lidera con el dinero en juego si no se actúa · exposición por zona priorizada · stat de la zona más cara · tabla más limpia.",
  historial: "Curva de supervivencia del equipo · tabla de retención por cohorte (#3) · rotación mensual · trayectoria del score promedio · ranking de mayores escaladas (#2).",
  actividad: "Lidera con el cumplimiento del canal · separa Televentas/Viajantes · ranking por menor cumplimiento · conecta baja actividad con riesgo de fuga."
};
function CompareApp() {
  const data = window.DASH_DATA;
  const [screen, setScreen] = React.useState("inicio");
  const [v, setV] = React.useState("v2");
  const [modal, setModal] = React.useState(null);
  const isFeature = V2_ONLY.includes(screen);
  const actual = {
    inicio: () => /*#__PURE__*/React.createElement(InicioView, {
      data: data,
      onOpenVendedor: setModal
    }),
    supervisor: () => /*#__PURE__*/React.createElement(SupervisorView, {
      data: data,
      onOpenVendedor: setModal
    }),
    intervenciones: () => /*#__PURE__*/React.createElement(InterventionsView, {
      data: data
    }),
    costo: () => /*#__PURE__*/React.createElement(CostView, {
      data: data
    }),
    historial: () => /*#__PURE__*/React.createElement(HistorialActual, {
      data: data
    }),
    actividad: () => /*#__PURE__*/React.createElement(ActividadActual, {
      data: data
    })
  }[screen];
  const v2 = {
    inicio: () => /*#__PURE__*/React.createElement(InicioV2, {
      data: data,
      onOpenVendedor: setModal
    }),
    supervisor: () => /*#__PURE__*/React.createElement(SupervisorV2, {
      data: data,
      onOpenVendedor: setModal
    }),
    intervenciones: () => /*#__PURE__*/React.createElement(InterventionsV2, {
      data: data
    }),
    costo: () => /*#__PURE__*/React.createElement(CostV2, {
      data: data
    }),
    historial: () => /*#__PURE__*/React.createElement(HistorialV2, {
      data: data,
      onOpenVendedor: setModal
    }),
    actividad: () => /*#__PURE__*/React.createElement(ActividadV2, {
      data: data,
      onOpenVendedor: setModal
    }),
    digest: () => /*#__PURE__*/React.createElement(DigestView, {
      data: data,
      onOpenVendedor: setModal
    }),
    mobile: () => /*#__PURE__*/React.createElement(MobileView, {
      data: data
    }),
    estados: () => /*#__PURE__*/React.createElement(EstadosView, null),
    precision: () => /*#__PURE__*/React.createElement(PrecisionView, {
      data: data
    })
  }[screen];
  const Tab = ({
    id,
    title,
    sub
  }) => /*#__PURE__*/React.createElement("button", {
    onClick: () => setV(id),
    style: {
      flex: 1,
      textAlign: "left",
      padding: "11px 18px",
      borderRadius: 10,
      cursor: "pointer",
      border: "1px solid",
      borderColor: v === id ? "var(--ink-900)" : "var(--line-strong)",
      background: v === id ? "var(--ink-900)" : "#fff"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14,
      color: v === id ? "#fff" : "var(--ink-700)"
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 12,
      color: v === id ? "rgba(255,255,255,.7)" : "var(--ink-400)",
      marginTop: 2
    }
  }, sub));
  const pill = (s, active, onClick) => /*#__PURE__*/React.createElement("button", {
    key: s.id,
    onClick: onClick,
    style: {
      padding: "8px 15px",
      borderRadius: 999,
      cursor: "pointer",
      border: "1px solid",
      borderColor: active ? "var(--blue-accent)" : "var(--line-strong)",
      background: active ? "var(--blue-bg)" : "#fff",
      color: active ? "var(--blue-text)" : "var(--ink-600)",
      fontFamily: "var(--font-sans)",
      fontWeight: 600,
      fontSize: 13,
      whiteSpace: "nowrap"
    }
  }, s.label);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1180,
      margin: "0 auto",
      padding: "28px 2.5rem 60px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start",
      flexWrap: "wrap",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 4,
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 22,
      color: "var(--ink-900)"
    }
  }, "\uD83D\uDD14 W\xFCrth Rotaci\xF3n \u2014 antes / despu\xE9s"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 18,
      fontFamily: "var(--font-sans)",
      fontSize: 13,
      color: "var(--ink-400)"
    }
  }, "Pantallas del producto con toggle actual/v2, y mejoras nuevas (precisi\xF3n, resumen semanal, m\xF3vil, estados).")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 7,
      fontFamily: "var(--font-sans)",
      fontSize: 12,
      color: "var(--ink-400)",
      whiteSpace: "nowrap"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 7,
      height: 7,
      borderRadius: "50%",
      background: "var(--green-bright)"
    }
  }), "Actualizado: 1 jun 2026, 08:00")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginBottom: 12,
      flexWrap: "wrap",
      alignItems: "center"
    }
  }, SCREENS.map(s => pill(s, screen === s.id, () => {
    setScreen(s.id);
    setModal(null);
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 1,
      height: 22,
      background: "var(--line-strong)",
      margin: "0 4px"
    }
  }), FEATURES.map(s => pill(s, screen === s.id, () => {
    setScreen(s.id);
    setModal(null);
  }))), !isFeature && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 12,
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement(Tab, {
    id: "actual",
    title: "Versi\xF3n actual",
    sub: "Recreaci\xF3n fiel del dashboard de hoy"
  }), /*#__PURE__*/React.createElement(Tab, {
    id: "v2",
    title: "Propuesta v2 profesional",
    sub: "Jerarqu\xEDa \xB7 acci\xF3n \xB7 charts limpios"
  })), !isFeature && v === "v2" && /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--blue-bg)",
      borderRadius: 10,
      padding: "12px 16px",
      marginBottom: 24,
      fontFamily: "var(--font-sans)",
      fontSize: 12.5,
      color: "var(--blue-text)",
      lineHeight: 1.5
    }
  }, /*#__PURE__*/React.createElement("b", null, "Qu\xE9 cambi\xF3:"), " ", V2_NOTES[screen]), isFeature && /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--green-bg)",
      borderRadius: 10,
      padding: "12px 16px",
      marginBottom: 24,
      fontFamily: "var(--font-sans)",
      fontSize: 12.5,
      color: "var(--green-text)",
      lineHeight: 1.5
    }
  }, /*#__PURE__*/React.createElement("b", null, "Mejora nueva"), " \u2014 no existe en el producto actual. ", NUEVA_NOTA[screen]), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "#f4f5f7",
      borderRadius: 14,
      padding: 28
    }
  }, isFeature ? v2() : v === "actual" ? actual() : v2()), /*#__PURE__*/React.createElement(VendedorModal, {
    r: modal,
    onClose: () => setModal(null)
  }));
}
ReactDOM.createRoot(document.getElementById("root")).render(/*#__PURE__*/React.createElement(CompareApp, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/CompareApp.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/CostV2.jsx
try { (() => {
/* Costo de Rotación — v2. Leads with the single number that matters
   (total exposure in pesos), makes the "what's at stake if we do nothing"
   tangible, ranks where to act, cleaner table. Reuses costoRotacion(). */

function CostV2({
  data
}) {
  const {
    V,
    Z
  } = data;
  const [niveles, setNiveles] = React.useState(["critico", "alto"]);
  const enriched = V.map(r => ({
    ...r,
    c: window.costoRotacion(r)
  }));
  const toggle = n => setNiveles(p => p.includes(n) ? p.filter(x => x !== n) : [...p, n]);
  const fil = enriched.filter(r => niveles.includes(r.nivel));
  const critArr = enriched.filter(r => r.nivel === "critico");
  const elevArr = enriched.filter(r => ["critico", "alto"].includes(r.nivel));
  const costoCrit = critArr.reduce((s, r) => s + r.c.total, 0);
  const costoTodos = elevArr.reduce((s, r) => s + r.c.total, 0);
  const costoProm = elevArr.length ? costoTodos / elevArr.length : 0;
  const byZone = Z.map(z => {
    const reps = enriched.filter(r => r.grupo === z.grupo && ["critico", "alto"].includes(r.nivel));
    return {
      grupo: z.grupo,
      total: reps.reduce((s, r) => s + r.c.total, 0),
      n: reps.length,
      scoreMax: Math.max(0, ...reps.map(r => r.score))
    };
  }).filter(z => z.total > 0).sort((a, b) => b.total - a.total);
  const maxZone = Math.max(...byZone.map(z => z.total), 1);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(V2Banner, {
    emoji: "\uD83D\uDCB0",
    tone: "red",
    title: `${fmtPesos(costoTodos)} en juego si no se actúa`,
    sub: `Exposición de los ${elevArr.length} vendedores en riesgo elevado. Cada baja cuesta en promedio ${fmtPesos(costoProm)} entre reemplazo y pérdida de cartera.`,
    cta: "Ver d\xF3nde priorizar \u2192"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement(HeroStat, {
    label: "Exposici\xF3n nivel cr\xEDtico",
    value: fmtPesos(costoCrit),
    accent: "var(--red-accent)",
    valueColor: "var(--red-accent)"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-500)"
    }
  }, critArr.length, " vendedores en riesgo inmediato de baja")), /*#__PURE__*/React.createElement(V2Card, {
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14,
      color: "var(--ink-900)",
      marginBottom: 14
    }
  }, "\uD83D\uDCCA D\xF3nde est\xE1 la exposici\xF3n"), byZone.map(z => /*#__PURE__*/React.createElement("div", {
    key: z.grupo,
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 64,
      fontSize: 12,
      fontWeight: 600,
      color: "var(--ink-700)",
      textAlign: "right"
    }
  }, z.grupo), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: "flex",
      alignItems: "center",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 20,
      borderRadius: 4,
      width: `${z.total / maxZone * 100}%`,
      minWidth: 4,
      background: z.scoreMax >= 8 ? "var(--red-accent)" : "var(--orange-accent)"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: "var(--ink-700)",
      whiteSpace: "nowrap"
    }
  }, fmtPesos(z.total), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontWeight: 400
    }
  }, "\xB7 ", z.n))))))), /*#__PURE__*/React.createElement(StatStrip, null, /*#__PURE__*/React.createElement(StatItem, {
    value: fmtPesos(costoTodos),
    label: "Exposici\xF3n total (cr\xEDtico + alto)"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: fmtPesos(costoProm),
    label: "Costo promedio por baja"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: elevArr.length,
    label: "Vendedores en riesgo"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: byZone[0] ? byZone[0].grupo : "—",
    label: "Zona de mayor exposici\xF3n"
  })), /*#__PURE__*/React.createElement(V2Section, {
    title: "\uD83E\uDDFE Detalle por vendedor",
    right: /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        gap: 8,
        alignItems: "center"
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        color: "var(--ink-400)"
      }
    }, "Nivel:"), ["critico", "alto", "medio", "bajo"].map(n => /*#__PURE__*/React.createElement("button", {
      key: n,
      onClick: () => toggle(n),
      style: {
        fontFamily: "var(--font-sans)",
        fontWeight: 600,
        fontSize: 12,
        padding: "4px 11px",
        borderRadius: 7,
        cursor: "pointer",
        border: "1px solid",
        borderColor: niveles.includes(n) ? "var(--blue-accent)" : "var(--line-strong)",
        background: niveles.includes(n) ? "var(--blue-bg)" : "#fff",
        color: niveles.includes(n) ? "var(--blue-text)" : "var(--ink-400)"
      }
    }, NIVEL_LABEL[n])))
  }), fil.length === 0 ? /*#__PURE__*/React.createElement(V2Empty, {
    emoji: "\uD83D\uDD0D",
    title: "Ning\xFAn vendedor en los niveles elegidos",
    sub: "Activ\xE1 al menos un nivel arriba para ver el detalle."
  }) : /*#__PURE__*/React.createElement(V2Card, {
    pad: false,
    style: {
      overflow: "hidden",
      padding: "8px 8px 0"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, ["Vendedor", "Tipo", "Zona", "Antigüedad", "Score", "Reemplazo", "Pérd. cartera", "Costo total"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: v2th
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, fil.sort((a, b) => b.c.total - a.c.total).map(r => /*#__PURE__*/React.createElement("tr", {
    key: r.id,
    className: "vrow"
  }, /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement("b", null, r.nombre), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontSize: 11
    }
  }, "(", r.id, ")")), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, r.tipo), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, r.grupo), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, fmtAntiguedad(r.meses)), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement(Badge, {
    nivel: r.nivel,
    label: String(r.score)
  })), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, fmtPesos(r.c.reemplazo)), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, fmtPesos(r.c.perdida)), /*#__PURE__*/React.createElement("td", {
    style: {
      ...v2td,
      fontWeight: 800,
      color: "var(--ink-900)"
    }
  }, fmtPesos(r.c.total))))))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 10
    }
  }, "Salarios seg\xFAn estructura W\xFCrth Argentina 2025 \xB7 datos simulados."));
}
Object.assign(window, {
  CostV2
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/CostV2.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/CostView.jsx
try { (() => {
/* Costo de Rotación — estimated peso cost of each potential departure. */

const SAL_INDUCCION = 1400000,
  SAL_PRODUCTIVO = 1800000,
  SAL_TELEVENTAS = 1215298;
const MESES_NUEVO = 1.5,
  MESES_RAMPA = 2,
  PCT_COB = 0.08,
  PCT_RAMPA = 0.12;
const PLAN_VIAJANTE = 17000000,
  PLAN_TELEVENTAS = 6000000;
function costoRotacion(r) {
  const sal = r.tipo === "Televentas" ? SAL_TELEVENTAS : r.meses <= 6 ? SAL_INDUCCION : SAL_PRODUCTIVO;
  const plan = r.tipo === "Televentas" ? PLAN_TELEVENTAS : PLAN_VIAJANTE;
  const directo = sal * 2 + SAL_INDUCCION * Math.round(MESES_NUEVO + MESES_RAMPA);
  const indirecto = plan * MESES_NUEVO * PCT_COB + plan * MESES_RAMPA * PCT_RAMPA;
  return {
    sal,
    reemplazo: SAL_INDUCCION * Math.round(MESES_NUEVO + MESES_RAMPA),
    perdida: indirecto,
    total: directo + indirecto
  };
}
function CostView({
  data
}) {
  const {
    V,
    Z
  } = data;
  const [niveles, setNiveles] = React.useState(["critico", "alto"]);
  const enriched = V.map(r => ({
    ...r,
    c: costoRotacion(r)
  }));
  const toggle = n => setNiveles(p => p.includes(n) ? p.filter(x => x !== n) : [...p, n]);
  const fil = enriched.filter(r => niveles.includes(r.nivel));
  const costoCrit = enriched.filter(r => r.nivel === "critico").reduce((s, r) => s + r.c.total, 0);
  const costoTodos = enriched.filter(r => ["critico", "alto"].includes(r.nivel)).reduce((s, r) => s + r.c.total, 0);
  const nElevado = enriched.filter(r => ["critico", "alto"].includes(r.nivel));
  const costoProm = nElevado.length ? costoTodos / nElevado.length : 0;
  const nCrit = enriched.filter(r => r.nivel === "critico").length;

  // exposure by zone
  const byZone = Z.map(z => {
    const reps = enriched.filter(r => r.grupo === z.grupo && ["critico", "alto"].includes(r.nivel));
    return {
      grupo: z.grupo,
      total: reps.reduce((s, r) => s + r.c.total, 0),
      scoreMax: Math.max(0, ...reps.map(r => r.score))
    };
  }).filter(z => z.total > 0).sort((a, b) => a.total - b.total);
  const maxZone = Math.max(...byZone.map(z => z.total), 1);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      font: "var(--w-black) 22px var(--font-sans)",
      color: "var(--ink-900)",
      marginBottom: 18
    }
  }, "\uD83D\uDCB0 Costo de Rotaci\xF3n"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 14,
      marginBottom: 28
    }
  }, /*#__PURE__*/React.createElement(KpiCard, {
    value: fmtPesos(costoCrit),
    accent: "red",
    label: "Exposici\xF3n nivel cr\xEDtico",
    sub: `${nCrit} vendedores en riesgo inmediato`
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: fmtPesos(costoTodos),
    accent: "orange",
    label: "Exposici\xF3n total (cr\xEDtico + alto)",
    sub: `${nElevado.length} en riesgo elevado`
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: fmtPesos(costoProm),
    accent: "blue",
    label: "Costo promedio por baja",
    sub: "Directo + p\xE9rdida de cartera"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: fmtPesos(fil.reduce((s, r) => s + r.c.total, 0)),
    accent: "green",
    label: "Vendedores en vista",
    sub: `${fil.length} con los filtros actuales`
  })), /*#__PURE__*/React.createElement(SectionHeader, null, "\uD83D\uDCCA Exposici\xF3n por zona"), /*#__PURE__*/React.createElement(Card, {
    style: {
      marginBottom: 28
    }
  }, byZone.map(z => /*#__PURE__*/React.createElement("div", {
    key: z.grupo,
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12,
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 70,
      fontSize: 13,
      fontWeight: 600,
      color: "var(--ink-700)",
      textAlign: "right"
    }
  }, z.grupo), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: "flex",
      alignItems: "center",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 22,
      borderRadius: 4,
      width: `${z.total / maxZone * 100}%`,
      minWidth: 4,
      background: z.scoreMax >= 8 ? "var(--red-accent)" : "var(--orange-accent)"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: "var(--ink-700)",
      whiteSpace: "nowrap"
    }
  }, fmtPesos(z.total)))))), /*#__PURE__*/React.createElement(SectionHeader, null, "\uD83E\uDDFE Detalle por vendedor"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginBottom: 12,
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginRight: 4
    }
  }, "Nivel:"), ["critico", "alto", "medio", "bajo"].map(n => /*#__PURE__*/React.createElement("button", {
    key: n,
    onClick: () => toggle(n),
    style: {
      font: "var(--w-semibold) 12px var(--font-sans)",
      padding: "4px 11px",
      borderRadius: 7,
      cursor: "pointer",
      border: "1px solid",
      borderColor: niveles.includes(n) ? "var(--blue-accent)" : "var(--line-strong)",
      background: niveles.includes(n) ? "var(--blue-bg)" : "#fff",
      color: niveles.includes(n) ? "var(--blue-text)" : "var(--ink-400)"
    }
  }, NIVEL_LABEL[n]))), /*#__PURE__*/React.createElement(Card, {
    pad: false,
    style: {
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, ["Vendedor", "Tipo", "Zona", "Antigüedad", "Score", "Salario/mes", "Reemplazo", "Pérd. cartera", "Costo total"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: thStyle
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, fil.sort((a, b) => b.c.total - a.c.total).map(r => /*#__PURE__*/React.createElement("tr", {
    key: r.id,
    className: "vrow"
  }, /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement("b", null, r.nombre), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontSize: 11
    }
  }, "(", r.id, ")")), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, r.tipo), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, r.grupo), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, fmtAntiguedad(r.meses)), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement(Badge, {
    nivel: r.nivel,
    label: String(r.score)
  })), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, fmtPesos(r.c.sal)), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, fmtPesos(r.c.reemplazo)), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, fmtPesos(r.c.perdida)), /*#__PURE__*/React.createElement("td", {
    style: {
      ...cellStyle,
      fontWeight: 800,
      color: "var(--ink-900)"
    }
  }, fmtPesos(r.c.total))))))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 8
    }
  }, "Salarios seg\xFAn estructura W\xFCrth Argentina 2025 \xB7 modelo de cobertura televentas. Datos simulados."));
}
function VendedorModal({
  r,
  onClose
}) {
  if (!r) return null;
  const zN = zonaNivel(r.rb);
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClose,
    style: {
      position: "fixed",
      inset: 0,
      background: "rgba(26,26,46,0.32)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 50
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: e => e.stopPropagation(),
    style: {
      width: 460,
      maxWidth: "90vw",
      background: "#fff",
      borderRadius: 12,
      boxShadow: "0 12px 40px rgba(0,0,0,0.2)",
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "20px 22px",
      borderBottom: "1px solid var(--line)",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      font: "var(--w-black) 18px var(--font-sans)",
      color: "var(--ink-900)"
    }
  }, r.nombre, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontWeight: 400,
      fontSize: 13
    }
  }, "(", r.id, ")")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 3
    }
  }, r.tipo, " \xB7 ", fmtAntiguedad(r.meses), " \xB7 ", r.grupo, " (", r.supervisor, ")")), /*#__PURE__*/React.createElement(ScoreCircle, {
    score: r.score,
    nivel: r.nivel,
    size: 44
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "18px 22px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 24,
      marginBottom: 18
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      marginBottom: 4
    }
  }, "% Plan 3m"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 22
    }
  }, r.plan3m, "%")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      marginBottom: 4
    }
  }, "Tendencia plan"), /*#__PURE__*/React.createElement(Sparkline, {
    vals: r.spark
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      marginBottom: 4
    }
  }, "Zona"), /*#__PURE__*/React.createElement(Badge, {
    nivel: zN,
    label: zonaLabel(r.rb)
  }))), r._hist && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 14,
      padding: "12px 14px",
      borderRadius: 8,
      background: "var(--table-head-bg)",
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      marginBottom: 2
    }
  }, "Trayectoria del score \xB7 \xFAltimos 6 meses"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-600)"
    }
  }, r._delta > 0 ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--red-text)",
      fontWeight: 700
    }
  }, "\u25B2 subi\xF3 ", r._delta, " este mes \u2014 empeorando") : r._delta < 0 ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--green-text)",
      fontWeight: 700
    }
  }, "\u25BC baj\xF3 ", Math.abs(r._delta), " este mes \u2014 mejorando") : /*#__PURE__*/React.createElement("span", null, "sin cambio respecto al mes anterior"))), /*#__PURE__*/React.createElement(ScoreHistory, {
    hist: r._hist,
    w: 110,
    h: 34
  })), window.ScoreBreakdown && /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement(ScoreBreakdown, {
    vendedor: r
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      marginBottom: 6
    }
  }, "Se\xF1ales detectadas"), /*#__PURE__*/React.createElement("div", {
    style: {
      minHeight: 26
    }
  }, /*#__PURE__*/React.createElement(Pills, {
    senales: r.senales
  })), window.recomendarAccion && ["critico", "alto"].includes(r.nivel) && (() => {
    const rec = window.recomendarAccion(r);
    return /*#__PURE__*/React.createElement("div", {
      style: {
        marginTop: 18,
        padding: "14px 16px",
        borderRadius: 10,
        background: r.nivel === "critico" ? "var(--red-bg)" : "var(--orange-bg)"
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: r.nivel === "critico" ? "var(--red-text)" : "var(--orange-text)",
        textTransform: "uppercase",
        letterSpacing: ".04em",
        marginBottom: 6,
        fontWeight: 700
      }
    }, "Acci\xF3n recomendada"), /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        alignItems: "baseline",
        gap: 8,
        flexWrap: "wrap"
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: "var(--font-sans)",
        fontWeight: 800,
        fontSize: 17,
        color: "var(--ink-900)"
      }
    }, rec.mejor.tipo), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 13,
        color: "var(--green-text)",
        fontWeight: 700
      }
    }, "\u2193 ", fmtNum(rec.mejor.avg, 1), " de score en promedio")), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 12,
        color: "var(--ink-600)",
        marginTop: 6,
        lineHeight: 1.5
      }
    }, "Es lo que mejor funcion\xF3 para ", /*#__PURE__*/React.createElement("b", null, rec.perfilLabel), " (", rec.mejor.n, " casos). ", r.nivel === "critico" ? "Agendá la reunión esta semana." : "Programá el seguimiento."), /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        gap: 6,
        marginTop: 10,
        flexWrap: "wrap"
      }
    }, rec.ranking.slice(1).map(a => /*#__PURE__*/React.createElement("span", {
      key: a.tipo,
      style: {
        fontSize: 11,
        color: "var(--ink-500)",
        background: "rgba(255,255,255,.6)",
        padding: "3px 8px",
        borderRadius: 6
      }
    }, a.tipo, " \xB7 \u2193", fmtNum(a.avg, 1)))));
  })(), (!window.recomendarAccion || !["critico", "alto"].includes(r.nivel)) && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 18,
      padding: "12px 14px",
      borderRadius: 8,
      background: "var(--table-head-bg)",
      fontSize: 12,
      color: "var(--ink-600)",
      lineHeight: 1.5
    }
  }, "Acci\xF3n sugerida: ", r.nivel === "medio" ? "monitoreo mensual." : "seguimiento normal."))));
}
Object.assign(window, {
  CostView,
  VendedorModal,
  costoRotacion
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/CostView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/FeatureViews.jsx
try { (() => {
/* Feature demos: #6 weekly digest · #7 mobile view · #5 loading/error/empty states. */

// ---------- #6 Resumen semanal (digest) ----------
function DigestView({
  data,
  onOpenVendedor
}) {
  const {
    V
  } = data;
  const reunion = V.filter(r => r.nivel === "critico").sort((a, b) => b.score - a.score);
  const escalaron = V.filter(r => r._delta > 0).sort((a, b) => b._delta - a._delta).slice(0, 4);
  const mejoraron = V.filter(r => r._delta < 0).sort((a, b) => a._delta - b._delta).slice(0, 3);
  const Row = ({
    r,
    right
  }) => /*#__PURE__*/React.createElement("div", {
    onClick: () => onOpenVendedor && onOpenVendedor(r),
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12,
      padding: "10px 0",
      borderBottom: "1px solid var(--line-faint)",
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement(ScoreCircle, {
    score: r.score,
    nivel: r.nivel,
    size: 32
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      fontSize: 13,
      color: "var(--ink-900)"
    }
  }, r.nombre), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)"
    }
  }, r.tipo, " \xB7 ", fmtAntiguedad(r.meses), " \xB7 ", r.grupo)), right);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 720,
      margin: "0 auto"
    }
  }, /*#__PURE__*/React.createElement(V2Card, {
    style: {
      padding: 0,
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "22px 26px",
      background: "var(--ink-900)",
      color: "#fff"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      opacity: .7,
      letterSpacing: ".04em",
      textTransform: "uppercase"
    }
  }, "\uD83D\uDD14 W\xFCrth Argentina \xB7 Resumen semanal"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 22,
      marginTop: 6
    }
  }, "Tu equipo esta semana"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      opacity: .8,
      marginTop: 4
    }
  }, "Semana del 27 ene \u2013 2 feb \xB7 enviado los lunes 8:00")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "20px 26px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 12,
      marginBottom: 22
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      padding: "12px 14px",
      borderRadius: 10,
      background: "var(--red-bg)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 24,
      color: "var(--red-text)"
    }
  }, reunion.length), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--red-text)"
    }
  }, "necesitan reuni\xF3n")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      padding: "12px 14px",
      borderRadius: 10,
      background: "var(--orange-bg)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 24,
      color: "var(--orange-text)"
    }
  }, escalaron.length), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--orange-text)"
    }
  }, "escalaron de score")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      padding: "12px 14px",
      borderRadius: 10,
      background: "var(--green-bg)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 24,
      color: "var(--green-text)"
    }
  }, mejoraron.length), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--green-text)"
    }
  }, "mejoraron"))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14,
      color: "var(--red-text)",
      marginBottom: 4
    }
  }, "\uD83D\uDD34 Reun\xED a estos vendedores esta semana"), reunion.map(r => /*#__PURE__*/React.createElement(Row, {
    key: r.id,
    r: r,
    right: /*#__PURE__*/React.createElement(AccionTag, {
      nivel: r.nivel
    })
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14,
      color: "var(--orange-text)",
      margin: "20px 0 4px"
    }
  }, "\u25B2 Empeoraron respecto a la semana pasada"), escalaron.map(r => /*#__PURE__*/React.createElement(Row, {
    key: r.id,
    r: r,
    right: /*#__PURE__*/React.createElement(ScoreDelta, {
      delta: r._delta
    })
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14,
      color: "var(--green-text)",
      margin: "20px 0 4px"
    }
  }, "\u25BC Buenas noticias \u2014 mejoraron"), mejoraron.map(r => /*#__PURE__*/React.createElement(Row, {
    key: r.id,
    r: r,
    right: /*#__PURE__*/React.createElement(ScoreDelta, {
      delta: r._delta
    })
  })), /*#__PURE__*/React.createElement("button", {
    style: {
      marginTop: 22,
      width: "100%",
      padding: "12px 0",
      borderRadius: 8,
      border: "none",
      cursor: "pointer",
      background: "var(--red-accent)",
      color: "#fff",
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14
    }
  }, "Abrir el dashboard completo \u2192"))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 12,
      textAlign: "center"
    }
  }, "Se env\xEDa por mail a cada supervisor con solo sus vendedores. Empuja la acci\xF3n sin depender de que entren al dashboard."));
}

// ---------- #7 Mobile (viajantes en la ruta) ----------
function MobileView({
  data
}) {
  const {
    V
  } = data;
  const reps = [...V].filter(r => r.supervisor === "Rodríguez, A.").sort((a, b) => b.score - a.score);
  const fallback = !window.IOSDevice;
  const list = /*#__PURE__*/React.createElement("div", {
    style: {
      background: "#f4f5f7",
      minHeight: "100%"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "8px 16px 12px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 24,
      color: "var(--ink-900)"
    }
  }, "Mis vendedores"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: "var(--ink-400)",
      marginTop: 2
    }
  }, "Centro \xB7 Rodr\xEDguez, A.")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      padding: "0 16px 12px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      background: "#fff",
      borderRadius: 10,
      padding: "10px 12px",
      boxShadow: "var(--shadow-card)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 20,
      color: "var(--red-accent)"
    }
  }, reps.filter(r => r.nivel === "critico").length), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)"
    }
  }, "cr\xEDticos")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      background: "#fff",
      borderRadius: 10,
      padding: "10px 12px",
      boxShadow: "var(--shadow-card)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 20,
      color: "var(--ink-900)"
    }
  }, reps.length), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)"
    }
  }, "activos"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 16px 24px",
      display: "flex",
      flexDirection: "column",
      gap: 10
    }
  }, reps.map(r => {
    const cc = {
      critico: "var(--red-accent)",
      alto: "var(--orange-accent)",
      medio: "var(--blue-accent)",
      bajo: "var(--green-accent)"
    }[r.nivel];
    return /*#__PURE__*/React.createElement("div", {
      key: r.id,
      style: {
        background: "#fff",
        borderRadius: 12,
        padding: "14px 16px",
        boxShadow: "var(--shadow-card)",
        borderLeft: `4px solid ${cc}`
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        alignItems: "center",
        gap: 12
      }
    }, /*#__PURE__*/React.createElement(ScoreCircle, {
      score: r.score,
      nivel: r.nivel,
      size: 40
    }), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        minWidth: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700,
        fontSize: 15,
        color: "var(--ink-900)"
      }
    }, r.nombre), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 12,
        color: "var(--ink-400)"
      }
    }, r.tipo, " \xB7 ", fmtAntiguedad(r.meses))), /*#__PURE__*/React.createElement(ScoreDelta, {
      delta: r._delta
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        marginTop: 10
      }
    }, /*#__PURE__*/React.createElement(AccionTag, {
      nivel: r.nivel
    })));
  })));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 36,
      alignItems: "center",
      justifyContent: "center",
      flexWrap: "wrap",
      padding: "12px 0"
    }
  }, fallback ? /*#__PURE__*/React.createElement("div", {
    style: {
      width: 320,
      height: 640,
      overflow: "auto",
      border: "10px solid #111",
      borderRadius: 40
    }
  }, list) : /*#__PURE__*/React.createElement(IOSDevice, {
    title: ""
  }, list), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 320
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 20,
      color: "var(--ink-900)",
      marginBottom: 10
    }
  }, "\uD83D\uDCF1 Para viajantes en la ruta"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: "var(--ink-600)",
      lineHeight: 1.6
    }
  }, "Los supervisores de campo no est\xE1n frente a una computadora. Esta vista compacta deja revisar", /*#__PURE__*/React.createElement("b", null, " \"mis vendedores\""), " desde el tel\xE9fono: misma jerarqu\xEDa de riesgo, score con tendencia (\u25B2/\u25BC) y la acci\xF3n sugerida a mano, antes de entrar a ver a un cliente."), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 16,
      padding: "12px 14px",
      borderRadius: 10,
      background: "var(--blue-bg)",
      fontSize: 13,
      color: "var(--blue-text)",
      lineHeight: 1.5
    }
  }, "Reusa exactamente los mismos componentes que el dashboard de escritorio \u2014 solo cambia el layout a una columna.")));
}

// ---------- #5 Loading / error / empty states ----------
function SkeletonRow() {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12,
      padding: "12px 0",
      borderBottom: "1px solid var(--line-faint)"
    }
  }, /*#__PURE__*/React.createElement(Skeleton, {
    w: 36,
    h: 36,
    r: 18
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement(Skeleton, {
    w: "55%",
    h: 12
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 6
    }
  }), /*#__PURE__*/React.createElement(Skeleton, {
    w: "35%",
    h: 10
  })), /*#__PURE__*/React.createElement(Skeleton, {
    w: 60,
    h: 20,
    r: 10
  }), /*#__PURE__*/React.createElement(Skeleton, {
    w: 36,
    h: 36,
    r: 18
  }));
}
function EstadosView() {
  const [state, setState] = React.useState("loading");
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(V2Section, {
    title: "\uD83E\uDDE9 Estados de la interfaz",
    right: /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        gap: 8
      }
    }, [["loading", "Cargando"], ["error", "Error"], ["empty", "Vacío"]].map(([k, l]) => /*#__PURE__*/React.createElement("button", {
      key: k,
      onClick: () => setState(k),
      style: {
        padding: "6px 14px",
        borderRadius: 8,
        cursor: "pointer",
        border: "1px solid",
        borderColor: state === k ? "var(--blue-accent)" : "var(--line-strong)",
        background: state === k ? "var(--blue-bg)" : "#fff",
        color: state === k ? "var(--blue-text)" : "var(--ink-600)",
        fontFamily: "var(--font-sans)",
        fontWeight: 600,
        fontSize: 13
      }
    }, l)))
  }), /*#__PURE__*/React.createElement(V2Card, {
    style: {
      minHeight: 320
    }
  }, state === "loading" && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 14,
      marginBottom: 24
    }
  }, [0, 1, 2, 3].map(i => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement(Skeleton, {
    w: "40%",
    h: 28
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 8
    }
  }), /*#__PURE__*/React.createElement(Skeleton, {
    w: "80%",
    h: 12
  })))), [0, 1, 2, 3, 4].map(i => /*#__PURE__*/React.createElement(SkeletonRow, {
    key: i
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-300)",
      marginTop: 14,
      textAlign: "center"
    }
  }, "Cargando datos del mes\u2026 los skeletons evitan el \"salto\" de layout.")), state === "error" && /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: "center",
      padding: "48px 22px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 34,
      marginBottom: 10
    }
  }, "\u26A0\uFE0F"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 16,
      color: "var(--ink-900)"
    }
  }, "No se pudo conectar a la base de datos"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: "var(--ink-500)",
      marginTop: 6,
      maxWidth: 420,
      marginLeft: "auto",
      marginRight: "auto",
      lineHeight: 1.5
    }
  }, "Los datos mostrados pueden estar desactualizados. Reintent\xE1 en unos minutos o avis\xE1 a sistemas si persiste."), /*#__PURE__*/React.createElement("button", {
    onClick: () => setState("loading"),
    style: {
      marginTop: 18,
      padding: "10px 22px",
      borderRadius: 8,
      border: "none",
      cursor: "pointer",
      background: "var(--ink-900)",
      color: "#fff",
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13
    }
  }, "\u21BB Reintentar")), state === "empty" && /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: "center",
      padding: "48px 22px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 34,
      marginBottom: 10
    }
  }, "\u2713"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 16,
      color: "var(--green-text)"
    }
  }, "No hay vendedores en riesgo \uD83C\uDF89"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: "var(--ink-500)",
      marginTop: 6,
      maxWidth: 420,
      marginLeft: "auto",
      marginRight: "auto",
      lineHeight: 1.5
    }
  }, "Ning\xFAn vendedor super\xF3 el umbral de alerta este mes. Buen trabajo del equipo de supervisi\xF3n."))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 10
    }
  }, "Tres estados que el dashboard real necesita y hoy no tiene: carga, error de conexi\xF3n y vac\xEDo."));
}
Object.assign(window, {
  DigestView,
  MobileView,
  EstadosView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/FeatureViews.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/HistorialViews.jsx
try { (() => {
/* Historial — faithful "actual" recreation + v2 redesign.
   v2 adds: company retention/survival curve, cohort table (#3), monthly rotation
   trend, average-risk-score trajectory, and a "biggest escalations" leaderboard (#2). */

// ---------- small SVG line chart ----------
function LineChart({
  series,
  w = 560,
  h = 150,
  max = 100,
  min = 0,
  labels,
  fmt = v => v,
  pad = 28
}) {
  const iw = w - pad * 2,
    ih = h - 24;
  const n = series[0].data.length;
  const xy = (v, i) => [pad + (n === 1 ? iw / 2 : i / (n - 1) * iw), 8 + ih - (v - min) / (max - min) * ih];
  return /*#__PURE__*/React.createElement("svg", {
    width: "100%",
    viewBox: `0 0 ${w} ${h}`,
    style: {
      display: "block"
    }
  }, [0, 0.5, 1].map(g => {
    const y = 8 + ih - g * ih;
    return /*#__PURE__*/React.createElement("line", {
      key: g,
      x1: pad,
      y1: y,
      x2: w - pad,
      y2: y,
      stroke: "var(--line-faint)",
      strokeWidth: "1"
    });
  }), series.map(s => {
    const pts = s.data.map((v, i) => xy(v, i));
    return /*#__PURE__*/React.createElement("g", {
      key: s.name
    }, /*#__PURE__*/React.createElement("polyline", {
      points: pts.map(p => p.join(",")).join(" "),
      fill: "none",
      stroke: s.color,
      strokeWidth: s.width || 2.5,
      strokeLinejoin: "round",
      strokeLinecap: "round",
      strokeDasharray: s.dash || "0"
    }), pts.map((p, i) => /*#__PURE__*/React.createElement("circle", {
      key: i,
      cx: p[0],
      cy: p[1],
      r: "3",
      fill: s.color
    })), s.showVals && pts.map((p, i) => /*#__PURE__*/React.createElement("text", {
      key: "t" + i,
      x: p[0],
      y: p[1] - 8,
      textAnchor: "middle",
      fontSize: "10",
      fontWeight: "700",
      fill: "var(--ink-500)",
      fontFamily: "var(--font-sans)"
    }, fmt(s.data[i]))));
  }), labels && labels.map((l, i) => /*#__PURE__*/React.createElement("text", {
    key: l + i,
    x: xy(min, i)[0],
    y: h - 4,
    textAnchor: "middle",
    fontSize: "10",
    fill: "var(--ink-400)",
    fontFamily: "var(--font-sans)"
  }, l)));
}

// ---------- v2 ----------
function HistorialV2({
  data,
  onOpenVendedor
}) {
  const {
    V,
    RETENCION,
    ROTACION,
    COHORTS
  } = data;
  const mesLabels = ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7"];
  const totalBajas = ROTACION.reduce((s, m) => s + m.bajas, 0);
  const retM6 = RETENCION[6];
  const escaladas = [...V].filter(r => r._delta > 0).sort((a, b) => b._delta - a._delta).slice(0, 5);

  // cohort color by retention at last known month
  const cohortCell = v => v == null ? "transparent" : v >= 70 ? "var(--green-pos-bg)" : v >= 50 ? "var(--cell-warn-bg)" : "var(--cell-bad-bg)";
  const cohortTx = v => v == null ? "var(--ink-200)" : v >= 70 ? "var(--green-pos-tx)" : v >= 50 ? "var(--cell-warn-tx)" : "var(--cell-bad-tx)";
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(V2Banner, {
    emoji: "\uD83D\uDCC8",
    tone: "red",
    title: `Solo ${retM6}% del equipo sigue activo al mes 6`,
    sub: `En los últimos 6 meses hubo ${totalBajas} bajas. La curva de supervivencia se desploma entre el mes 3 y el 5 — ahí está la fuga.`,
    cta: "Ver cohortes \u2192"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement(HeroStat, {
    label: "Permanencia al egreso",
    value: "5,2",
    unit: "meses",
    accent: "var(--orange-accent)"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-500)"
    }
  }, /*#__PURE__*/React.createElement("b", {
    style: {
      color: "var(--red-accent)"
    }
  }, "\u221271%"), " vs. 18 meses hace una d\xE9cada")), /*#__PURE__*/React.createElement(V2Card, {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "baseline",
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14,
      color: "var(--ink-900)"
    }
  }, "Curva de supervivencia del equipo"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)"
    }
  }, "% activos por mes de antig\xFCedad")), /*#__PURE__*/React.createElement(LineChart, {
    w: 560,
    h: 150,
    max: 100,
    min: 0,
    series: [{
      name: "ret",
      color: "var(--red-accent)",
      data: RETENCION,
      showVals: true
    }],
    labels: mesLabels,
    fmt: v => v + "%"
  }))), /*#__PURE__*/React.createElement(StatStrip, null, /*#__PURE__*/React.createElement(StatItem, {
    value: totalBajas,
    label: "Bajas \xFAltimos 6 meses"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: `${retM6}%`,
    label: "Retenci\xF3n al mes 6"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: `${RETENCION[3]}%`,
    label: "Retenci\xF3n al mes 3"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: escaladas.length,
    label: "Vendedores escalando este mes"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1.3fr 1fr",
      gap: 24,
      marginBottom: 32,
      alignItems: "start"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(V2Section, {
    title: "\uD83D\uDD04 Rotaci\xF3n mensual \u2014 bajas vs. altas"
  }), /*#__PURE__*/React.createElement(V2Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-end",
      gap: 16,
      height: 150
    }
  }, ROTACION.map(m => {
    const mx = Math.max(...ROTACION.flatMap(x => [x.bajas, x.altas]));
    return /*#__PURE__*/React.createElement("div", {
      key: m.mes,
      style: {
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 6,
        height: "100%",
        justifyContent: "flex-end"
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        gap: 3,
        alignItems: "flex-end",
        height: 110
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 12,
        height: `${m.altas / mx * 100}%`,
        background: "var(--green-soft)",
        borderRadius: "2px 2px 0 0"
      },
      title: `${m.altas} altas`
    }), /*#__PURE__*/React.createElement("div", {
      style: {
        width: 12,
        height: `${m.bajas / mx * 100}%`,
        background: "var(--red-accent)",
        borderRadius: "2px 2px 0 0"
      },
      title: `${m.bajas} bajas`
    })), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        color: "var(--ink-400)"
      }
    }, m.mes));
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      marginTop: 12,
      fontSize: 11,
      color: "var(--ink-500)"
    }
  }, /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-block",
      width: 9,
      height: 9,
      background: "var(--red-accent)",
      borderRadius: 2,
      marginRight: 5
    }
  }), "Bajas"), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-block",
      width: 9,
      height: 9,
      background: "var(--green-soft)",
      borderRadius: 2,
      marginRight: 5
    }
  }), "Altas")))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(V2Section, {
    title: "\uD83D\uDCCA Score de riesgo promedio"
  }), /*#__PURE__*/React.createElement(V2Card, null, /*#__PURE__*/React.createElement(LineChart, {
    w: 360,
    h: 150,
    max: 7,
    min: 3,
    series: [{
      name: "score",
      color: "var(--red-accent)",
      data: ROTACION.map(m => m.scoreProm),
      showVals: true
    }],
    labels: ROTACION.map(m => m.mes),
    fmt: v => v.toFixed(1)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      marginTop: 8
    }
  }, "El riesgo promedio del equipo viene en aumento \u2014 m\xE1s vendedores entran en zona de alerta.")))), /*#__PURE__*/React.createElement(V2Section, {
    title: "\uD83D\uDC65 Retenci\xF3n por cohorte de ingreso",
    right: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        color: "var(--ink-400)"
      }
    }, "% que sigue activo cada mes")
  }), /*#__PURE__*/React.createElement(V2Card, {
    pad: false,
    style: {
      overflow: "hidden",
      padding: "8px 8px 8px"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Cohorte"), /*#__PURE__*/React.createElement("th", {
    style: {
      ...v2th,
      textAlign: "center"
    }
  }, "Ingresos"), ["M0", "M1", "M2", "M3", "M4", "M5"].map(m => /*#__PURE__*/React.createElement("th", {
    key: m,
    style: {
      ...v2th,
      textAlign: "center"
    }
  }, m)))), /*#__PURE__*/React.createElement("tbody", null, COHORTS.map(c => /*#__PURE__*/React.createElement("tr", {
    key: c.cohorte
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      ...v2td,
      fontWeight: 700
    }
  }, c.cohorte), /*#__PURE__*/React.createElement("td", {
    style: {
      ...v2td,
      textAlign: "center",
      color: "var(--ink-500)"
    }
  }, c.ingresos), [0, 1, 2, 3, 4, 5].map(mi => {
    const v = c.ret[mi];
    return /*#__PURE__*/React.createElement("td", {
      key: mi,
      style: {
        ...v2td,
        textAlign: "center",
        padding: 6
      }
    }, v == null ? /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--ink-150)"
      }
    }, "\xB7") : /*#__PURE__*/React.createElement("span", {
      style: {
        display: "inline-block",
        minWidth: 40,
        padding: "5px 0",
        borderRadius: 6,
        background: cohortCell(v),
        color: cohortTx(v),
        fontWeight: 700,
        fontSize: 12
      }
    }, v, "%"));
  })))))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      margin: "8px 0 32px"
    }
  }, "Cada cohorte pierde ~25-40% para el mes 3. Las cohortes en zonas quemadas (Centro) caen m\xE1s r\xE1pido."), /*#__PURE__*/React.createElement(V2Section, {
    title: "\u26A0\uFE0F Mayores escaladas de score este mes",
    right: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        color: "var(--ink-400)"
      }
    }, "Qui\xE9nes empeoraron m\xE1s r\xE1pido")
  }), escaladas.length === 0 ? /*#__PURE__*/React.createElement(V2Empty, {
    title: "Nadie escal\xF3 este mes",
    sub: "Ning\xFAn vendedor subi\xF3 su score respecto al mes anterior."
  }) : /*#__PURE__*/React.createElement(V2Card, {
    pad: false,
    style: {
      overflow: "hidden",
      padding: "8px 8px 0"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Vendedor"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Score actual"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "\u0394 mes"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Trayectoria 6m"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Zona"))), /*#__PURE__*/React.createElement("tbody", null, escaladas.map(r => /*#__PURE__*/React.createElement("tr", {
    key: r.id,
    className: "vrow",
    onClick: () => onOpenVendedor && onOpenVendedor(r),
    style: {
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement("b", null, r.nombre), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontSize: 11
    }
  }, "(", r.id, ")"), /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--ink-250)",
      fontSize: 11
    }
  }, r.tipo, " \xB7 ", fmtAntiguedad(r.meses))), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement(ScoreCircle, {
    score: r.score,
    nivel: r.nivel
  })), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement(ScoreDelta, {
    delta: r._delta
  })), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement(ScoreHistory, {
    hist: r._hist,
    w: 100,
    h: 30
  })), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement(Badge, {
    nivel: zonaNivel(r.rb),
    label: r.grupo
  }))))))));
}

// ---------- faithful "actual" ----------
function HistorialActual({
  data
}) {
  const {
    ROTACION,
    RETENCION
  } = data;
  const mx = Math.max(...ROTACION.flatMap(x => [x.bajas, x.altas]));
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 22,
      color: "var(--ink-900)",
      marginBottom: 18
    }
  }, "\uD83D\uDCC8 Historial de rotaci\xF3n"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 14,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(KpiCard, {
    value: ROTACION.reduce((s, m) => s + m.bajas, 0),
    label: "Bajas (6 meses)"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: "5,2 m",
    label: "Permanencia prom."
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: `${RETENCION[6]}%`,
    label: "Retenci\xF3n al mes 6"
  })), /*#__PURE__*/React.createElement(SectionHeader, null, "Rotaci\xF3n mensual"), /*#__PURE__*/React.createElement(Card, {
    style: {
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-end",
      gap: 16,
      height: 180
    }
  }, ROTACION.map(m => /*#__PURE__*/React.createElement("div", {
    key: m.mes,
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 6,
      height: "100%",
      justifyContent: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 4,
      alignItems: "flex-end",
      height: 140
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 14,
      height: `${m.altas / mx * 100}%`,
      background: "#8DB56B"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 14,
      height: `${m.bajas / mx * 100}%`,
      background: "#E24B4A"
    }
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "var(--ink-500)"
    }
  }, m.mes)))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-500)",
      marginTop: 12
    }
  }, "\uD83D\uDD34 Bajas \xB7 \uD83D\uDFE2 Altas")), /*#__PURE__*/React.createElement(SectionHeader, null, "Permanencia al egreso por mes"), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-end",
      gap: 12,
      height: 120
    }
  }, RETENCION.map((v, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 5,
      height: "100%",
      justifyContent: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: "var(--ink-500)"
    }
  }, v, "%"), /*#__PURE__*/React.createElement("div", {
    style: {
      width: "70%",
      height: `${v}%`,
      background: "#4A90D9",
      borderRadius: "2px 2px 0 0"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: "var(--ink-400)"
    }
  }, "M", i))))));
}
Object.assign(window, {
  HistorialV2,
  HistorialActual,
  LineChart
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/HistorialViews.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/InicioV2.jsx
try { (() => {
/* Inicio v2 — "propuesta profesional". Same data as InicioView, rebuilt to apply:
   1) jerarquía visual  2) densidad/respiración  3) permanencia como estrella
   4) acción no solo diagnóstico  5) charts limpios  6) estados vacíos.
   Reuses primitives.jsx (Card, ScoreCircle, Pills, Badge, Sparkline). */

// ---- Acción sugerida por nivel (diagnóstico → to-do) ----
const ACCION = {
  critico: ["Reunión esta semana", "var(--red-text)", "var(--red-bg)"],
  alto: ["Seguimiento activo", "var(--orange-text)", "var(--orange-bg)"],
  medio: ["Monitoreo mensual", "var(--ink-600)", "var(--table-head-bg)"],
  bajo: ["Seguimiento normal", "var(--ink-400)", "transparent"]
};

// ---- 1+4: banner de acción del día ----
function ActionBanner({
  nCrit,
  nOnb
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 14,
      padding: "14px 20px",
      borderRadius: 12,
      background: "var(--red-bg)",
      border: "1px solid #f4cfcd",
      marginBottom: 28
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 22
    }
  }, "\uD83D\uDD34"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 16,
      color: "var(--red-text)"
    }
  }, nCrit, " vendedores necesitan reuni\xF3n esta semana"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 13,
      color: "#8a3331",
      marginTop: 2
    }
  }, nOnb, " de ellos est\xE1n en su ventana cr\xEDtica de onboarding (primeros 6 meses).")), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: "9px 18px",
      borderRadius: 8,
      border: "none",
      cursor: "pointer",
      background: "var(--red-accent)",
      color: "#fff",
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13,
      whiteSpace: "nowrap"
    }
  }, "Ver lista de acci\xF3n \u2192"));
}

// ---- 1: KPI hero dominante (riesgo elevado) ----
function HeroKpi({
  nElevado,
  nCrit,
  nAlto,
  total
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: "0 0 320px",
      background: "var(--surface)",
      borderRadius: 14,
      padding: "22px 24px",
      boxShadow: "var(--shadow-card)",
      borderTop: "4px solid var(--red-accent)",
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13,
      color: "var(--ink-600)",
      textTransform: "uppercase",
      letterSpacing: ".04em"
    }
  }, "En riesgo elevado"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: 10,
      marginTop: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 64,
      lineHeight: 1,
      color: "var(--red-accent)"
    }
  }, nElevado), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 16,
      color: "var(--ink-400)"
    }
  }, "de ", total, " activos")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginTop: 16
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      textAlign: "center",
      padding: "8px 0",
      borderRadius: 8,
      background: "var(--red-bg)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontWeight: 800,
      fontSize: 20,
      color: "var(--red-text)"
    }
  }, nCrit), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "var(--red-text)",
      fontWeight: 600
    }
  }, "Cr\xEDtico")), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      textAlign: "center",
      padding: "8px 0",
      borderRadius: 8,
      background: "var(--orange-bg)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontWeight: 800,
      fontSize: 20,
      color: "var(--orange-text)"
    }
  }, nAlto), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "var(--orange-text)",
      fontWeight: 600
    }
  }, "Alto"))));
}

// ---- 3: permanencia como estrella, con la caída 18 → 5 ----
function PermanenciaCard() {
  const serie = [{
    y: "2016",
    m: 18
  }, {
    y: "2019",
    m: 13
  }, {
    y: "2022",
    m: 8
  }, {
    y: "2025",
    m: 5.2
  }];
  const max = 18;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      background: "var(--surface)",
      borderRadius: 14,
      padding: "22px 24px",
      boxShadow: "var(--shadow-card)",
      borderTop: "4px solid var(--orange-accent)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13,
      color: "var(--ink-600)",
      textTransform: "uppercase",
      letterSpacing: ".04em"
    }
  }, "Permanencia al egreso"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: 8,
      marginTop: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 44,
      lineHeight: 1,
      color: "var(--ink-900)"
    }
  }, "5,2"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 18,
      color: "var(--ink-400)"
    }
  }, "meses"))), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: "right"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 22,
      color: "var(--red-accent)"
    }
  }, "\u221271%"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      maxWidth: 130,
      lineHeight: 1.35,
      marginTop: 2
    }
  }, "vs. 18 meses hace una d\xE9cada"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-end",
      gap: 14,
      height: 70,
      marginTop: 18
    }
  }, serie.map((d, i) => /*#__PURE__*/React.createElement("div", {
    key: d.y,
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 5,
      height: "100%",
      justifyContent: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      color: i === serie.length - 1 ? "var(--red-accent)" : "var(--ink-400)"
    }
  }, String(d.m).replace(".", ","), "m"), /*#__PURE__*/React.createElement("div", {
    style: {
      width: "70%",
      maxWidth: 30,
      height: `${d.m / max * 48}px`,
      borderRadius: "3px 3px 0 0",
      background: i === serie.length - 1 ? "var(--red-accent)" : "var(--chart-neutral)"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: "var(--ink-300)"
    }
  }, d.y)))));
}

// ---- 1: stats secundarias, de-enfatizadas ----
function SecondaryStat({
  value,
  label
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      padding: "4px 2px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 26,
      color: "var(--ink-900)"
    }
  }, value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 2
    }
  }, label));
}

// ---- 5: chart limpio (ventana crítica) ----
function CleanWindowChart({
  data
}) {
  const max = Math.max(...data.map(d => d.n));
  const color = m => m <= 3 ? "var(--red-accent)" : m <= 6 ? "var(--orange-accent)" : "var(--chart-neutral)";
  const totalEarly = data.filter(d => d.m <= 6).reduce((s, d) => s + d.n, 0);
  const totalAll = data.reduce((s, d) => s + d.n, 0);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderRadius: 14,
      padding: "20px 24px",
      boxShadow: "var(--shadow-card)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "baseline",
      marginBottom: 18
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 15,
      color: "var(--ink-900)"
    }
  }, "\u23F1\uFE0F Ventanas cr\xEDticas de permanencia"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 13,
      color: "var(--red-text)",
      fontWeight: 700
    }
  }, Math.round(totalEarly / totalAll * 100), "% se va antes del mes 7")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-end",
      gap: 7,
      height: 150
    }
  }, data.map(d => /*#__PURE__*/React.createElement("div", {
    key: d.m,
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 5,
      height: "100%",
      justifyContent: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      fontWeight: 700,
      color: "var(--ink-400)"
    }
  }, d.n), /*#__PURE__*/React.createElement("div", {
    style: {
      width: "100%",
      maxWidth: 24,
      height: `${d.n / max * 110}px`,
      borderRadius: "3px 3px 0 0",
      background: color(d.m)
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: "var(--ink-300)"
    }
  }, "M", d.m)))));
}

// ---- 4: tabla con columna de acción ----
function V2Table({
  rows,
  onOpen,
  empty
}) {
  const density = useDensity();
  const th = {
    background: "transparent",
    padding: "0 14px 10px",
    textAlign: "left",
    fontSize: 11,
    fontWeight: 700,
    color: "var(--ink-400)",
    textTransform: "uppercase",
    letterSpacing: ".04em",
    borderBottom: "2px solid var(--line-strong)"
  };
  const td = tdFor(density);
  if (!rows.length) {
    return /*#__PURE__*/React.createElement("div", {
      style: {
        background: "var(--surface)",
        borderRadius: 14,
        boxShadow: "var(--shadow-card)",
        padding: "48px 22px",
        textAlign: "center"
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 30,
        marginBottom: 8
      }
    }, "\u2713"), /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700,
        fontSize: 14,
        color: "var(--green-text)"
      }
    }, empty || "Sin vendedores en esta vista"), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 13,
        color: "var(--ink-400)",
        marginTop: 4
      }
    }, "Prob\xE1 con otro filtro o limpi\xE1 la b\xFAsqueda."));
  }
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderRadius: 14,
      boxShadow: "var(--shadow-card)",
      overflow: "hidden",
      padding: "8px 8px 0"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: th
  }, "Vendedor"), /*#__PURE__*/React.createElement("th", {
    style: th
  }, "Se\xF1ales"), /*#__PURE__*/React.createElement("th", {
    style: th
  }, "% Plan 3m"), /*#__PURE__*/React.createElement("th", {
    style: th
  }, "Tendencia"), /*#__PURE__*/React.createElement("th", {
    style: th
  }, "Score \xB7 \u0394 mes"), /*#__PURE__*/React.createElement("th", {
    style: th
  }, "Acci\xF3n sugerida"))), /*#__PURE__*/React.createElement("tbody", null, rows.map(r => {
    const [acc, accTx, accBg] = ACCION[r.nivel];
    return /*#__PURE__*/React.createElement("tr", {
      key: r.id,
      className: "vrow",
      onClick: () => onOpen && onOpen(r),
      style: {
        cursor: "pointer"
      }
    }, /*#__PURE__*/React.createElement("td", {
      style: td
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700,
        color: "var(--ink-900)",
        fontSize: 13
      }
    }, r.nombre, " ", /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--ink-400)",
        fontWeight: 400,
        fontSize: 11
      }
    }, "(", r.id, ")")), /*#__PURE__*/React.createElement("div", {
      style: {
        color: "var(--ink-250)",
        fontSize: 11,
        marginTop: 2
      }
    }, r.tipo, " \xB7 ", fmtAntiguedad(r.meses), " \xB7 ", r.grupo)), /*#__PURE__*/React.createElement("td", {
      style: td
    }, /*#__PURE__*/React.createElement(Pills, {
      senales: r.senales
    })), /*#__PURE__*/React.createElement("td", {
      style: td
    }, /*#__PURE__*/React.createElement("b", null, r.plan3m, "%")), /*#__PURE__*/React.createElement("td", {
      style: td
    }, /*#__PURE__*/React.createElement(Sparkline, {
      vals: r.spark
    })), /*#__PURE__*/React.createElement("td", {
      style: td
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        alignItems: "center",
        gap: 8
      }
    }, /*#__PURE__*/React.createElement(ScoreCircle, {
      score: r.score,
      nivel: r.nivel
    }), /*#__PURE__*/React.createElement(ScoreDelta, {
      delta: r._delta
    }))), /*#__PURE__*/React.createElement("td", {
      style: td
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: "inline-block",
        padding: "4px 10px",
        borderRadius: 7,
        background: accBg,
        color: accTx,
        fontSize: 12,
        fontWeight: 700,
        whiteSpace: "nowrap"
      }
    }, acc)));
  }))));
}
function InicioV2({
  data,
  onOpenVendedor
}) {
  const {
    V,
    VENTANAS
  } = data;
  const [filtro, setFiltro] = React.useState("Requieren acción");
  const [busq, setBusq] = React.useState("");
  const total = V.length;
  const crit = V.filter(r => r.nivel === "critico");
  const alto = V.filter(r => r.nivel === "alto");
  const nElevado = crit.length + alto.length;
  const nOnbCrit = V.filter(r => r.meses <= 6 && r.nivel === "critico").length;
  let df = [...V].sort((a, b) => b.score - a.score);
  if (filtro === "Requieren acción") df = df.filter(r => ["critico", "alto"].includes(r.nivel));else if (filtro === "Crítico") df = df.filter(r => r.nivel === "critico");else if (filtro === "Onboarding") df = df.filter(r => r.meses <= 6);
  if (busq) df = df.filter(r => r.nombre.toLowerCase().includes(busq.toLowerCase()) || String(r.id).includes(busq));
  const pill = o => /*#__PURE__*/React.createElement("button", {
    key: o,
    onClick: () => setFiltro(o),
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 600,
      fontSize: 13,
      padding: "6px 15px",
      borderRadius: 8,
      cursor: "pointer",
      border: "1px solid",
      borderColor: filtro === o ? "var(--blue-accent)" : "var(--line-strong)",
      background: filtro === o ? "var(--blue-bg)" : "#fff",
      color: filtro === o ? "var(--blue-text)" : "var(--ink-600)"
    }
  }, o);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionBanner, {
    nCrit: crit.length,
    nOnb: nOnbCrit
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement(HeroKpi, {
    nElevado: nElevado,
    nCrit: crit.length,
    nAlto: alto.length,
    total: total
  }), /*#__PURE__*/React.createElement(PermanenciaCard, null)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 0,
      padding: "0 4px",
      marginBottom: 36,
      borderBottom: "1px solid var(--line-faint)",
      paddingBottom: 18
    }
  }, /*#__PURE__*/React.createElement(SecondaryStat, {
    value: total,
    label: "Vendedores activos"
  }), /*#__PURE__*/React.createElement(SecondaryStat, {
    value: nOnbCrit,
    label: "Onboarding en riesgo"
  }), /*#__PURE__*/React.createElement(SecondaryStat, {
    value: "4",
    label: "Supervisores activos"
  }), /*#__PURE__*/React.createElement(SecondaryStat, {
    value: "3,5",
    label: "Vendedores / supervisor"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: 16,
      flexWrap: "wrap",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 16,
      color: "var(--ink-900)"
    }
  }, "\uD83D\uDCCB Vendedores por prioridad"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      alignItems: "center"
    }
  }, ["Requieren acción", "Crítico", "Onboarding", "Todos"].map(pill), /*#__PURE__*/React.createElement("input", {
    value: busq,
    onChange: e => setBusq(e.target.value),
    placeholder: "\uD83D\uDD0D Buscar\u2026",
    style: {
      padding: "7px 12px",
      borderRadius: 8,
      border: "1px solid var(--line-strong)",
      fontFamily: "var(--font-sans)",
      fontSize: 13,
      width: 150,
      outline: "none"
    }
  }), /*#__PURE__*/React.createElement(DensityToggle, null))), /*#__PURE__*/React.createElement(V2Table, {
    rows: df,
    onOpen: onOpenVendedor,
    empty: "No hay vendedores que requieran acci\xF3n \uD83C\uDF89"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 10
    }
  }, df.length, " vendedores \xB7 ordenados por score \xB7 clic para ver el detalle."), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 40
    }
  }, /*#__PURE__*/React.createElement(CleanWindowChart, {
    data: VENTANAS
  })));
}
Object.assign(window, {
  InicioV2
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/InicioV2.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/InicioView.jsx
try { (() => {
/* Inicio — the main board. KPI row, filter, vendedor table, zones + critical
   window chart, onboarding tracker. */

function FilterRadio({
  value,
  onChange,
  options
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginBottom: 14,
      flexWrap: "wrap"
    }
  }, options.map(o => /*#__PURE__*/React.createElement("button", {
    key: o,
    onClick: () => onChange(o),
    style: {
      font: "var(--w-semibold) 13px var(--font-sans)",
      padding: "5px 14px",
      borderRadius: 8,
      cursor: "pointer",
      border: "1px solid",
      borderColor: value === o ? "var(--blue-accent)" : "var(--line-strong)",
      background: value === o ? "var(--blue-bg)" : "#fff",
      color: value === o ? "var(--blue-text)" : "var(--ink-600)"
    }
  }, o)));
}
function SearchInput({
  value,
  onChange,
  placeholder
}) {
  return /*#__PURE__*/React.createElement("input", {
    value: value,
    onChange: e => onChange(e.target.value),
    placeholder: placeholder,
    style: {
      width: "100%",
      padding: "9px 12px",
      borderRadius: 8,
      border: "1px solid var(--line-strong)",
      font: "var(--w-regular) 13px var(--font-sans)",
      color: "var(--ink-900)",
      background: "#fff",
      outline: "none",
      boxSizing: "border-box"
    }
  });
}
function VendedorRow({
  r,
  onOpen
}) {
  const zN = zonaNivel(r.rb),
    zL = zonaLabel(r.rb);
  return /*#__PURE__*/React.createElement("tr", {
    onClick: () => onOpen && onOpen(r),
    style: {
      cursor: onOpen ? "pointer" : "default"
    },
    className: "vrow"
  }, /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      color: "var(--ink-900)",
      fontSize: 13
    }
  }, r.nombre, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontWeight: 400,
      fontSize: 11
    }
  }, "(", r.id, ")")), /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--ink-250)",
      fontSize: 11,
      marginTop: 2
    }
  }, r.tipo, " \xB7 ", fmtAntiguedad(r.meses))), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement(Pills, {
    senales: r.senales
  })), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement("b", null, r.plan3m, "%")), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement(Sparkline, {
    vals: r.spark
  })), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 600,
      fontSize: 13
    }
  }, r.grupo), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 3
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    nivel: zN,
    label: zL
  }))), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement(ScoreCircle, {
    score: r.score,
    nivel: r.nivel
  })));
}
const cellStyle = {
  padding: "11px 12px",
  borderBottom: "1px solid var(--line-faint)",
  verticalAlign: "middle",
  fontSize: 13
};
const thStyle = {
  background: "var(--table-head-bg)",
  padding: "10px 12px",
  textAlign: "left",
  fontSize: 12,
  fontWeight: 600,
  color: "var(--ink-500)",
  borderBottom: "2px solid var(--line-strong)"
};
function VendedorTable({
  rows,
  onOpen
}) {
  return /*#__PURE__*/React.createElement(Card, {
    pad: false,
    style: {
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, ["Vendedor", "Señales detectadas", "% Plan 3m", "Tendencia ⓘ", "Zona ⓘ", "Score ⓘ"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: thStyle
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, rows.map(r => /*#__PURE__*/React.createElement(VendedorRow, {
    key: r.id,
    r: r,
    onOpen: onOpen
  })))));
}
function CriticalWindowChart({
  data
}) {
  const max = Math.max(...data.map(d => d.n));
  const colorMes = m => m <= 3 ? "var(--red-accent)" : m <= 6 ? "var(--orange-accent)" : m <= 12 ? "var(--chart-neutral)" : "var(--green-soft)";
  return /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-end",
      gap: 6,
      height: 200,
      paddingTop: 10
    }
  }, data.map(d => /*#__PURE__*/React.createElement("div", {
    key: d.m,
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 4,
      height: "100%",
      justifyContent: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      color: "var(--ink-500)"
    }
  }, d.n), /*#__PURE__*/React.createElement("div", {
    style: {
      width: "100%",
      maxWidth: 26,
      height: `${d.n / max * 150}px`,
      background: colorMes(d.m),
      borderRadius: "2px 2px 0 0"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: "var(--ink-400)"
    }
  }, "M", d.m)))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      marginTop: 10,
      lineHeight: 1.5
    }
  }, "\uD83D\uDD34 Mes 1-3 (inducci\xF3n) \xB7 \uD83D\uDFE0 Mes 4-6 (adaptaci\xF3n) \xB7 \u2B1C Mes 7-12. M\xE1s de la mitad de las renuncias ocurren antes del mes 7."));
}
function ZonesPanel({
  zones
}) {
  const sorted = [...zones].sort((a, b) => b.rb - a.rb);
  return /*#__PURE__*/React.createElement(Card, {
    pad: false,
    style: {
      padding: "4px 20px"
    }
  }, sorted.map((g, i) => {
    const nivel = zonaNivel(g.rb);
    return /*#__PURE__*/React.createElement("div", {
      key: g.grupo,
      style: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "13px 0",
        borderBottom: i < sorted.length - 1 ? "1px solid var(--line-faint)" : "none"
      }
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700,
        fontSize: 13,
        color: "var(--ink-900)"
      }
    }, g.grupo, " \xB7 ", g.supervisor), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: "var(--ink-250)",
        marginTop: 2
      }
    }, g.historicos, " vendedores hist\xF3ricos \xB7 duraci\xF3n prom. al egreso: ", g.permEgreso.toFixed(1).replace(".", ","), "m")), /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
        gap: 4
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700,
        fontSize: 13
      }
    }, g.planProm, "% plan"), /*#__PURE__*/React.createElement(Badge, {
      nivel: nivel
    })));
  }));
}
function InicioView({
  data,
  onOpenVendedor
}) {
  const {
    V,
    Z,
    VENTANAS
  } = data;
  const [filtro, setFiltro] = React.useState("Todos");
  const [busq, setBusq] = React.useState("");
  let df = [...V].sort((a, b) => b.score - a.score);
  if (filtro === "Crítico") df = df.filter(r => r.nivel === "critico");else if (filtro === "Alto") df = df.filter(r => r.nivel === "alto");else if (filtro === "Viajantes") df = df.filter(r => r.tipo === "Viajante");else if (filtro === "Televentas") df = df.filter(r => r.tipo === "Televentas");
  if (busq) df = df.filter(r => r.nombre.toLowerCase().includes(busq.toLowerCase()) || String(r.id).includes(busq));
  const total = V.length;
  const enRiesgo = V.filter(r => ["critico", "alto"].includes(r.nivel)).length;
  const permProm = V.reduce((s, r) => s + r.meses, 0) / V.length;
  const obCritico = V.filter(r => r.meses <= 6 && ["critico", "alto"].includes(r.nivel)).length;
  const onb = [...V].filter(r => r.meses <= 6).sort((a, b) => b.score - a.score);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 14,
      marginBottom: 28
    }
  }, /*#__PURE__*/React.createElement(KpiCard, {
    value: total,
    label: "Vendedores activos",
    sub: "Actualizando mensualmente"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: enRiesgo,
    valueColor: "var(--red-accent)",
    accent: "red",
    label: "En riesgo elevado",
    sub: "Score \u2265 6 (alto o cr\xEDtico)"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: "5,2 m",
    accent: "orange",
    label: "Permanencia al egreso",
    sub: "Solo \xFAltimos 12 meses"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: obCritico,
    valueColor: "var(--blue-accent)",
    accent: "blue",
    label: "Onboarding en riesgo",
    sub: "Score \u2265 6 en sus primeros 6 meses"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: 4,
    label: "Supervisores activos",
    sub: "3.5 vendedores/supervisor"
  })), /*#__PURE__*/React.createElement(SectionHeader, null, "\uD83D\uDCCB Vendedores por score de riesgo de fuga"), /*#__PURE__*/React.createElement(FilterRadio, {
    value: filtro,
    onChange: setFiltro,
    options: ["Todos", "Crítico", "Alto", "Viajantes", "Televentas"]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 360,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(SearchInput, {
    value: busq,
    onChange: setBusq,
    placeholder: "\uD83D\uDD0D Buscar por nombre o n\xFAmero de vendedor..."
  })), /*#__PURE__*/React.createElement(VendedorTable, {
    rows: df,
    onOpen: onOpenVendedor
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 8
    }
  }, df.length, " vendedores \xB7 clic en una fila para ver el detalle."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1.6fr",
      gap: 28,
      marginTop: 32,
      alignItems: "start"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SectionHeader, null, "\uD83D\uDCCD Zonas con mayor rotaci\xF3n hist\xF3rica"), /*#__PURE__*/React.createElement(ZonesPanel, {
    zones: Z
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SectionHeader, null, "\u23F1\uFE0F Ventanas cr\xEDticas de permanencia"), /*#__PURE__*/React.createElement(CriticalWindowChart, {
    data: VENTANAS
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 32
    }
  }, /*#__PURE__*/React.createElement(SectionHeader, {
    note: `${onb.length} vendedores en sus primeros 6 meses`
  }, "\uD83D\uDC65 Onboarding activo \u2014 meses 1 a 6"), /*#__PURE__*/React.createElement(Card, {
    pad: false,
    style: {
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, ["Vendedor", "Tipo", "Mes en empresa", "Zona asignada", "% Plan 3m", "Riesgo"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: thStyle
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, onb.map(r => {
    const zN = zonaNivel(r.rb),
      zL = zonaLabel(r.rb);
    const warn = zN === "critico" || zN === "alto" ? " ⚠️" : "";
    return /*#__PURE__*/React.createElement("tr", {
      key: r.id,
      className: "vrow"
    }, /*#__PURE__*/React.createElement("td", {
      style: cellStyle
    }, /*#__PURE__*/React.createElement("b", null, r.nombre), " ", /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--ink-400)",
        fontSize: 11
      }
    }, "(", r.id, ")")), /*#__PURE__*/React.createElement("td", {
      style: cellStyle
    }, r.tipo), /*#__PURE__*/React.createElement("td", {
      style: cellStyle
    }, fmtAntiguedad(r.meses)), /*#__PURE__*/React.createElement("td", {
      style: cellStyle
    }, r.grupo, " ", /*#__PURE__*/React.createElement(Badge, {
      nivel: zN,
      label: zL + warn
    })), /*#__PURE__*/React.createElement("td", {
      style: cellStyle
    }, /*#__PURE__*/React.createElement("b", null, r.plan3m, "%")), /*#__PURE__*/React.createElement("td", {
      style: cellStyle
    }, /*#__PURE__*/React.createElement(Badge, {
      nivel: r.nivel
    })));
  }))))));
}
Object.assign(window, {
  InicioView,
  VendedorTable,
  thStyle,
  cellStyle
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/InicioView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/InterventionsV2.jsx
try { (() => {
/* Intervenciones — v2. Leads with effectiveness (does intervening work?),
   foregrounds which types move the score, keeps the form but tightens it. */

function ImpactCellV2({
  imp,
  estado
}) {
  if (estado === "Baja") return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontSize: 13
    }
  }, "\u2014 dio de baja");
  if (imp == null) return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontSize: 13
    }
  }, "\u2014 sin medir");
  if (imp > 0.4) return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--green-text)",
      fontWeight: 700,
      fontSize: 14
    }
  }, "\u2193 ", imp.toFixed(1), " mejor\xF3");
  if (imp < -0.4) return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--red-text)",
      fontWeight: 700,
      fontSize: 14
    }
  }, "\u2191 ", Math.abs(imp).toFixed(1), " empeor\xF3");
  return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontSize: 13
    }
  }, "= sin cambio");
}
function InterventionsV2({
  data
}) {
  const {
    V,
    INTERV,
    TIPOS_INTERV
  } = data;
  const enRiesgo = V.filter(r => ["critico", "alto"].includes(r.nivel)).sort((a, b) => b.score - a.score);
  const sups = [...new Set(V.map(r => r.supervisor))].sort();
  const [rows, setRows] = React.useState(INTERV);
  const [vid, setVid] = React.useState(enRiesgo[0].id);
  const [tipo, setTipo] = React.useState(TIPOS_INTERV[0]);
  const [sup, setSup] = React.useState(enRiesgo[0].supervisor);
  const [obs, setObs] = React.useState("");
  const [flash, setFlash] = React.useState(null);
  const [openForm, setOpenForm] = React.useState(false);
  const submit = e => {
    e.preventDefault();
    const v = V.find(r => r.id === Number(vid));
    setRows([{
      fecha: "2025-01-24",
      id: v.id,
      tipoV: v.tipo,
      grupo: v.grupo,
      tipo,
      sup,
      si: v.score,
      sa: v.score,
      nivelI: v.nivel,
      nivelA: v.nivel,
      estado: "activo",
      obs: obs || "—",
      _new: true
    }, ...rows]);
    setObs("");
    setFlash(`✓ Intervención registrada para ID ${v.id} — ${tipo}`);
    setTimeout(() => setFlash(null), 3200);
    setOpenForm(false);
  };
  const withImp = rows.map(r => ({
    ...r,
    imp: r.sa == null ? null : r.si - r.sa
  }));
  const total = rows.length;
  const medidas = withImp.filter(r => r.imp != null && r.estado !== "Baja");
  const mejoraron = medidas.filter(r => r.imp > 0.4).length;
  const tasa = medidas.length ? Math.round(mejoraron / medidas.length * 100) : 0;
  const bajas = rows.filter(r => r.estado === "Baja").length;

  // efectividad por tipo
  const porTipo = {};
  withImp.forEach(r => {
    if (r.imp == null || r.estado === "Baja") return;
    (porTipo[r.tipo] ||= []).push(r.imp);
  });
  const efTipo = Object.entries(porTipo).map(([t, arr]) => ({
    t,
    avg: arr.reduce((s, x) => s + x, 0) / arr.length,
    n: arr.length
  })).sort((a, b) => b.avg - a.avg);
  const maxAbs = Math.max(0.1, ...efTipo.map(e => Math.abs(e.avg)));
  const inputStyle = {
    width: "100%",
    padding: "9px 11px",
    borderRadius: 8,
    border: "1px solid var(--line-strong)",
    fontFamily: "var(--font-sans)",
    fontSize: 13,
    color: "var(--ink-900)",
    background: "#fff",
    outline: "none",
    boxSizing: "border-box"
  };
  const Field = ({
    label,
    children
  }) => /*#__PURE__*/React.createElement("label", {
    style: {
      display: "block",
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13,
      color: "var(--ink-700)",
      marginBottom: 5
    }
  }, label), children);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(V2Banner, {
    emoji: "\uD83D\uDCDD",
    tone: "blue",
    title: "Intervenir funciona \u2014 el score baja en la mayor\xEDa de los casos",
    sub: `${mejoraron} de ${medidas.length} intervenciones medidas mejoraron el riesgo del vendedor.`,
    cta: openForm ? "Cerrar formulario" : "➕ Registrar intervención",
    onCta: () => setOpenForm(o => !o)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement(HeroStat, {
    label: "Tasa de efectividad",
    value: `${tasa}%`,
    accent: "var(--green-accent)",
    valueColor: "var(--green-text)"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-500)"
    }
  }, mejoraron, " de ", medidas.length, " intervenciones bajaron el score \u2265 0,5")), /*#__PURE__*/React.createElement(V2Card, {
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14,
      color: "var(--ink-900)",
      marginBottom: 14
    }
  }, "\xBFQu\xE9 tipo de intervenci\xF3n mueve m\xE1s el score?"), efTipo.map(e => /*#__PURE__*/React.createElement("div", {
    key: e.t,
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12,
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 150,
      fontSize: 12,
      color: "var(--ink-600)",
      textAlign: "right",
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis"
    }
  }, e.t), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: "flex",
      alignItems: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 18,
      borderRadius: 4,
      width: `${Math.abs(e.avg) / maxAbs * 100}%`,
      minWidth: 4,
      background: e.avg > 0 ? "var(--green-accent)" : "var(--red-accent)"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: e.avg > 0 ? "var(--green-text)" : "var(--red-text)",
      whiteSpace: "nowrap"
    }
  }, e.avg > 0 ? "↓" : "↑", " ", Math.abs(e.avg).toFixed(1))))))), /*#__PURE__*/React.createElement(StatStrip, null, /*#__PURE__*/React.createElement(StatItem, {
    value: total,
    label: "Intervenciones registradas"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: mejoraron,
    label: "Con mejora de score"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: medidas.length - mejoraron,
    label: "Sin mejora a\xFAn"
  }), /*#__PURE__*/React.createElement(StatItem, {
    value: bajas,
    label: "Vendedor dio de baja"
  })), flash && /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 18,
      padding: "11px 16px",
      borderRadius: 8,
      background: "var(--green-bg)",
      color: "var(--green-text)",
      fontSize: 13,
      fontWeight: 600
    }
  }, flash), openForm && /*#__PURE__*/React.createElement(V2Card, {
    style: {
      marginBottom: 28
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 15,
      color: "var(--ink-900)",
      marginBottom: 16
    }
  }, "\u2795 Registrar nueva intervenci\xF3n"), /*#__PURE__*/React.createElement("form", {
    onSubmit: submit
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "0 20px"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Field, {
    label: "Vendedor en riesgo"
  }, /*#__PURE__*/React.createElement("select", {
    value: vid,
    onChange: e => {
      setVid(e.target.value);
      const v = V.find(r => r.id === Number(e.target.value));
      if (v) setSup(v.supervisor);
    },
    style: inputStyle
  }, enRiesgo.map(r => /*#__PURE__*/React.createElement("option", {
    key: r.id,
    value: r.id
  }, "ID ", r.id, " \u2014 ", r.grupo, " \u2014 Score ", r.score, " (", r.nivel.toUpperCase(), ")")))), /*#__PURE__*/React.createElement(Field, {
    label: "Tipo de intervenci\xF3n"
  }, /*#__PURE__*/React.createElement("select", {
    value: tipo,
    onChange: e => setTipo(e.target.value),
    style: inputStyle
  }, TIPOS_INTERV.map(t => /*#__PURE__*/React.createElement("option", {
    key: t
  }, t))))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Field, {
    label: "Supervisor que intervino"
  }, /*#__PURE__*/React.createElement("select", {
    value: sup,
    onChange: e => setSup(e.target.value),
    style: inputStyle
  }, sups.map(s => /*#__PURE__*/React.createElement("option", {
    key: s
  }, s)))), /*#__PURE__*/React.createElement(Field, {
    label: "Observaciones"
  }, /*#__PURE__*/React.createElement("textarea", {
    value: obs,
    onChange: e => setObs(e.target.value),
    placeholder: "\xBFQu\xE9 se habl\xF3? \xBFQu\xE9 se acord\xF3?",
    style: {
      ...inputStyle,
      height: 64,
      resize: "vertical"
    }
  })))), /*#__PURE__*/React.createElement("button", {
    type: "submit",
    style: {
      width: "100%",
      marginTop: 4,
      padding: "11px 0",
      borderRadius: 8,
      cursor: "pointer",
      border: "none",
      background: "var(--red-accent)",
      color: "#fff",
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14
    }
  }, "\uD83D\uDCBE Guardar intervenci\xF3n"))), /*#__PURE__*/React.createElement(V2Section, {
    title: "\uD83D\uDCCA Historial de intervenciones e impacto",
    right: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        color: "var(--ink-400)"
      }
    }, "Impacto = score inicial \u2212 actual")
  }), /*#__PURE__*/React.createElement(V2Card, {
    pad: false,
    style: {
      overflow: "hidden",
      padding: "8px 8px 0"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, ["Fecha", "Vendedor", "Tipo", "Supervisor", "Inicial", "Actual", "Impacto", "Observaciones"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: v2th
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, withImp.map((r, i) => /*#__PURE__*/React.createElement("tr", {
    key: i,
    className: "vrow",
    style: {
      background: r._new ? "var(--green-bg)" : "transparent"
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      ...v2td,
      color: "var(--ink-250)",
      fontSize: 12
    }
  }, r.fecha), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700
    }
  }, "ID ", r.id), /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--ink-250)",
      fontSize: 11
    }
  }, r.tipoV, " \xB7 ", r.grupo)), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement(Badge, {
    kind: "tipo",
    label: r.tipo
  })), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, r.sup), /*#__PURE__*/React.createElement("td", {
    style: {
      ...v2td,
      textAlign: "center"
    }
  }, /*#__PURE__*/React.createElement(ScoreCircle, {
    score: r.si,
    nivel: r.nivelI,
    size: 32
  })), /*#__PURE__*/React.createElement("td", {
    style: {
      ...v2td,
      textAlign: "center"
    }
  }, r.sa != null ? /*#__PURE__*/React.createElement(ScoreCircle, {
    score: r.sa,
    nivel: r.nivelA,
    size: 32
  }) : /*#__PURE__*/React.createElement(Badge, {
    kind: "bajo",
    label: "Baja"
  })), /*#__PURE__*/React.createElement("td", {
    style: v2td
  }, /*#__PURE__*/React.createElement(ImpactCellV2, {
    imp: r.imp,
    estado: r.estado
  })), /*#__PURE__*/React.createElement("td", {
    style: {
      ...v2td,
      color: "var(--ink-400)",
      fontSize: 12,
      maxWidth: 220
    }
  }, r.obs)))))));
}
Object.assign(window, {
  InterventionsV2
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/InterventionsV2.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/InterventionsView.jsx
try { (() => {
/* Intervenciones — register an action on an at-risk rep, see impact history. */

function Field({
  label,
  children
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "block",
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: "var(--w-bold) 13px var(--font-sans)",
      color: "var(--ink-700)",
      marginBottom: 5
    }
  }, label), children);
}
const inputStyle = {
  width: "100%",
  padding: "9px 11px",
  borderRadius: 8,
  border: "1px solid var(--line-strong)",
  font: "var(--w-regular) 13px var(--font-sans)",
  color: "var(--ink-900)",
  background: "#fff",
  outline: "none",
  boxSizing: "border-box"
};
function ImpactCell({
  imp,
  estado
}) {
  if (estado === "Baja") return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontSize: 13
    }
  }, "\u2014 Baja");
  if (imp == null) return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontSize: 13
    }
  }, "\u2014");
  if (imp > 0.4) return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--green-text)",
      fontWeight: 700,
      fontSize: 14
    }
  }, "\u2193 ", imp.toFixed(1), " mejora");
  if (imp < -0.4) return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--red-text)",
      fontWeight: 700,
      fontSize: 14
    }
  }, "\u2191 ", Math.abs(imp).toFixed(1), " empeora");
  return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontSize: 13
    }
  }, "= sin cambio");
}
function InterventionsView({
  data
}) {
  const {
    V,
    INTERV,
    TIPOS_INTERV
  } = data;
  const enRiesgo = V.filter(r => ["critico", "alto"].includes(r.nivel)).sort((a, b) => b.score - a.score);
  const sups = [...new Set(V.map(r => r.supervisor))].sort();
  const [rows, setRows] = React.useState(INTERV);
  const [vid, setVid] = React.useState(enRiesgo[0].id);
  const [tipo, setTipo] = React.useState(TIPOS_INTERV[0]);
  const [sup, setSup] = React.useState(enRiesgo[0].supervisor);
  const [obs, setObs] = React.useState("");
  const [flash, setFlash] = React.useState(null);
  const submit = e => {
    e.preventDefault();
    const v = V.find(r => r.id === Number(vid));
    setRows([{
      fecha: "2025-01-24",
      id: v.id,
      tipoV: v.tipo,
      grupo: v.grupo,
      tipo,
      sup,
      si: v.score,
      sa: v.score,
      nivelI: v.nivel,
      nivelA: v.nivel,
      estado: "activo",
      obs: obs || "—",
      _new: true
    }, ...rows]);
    setObs("");
    setFlash(`✓ Intervención registrada para ID ${v.id} — ${tipo}`);
    setTimeout(() => setFlash(null), 3200);
  };
  const withImp = rows.map(r => ({
    ...r,
    imp: r.sa == null ? null : r.si - r.sa
  }));
  const total = rows.length;
  const mejoraron = withImp.filter(r => (r.imp || 0) > 0.4).length;
  const empeoraron = withImp.filter(r => (r.imp || 0) < -0.4 && r.estado !== "Baja").length;
  const bajas = rows.filter(r => r.estado === "Baja").length;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      font: "var(--w-black) 22px var(--font-sans)",
      color: "var(--ink-900)"
    }
  }, "\uD83D\uDCDD Registro de intervenciones"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: "var(--ink-400)",
      marginTop: 4,
      marginBottom: 22
    }
  }, "Document\xE1 qu\xE9 acci\xF3n se tom\xF3 sobre cada vendedor en riesgo y med\xED el impacto real."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 14,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(KpiCard, {
    value: total,
    label: "Intervenciones registradas"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: mejoraron,
    valueColor: "var(--green-text)",
    accent: "green",
    label: "Con mejora de score",
    sub: "Score baj\xF3 \u2265 0.5 despu\xE9s"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: empeoraron,
    valueColor: "var(--red-accent)",
    accent: "red",
    label: "Sin mejora",
    sub: "Score igual o subi\xF3"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: bajas,
    valueColor: "var(--ink-400)",
    accent: "blue",
    label: "Vendedor dio de baja",
    sub: "A pesar de la intervenci\xF3n"
  })), /*#__PURE__*/React.createElement(SectionHeader, null, "\u2795 Registrar nueva intervenci\xF3n"), /*#__PURE__*/React.createElement(Card, {
    style: {
      marginBottom: 28
    }
  }, /*#__PURE__*/React.createElement("form", {
    onSubmit: submit
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "0 20px"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Field, {
    label: "Vendedor en riesgo"
  }, /*#__PURE__*/React.createElement("select", {
    value: vid,
    onChange: e => {
      setVid(e.target.value);
      const v = V.find(r => r.id === Number(e.target.value));
      if (v) setSup(v.supervisor);
    },
    style: inputStyle
  }, enRiesgo.map(r => /*#__PURE__*/React.createElement("option", {
    key: r.id,
    value: r.id
  }, "ID ", r.id, " \u2014 ", r.grupo, " \u2014 Score ", r.score, " (", r.nivel.toUpperCase(), ")")))), /*#__PURE__*/React.createElement(Field, {
    label: "Tipo de intervenci\xF3n"
  }, /*#__PURE__*/React.createElement("select", {
    value: tipo,
    onChange: e => setTipo(e.target.value),
    style: inputStyle
  }, TIPOS_INTERV.map(t => /*#__PURE__*/React.createElement("option", {
    key: t
  }, t)))), /*#__PURE__*/React.createElement(Field, {
    label: "Fecha"
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    defaultValue: "2025-01-24",
    style: inputStyle
  }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Field, {
    label: "Supervisor que intervino"
  }, /*#__PURE__*/React.createElement("select", {
    value: sup,
    onChange: e => setSup(e.target.value),
    style: inputStyle
  }, sups.map(s => /*#__PURE__*/React.createElement("option", {
    key: s
  }, s)))), /*#__PURE__*/React.createElement(Field, {
    label: "Observaciones"
  }, /*#__PURE__*/React.createElement("textarea", {
    value: obs,
    onChange: e => setObs(e.target.value),
    placeholder: "\xBFQu\xE9 se habl\xF3? \xBFQu\xE9 se acord\xF3? \xBFC\xF3mo reaccion\xF3 el vendedor?",
    style: {
      ...inputStyle,
      height: 92,
      resize: "vertical",
      fontFamily: "var(--font-sans)"
    }
  })))), /*#__PURE__*/React.createElement("button", {
    type: "submit",
    style: {
      width: "100%",
      marginTop: 4,
      padding: "11px 0",
      borderRadius: 8,
      cursor: "pointer",
      border: "none",
      background: "var(--red-accent)",
      color: "#fff",
      font: "var(--w-bold) 14px var(--font-sans)"
    }
  }, "\uD83D\uDCBE Guardar intervenci\xF3n"), flash && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 12,
      padding: "10px 14px",
      borderRadius: 8,
      background: "var(--green-bg)",
      color: "var(--green-text)",
      fontSize: 13,
      fontWeight: 600
    }
  }, flash))), /*#__PURE__*/React.createElement(SectionHeader, null, "\uD83D\uDCCA Historial de intervenciones e impacto"), /*#__PURE__*/React.createElement(Card, {
    pad: false,
    style: {
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, ["Fecha", "Vendedor", "Tipo", "Supervisor", "Score inicial", "Score actual", "Impacto", "Observaciones"].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: thStyle
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, withImp.map((r, i) => /*#__PURE__*/React.createElement("tr", {
    key: i,
    className: "vrow",
    style: {
      background: r._new ? "var(--green-bg)" : "transparent"
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      ...cellStyle,
      color: "var(--ink-250)",
      fontSize: 12
    }
  }, r.fecha), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700
    }
  }, "ID ", r.id), /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--ink-250)",
      fontSize: 11
    }
  }, r.tipoV, " \xB7 ", r.grupo)), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement(Badge, {
    kind: "tipo",
    label: r.tipo
  })), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, r.sup), /*#__PURE__*/React.createElement("td", {
    style: {
      ...cellStyle,
      textAlign: "center"
    }
  }, /*#__PURE__*/React.createElement(ScoreCircle, {
    score: r.si,
    nivel: r.nivelI,
    size: 32
  })), /*#__PURE__*/React.createElement("td", {
    style: {
      ...cellStyle,
      textAlign: "center"
    }
  }, r.sa != null ? /*#__PURE__*/React.createElement(ScoreCircle, {
    score: r.sa,
    nivel: r.nivelA,
    size: 32
  }) : /*#__PURE__*/React.createElement(Badge, {
    kind: "bajo",
    label: "Baja"
  })), /*#__PURE__*/React.createElement("td", {
    style: cellStyle
  }, /*#__PURE__*/React.createElement(ImpactCell, {
    imp: r.imp,
    estado: r.estado
  })), /*#__PURE__*/React.createElement("td", {
    style: {
      ...cellStyle,
      color: "var(--ink-400)",
      fontSize: 12,
      maxWidth: 220
    }
  }, r.obs)))))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 8
    }
  }, "Impacto = score inicial \u2212 score actual. Positivo = riesgo baj\xF3 = intervenci\xF3n efectiva."));
}
Object.assign(window, {
  InterventionsView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/InterventionsView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/PrecisionView.jsx
try { (() => {
/* Precisión del modelo (#1) — does the risk score actually predict who leaves?
   Confusion matrix over last month's cohort + recall/precision, framed in plain
   language. This is the screen that validates the whole product. */

function PrecisionView({
  data
}) {
  const P = data.PREDICCION;
  const {
    vp,
    fn,
    fp,
    vn,
    fp_intervenidos,
    periodo
  } = P;
  const totalFugas = vp + fn;
  const totalMarcados = vp + fp;
  const recall = Math.round(vp / totalFugas * 100); // % de fugas que anticipamos
  const precision = Math.round(vp / totalMarcados * 100); // % de marcados que se fueron
  const fpReales = fp - fp_intervenidos; // falsos positivos no explicados por intervención
  const total = vp + fn + fp + vn;
  const accuracy = Math.round((vp + vn) / total * 100);
  const Cell = ({
    n,
    label,
    tone,
    big
  }) => {
    const map = {
      good: ["var(--green-bg)", "var(--green-text)", "#cfe6b8"],
      bad: ["var(--red-bg)", "var(--red-text)", "#f4cfcd"],
      warn: ["var(--orange-bg)", "var(--orange-text)", "#f3d9a8"],
      neutral: ["var(--table-head-bg)", "var(--ink-600)", "var(--line-strong)"]
    }[tone];
    return /*#__PURE__*/React.createElement("div", {
      style: {
        background: map[0],
        border: `1px solid ${map[2]}`,
        borderRadius: 10,
        padding: "16px 18px"
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontFamily: "var(--font-sans)",
        fontWeight: 800,
        fontSize: big ? 34 : 30,
        color: map[1],
        lineHeight: 1
      }
    }, n), /*#__PURE__*/React.createElement("div", {
      style: {
        fontFamily: "var(--font-sans)",
        fontSize: 12.5,
        color: map[1],
        marginTop: 6,
        lineHeight: 1.4
      }
    }, label));
  };
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(V2Banner, {
    emoji: "\uD83C\uDFAF",
    tone: recall >= 75 ? "green" : "orange",
    title: `El modelo anticipó ${recall}% de las fugas del mes`,
    sub: `De ${totalFugas} vendedores que se fueron en ${periodo}, ${vp} estaban marcados en riesgo el mes anterior. Esto valida que el score sirve para actuar a tiempo.`,
    cta: "Ver detalle \u2192"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement(HeroStat, {
    label: "Sensibilidad (recall)",
    value: fmtPct(recall),
    accent: "var(--green-accent)",
    valueColor: "var(--green-text)"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-500)"
    }
  }, vp, " de ", totalFugas, " fugas fueron anticipadas por el score")), /*#__PURE__*/React.createElement(V2Card, {
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14,
      color: "var(--ink-900)",
      marginBottom: 14
    }
  }, "Precisi\xF3n de las alertas"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 24
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 30,
      color: "var(--ink-900)"
    }
  }, fmtPct(precision)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 2,
      maxWidth: 150,
      lineHeight: 1.4
    }
  }, "de los marcados realmente se fue")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 30,
      color: "var(--green-text)"
    }
  }, fp_intervenidos), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 2,
      maxWidth: 160,
      lineHeight: 1.4
    }
  }, "marcados que retuvimos tras intervenir (no son errores)")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 30,
      color: "var(--ink-900)"
    }
  }, fmtPct(accuracy)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 2,
      maxWidth: 140,
      lineHeight: 1.4
    }
  }, "precisi\xF3n global del modelo"))))), /*#__PURE__*/React.createElement(V2Section, {
    title: "\uD83D\uDCCA Predicci\xF3n vs. resultado real",
    right: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        color: "var(--ink-400)"
      }
    }, "Cohorte de ", periodo, " \xB7 ", total, " vendedores activos")
  }), /*#__PURE__*/React.createElement(V2Card, {
    style: {
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "120px 1fr 1fr",
      gap: 12,
      alignItems: "stretch"
    }
  }, /*#__PURE__*/React.createElement("div", null), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: "center",
      fontSize: 12,
      fontWeight: 700,
      color: "var(--ink-500)",
      paddingBottom: 4
    }
  }, "Se fue \u2713"), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: "center",
      fontSize: 12,
      fontWeight: 700,
      color: "var(--ink-500)",
      paddingBottom: 4
    }
  }, "Se qued\xF3"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "flex-end",
      fontSize: 12,
      fontWeight: 700,
      color: "var(--ink-500)",
      textAlign: "right",
      paddingRight: 4
    }
  }, "Marcado en riesgo \u25B2"), /*#__PURE__*/React.createElement(Cell, {
    n: vp,
    tone: "good",
    big: true,
    label: "Acertado \u2014 lo vimos venir y pudimos actuar"
  }), /*#__PURE__*/React.createElement(Cell, {
    n: fp,
    tone: "warn",
    label: `Marcado pero retenido — ${fp_intervenidos} salvados por intervención, ${fpReales} falsa alarma`
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "flex-end",
      fontSize: 12,
      fontWeight: 700,
      color: "var(--ink-500)",
      textAlign: "right",
      paddingRight: 4
    }
  }, "No marcado"), /*#__PURE__*/React.createElement(Cell, {
    n: fn,
    tone: "bad",
    big: true,
    label: "Fuga sorpresa \u2014 el modelo NO la anticip\xF3. Ac\xE1 hay que mejorar."
  }), /*#__PURE__*/React.createElement(Cell, {
    n: vn,
    tone: "neutral",
    label: "Correcto \u2014 sin alerta y se qued\xF3"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginBottom: 32,
      lineHeight: 1.5
    }
  }, "Le\xE9 las filas como \u201Cqu\xE9 dijo el modelo\u201D y las columnas como \u201Cqu\xE9 pas\xF3 de verdad\u201D. La celda roja (fugas no anticipadas) es la que quer\xE9s llevar a cero \u2014 son las ", fn, " personas que se fueron sin que saltara la alerta."), /*#__PURE__*/React.createElement(V2Section, {
    title: "\uD83D\uDD0D \xBFD\xF3nde fall\xF3 el modelo?"
  }), /*#__PURE__*/React.createElement(V2Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 28,
      flexWrap: "wrap"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 240
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13,
      color: "var(--red-text)",
      marginBottom: 6
    }
  }, "\u25B2 ", fn, " fugas sorpresa"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: "var(--ink-600)",
      lineHeight: 1.6
    }
  }, "Vendedores que se fueron sin alerta previa. Patr\xF3n com\xFAn: renuncias r\xE1pidas en el mes 1-2, antes de que el score acumule se\xF1ales. ", /*#__PURE__*/React.createElement("b", null, "Sugerencia:"), " dar m\xE1s peso a la inactividad temprana.")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 240
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13,
      color: "var(--green-text)",
      marginBottom: 6
    }
  }, "\u2713 ", fp_intervenidos, " retenciones"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: "var(--ink-600)",
      lineHeight: 1.6
    }
  }, "Marcados como riesgo que ", /*#__PURE__*/React.createElement("b", null, "no"), " se fueron \u2014 y la mayor\xEDa tuvo una intervenci\xF3n. No son errores del modelo: son los casos donde actuar funcion\xF3. El sistema se paga solo ac\xE1.")))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 10
    }
  }, "Datos simulados de validaci\xF3n. En producci\xF3n se calcula comparando el snapshot de score del mes anterior con las bajas efectivas del mes."));
}
Object.assign(window, {
  PrecisionView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/PrecisionView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/SupervisorV2.jsx
try { (() => {
/* Por supervisor — v2. Ranked by urgency, action-oriented cards, hero on the
   most at-risk zone, cleaner detail. Reuses primitives + v2common. */

function SupCardV2({
  row,
  onOpen,
  rank
}) {
  const nivel = zonaNivel(row.rb);
  const cc = {
    critico: "var(--red-accent)",
    alto: "var(--orange-accent)",
    medio: "var(--blue-accent)",
    bajo: "var(--green-accent)"
  }[nivel];
  const c = row.criticos,
    a = row.altos;
  const necesita = c + a;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderRadius: 14,
      padding: "18px 20px",
      boxShadow: "var(--shadow-card)",
      borderTop: `4px solid ${cc}`,
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 16,
      color: "var(--ink-900)",
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis"
    }
  }, row.supervisor), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 2
    }
  }, row.grupo, " \xB7 ", row.activos, " activos")), /*#__PURE__*/React.createElement("div", {
    style: {
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    nivel: nivel,
    label: zonaLabel(row.rb)
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: 8,
      marginTop: 16
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 34,
      lineHeight: 1,
      color: necesita ? "var(--red-accent)" : "var(--green-text)"
    }
  }, necesita), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      color: "var(--ink-500)"
    }
  }, "requieren atenci\xF3n")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 6
    }
  }, c ? /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("b", {
    style: {
      color: "var(--red-text)"
    }
  }, c, " cr\xEDtico", c > 1 ? "s" : "")) : null, c && a ? " · " : null, a ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--orange-text)"
    }
  }, a, " alto", a > 1 ? "s" : "") : null, !necesita ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--green-text)"
    }
  }, "Sin alertas activas") : null, /*#__PURE__*/React.createElement("span", null, " \xB7 perm. ", row.permEgreso.toFixed(1).replace(".", ","), "m")), /*#__PURE__*/React.createElement("button", {
    onClick: () => onOpen(row.supervisor),
    style: {
      marginTop: 16,
      width: "100%",
      padding: "9px 0",
      borderRadius: 8,
      cursor: "pointer",
      border: "none",
      background: necesita ? "var(--ink-900)" : "#fff",
      color: necesita ? "#fff" : "var(--ink-600)",
      boxShadow: necesita ? "none" : "inset 0 0 0 1px var(--line-strong)",
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13
    }
  }, "Ver mis vendedores \u2192"));
}
function SupervisorV2({
  data,
  onOpenVendedor
}) {
  const {
    V,
    Z
  } = data;
  const [sel, setSel] = React.useState(null);
  const resumen = Z.map(z => {
    const reps = V.filter(r => r.supervisor === z.supervisor);
    return {
      supervisor: z.supervisor,
      grupo: z.grupo,
      rb: z.rb,
      permEgreso: z.permEgreso,
      activos: reps.length,
      criticos: reps.filter(r => r.nivel === "critico").length,
      altos: reps.filter(r => r.nivel === "alto").length
    };
  }).sort((a, b) => b.criticos * 10 + b.altos - (a.criticos * 10 + a.altos));
  if (!sel) {
    const totalAccion = resumen.reduce((s, r) => s + r.criticos + r.altos, 0);
    const peor = resumen[0];
    return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(V2Banner, {
      emoji: "\uD83D\uDC64",
      tone: "orange",
      title: `${peor.grupo} (${peor.supervisor}) es la zona que más atención necesita`,
      sub: `${totalAccion} vendedores en riesgo elevado repartidos entre 4 supervisores.`,
      cta: "Ver zona cr\xEDtica \u2192"
    }), /*#__PURE__*/React.createElement(StatStrip, null, /*#__PURE__*/React.createElement(StatItem, {
      value: resumen.length,
      label: "Supervisores activos"
    }), /*#__PURE__*/React.createElement(StatItem, {
      value: V.length,
      label: "Vendedores totales"
    }), /*#__PURE__*/React.createElement(StatItem, {
      value: totalAccion,
      label: "En riesgo elevado"
    }), /*#__PURE__*/React.createElement(StatItem, {
      value: "3,5",
      label: "Vendedores / supervisor"
    })), /*#__PURE__*/React.createElement(V2Section, {
      title: "\uD83D\uDCCB Supervisores por urgencia",
      right: /*#__PURE__*/React.createElement("span", {
        style: {
          fontSize: 12,
          color: "var(--ink-400)"
        }
      }, "Ordenados por vendedores en riesgo")
    }), /*#__PURE__*/React.createElement("div", {
      style: {
        display: "grid",
        gridTemplateColumns: "repeat(3, 1fr)",
        gap: 16
      }
    }, resumen.map((row, i) => /*#__PURE__*/React.createElement(SupCardV2, {
      key: row.supervisor,
      row: row,
      onOpen: setSel,
      rank: i
    }))));
  }
  const reps = V.filter(r => r.supervisor === sel).sort((a, b) => b.score - a.score);
  const z = Z.find(x => x.supervisor === sel);
  const nivelZona = zonaNivel(z.rb);
  const nCrit = reps.filter(r => r.nivel === "critico").length;
  const nAlto = reps.filter(r => r.nivel === "alto").length;
  const accion = reps.filter(r => ["critico", "alto"].includes(r.nivel));
  const nOnb = reps.filter(r => r.meses <= 6).length;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("button", {
    onClick: () => setSel(null),
    style: {
      marginBottom: 16,
      padding: "6px 14px",
      borderRadius: 8,
      cursor: "pointer",
      border: "1px solid var(--line-strong)",
      background: "#fff",
      fontFamily: "var(--font-sans)",
      fontWeight: 600,
      fontSize: 13,
      color: "var(--ink-600)"
    }
  }, "\u2190 Todas las zonas"), z.rb > 0.45 && /*#__PURE__*/React.createElement(V2Banner, {
    emoji: "\u26A0\uFE0F",
    tone: z.rb > 0.60 ? "red" : "orange",
    title: `${z.grupo} es una zona de alta rotación histórica`,
    sub: "Los vendedores nuevos aqu\xED tienen mayor probabilidad de irse antes de los 6 meses. Prioriz\xE1 el onboarding."
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement(HeroStat, {
    label: `${sel} — requieren acción`,
    value: nCrit + nAlto,
    unit: `de ${reps.length}`,
    accent: "var(--red-accent)",
    valueColor: "var(--red-accent)"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      textAlign: "center",
      padding: "8px 0",
      borderRadius: 8,
      background: "var(--red-bg)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontWeight: 800,
      fontSize: 20,
      color: "var(--red-text)"
    }
  }, nCrit), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "var(--red-text)",
      fontWeight: 600
    }
  }, "Cr\xEDtico")), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      textAlign: "center",
      padding: "8px 0",
      borderRadius: 8,
      background: "var(--orange-bg)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontWeight: 800,
      fontSize: 20,
      color: "var(--orange-text)"
    }
  }, nAlto), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "var(--orange-text)",
      fontWeight: 600
    }
  }, "Alto")))), /*#__PURE__*/React.createElement(V2Card, {
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      gap: 18
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 28
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      textTransform: "uppercase",
      letterSpacing: ".04em"
    }
  }, "Zona"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 6
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    nivel: nivelZona,
    label: `${z.grupo} · ${zonaLabel(z.rb)}`
  }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      textTransform: "uppercase",
      letterSpacing: ".04em"
    }
  }, "Permanencia prom."), /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 24,
      marginTop: 4
    }
  }, z.permEgreso.toFixed(1).replace(".", ","), "m")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      textTransform: "uppercase",
      letterSpacing: ".04em"
    }
  }, "En onboarding"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 800,
      fontSize: 24,
      marginTop: 4,
      color: "var(--blue-accent)"
    }
  }, nOnb))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      lineHeight: 1.5
    }
  }, "Empez\xE1 por los ", accion.length, " vendedores marcados abajo \u2014 los cr\xEDticos necesitan una reuni\xF3n esta semana."))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 20
    }
  }), /*#__PURE__*/React.createElement(V2Section, {
    title: "\uD83D\uDCCB Mis vendedores por prioridad"
  }), reps.length === 0 ? /*#__PURE__*/React.createElement(V2Empty, {
    title: "Sin vendedores asignados",
    sub: "Esta zona no tiene vendedores activos."
  }) : /*#__PURE__*/React.createElement(V2VendedorTable, {
    rows: reps,
    onOpen: onOpenVendedor
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 10
    }
  }, reps.length, " vendedores en ", z.grupo));
}

// reusable v2 table with acción column (shared by Supervisor + Inicio v2)
function V2VendedorTable({
  rows,
  onOpen
}) {
  const density = useDensity();
  const td = tdFor(density);
  return /*#__PURE__*/React.createElement(V2Card, {
    pad: false,
    style: {
      overflow: "hidden",
      padding: "8px 8px 0"
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Vendedor"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Se\xF1ales"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "% Plan 3m"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Tendencia"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Score \xB7 \u0394 mes"), /*#__PURE__*/React.createElement("th", {
    style: v2th
  }, "Acci\xF3n sugerida"))), /*#__PURE__*/React.createElement("tbody", null, rows.map(r => /*#__PURE__*/React.createElement("tr", {
    key: r.id,
    className: "vrow",
    onClick: () => onOpen && onOpen(r),
    style: {
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: td
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      color: "var(--ink-900)",
      fontSize: 13
    }
  }, r.nombre, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-400)",
      fontWeight: 400,
      fontSize: 11
    }
  }, "(", r.id, ")")), /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--ink-250)",
      fontSize: 11,
      marginTop: 2
    }
  }, r.tipo, " \xB7 ", fmtAntiguedad(r.meses), " \xB7 ", r.grupo)), /*#__PURE__*/React.createElement("td", {
    style: td
  }, /*#__PURE__*/React.createElement(Pills, {
    senales: r.senales
  })), /*#__PURE__*/React.createElement("td", {
    style: td
  }, /*#__PURE__*/React.createElement("b", null, r.plan3m, "%")), /*#__PURE__*/React.createElement("td", {
    style: td
  }, /*#__PURE__*/React.createElement(Sparkline, {
    vals: r.spark
  })), /*#__PURE__*/React.createElement("td", {
    style: td
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(ScoreCircle, {
    score: r.score,
    nivel: r.nivel
  }), /*#__PURE__*/React.createElement(ScoreDelta, {
    delta: r._delta
  }))), /*#__PURE__*/React.createElement("td", {
    style: td
  }, /*#__PURE__*/React.createElement(AccionTag, {
    nivel: r.nivel
  })))))));
}
Object.assign(window, {
  SupervisorV2,
  V2VendedorTable
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/SupervisorV2.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/SupervisorView.jsx
try { (() => {
/* Por supervisor — landing grid of supervisor cards → drill into "my reps". */

function SupCard({
  row,
  onOpen
}) {
  const nivel = zonaNivel(row.rb);
  const cc = {
    critico: "var(--red-accent)",
    alto: "var(--orange-accent)",
    medio: "var(--blue-accent)",
    bajo: "var(--green-accent)"
  }[nivel];
  const c = row.criticos,
    a = row.altos;
  let alerta;
  if (c > 0) alerta = /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--red-accent)",
      fontWeight: 700
    }
  }, c, " cr\xEDtico", c > 1 ? "s" : ""), a ? /*#__PURE__*/React.createElement("span", null, " \xB7 ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--orange-text)"
    }
  }, a, " alto", a > 1 ? "s" : "")) : null);else if (a) alerta = /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--orange-text)"
    }
  }, a, " alto", a > 1 ? "s" : "");else alerta = /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--green-text)"
    }
  }, "Sin alertas activas");
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderRadius: "var(--radius-card)",
      padding: "18px 20px",
      boxShadow: "var(--shadow-card)",
      borderLeft: `4px solid ${cc}`
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      font: "var(--w-black) 15px var(--font-sans)",
      color: "var(--ink-900)"
    }
  }, row.supervisor), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 2
    }
  }, row.grupo), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 20,
      marginTop: 12
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 20,
      fontWeight: 800
    }
  }, row.activos), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-250)"
    }
  }, "activos")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 20,
      fontWeight: 800
    }
  }, row.permEgreso.toFixed(1).replace(".", ","), "m"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-250)"
    }
  }, "perm. prom.")), /*#__PURE__*/React.createElement("div", {
    style: {
      marginLeft: "auto",
      alignSelf: "center"
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    nivel: nivel
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      marginTop: 10
    }
  }, alerta), /*#__PURE__*/React.createElement("button", {
    onClick: () => onOpen(row.supervisor),
    style: {
      marginTop: 14,
      width: "100%",
      padding: "8px 0",
      borderRadius: 8,
      cursor: "pointer",
      border: "1px solid var(--line-strong)",
      background: "#fff",
      font: "var(--w-semibold) 13px var(--font-sans)",
      color: "var(--ink-700)"
    }
  }, "Ver mis vendedores \u2192"));
}
function SupervisorView({
  data,
  onOpenVendedor
}) {
  const {
    V,
    Z
  } = data;
  const [sel, setSel] = React.useState(null);
  const resumen = Z.map(z => {
    const reps = V.filter(r => r.supervisor === z.supervisor);
    return {
      supervisor: z.supervisor,
      grupo: z.grupo,
      rb: z.rb,
      permEgreso: z.permEgreso,
      activos: reps.length,
      criticos: reps.filter(r => r.nivel === "critico").length,
      altos: reps.filter(r => r.nivel === "alto").length,
      scoreMax: Math.max(0, ...reps.map(r => r.score))
    };
  }).sort((a, b) => b.scoreMax - a.scoreMax);
  if (!sel) {
    return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        font: "var(--w-black) 22px var(--font-sans)",
        color: "var(--ink-900)",
        marginBottom: 4
      }
    }, "\uD83D\uDC64 Por supervisor"), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 14,
        color: "var(--ink-400)",
        marginBottom: 22
      }
    }, "Cada supervisor ve solo sus vendedores. Clic en una tarjeta para entrar."), /*#__PURE__*/React.createElement("div", {
      style: {
        display: "grid",
        gridTemplateColumns: "repeat(3, 1fr)",
        gap: 14
      }
    }, resumen.map(row => /*#__PURE__*/React.createElement(SupCard, {
      key: row.supervisor,
      row: row,
      onOpen: setSel
    }))));
  }

  // detail
  const reps = V.filter(r => r.supervisor === sel).sort((a, b) => b.score - a.score);
  const z = Z.find(x => x.supervisor === sel);
  const nivelZona = zonaNivel(z.rb);
  const nCrit = reps.filter(r => r.nivel === "critico").length;
  const nAlto = reps.filter(r => r.nivel === "alto").length;
  const nOnb = reps.filter(r => r.meses <= 3).length;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("button", {
    onClick: () => setSel(null),
    style: {
      marginBottom: 16,
      padding: "6px 14px",
      borderRadius: 8,
      cursor: "pointer",
      border: "1px solid var(--line-strong)",
      background: "#fff",
      font: "var(--w-semibold) 13px var(--font-sans)",
      color: "var(--ink-600)"
    }
  }, "\u2190 Todas las zonas"), /*#__PURE__*/React.createElement("div", {
    style: {
      font: "var(--w-black) 22px var(--font-sans)",
      color: "var(--ink-900)"
    }
  }, "\uD83D\uDC64 ", sel), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: "var(--ink-400)",
      marginTop: 4,
      marginBottom: 18
    }
  }, "Zona: ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: "var(--ink-900)"
    }
  }, z.grupo), " \xA0\xB7\xA0 ", /*#__PURE__*/React.createElement(Badge, {
    nivel: nivelZona,
    label: zonaLabel(z.rb)
  })), z.rb > 0.60 && /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--orange-bg)",
      border: "1px solid #f3d9a8",
      borderRadius: 8,
      padding: "12px 16px",
      marginBottom: 20,
      fontSize: 13,
      color: "#7a4a00"
    }
  }, "\u26A0\uFE0F ", /*#__PURE__*/React.createElement("b", null, z.grupo), " es una zona con alta rotaci\xF3n hist\xF3rica. Los vendedores nuevos aqu\xED tienen mayor probabilidad de irse antes de los 6 meses."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 14,
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement(KpiCard, {
    value: reps.length,
    label: "Vendedores activos",
    sub: "En tu zona"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: nCrit + nAlto,
    valueColor: "var(--red-accent)",
    accent: "red",
    label: "Requieren atenci\xF3n",
    sub: `${nCrit} crítico${nCrit !== 1 ? "s" : ""} · ${nAlto} alto${nAlto !== 1 ? "s" : ""}`
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: `${z.permEgreso.toFixed(1).replace(".", ",")}m`,
    accent: "orange",
    label: "Permanencia prom. zona",
    sub: "Duraci\xF3n al egreso"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    value: nOnb,
    valueColor: "var(--blue-accent)",
    accent: "blue",
    label: "En onboarding",
    sub: "Primeros 3 meses"
  })), /*#__PURE__*/React.createElement(SectionHeader, null, "\uD83D\uDCCB Mis vendedores por score de riesgo"), /*#__PURE__*/React.createElement(VendedorTable, {
    rows: reps,
    onOpen: onOpenVendedor
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 8
    }
  }, reps.length, " vendedores en ", z.grupo));
}
Object.assign(window, {
  SupervisorView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/SupervisorView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/data.js
try { (() => {
/* Mock data for the Würth Rotación dashboard UI kit.
   Shapes mirror src/score_engine.py output (scores_df) + grupos + sparklines.
   Numbers are invented; nothing here is real Würth data. */
(function () {
  // sparkline = last 3 months % Plan (oldest → newest)
  const V = [{
    id: 1119,
    nombre: "Pérez, Martín",
    tipo: "Viajante",
    grupo: "Centro",
    supervisor: "Rodríguez, A.",
    meses: 3,
    score: 9,
    nivel: "critico",
    plan3m: 62,
    spark: [74, 66, 62],
    rb: 0.68,
    senales: [["caída 3m", "red"], ["onboarding", "red"], ["plan<80%", "orange"], ["zona quemada", "orange"]]
  }, {
    id: 6453,
    nombre: "Gómez, Laura",
    tipo: "Televentas",
    grupo: "Norte",
    supervisor: "Díaz, M.",
    meses: 2,
    score: 8,
    nivel: "critico",
    plan3m: 58,
    spark: [70, 61, 58],
    rb: 0.41,
    senales: [["onboarding", "red"], ["días cero↑", "red"], ["plan<80%", "orange"]]
  }, {
    id: 5855,
    nombre: "Sosa, Diego",
    tipo: "Viajante",
    grupo: "Centro",
    supervisor: "Rodríguez, A.",
    meses: 5,
    score: 8,
    nivel: "critico",
    plan3m: 64,
    spark: [80, 72, 64],
    rb: 0.68,
    senales: [["caída 3m", "red"], ["mes 4-6", "orange"], ["zona quemada", "orange"], ["inactivos↑", "orange"]]
  }, {
    id: 2207,
    nombre: "Ibáñez, Carla",
    tipo: "Televentas",
    grupo: "Oeste",
    supervisor: "Vega, P.",
    meses: 14,
    score: 7,
    nivel: "alto",
    plan3m: 71,
    spark: [78, 74, 71],
    rb: 0.52,
    senales: [["plan<80%", "orange"], ["cobranza baja", "orange"], ["clientes L:0", "yellow"]]
  }, {
    id: 4419,
    nombre: "López, Hernán",
    tipo: "Viajante",
    grupo: "Sur",
    supervisor: "Fernández, J.",
    meses: 4,
    score: 7,
    nivel: "alto",
    plan3m: 73,
    spark: [69, 71, 73],
    rb: 0.28,
    senales: [["mes 4-6", "orange"], ["clientes L:0", "yellow"]]
  }, {
    id: 7781,
    nombre: "Méndez, Sofía",
    tipo: "Televentas",
    grupo: "Norte",
    supervisor: "Díaz, M.",
    meses: 9,
    score: 6,
    nivel: "alto",
    plan3m: 77,
    spark: [72, 75, 77],
    rb: 0.41,
    senales: [["plan<80%", "orange"], ["ticket↓", "yellow"]]
  }, {
    id: 3392,
    nombre: "Castro, Julián",
    tipo: "Viajante",
    grupo: "Centro",
    supervisor: "Rodríguez, A.",
    meses: 22,
    score: 5,
    nivel: "medio",
    plan3m: 84,
    spark: [82, 83, 84],
    rb: 0.68,
    senales: [["zona quemada", "orange"]]
  }, {
    id: 1280,
    nombre: "Romero, Valeria",
    tipo: "Televentas",
    grupo: "Oeste",
    supervisor: "Vega, P.",
    meses: 7,
    score: 5,
    nivel: "medio",
    plan3m: 86,
    spark: [80, 84, 86],
    rb: 0.52,
    senales: [["cobranza baja", "orange"]]
  }, {
    id: 9014,
    nombre: "Acosta, Pablo",
    tipo: "Viajante",
    grupo: "Sur",
    supervisor: "Fernández, J.",
    meses: 31,
    score: 4,
    nivel: "medio",
    plan3m: 89,
    spark: [85, 87, 89],
    rb: 0.28,
    senales: [["clientes L:0", "yellow"]]
  }, {
    id: 6627,
    nombre: "Núñez, Florencia",
    tipo: "Televentas",
    grupo: "Norte",
    supervisor: "Díaz, M.",
    meses: 18,
    score: 3,
    nivel: "bajo",
    plan3m: 94,
    spark: [91, 93, 94],
    rb: 0.41,
    senales: []
  }, {
    id: 3105,
    nombre: "Vera, Maximiliano",
    tipo: "Viajante",
    grupo: "Sur",
    supervisor: "Fernández, J.",
    meses: 41,
    score: 2,
    nivel: "bajo",
    plan3m: 98,
    spark: [96, 97, 98],
    rb: 0.28,
    senales: []
  }, {
    id: 8890,
    nombre: "Ríos, Camila",
    tipo: "Televentas",
    grupo: "Oeste",
    supervisor: "Vega, P.",
    meses: 26,
    score: 2,
    nivel: "bajo",
    plan3m: 101,
    spark: [99, 100, 101],
    rb: 0.52,
    senales: []
  }, {
    id: 1407,
    nombre: "Torres, Nicolás",
    tipo: "Viajante",
    grupo: "Centro",
    supervisor: "Rodríguez, A.",
    meses: 1,
    score: 9,
    nivel: "critico",
    plan3m: 55,
    spark: [0, 60, 55],
    rb: 0.68,
    senales: [["onboarding", "red"], ["días cero↑", "red"], ["zona quemada", "orange"]]
  }, {
    id: 5520,
    nombre: "Silva, Agustina",
    tipo: "Televentas",
    grupo: "Norte",
    supervisor: "Díaz, M.",
    meses: 6,
    score: 6,
    nivel: "alto",
    plan3m: 76,
    spark: [82, 79, 76],
    rb: 0.41,
    senales: [["caída 3m", "red"], ["mes 4-6", "orange"]]
  }];

  // grupos / zones — riesgo_base drives zona level
  const Z = [{
    grupo: "Centro",
    supervisor: "Rodríguez, A.",
    historicos: 38,
    permEgreso: 4.1,
    planProm: 64,
    rb: 0.68,
    activos: 4
  }, {
    grupo: "Oeste",
    supervisor: "Vega, P.",
    historicos: 24,
    permEgreso: 5.8,
    planProm: 79,
    rb: 0.52,
    activos: 3
  }, {
    grupo: "Norte",
    supervisor: "Díaz, M.",
    historicos: 21,
    permEgreso: 6.8,
    planProm: 81,
    rb: 0.41,
    activos: 4
  }, {
    grupo: "Sur",
    supervisor: "Fernández, J.",
    historicos: 14,
    permEgreso: 12.4,
    planProm: 96,
    rb: 0.28,
    activos: 3
  }];

  // critical-window histogram: month of career → resignations
  const VENTANAS = [{
    m: 1,
    n: 9
  }, {
    m: 2,
    n: 14
  }, {
    m: 3,
    n: 17
  }, {
    m: 4,
    n: 11
  }, {
    m: 5,
    n: 8
  }, {
    m: 6,
    n: 7
  }, {
    m: 7,
    n: 4
  }, {
    m: 8,
    n: 3
  }, {
    m: 9,
    n: 3
  }, {
    m: 10,
    n: 2
  }, {
    m: 11,
    n: 2
  }, {
    m: 12,
    n: 3
  }, {
    m: 14,
    n: 1
  }, {
    m: 16,
    n: 1
  }];

  // intervention history
  const INTERV = [{
    fecha: "2025-01-22",
    id: 1119,
    tipoV: "Viajante",
    grupo: "Centro",
    tipo: "Reunión 1:1",
    sup: "Rodríguez, A.",
    si: 9,
    sa: 7,
    nivelI: "critico",
    nivelA: "alto",
    estado: "activo",
    obs: "Acordó plan de visitas semanal. Se lo notó receptivo."
  }, {
    fecha: "2025-01-20",
    id: 6453,
    tipoV: "Televentas",
    grupo: "Norte",
    tipo: "Acompañamiento",
    sup: "Díaz, M.",
    si: 8,
    sa: 8,
    nivelI: "critico",
    nivelA: "critico",
    estado: "activo",
    obs: "Sin cambios todavía. Reprogramar seguimiento."
  }, {
    fecha: "2025-01-15",
    id: 2207,
    tipoV: "Televentas",
    grupo: "Oeste",
    tipo: "Capacitación",
    sup: "Vega, P.",
    si: 7,
    sa: 5,
    nivelI: "alto",
    nivelA: "medio",
    estado: "activo",
    obs: "Capacitación en gestión de cartera. Mejoró cobranza."
  }, {
    fecha: "2025-01-10",
    id: 5855,
    tipoV: "Viajante",
    grupo: "Centro",
    tipo: "Ajuste de cartera",
    sup: "Rodríguez, A.",
    si: 8,
    sa: null,
    nivelI: "critico",
    nivelA: null,
    estado: "Baja",
    obs: "Renunció antes del seguimiento. Zona crítica."
  }];
  const TIPOS_INTERV = ["Reunión 1:1", "Acompañamiento", "Capacitación", "Ajuste de cartera", "Reasignación de zona"];

  // ── Historial: cohortes por año de ingreso (mediana de permanencia de los que se fueron) ──
  const COHORTES = [{
    anio: 2016,
    mediana: 17,
    bajas: 22
  }, {
    anio: 2017,
    mediana: 15,
    bajas: 26
  }, {
    anio: 2018,
    mediana: 14,
    bajas: 31
  }, {
    anio: 2019,
    mediana: 12,
    bajas: 35
  }, {
    anio: 2020,
    mediana: 9,
    bajas: 28
  }, {
    anio: 2021,
    mediana: 8,
    bajas: 41
  }, {
    anio: 2022,
    mediana: 7,
    bajas: 44
  }, {
    anio: 2023,
    mediana: 6,
    bajas: 52
  }, {
    anio: 2024,
    mediana: 5,
    bajas: 58
  }, {
    anio: 2025,
    mediana: 5,
    bajas: 49
  }];
  // bajas reales por año de egreso + tasa de rotación
  const ROTACION = [{
    anio: 2019,
    bajas: 30,
    tasa: 38
  }, {
    anio: 2020,
    bajas: 34,
    tasa: 44
  }, {
    anio: 2021,
    bajas: 47,
    tasa: 55
  }, {
    anio: 2022,
    bajas: 51,
    tasa: 58
  }, {
    anio: 2023,
    bajas: 56,
    tasa: 61
  }, {
    anio: 2024,
    bajas: 62,
    tasa: 64
  }, {
    anio: 2025,
    bajas: 59,
    tasa: 63
  }];
  // zonas históricas: % que se fue en <6 meses
  const ZONAS_HIST = [{
    grupo: "Centro",
    supervisor: "Rodríguez, A.",
    activos: 4,
    total: 38,
    bajasRapidas: 23,
    pctRapida: 61,
    permMediana: 4
  }, {
    grupo: "Televentas Auto",
    supervisor: "Vega, P.",
    activos: 3,
    total: 24,
    bajasRapidas: 13,
    pctRapida: 54,
    permMediana: 5
  }, {
    grupo: "Norte",
    supervisor: "Díaz, M.",
    activos: 4,
    total: 21,
    bajasRapidas: 9,
    pctRapida: 43,
    permMediana: 7
  }, {
    grupo: "Televentas Metal",
    supervisor: "Vega, P.",
    activos: 2,
    total: 18,
    bajasRapidas: 7,
    pctRapida: 39,
    permMediana: 6
  }, {
    grupo: "Oeste",
    supervisor: "Vega, P.",
    activos: 3,
    total: 16,
    bajasRapidas: 5,
    pctRapida: 31,
    permMediana: 9
  }, {
    grupo: "Sur",
    supervisor: "Fernández, J.",
    activos: 3,
    total: 14,
    bajasRapidas: 3,
    pctRapida: 21,
    permMediana: 12
  }];

  // ── Actividad: cumplimiento de plan, por período ──
  const PERIODOS = ["2025-01", "2024-12", "2024-11"];
  // resumen por tipo (período actual 2025-01)
  const ACTIVIDAD = {
    "2025-01": {
      televentas: {
        vendedores: 6,
        targetDia: 80,
        planDia: 72,
        ejecPlanDia: 41,
        espontaneasDia: 9,
        totalDia: 50,
        cumpl: 69
      },
      viajantes: {
        vendedores: 8,
        targetDia: 15,
        planDia: 13,
        ejecPlanDia: 7,
        espontaneasDia: 2,
        totalDia: 9,
        cumpl: 69
      }
    },
    "2024-12": {
      televentas: {
        vendedores: 6,
        targetDia: 80,
        planDia: 70,
        ejecPlanDia: 38,
        espontaneasDia: 8,
        totalDia: 46,
        cumpl: 66
      },
      viajantes: {
        vendedores: 8,
        targetDia: 15,
        planDia: 13,
        ejecPlanDia: 6,
        espontaneasDia: 2,
        totalDia: 8,
        cumpl: 62
      }
    },
    "2024-11": {
      televentas: {
        vendedores: 5,
        targetDia: 80,
        planDia: 68,
        ejecPlanDia: 35,
        espontaneasDia: 7,
        totalDia: 42,
        cumpl: 62
      },
      viajantes: {
        vendedores: 7,
        targetDia: 15,
        planDia: 12,
        ejecPlanDia: 6,
        espontaneasDia: 1,
        totalDia: 7,
        cumpl: 58
      }
    }
  };
  // tendencia mensual (cumplimiento %)
  const ACT_TREND = {
    televentas: [{
      p: "2024-11",
      c: 62
    }, {
      p: "2024-12",
      c: 66
    }, {
      p: "2025-01",
      c: 69
    }],
    viajantes: [{
      p: "2024-11",
      c: 58
    }, {
      p: "2024-12",
      c: 62
    }, {
      p: "2025-01",
      c: 69
    }]
  };
  // ranking por vendedor (período actual)
  const ACT_RANKING = {
    televentas: [{
      nombre: "Gómez, Laura",
      id: 6453,
      grupo: "Televentas Auto",
      plan: 80,
      delPlan: 14,
      esp: 4,
      total: 18,
      cumpl: 23
    }, {
      nombre: "Méndez, Sofía",
      id: 7781,
      grupo: "Televentas Metal",
      plan: 72,
      delPlan: 28,
      esp: 6,
      total: 34,
      cumpl: 47
    }, {
      nombre: "Romero, Valeria",
      id: 1280,
      grupo: "Televentas Auto",
      plan: 70,
      delPlan: 36,
      esp: 8,
      total: 44,
      cumpl: 63
    }, {
      nombre: "Silva, Agustina",
      id: 5520,
      grupo: "Televentas Metal",
      plan: 74,
      delPlan: 42,
      esp: 9,
      total: 51,
      cumpl: 69
    }, {
      nombre: "Ríos, Camila",
      id: 8890,
      grupo: "Televentas Auto",
      plan: 68,
      delPlan: 51,
      esp: 11,
      total: 62,
      cumpl: 91
    }, {
      nombre: "Núñez, Florencia",
      id: 6627,
      grupo: "Televentas Metal",
      plan: 70,
      delPlan: 55,
      esp: 12,
      total: 67,
      cumpl: 96
    }],
    viajantes: [{
      nombre: "Torres, Nicolás",
      id: 1407,
      grupo: "Centro",
      plan: 15,
      delPlan: 2,
      esp: 1,
      total: 3,
      cumpl: 20
    }, {
      nombre: "Pérez, Martín",
      id: 1119,
      grupo: "Centro",
      plan: 14,
      delPlan: 5,
      esp: 1,
      total: 6,
      cumpl: 43
    }, {
      nombre: "Sosa, Diego",
      id: 5855,
      grupo: "Centro",
      plan: 13,
      delPlan: 7,
      esp: 2,
      total: 9,
      cumpl: 69
    }, {
      nombre: "López, Hernán",
      id: 4419,
      grupo: "Sur",
      plan: 13,
      delPlan: 8,
      esp: 2,
      total: 10,
      cumpl: 77
    }, {
      nombre: "Castro, Julián",
      id: 3392,
      grupo: "Centro",
      plan: 12,
      delPlan: 9,
      esp: 2,
      total: 11,
      cumpl: 92
    }, {
      nombre: "Acosta, Pablo",
      id: 9014,
      grupo: "Sur",
      plan: 12,
      delPlan: 10,
      esp: 2,
      total: 12,
      cumpl: 100
    }, {
      nombre: "Vera, Maximiliano",
      id: 3105,
      grupo: "Sur",
      plan: 11,
      delPlan: 10,
      esp: 3,
      total: 13,
      cumpl: 118
    }]
  };
  window.DASH_DATA = {
    V,
    Z,
    VENTANAS,
    INTERV,
    TIPOS_INTERV,
    COHORTES,
    ROTACION,
    ZONAS_HIST,
    PERIODOS,
    ACTIVIDAD,
    ACT_TREND,
    ACT_RANKING
  };
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/data.js", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/ios-frame.jsx
try { (() => {
// @ds-adherence-ignore -- omelette starter scaffold (raw elements/hex/px by design)

/* BEGIN USAGE */
// iOS.jsx — Simplified iOS 26 (Liquid Glass) device frame
// Based on the iOS 26 UI Kit + Figma status bar spec. No assets, no deps.
// Exports (to window): IOSDevice, IOSStatusBar, IOSNavBar, IOSGlassPill, IOSList, IOSListRow, IOSKeyboard
//
// Usage — wrap your screen content in <IOSDevice> to get the bezel, status bar
// and home indicator (props: title, dark, keyboard):
//
//   <IOSDevice title="Settings">
//     ...your screen content...
//   </IOSDevice>
//   <IOSDevice dark title="Search" keyboard>…</IOSDevice>
/* END USAGE */

// ─────────────────────────────────────────────────────────────
// Status bar
// ─────────────────────────────────────────────────────────────
function IOSStatusBar({
  dark = false,
  time = '9:41'
}) {
  const c = dark ? '#fff' : '#000';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 154,
      alignItems: 'center',
      justifyContent: 'center',
      padding: '21px 24px 19px',
      boxSizing: 'border-box',
      position: 'relative',
      zIndex: 20,
      width: '100%'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 22,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      paddingTop: 1.5
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: '-apple-system, "SF Pro", system-ui',
      fontWeight: 590,
      fontSize: 17,
      lineHeight: '22px',
      color: c
    }
  }, time)), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 22,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 7,
      paddingTop: 1,
      paddingRight: 1
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "19",
    height: "12",
    viewBox: "0 0 19 12"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "0",
    y: "7.5",
    width: "3.2",
    height: "4.5",
    rx: "0.7",
    fill: c
  }), /*#__PURE__*/React.createElement("rect", {
    x: "4.8",
    y: "5",
    width: "3.2",
    height: "7",
    rx: "0.7",
    fill: c
  }), /*#__PURE__*/React.createElement("rect", {
    x: "9.6",
    y: "2.5",
    width: "3.2",
    height: "9.5",
    rx: "0.7",
    fill: c
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14.4",
    y: "0",
    width: "3.2",
    height: "12",
    rx: "0.7",
    fill: c
  })), /*#__PURE__*/React.createElement("svg", {
    width: "17",
    height: "12",
    viewBox: "0 0 17 12"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M8.5 3.2C10.8 3.2 12.9 4.1 14.4 5.6L15.5 4.5C13.7 2.7 11.2 1.5 8.5 1.5C5.8 1.5 3.3 2.7 1.5 4.5L2.6 5.6C4.1 4.1 6.2 3.2 8.5 3.2Z",
    fill: c
  }), /*#__PURE__*/React.createElement("path", {
    d: "M8.5 6.8C9.9 6.8 11.1 7.3 12 8.2L13.1 7.1C11.8 5.9 10.2 5.1 8.5 5.1C6.8 5.1 5.2 5.9 3.9 7.1L5 8.2C5.9 7.3 7.1 6.8 8.5 6.8Z",
    fill: c
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "8.5",
    cy: "10.5",
    r: "1.5",
    fill: c
  })), /*#__PURE__*/React.createElement("svg", {
    width: "27",
    height: "13",
    viewBox: "0 0 27 13"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "0.5",
    y: "0.5",
    width: "23",
    height: "12",
    rx: "3.5",
    stroke: c,
    strokeOpacity: "0.35",
    fill: "none"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "2",
    y: "2",
    width: "20",
    height: "9",
    rx: "2",
    fill: c
  }), /*#__PURE__*/React.createElement("path", {
    d: "M25 4.5V8.5C25.8 8.2 26.5 7.2 26.5 6.5C26.5 5.8 25.8 4.8 25 4.5Z",
    fill: c,
    fillOpacity: "0.4"
  }))));
}

// ─────────────────────────────────────────────────────────────
// Liquid glass pill — blur + tint + shine
// ─────────────────────────────────────────────────────────────
function IOSGlassPill({
  children,
  dark = false,
  style = {}
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      height: 44,
      minWidth: 44,
      borderRadius: 9999,
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: dark ? '0 2px 6px rgba(0,0,0,0.35), 0 6px 16px rgba(0,0,0,0.2)' : '0 1px 3px rgba(0,0,0,0.07), 0 3px 10px rgba(0,0,0,0.06)',
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      borderRadius: 9999,
      backdropFilter: 'blur(12px) saturate(180%)',
      WebkitBackdropFilter: 'blur(12px) saturate(180%)',
      background: dark ? 'rgba(120,120,128,0.28)' : 'rgba(255,255,255,0.5)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      borderRadius: 9999,
      boxShadow: dark ? 'inset 1.5px 1.5px 1px rgba(255,255,255,0.15), inset -1px -1px 1px rgba(255,255,255,0.08)' : 'inset 1.5px 1.5px 1px rgba(255,255,255,0.7), inset -1px -1px 1px rgba(255,255,255,0.4)',
      border: dark ? '0.5px solid rgba(255,255,255,0.15)' : '0.5px solid rgba(0,0,0,0.06)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1,
      display: 'flex',
      alignItems: 'center',
      padding: '0 4px'
    }
  }, children));
}

// ─────────────────────────────────────────────────────────────
// Navigation bar — glass pills + large title
// ─────────────────────────────────────────────────────────────
function IOSNavBar({
  title = 'Title',
  dark = false,
  trailingIcon = true
}) {
  const muted = dark ? 'rgba(255,255,255,0.6)' : '#404040';
  const text = dark ? '#fff' : '#000';
  const pillIcon = content => /*#__PURE__*/React.createElement(IOSGlassPill, {
    dark: dark
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 36,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, content));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      paddingTop: 62,
      paddingBottom: 10,
      position: 'relative',
      zIndex: 5
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px'
    }
  }, pillIcon(/*#__PURE__*/React.createElement("svg", {
    width: "12",
    height: "20",
    viewBox: "0 0 12 20",
    fill: "none",
    style: {
      marginLeft: -1
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M10 2L2 10l8 8",
    stroke: muted,
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }))), trailingIcon && pillIcon(/*#__PURE__*/React.createElement("svg", {
    width: "22",
    height: "6",
    viewBox: "0 0 22 6"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "3",
    cy: "3",
    r: "2.5",
    fill: muted
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "11",
    cy: "3",
    r: "2.5",
    fill: muted
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "19",
    cy: "3",
    r: "2.5",
    fill: muted
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px',
      fontFamily: '-apple-system, system-ui',
      fontSize: 34,
      fontWeight: 700,
      lineHeight: '41px',
      color: text,
      letterSpacing: 0.4
    }
  }, title));
}

// ─────────────────────────────────────────────────────────────
// Grouped list (inset card, r:26) + row (52px)
// ─────────────────────────────────────────────────────────────
function IOSListRow({
  title,
  detail,
  icon,
  chevron = true,
  isLast = false,
  dark = false
}) {
  const text = dark ? '#fff' : '#000';
  const sec = dark ? 'rgba(235,235,245,0.6)' : 'rgba(60,60,67,0.6)';
  const ter = dark ? 'rgba(235,235,245,0.3)' : 'rgba(60,60,67,0.3)';
  const sep = dark ? 'rgba(84,84,88,0.65)' : 'rgba(60,60,67,0.12)';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      minHeight: 52,
      padding: '0 16px',
      position: 'relative',
      fontFamily: '-apple-system, system-ui',
      fontSize: 17,
      letterSpacing: -0.43
    }
  }, icon && /*#__PURE__*/React.createElement("div", {
    style: {
      width: 30,
      height: 30,
      borderRadius: 7,
      background: icon,
      marginRight: 12,
      flexShrink: 0
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      color: text
    }
  }, title), detail && /*#__PURE__*/React.createElement("span", {
    style: {
      color: sec,
      marginRight: 6
    }
  }, detail), chevron && /*#__PURE__*/React.createElement("svg", {
    width: "8",
    height: "14",
    viewBox: "0 0 8 14",
    style: {
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M1 1l6 6-6 6",
    stroke: ter,
    strokeWidth: "2",
    fill: "none",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  })), !isLast && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      bottom: 0,
      right: 0,
      left: icon ? 58 : 16,
      height: 0.5,
      background: sep
    }
  }));
}
function IOSList({
  header,
  children,
  dark = false
}) {
  const hc = dark ? 'rgba(235,235,245,0.6)' : 'rgba(60,60,67,0.6)';
  const bg = dark ? '#1C1C1E' : '#fff';
  return /*#__PURE__*/React.createElement("div", null, header && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: '-apple-system, system-ui',
      fontSize: 13,
      color: hc,
      textTransform: 'uppercase',
      padding: '8px 36px 6px',
      letterSpacing: -0.08
    }
  }, header), /*#__PURE__*/React.createElement("div", {
    style: {
      background: bg,
      borderRadius: 26,
      margin: '0 16px',
      overflow: 'hidden'
    }
  }, children));
}

// ─────────────────────────────────────────────────────────────
// Device frame
// ─────────────────────────────────────────────────────────────
function IOSDevice({
  children,
  width = 402,
  height = 874,
  dark = false,
  title,
  keyboard = false
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width,
      height,
      borderRadius: 48,
      overflow: 'hidden',
      position: 'relative',
      background: dark ? '#000' : '#F2F2F7',
      boxShadow: '0 40px 80px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.12)',
      fontFamily: '-apple-system, system-ui, sans-serif',
      WebkitFontSmoothing: 'antialiased'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 11,
      left: '50%',
      transform: 'translateX(-50%)',
      width: 126,
      height: 37,
      borderRadius: 24,
      background: '#000',
      zIndex: 50
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 10
    }
  }, /*#__PURE__*/React.createElement(IOSStatusBar, {
    dark: dark
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }
  }, title !== undefined && /*#__PURE__*/React.createElement(IOSNavBar, {
    title: title,
    dark: dark
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: 'auto'
    }
  }, children), keyboard && /*#__PURE__*/React.createElement(IOSKeyboard, {
    dark: dark
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      zIndex: 60,
      height: 34,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'flex-end',
      paddingBottom: 8,
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 139,
      height: 5,
      borderRadius: 100,
      background: dark ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.25)'
    }
  })));
}

// ─────────────────────────────────────────────────────────────
// Keyboard — iOS 26 liquid glass
// ─────────────────────────────────────────────────────────────
function IOSKeyboard({
  dark = false
}) {
  const glyph = dark ? 'rgba(255,255,255,0.7)' : '#595959';
  const sugg = dark ? 'rgba(255,255,255,0.6)' : '#333';
  const keyBg = dark ? 'rgba(255,255,255,0.22)' : 'rgba(255,255,255,0.85)';

  // special-key icons
  const icons = {
    shift: /*#__PURE__*/React.createElement("svg", {
      width: "19",
      height: "17",
      viewBox: "0 0 19 17"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M9.5 1L1 9.5h4.5V16h8V9.5H18L9.5 1z",
      fill: glyph
    })),
    del: /*#__PURE__*/React.createElement("svg", {
      width: "23",
      height: "17",
      viewBox: "0 0 23 17"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M7 1h13a2 2 0 012 2v11a2 2 0 01-2 2H7l-6-7.5L7 1z",
      fill: "none",
      stroke: glyph,
      strokeWidth: "1.6",
      strokeLinejoin: "round"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M10 5l7 7M17 5l-7 7",
      stroke: glyph,
      strokeWidth: "1.6",
      strokeLinecap: "round"
    })),
    ret: /*#__PURE__*/React.createElement("svg", {
      width: "20",
      height: "14",
      viewBox: "0 0 20 14"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M18 1v6H4m0 0l4-4M4 7l4 4",
      fill: "none",
      stroke: "#fff",
      strokeWidth: "1.8",
      strokeLinecap: "round",
      strokeLinejoin: "round"
    }))
  };
  const key = (content, {
    w,
    flex,
    ret,
    fs = 25,
    k
  } = {}) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      height: 42,
      borderRadius: 8.5,
      flex: flex ? 1 : undefined,
      width: w,
      minWidth: 0,
      background: ret ? '#08f' : keyBg,
      boxShadow: '0 1px 0 rgba(0,0,0,0.075)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, "SF Compact", system-ui',
      fontSize: fs,
      fontWeight: 458,
      color: ret ? '#fff' : glyph
    }
  }, content);
  const row = (keys, pad = 0) => /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6.5,
      justifyContent: 'center',
      padding: `0 ${pad}px`
    }
  }, keys.map(l => key(l, {
    flex: true,
    k: l
  })));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 15,
      borderRadius: 27,
      overflow: 'hidden',
      padding: '11px 0 2px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      boxShadow: dark ? '0 -2px 20px rgba(0,0,0,0.09)' : '0 -1px 6px rgba(0,0,0,0.018), 0 -3px 20px rgba(0,0,0,0.012)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      borderRadius: 27,
      backdropFilter: 'blur(12px) saturate(180%)',
      WebkitBackdropFilter: 'blur(12px) saturate(180%)',
      background: dark ? 'rgba(120,120,128,0.14)' : 'rgba(255,255,255,0.25)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      borderRadius: 27,
      boxShadow: dark ? 'inset 1.5px 1.5px 1px rgba(255,255,255,0.15)' : 'inset 1.5px 1.5px 1px rgba(255,255,255,0.7), inset -1px -1px 1px rgba(255,255,255,0.4)',
      border: dark ? '0.5px solid rgba(255,255,255,0.15)' : '0.5px solid rgba(0,0,0,0.06)',
      pointerEvents: 'none'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 20,
      alignItems: 'center',
      padding: '8px 22px 13px',
      width: '100%',
      boxSizing: 'border-box',
      position: 'relative'
    }
  }, ['"The"', 'the', 'to'].map((w, i) => /*#__PURE__*/React.createElement(React.Fragment, {
    key: i
  }, i > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      width: 1,
      height: 25,
      background: '#ccc',
      opacity: 0.3
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      textAlign: 'center',
      fontFamily: '-apple-system, system-ui',
      fontSize: 17,
      color: sugg,
      letterSpacing: -0.43,
      lineHeight: '22px'
    }
  }, w)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 13,
      padding: '0 6.5px',
      width: '100%',
      boxSizing: 'border-box',
      position: 'relative'
    }
  }, row(['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']), row(['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'], 20), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 14.25,
      alignItems: 'center'
    }
  }, key(icons.shift, {
    w: 45,
    k: 'shift'
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6.5,
      flex: 1
    }
  }, ['z', 'x', 'c', 'v', 'b', 'n', 'm'].map(l => key(l, {
    flex: true,
    k: l
  }))), key(icons.del, {
    w: 45,
    k: 'del'
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6,
      alignItems: 'center'
    }
  }, key('ABC', {
    w: 92.25,
    fs: 18,
    k: 'abc'
  }), key('', {
    flex: true,
    k: 'space'
  }), key(icons.ret, {
    w: 92.25,
    ret: true,
    k: 'ret'
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 56,
      width: '100%',
      position: 'relative'
    }
  }));
}
Object.assign(window, {
  IOSDevice,
  IOSStatusBar,
  IOSNavBar,
  IOSGlassPill,
  IOSList,
  IOSListRow,
  IOSKeyboard
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/ios-frame.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/model.js
try { (() => {
/* model.js — derived scoring model + extra datasets for the v2 screens.
   Loads AFTER data.js. Adds helpers to window and extends DASH_DATA with
   cohort retention, monthly rotation, and activity data. All simulated. */
(function () {
  const D = window.DASH_DATA;

  // ---- #1 Score explainability: signal catalog with weights ----
  // Keys match the señal labels used in data.js.
  const SIGNAL_CATALOG = {
    "onboarding": {
      peso: 2.0,
      desc: "En ventana crítica de inducción (primeros 6 meses)"
    },
    "días cero↑": {
      peso: 2.0,
      desc: "Días sin registrar ventas en aumento"
    },
    "caída 3m": {
      peso: 2.0,
      desc: "Cumplimiento de plan cayó 3 meses seguidos"
    },
    "plan<80%": {
      peso: 1.5,
      desc: "Cumplimiento de plan por debajo del 80%"
    },
    "zona quemada": {
      peso: 1.5,
      desc: "Asignado a zona con alta rotación histórica"
    },
    "mes 4-6": {
      peso: 1.0,
      desc: "Mes 4 a 6: ventana de adaptación"
    },
    "inactivos↑": {
      peso: 1.0,
      desc: "Clientes inactivos en su cartera en aumento"
    },
    "cobranza baja": {
      peso: 1.0,
      desc: "Cobranza por debajo del objetivo"
    },
    "clientes L:0": {
      peso: 0.5,
      desc: "Sin altas de clientes nuevos en el período"
    },
    "ticket↓": {
      peso: 0.5,
      desc: "Ticket promedio en descenso"
    }
  };

  // returns { base, factores:[{label,peso,desc}], suma } for a vendor
  function scoreBreakdown(r) {
    const base = 1.0;
    const factores = (r.senales || []).map(([label]) => ({
      label,
      peso: (SIGNAL_CATALOG[label] || {
        peso: 0.5
      }).peso,
      desc: (SIGNAL_CATALOG[label] || {
        desc: "Señal de riesgo"
      }).desc
    })).sort((a, b) => b.peso - a.peso);
    const suma = base + factores.reduce((s, f) => s + f.peso, 0);
    return {
      base,
      factores,
      suma: Math.min(10, Math.round(suma))
    };
  }

  // ---- #2 Score trajectory: deterministic 6-month history ending near score ----
  function buildScoreHistory(r) {
    // worsening signals → score climbed recently; recovering → fell
    const worsening = (r.senales || []).some(([l]) => ["caída 3m", "onboarding", "días cero↑"].includes(l));
    const seed = r.id % 7;
    const cur = r.score;
    const hist = [];
    for (let i = 5; i >= 0; i--) {
      let v;
      if (worsening) v = cur - Math.round(i * (0.6 + seed * 0.06));else v = cur + Math.round(i * (0.25 + seed % 3 * 0.08)) - (i > 3 ? 1 : 0);
      hist.push(Math.max(1, Math.min(10, v)));
    }
    hist[5] = cur;
    return hist;
  }
  function scoreDelta(r) {
    const h = r._hist || buildScoreHistory(r);
    return h[5] - h[4];
  }

  // attach hist + delta to every vendor (in place)
  D.V.forEach(r => {
    r._hist = buildScoreHistory(r);
    r._delta = r._hist[5] - r._hist[4];
  });

  // ---- #3 Onboarding cohort retention (% still active by month of tenure) ----
  D.COHORTS = [{
    cohorte: "Jul 25",
    ingresos: 8,
    ret: [100, 88, 75, 50, 38, 38]
  }, {
    cohorte: "Ago 25",
    ingresos: 6,
    ret: [100, 83, 67, 50, 33]
  }, {
    cohorte: "Sep 25",
    ingresos: 9,
    ret: [100, 89, 78, 56]
  }, {
    cohorte: "Oct 25",
    ingresos: 5,
    ret: [100, 80, 60]
  }, {
    cohorte: "Nov 25",
    ingresos: 7,
    ret: [100, 86]
  }, {
    cohorte: "Dic 25",
    ingresos: 4,
    ret: [100]
  }];
  // company-wide survival curve, months 0..7
  D.RETENCION = [100, 86, 71, 53, 41, 33, 28, 25];

  // ---- Historial: monthly rotation + avg risk score trend (last 6 months) ----
  D.ROTACION = [{
    mes: "Ago",
    bajas: 6,
    altas: 5,
    scoreProm: 4.1
  }, {
    mes: "Sep",
    bajas: 4,
    altas: 9,
    scoreProm: 4.4
  }, {
    mes: "Oct",
    bajas: 7,
    altas: 5,
    scoreProm: 4.9
  }, {
    mes: "Nov",
    bajas: 5,
    altas: 7,
    scoreProm: 5.2
  }, {
    mes: "Dic",
    bajas: 8,
    altas: 4,
    scoreProm: 5.6
  }, {
    mes: "Ene",
    bajas: 6,
    altas: 6,
    scoreProm: 5.4
  }];

  // ---- Actividad: Televentas (llamadas) + Viajantes (visitas) vs plan ----
  // derived from V so names line up
  function actividadDe(r) {
    const esTel = r.tipo === "Televentas";
    const planUnidad = esTel ? 60 : 22; // llamadas/día or visitas/semana target
    const cumpl = Math.max(35, Math.min(112, Math.round(r.plan3m * (0.9 + r.id % 5 * 0.03))));
    const real = Math.round(planUnidad * cumpl / 100);
    const contactos = esTel ? Math.round(real * (0.55 + r.id % 4 * 0.05)) : Math.round(real * 0.8);
    return {
      tipo: r.tipo,
      plan: planUnidad,
      real,
      cumpl,
      contactos,
      clientesL: r.senales.some(([l]) => l === "clientes L:0") ? 0 : 1 + r.id % 4
    };
  }
  D.ACTIVIDAD = D.V.map(r => ({
    id: r.id,
    nombre: r.nombre,
    grupo: r.grupo,
    supervisor: r.supervisor,
    nivel: r.nivel,
    ...actividadDe(r)
  }));

  // ---- #1 Prediction vs. outcome: did last month's score predict who left? ----
  // Confusion matrix over the cohort scored 1 month ago (simulated but internally
  // consistent: high score → much higher base rate of leaving).
  // marcado = score >= 6 last month ("alertado"); se_fue = actually left this month.
  D.PREDICCION = {
    periodo: "Mayo 2025",
    // counts
    vp: 11,
    // marcado alto Y se fue          (verdadero positivo)
    fn: 3,
    // NO marcado pero se fue          (falso negativo — la fuga sorpresa)
    fp: 8,
    // marcado alto pero retenido      (falso positivo — incluye los que salvamos)
    vn: 39,
    // NO marcado y se quedó           (verdadero negativo)
    // of the FP, how many had an intervention (i.e. we likely saved them)
    fp_intervenidos: 6
  };

  // ---- #2 Action effectiveness by PROFILE (mejora promedio de score) ----
  // perfil = combinación de antigüedad + zona; tells you what worked for similar reps.
  D.EFECTIVIDAD = {
    onboarding_quemada: [
    // nuevos (<6m) en zona de alta rotación
    {
      tipo: "Reunión 1:1",
      avg: 1.8,
      n: 7
    }, {
      tipo: "Acompañamiento",
      avg: 1.3,
      n: 5
    }, {
      tipo: "Reasignación de zona",
      avg: 1.1,
      n: 3
    }, {
      tipo: "Capacitación",
      avg: 0.4,
      n: 4
    }],
    onboarding_normal: [
    // nuevos en zona normal
    {
      tipo: "Acompañamiento",
      avg: 1.6,
      n: 6
    }, {
      tipo: "Reunión 1:1",
      avg: 1.2,
      n: 8
    }, {
      tipo: "Capacitación",
      avg: 0.9,
      n: 5
    }],
    senior_caida: [
    // veteranos (>12m) con caída de plan
    {
      tipo: "Ajuste de cartera",
      avg: 1.5,
      n: 4
    }, {
      tipo: "Reunión 1:1",
      avg: 1.1,
      n: 9
    }, {
      tipo: "Capacitación",
      avg: 0.7,
      n: 6
    }],
    default: [{
      tipo: "Reunión 1:1",
      avg: 1.3,
      n: 12
    }, {
      tipo: "Acompañamiento",
      avg: 1.0,
      n: 8
    }, {
      tipo: "Capacitación",
      avg: 0.6,
      n: 7
    }]
  };
  function perfilDe(r) {
    if (r.meses <= 6) return r.rb > 0.45 ? "onboarding_quemada" : "onboarding_normal";
    if (r.meses > 12 && r.senales.some(([l]) => l === "caída 3m" || l === "plan<80%")) return "senior_caida";
    return "default";
  }
  function perfilLabel(p) {
    return {
      onboarding_quemada: "nuevos en zona de alta rotación",
      onboarding_normal: "nuevos en zona normal",
      senior_caida: "veteranos con caída de plan",
      default: "vendedores en riesgo"
    }[p];
  }
  // best action + the whole ranking for a vendor's profile
  function recomendarAccion(r) {
    const p = perfilDe(r);
    const ranking = D.EFECTIVIDAD[p] || D.EFECTIVIDAD.default;
    return {
      perfil: p,
      perfilLabel: perfilLabel(p),
      ranking,
      mejor: ranking[0]
    };
  }
  Object.assign(window, {
    SIGNAL_CATALOG,
    scoreBreakdown,
    buildScoreHistory,
    scoreDelta,
    perfilDe,
    perfilLabel,
    recomendarAccion
  });
})();
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/model.js", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/primitives.jsx
try { (() => {
/* Würth Rotación UI kit — shared primitives + helpers.
   Faithful ports of the dashboard's CSS-in-Python components. */

const NIVEL_LABEL = {
  critico: "Crítico",
  alto: "Alto",
  medio: "Medio",
  bajo: "Bajo"
};
function fmtAntiguedad(m) {
  if (m < 12) return `${m} mes${m !== 1 ? "es" : ""}`;
  const a = Math.floor(m / 12),
    r = m % 12;
  let s = `${a} año${a !== 1 ? "s" : ""}`;
  if (r) s += ` y ${r} mes${r !== 1 ? "es" : ""}`;
  return s;
}
function fmtPesos(n) {
  return "$" + Math.round(n).toLocaleString("es-AR").replace(/,/g, ".");
}
// ---- #3 unified number formatting (one rule set, used everywhere) ----
// pesos abreviados para titulares: $1,4 M / $980 mil
function fmtPesosCorto(n) {
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(1).replace(".", ",") + " M";
  if (n >= 1e3) return "$" + Math.round(n / 1e3) + " mil";
  return "$" + Math.round(n);
}
function fmtPct(n, dec = 0) {
  return n.toFixed(dec).replace(".", ",") + "%";
}
function fmtNum(n, dec = 0) {
  return n.toFixed(dec).replace(".", ",");
}
function fmtMeses(n) {
  return fmtNum(n, 1) + " m";
}
// signed delta with the product's tendency glyph (▲ worse, ▼ better when invert)
function fmtDelta(n, {
  invert = false,
  dec = 1
} = {}) {
  if (!n) return "=";
  const up = n > 0;
  const glyph = up ? "▲" : "▼";
  return glyph + " " + fmtNum(Math.abs(n), dec);
}
function zonaNivel(rb) {
  if (rb > 0.60) return "critico";
  if (rb > 0.45) return "alto";
  if (rb > 0.30) return "medio";
  return "bajo";
}
function zonaLabel(rb) {
  return {
    critico: "rot alta",
    alto: "rot alta",
    medio: "rot media",
    bajo: "rot baja"
  }[zonaNivel(rb)];
}

// ---- Card ----
function Card({
  children,
  style,
  pad = true
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderRadius: "var(--radius-card)",
      padding: pad ? "var(--pad-card)" : 0,
      boxShadow: "var(--shadow-card)",
      ...style
    }
  }, children);
}

// ---- Section header ----
function SectionHeader({
  children,
  note
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6,
      margin: "8px 0 14px"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      font: "var(--w-bold) var(--t-section) var(--font-sans)",
      color: "var(--ink-900)"
    }
  }, children), note && /*#__PURE__*/React.createElement("span", {
    style: {
      font: "var(--w-regular) var(--t-sub) var(--font-sans)",
      color: "var(--ink-400)"
    }
  }, note));
}

// ---- Score circle ----
function ScoreCircle({
  score,
  nivel,
  size = 36
}) {
  const c = {
    critico: ["var(--red-bg)", "var(--red-text)", "var(--red-accent)"],
    alto: ["var(--orange-bg)", "var(--orange-text)", "var(--orange-accent)"],
    medio: ["var(--blue-bg)", "var(--blue-text)", "var(--blue-accent)"],
    bajo: ["var(--green-bg)", "var(--green-text)", "var(--green-accent)"]
  }[nivel] || ["#f0f0f0", "#999", "#ccc"];
  return /*#__PURE__*/React.createElement("div", {
    title: NIVEL_LABEL[nivel],
    style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: size,
      height: size,
      borderRadius: "50%",
      fontWeight: 800,
      fontSize: size * 0.42,
      fontFamily: "var(--font-sans)",
      background: c[0],
      color: c[1],
      border: `2px solid ${c[2]}`
    }
  }, score);
}

// ---- Pill (signal tag) ----
function Pill({
  label,
  color
}) {
  const c = {
    red: ["var(--red-bg)", "var(--red-text)"],
    orange: ["var(--orange-bg)", "var(--orange-text)"],
    yellow: ["var(--yellow-bg)", "var(--yellow-text)"]
  }[color] || ["var(--yellow-bg)", "var(--yellow-text)"];
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: "var(--radius-pill)",
      fontSize: 11,
      fontWeight: 600,
      margin: "1px 2px",
      whiteSpace: "nowrap",
      fontFamily: "var(--font-sans)",
      background: c[0],
      color: c[1]
    }
  }, label);
}
function Pills({
  senales
}) {
  if (!senales || !senales.length) return /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-150)",
      fontSize: 12
    }
  }, "Sin alertas");
  return /*#__PURE__*/React.createElement("span", null, senales.map((s, i) => /*#__PURE__*/React.createElement(Pill, {
    key: i,
    label: s[0],
    color: s[1]
  })));
}

// ---- Accessibility: distinct SHAPE per risk level so meaning survives w/o color ----
const NIVEL_SHAPE = {
  critico: "▲",
  alto: "◆",
  medio: "■",
  bajo: "●"
};

// ---- Badge ----
// `shape` (default true for risk levels) prepends the level glyph so color-blind
// users distinguish levels by form, not hue alone.
function Badge({
  nivel,
  label,
  kind,
  shape
}) {
  const map = {
    critico: ["var(--red-bg)", "var(--red-text)"],
    alto: ["var(--orange-bg)", "var(--orange-text)"],
    medio: ["var(--blue-bg)", "var(--blue-text)"],
    bajo: ["var(--green-bg)", "var(--green-text)"],
    tipo: ["var(--purple-bg)", "var(--purple-text)"]
  };
  const key = kind || nivel;
  const c = map[key] || map.medio;
  const showShape = shape !== false && NIVEL_SHAPE[key];
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 4,
      padding: "2px 8px",
      borderRadius: "var(--radius-badge)",
      fontSize: 11,
      fontWeight: 600,
      fontFamily: "var(--font-sans)",
      whiteSpace: "nowrap",
      background: c[0],
      color: c[1]
    }
  }, showShape && /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      fontSize: 8,
      lineHeight: 1
    }
  }, NIVEL_SHAPE[key]), label || NIVEL_LABEL[nivel]);
}

// ---- Sparkline ----
function Sparkline({
  vals
}) {
  if (!vals || !vals.length) return /*#__PURE__*/React.createElement("span", null, "\u2014");
  const cap = Math.max(...vals, 100);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "inline-flex",
      alignItems: "flex-end",
      gap: 3,
      height: 24
    }
  }, vals.map((v, i) => {
    const h = Math.max(3, Math.round(v / cap * 22));
    const c = v >= 90 ? "var(--green-accent)" : v >= 70 ? "var(--orange-accent)" : "var(--red-accent)";
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      style: {
        width: 9,
        borderRadius: "2px 2px 0 0",
        height: h,
        background: c
      }
    });
  }));
}

// ---- KPI card ----
function KpiCard({
  value,
  label,
  sub,
  accent,
  valueColor
}) {
  const border = {
    red: "var(--red-accent)",
    orange: "var(--orange-accent)",
    blue: "var(--blue-accent)",
    green: "var(--green-accent)"
  }[accent] || "var(--border-idle)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0,
      background: "var(--surface)",
      borderRadius: "var(--radius-card)",
      padding: "var(--pad-card-y) var(--pad-card-x)",
      boxShadow: "var(--shadow-card)",
      borderLeft: `var(--accent-border) solid ${border}`,
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 30,
      lineHeight: 1.1,
      color: valueColor || "var(--ink-900)"
    }
  }, value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 12,
      lineHeight: 1.35,
      color: "var(--ink-700)",
      marginTop: 6
    }
  }, label), sub && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 400,
      fontSize: 11,
      lineHeight: 1.35,
      color: "var(--ink-300)",
      marginTop: 4
    }
  }, sub));
}

// ---- Top nav ----
function TopNav({
  current,
  onNav
}) {
  const items = [["inicio", "🏠 Inicio"], ["supervisor", "👤 Por supervisor"], ["intervenciones", "📝 Intervenciones"], ["historial", "📈 Historial"], ["costo", "💰 Costo de rotación"], ["actividad", "📞 Actividad"]];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: 20,
      paddingBottom: 14,
      borderBottom: "1px solid var(--line)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 9
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 20
    }
  }, "\uD83D\uDD14"), /*#__PURE__*/React.createElement("span", {
    style: {
      font: "var(--w-black) var(--t-header) var(--font-sans)",
      color: "var(--ink-900)"
    }
  }, "W\xFCrth Argentina \u2014 Alertas de Rotaci\xF3n")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 20,
      flexWrap: "wrap"
    }
  }, items.map(([k, label]) => /*#__PURE__*/React.createElement("a", {
    key: k,
    onClick: () => onNav(k),
    style: {
      font: "var(--w-regular) var(--t-table) var(--font-sans)",
      cursor: "pointer",
      whiteSpace: "nowrap",
      textDecoration: "none",
      color: current === k ? "var(--ink-900)" : "var(--blue-accent)",
      fontWeight: current === k ? 700 : 400
    }
  }, label))));
}
Object.assign(window, {
  fmtAntiguedad,
  fmtPesos,
  fmtPesosCorto,
  fmtPct,
  fmtNum,
  fmtMeses,
  fmtDelta,
  zonaNivel,
  zonaLabel,
  NIVEL_LABEL,
  NIVEL_SHAPE,
  Card,
  SectionHeader,
  ScoreCircle,
  Pill,
  Pills,
  Badge,
  Sparkline,
  KpiCard,
  TopNav
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/primitives.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/v2common.jsx
try { (() => {
/* Shared v2 building blocks used across the "propuesta profesional" screens.
   Applies the same language as InicioV2: hero stat, secondary strip, clean
   section header, empty states. Reuses primitives.jsx. */

// big dominant stat card with a colored top-border
function HeroStat({
  label,
  value,
  unit,
  accent = "var(--red-accent)",
  valueColor,
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: "0 0 320px",
      background: "var(--surface)",
      borderRadius: 14,
      padding: "22px 24px",
      boxShadow: "var(--shadow-card)",
      borderTop: `4px solid ${accent}`,
      display: "flex",
      flexDirection: "column"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13,
      color: "var(--ink-600)",
      textTransform: "uppercase",
      letterSpacing: ".04em"
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: 10,
      marginTop: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 56,
      lineHeight: 1,
      color: valueColor || "var(--ink-900)"
    }
  }, value), unit && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 16,
      color: "var(--ink-400)"
    }
  }, unit)), children && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 16
    }
  }, children));
}

// secondary, de-emphasised stat (inside a strip)
function StatItem({
  value,
  label
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      padding: "4px 2px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 26,
      color: "var(--ink-900)"
    }
  }, value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 12,
      color: "var(--ink-400)",
      marginTop: 2
    }
  }, label));
}
function StatStrip({
  children
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 0,
      padding: "0 4px 18px",
      marginBottom: 36,
      borderBottom: "1px solid var(--line-faint)"
    }
  }, children);
}

// section header with optional right-aligned note/callout
function V2Section({
  title,
  right,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: 16,
      flexWrap: "wrap",
      gap: 12,
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 16,
      color: "var(--ink-900)"
    }
  }, title), right);
}

// callout banner (action of the day / context)
function V2Banner({
  emoji,
  title,
  sub,
  cta,
  onCta,
  tone = "red"
}) {
  const map = {
    red: ["var(--red-bg)", "#f4cfcd", "var(--red-text)", "#8a3331", "var(--red-accent)"],
    orange: ["var(--orange-bg)", "#f3d9a8", "var(--orange-text)", "#7a4a00", "var(--orange-accent)"],
    blue: ["var(--blue-bg)", "#bcdcf5", "var(--blue-text)", "#2f5e86", "var(--blue-accent)"],
    green: ["var(--green-bg)", "#cfe6b8", "var(--green-text)", "#3f6326", "var(--green-accent)"]
  }[tone];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 14,
      padding: "14px 20px",
      borderRadius: 12,
      background: map[0],
      border: `1px solid ${map[1]}`,
      marginBottom: 28
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 22
    }
  }, emoji), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 800,
      fontSize: 16,
      color: map[2]
    }
  }, title), sub && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 13,
      color: map[3],
      marginTop: 2
    }
  }, sub)), cta && /*#__PURE__*/React.createElement("button", {
    onClick: onCta,
    style: {
      padding: "9px 18px",
      borderRadius: 8,
      border: "none",
      cursor: "pointer",
      background: map[4],
      color: "#fff",
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 13,
      whiteSpace: "nowrap"
    }
  }, cta));
}

// surface card (rounded 14, no left-border) — v2 default container
function V2Card({
  children,
  style,
  pad = true
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderRadius: 14,
      boxShadow: "var(--shadow-card)",
      padding: pad ? "20px 24px" : 0,
      ...style
    }
  }, children);
}

// empty state
function V2Empty({
  emoji = "✓",
  title,
  sub
}) {
  return /*#__PURE__*/React.createElement(V2Card, {
    style: {
      padding: "48px 22px",
      textAlign: "center"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 30,
      marginBottom: 8
    }
  }, emoji), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 14,
      color: "var(--green-text)"
    }
  }, title), sub && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 13,
      color: "var(--ink-400)",
      marginTop: 4
    }
  }, sub));
}
const ACCION_V2 = {
  critico: ["Reunión esta semana", "var(--red-text)", "var(--red-bg)"],
  alto: ["Seguimiento activo", "var(--orange-text)", "var(--orange-bg)"],
  medio: ["Monitoreo mensual", "var(--ink-600)", "var(--table-head-bg)"],
  bajo: ["Seguimiento normal", "var(--ink-400)", "transparent"]
};
function AccionTag({
  nivel
}) {
  const [acc, tx, bg] = ACCION_V2[nivel];
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-block",
      padding: "4px 10px",
      borderRadius: 7,
      background: bg,
      color: tx,
      fontSize: 12,
      fontWeight: 700,
      whiteSpace: "nowrap"
    }
  }, acc);
}

// shared v2 table chrome
const v2th = {
  background: "transparent",
  padding: "0 14px 10px",
  textAlign: "left",
  fontSize: 11,
  fontWeight: 700,
  color: "var(--ink-400)",
  textTransform: "uppercase",
  letterSpacing: ".04em",
  borderBottom: "2px solid var(--line-strong)"
};
const v2td = {
  padding: "14px",
  borderBottom: "1px solid var(--line-faint)",
  verticalAlign: "middle",
  fontSize: 13
};

// ---- #2 score trajectory: Δ vs previous month (higher score = worse = red) ----
function ScoreDelta({
  delta
}) {
  if (!delta) return /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: "var(--ink-300)"
    }
  }, "=");
  const worse = delta > 0;
  return /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: worse ? "var(--red-text)" : "var(--green-text)",
      whiteSpace: "nowrap"
    }
  }, worse ? "▲" : "▼", " ", Math.abs(delta));
}

// mini line of the 6-month score history (1..10, higher = worse)
function ScoreHistory({
  hist,
  w = 90,
  h = 30
}) {
  if (!hist || hist.length < 2) return /*#__PURE__*/React.createElement("span", null, "\u2014");
  const max = 10,
    min = 1,
    n = hist.length;
  const pts = hist.map((v, i) => {
    const x = i / (n - 1) * w;
    const y = h - (v - min) / (max - min) * h;
    return [x, y];
  });
  const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  const last = hist[n - 1],
    prev = hist[n - 2];
  const col = last > prev ? "var(--red-accent)" : last < prev ? "var(--green-accent)" : "var(--ink-300)";
  return /*#__PURE__*/React.createElement("svg", {
    width: w,
    height: h,
    style: {
      display: "block",
      overflow: "visible"
    }
  }, /*#__PURE__*/React.createElement("polyline", {
    points: pts.map(p => p.join(",")).join(" "),
    fill: "none",
    stroke: col,
    strokeWidth: "2",
    strokeLinejoin: "round",
    strokeLinecap: "round"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: pts[n - 1][0],
    cy: pts[n - 1][1],
    r: "3",
    fill: col
  }));
}

// ---- #1 score explainability: weighted factor breakdown ----
function ScoreBreakdown({
  vendedor
}) {
  const {
    base,
    factores
  } = window.scoreBreakdown(vendedor);
  const maxPeso = 2.0;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--ink-400)",
      textTransform: "uppercase",
      letterSpacing: ".04em",
      marginBottom: 10
    }
  }, "Por qu\xE9 este score"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 9
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 150,
      fontSize: 12,
      color: "var(--ink-500)"
    }
  }, "Base (todos arrancan en 1)"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 14,
      background: "var(--line-faint)",
      borderRadius: 4,
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: `${base / maxPeso * 100}%`,
      height: "100%",
      background: "var(--ink-200)"
    }
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 34,
      textAlign: "right",
      fontSize: 12,
      fontWeight: 700,
      color: "var(--ink-500)"
    }
  }, "+", base.toFixed(0))), factores.map(f => /*#__PURE__*/React.createElement("div", {
    key: f.label,
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10
    },
    title: f.desc
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 150,
      fontSize: 12,
      color: "var(--ink-700)",
      fontWeight: 600,
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis"
    }
  }, f.label), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 14,
      background: "var(--line-faint)",
      borderRadius: 4,
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: `${f.peso / maxPeso * 100}%`,
      height: "100%",
      background: f.peso >= 2 ? "var(--red-accent)" : f.peso >= 1.5 ? "var(--orange-accent)" : "var(--yellow-text)"
    }
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 34,
      textAlign: "right",
      fontSize: 12,
      fontWeight: 700,
      color: "var(--ink-700)"
    }
  }, "+", f.peso.toFixed(1)))), !factores.length && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--ink-400)"
    }
  }, "Sin se\xF1ales de riesgo activas \u2014 score bajo.")), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 10,
      fontSize: 11,
      color: "var(--ink-300)",
      lineHeight: 1.5
    }
  }, "Pas\xE1 el mouse sobre cada factor para ver su definici\xF3n. Pesos del modelo de scoring."));
}

// ---- #5 loading skeleton ----
function Skeleton({
  w = "100%",
  h = 14,
  r = 6,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "sk",
    style: {
      width: w,
      height: h,
      borderRadius: r,
      ...style
    }
  });
}

// ---- #4 adjustable density (shared across separately-transpiled files) ----
function setDensity(d) {
  window.__density = d;
  window.dispatchEvent(new Event("densitychange"));
}
function useDensity() {
  const [d, setD] = React.useState(window.__density || "comodo");
  React.useEffect(() => {
    const h = () => setD(window.__density || "comodo");
    window.addEventListener("densitychange", h);
    return () => window.removeEventListener("densitychange", h);
  }, []);
  return d;
}
// returns the td style for the current density
function tdFor(density) {
  return density === "compacto" ? {
    padding: "7px 14px",
    borderBottom: "1px solid var(--line-faint)",
    verticalAlign: "middle",
    fontSize: 12.5
  } : {
    padding: "14px",
    borderBottom: "1px solid var(--line-faint)",
    verticalAlign: "middle",
    fontSize: 13
  };
}
function DensityToggle() {
  const d = useDensity();
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "inline-flex",
      border: "1px solid var(--line-strong)",
      borderRadius: 8,
      overflow: "hidden"
    }
  }, [["comodo", "Cómodo"], ["compacto", "Compacto"]].map(([k, l]) => /*#__PURE__*/React.createElement("button", {
    key: k,
    onClick: () => setDensity(k),
    style: {
      padding: "5px 12px",
      border: "none",
      cursor: "pointer",
      background: d === k ? "var(--ink-900)" : "#fff",
      color: d === k ? "#fff" : "var(--ink-600)",
      fontFamily: "var(--font-sans)",
      fontWeight: 600,
      fontSize: 12
    }
  }, l)));
}
Object.assign(window, {
  HeroStat,
  StatItem,
  StatStrip,
  V2Section,
  V2Banner,
  V2Card,
  V2Empty,
  AccionTag,
  ACCION_V2,
  v2th,
  v2td,
  ScoreDelta,
  ScoreHistory,
  ScoreBreakdown,
  Skeleton,
  setDensity,
  useDensity,
  tdFor,
  DensityToggle
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/v2common.jsx", error: String((e && e.message) || e) }); }

})();
