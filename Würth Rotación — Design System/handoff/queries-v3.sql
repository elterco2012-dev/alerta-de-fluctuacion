-- ============================================================================
-- queries-v3.sql — Würth Rotación
-- Consultas reales para las 3 pantallas/datos que en snippets-v3.py vienen
-- con números de ejemplo. Reemplazá los ejemplos por estos resultados.
--
-- Dialecto: SQLite (data/wurth.db). Cuando migren a Informix, las funciones de
-- fecha cambian (ver notas). La REGLA del proyecto es SOLO LECTURA sobre las
-- bases de producción; lo único que se escribe es wurth.db.
--
-- Esquema usado (de CLAUDE.md):
--   vendedores(id_vendedor, tipo, id_grupo, nombre_grupo, supervisor,
--              fecha_ingreso, fecha_egreso, motivo_egreso, activo)
--   ventas_mensual(id_vendedor, anio, mes, mes_numero, dias_venta_cero,
--              pct_plan, clientes_activos, clientes_nuevos, pct_cobranza, ...)
--   grupos(id_grupo, nombre_grupo, supervisor, riesgo_base)
--   intervenciones(id, id_vendedor, fecha, tipo, supervisor,
--              score_inicial, nivel_inicial, observaciones)
-- ============================================================================


-- ════════════════════════════════════════════════════════════════════════════
-- #3  EFECTIVIDAD DE INTERVENCIONES POR PERFIL
--     "¿Qué tipo de intervención bajó más el score para perfiles parecidos?"
--     Es 100% enchufable: la tabla intervenciones YA existe y guarda score_inicial.
--
--     OJO: el score ACTUAL no está en ninguna tabla — score_engine.py lo calcula
--     en vivo. Así que el impacto se cierra en Python (como ya hace
--     intervenciones.calcular_impacto). Esta query trae todo lo necesario MENOS
--     score_actual; ese se agrega en Python desde el DataFrame de scores en vivo.
-- ════════════════════════════════════════════════════════════════════════════
SELECT
    i.id,
    i.id_vendedor,
    i.tipo                       AS tipo_intervencion,
    i.score_inicial,
    i.fecha,
    v.activo,
    v.motivo_egreso,
    -- campos que definen el PERFIL del vendedor:
    g.riesgo_base,                                   -- zona quemada si > 0.45
    vm.mes_numero               AS antiguedad_meses  -- mes de carrera al último período
FROM intervenciones i
JOIN vendedores v   ON v.id_vendedor = i.id_vendedor
JOIN grupos g       ON g.id_grupo    = v.id_grupo
-- último período cargado de cada vendedor (su antigüedad actual):
LEFT JOIN ventas_mensual vm
       ON vm.id_vendedor = i.id_vendedor
      AND (vm.anio * 100 + vm.mes) = (
            SELECT MAX(v2.anio * 100 + v2.mes)
            FROM ventas_mensual v2
            WHERE v2.id_vendedor = i.id_vendedor
      );

-- En Python, después de traer esto y el DataFrame de scores en vivo:
--   df["score_actual"] = df["id_vendedor"].map(score_map)          # solo activos
--   df["impacto"]      = df["score_inicial"] - df["score_actual"]   # + = mejoró
--   df["perfil"]       = perfil_de(df["antiguedad_meses"], df["riesgo_base"], senales)
--   efectividad = df[df.activo==1].groupby(["perfil","tipo_intervencion"])["impacto"] \
--                   .agg(["mean","count"]).reset_index()
-- Eso reemplaza el dict EFECTIVIDAD de snippets-v3.py con datos reales.
-- (Nota: los TIPOS reales están en intervenciones.py — usá esos nombres exactos.)


-- ════════════════════════════════════════════════════════════════════════════
-- #2/#3  COHORTES DE RETENCIÓN
--     "De los que ingresaron en cada mes, ¿qué % sigue activo a los N meses?"
--     100% enchufable: solo usa fecha_ingreso y fecha_egreso de vendedores.
--
--     Idea: para cada vendedor calculamos su "tenure" (meses entre ingreso y
--     egreso, o entre ingreso y hoy si sigue activo) y lo agrupamos por cohorte
--     (año-mes de ingreso). Después, en Python, la curva de retención al mes N
--     es: (# de la cohorte con tenure >= N) / (# total de la cohorte).
-- ════════════════════════════════════════════════════════════════════════════
SELECT
    strftime('%Y-%m', fecha_ingreso)                          AS cohorte,   -- ej '2025-07'
    id_vendedor,
    activo,
    -- meses de permanencia (tenure). En SQLite restamos fechas como días/30.4:
    CAST(
      ( julianday(COALESCE(fecha_egreso, date('now'))) - julianday(fecha_ingreso) )
      / 30.4375 AS INTEGER
    )                                                          AS tenure_meses
FROM vendedores
WHERE fecha_ingreso IS NOT NULL
  AND fecha_ingreso >= date('now', '-12 months')   -- últimas 12 cohortes
ORDER BY cohorte, id_vendedor;

-- En Python:
--   coh = df.groupby("cohorte")
--   for nombre, g in coh:
--       total = len(g)
--       ret = [ round((g.tenure_meses >= n).sum() / total * 100) for n in range(0, 6) ]
--   → eso llena la tabla/curva de cohortes (D.COHORTS / D.RETENCION en el mock).
--
-- INFORMIX: strftime/julianday no existen. Equivalente:
--   cohorte  = TO_CHAR(fecha_ingreso, '%Y-%m')
--   tenure   = MONTHS_BETWEEN(NVL(fecha_egreso, TODAY), fecha_ingreso)


-- ════════════════════════════════════════════════════════════════════════════
-- #1  PRECISIÓN DEL MODELO  (matriz predicción vs. resultado)
--     "De los que marqué en riesgo el mes pasado, ¿cuántos se fueron?"
--
--     ⚠️ BLOQUEANTE REAL — leer esto antes de implementar:
--     El score NO se guarda. score_engine.py lo calcula en vivo y CLAUDE.md dice
--     explícitamente "el score NO es una foto mensual". No existe tabla de
--     snapshots. Por lo tanto HOY no hay con qué comparar el pasado.
--
--     Hay dos caminos:
--
--     CAMINO A (recomendado, simple, hacia adelante):
--     empezar a guardar una foto mensual del score en wurth.db. Una vez por mes:
--
--         CREATE TABLE IF NOT EXISTS score_snapshot (
--             periodo        TEXT NOT NULL,      -- 'YYYY-MM'
--             id_vendedor    INTEGER NOT NULL,
--             score          REAL NOT NULL,
--             nivel          TEXT NOT NULL,      -- critico/alto/medio/bajo
--             marcado_riesgo INTEGER NOT NULL,   -- 1 si score >= 6
--             PRIMARY KEY (periodo, id_vendedor)
--         );
--         -- al cierre de cada mes, correr score_engine y volcar el resultado:
--         INSERT OR REPLACE INTO score_snapshot
--             SELECT '2026-05', id_vendedor, score, nivel_riesgo,
--                    CASE WHEN score >= 6 THEN 1 ELSE 0 END
--             FROM (<DataFrame de scores del mes, escrito desde Python>);
--
--     Con eso, la matriz del mes siguiente sale de esta query:
--
SELECT
    SUM(CASE WHEN s.marcado_riesgo = 1 AND bajo = 1 THEN 1 ELSE 0 END) AS vp, -- acertado
    SUM(CASE WHEN s.marcado_riesgo = 0 AND bajo = 1 THEN 1 ELSE 0 END) AS fn, -- fuga sorpresa
    SUM(CASE WHEN s.marcado_riesgo = 1 AND bajo = 0 THEN 1 ELSE 0 END) AS fp, -- marcado pero retenido
    SUM(CASE WHEN s.marcado_riesgo = 0 AND bajo = 0 THEN 1 ELSE 0 END) AS vn  -- correcto
FROM score_snapshot s
JOIN (
    -- ¿se fue durante el mes EVALUADO (el mes posterior al snapshot)?
    SELECT v.id_vendedor,
           CASE WHEN v.fecha_egreso IS NOT NULL
                     AND strftime('%Y-%m', v.fecha_egreso) = '2026-06'   -- mes evaluado
                     AND v.motivo_egreso IN ('Renuncia voluntaria','Abandono')
                THEN 1 ELSE 0 END AS bajo
    FROM vendedores v
) b ON b.id_vendedor = s.id_vendedor
WHERE s.periodo = '2026-05';                                            -- snapshot previo

--     Para el sub-dato "fp_intervenidos" (marcados que retuvimos tras intervenir):
SELECT COUNT(DISTINCT s.id_vendedor) AS fp_intervenidos
FROM score_snapshot s
JOIN vendedores v        ON v.id_vendedor = s.id_vendedor
JOIN intervenciones i    ON i.id_vendedor = s.id_vendedor
WHERE s.periodo = '2026-05'
  AND s.marcado_riesgo = 1
  AND v.activo = 1                                  -- no se fue
  AND strftime('%Y-%m', i.fecha) >= '2026-05';      -- hubo intervención en la ventana
--
--     CAMINO B (backfill, más trabajo): como ventas_mensual SÍ guarda el histórico
--     mensual, se puede RECALCULAR el score "como era" en un mes pasado corriendo
--     score_engine con un corte de período (las 3 ventanas hasta ese mes). Si el
--     motor acepta un parámetro "hasta_periodo", se reconstruye la serie histórica
--     sin esperar meses. Es la forma de tener la matriz YA, con datos reales.
-- ════════════════════════════════════════════════════════════════════════════
