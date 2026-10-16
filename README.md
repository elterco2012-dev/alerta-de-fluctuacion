# Würth Argentina — Alerta temprana de rotación de vendedores

Prioriza a qué vendedores conviene **acompañar** antes de que aparezca la
intención de irse. Es una herramienta de apoyo a conversaciones de supervisores:
**no** es un mecanismo de sanción ni de desvinculación, y el score **no** es una
probabilidad de renuncia.

Documentación técnica completa y decisiones de diseño: [`CLAUDE.md`](CLAUDE.md).
Auditoría de octubre 2026 (hallazgos, limitaciones, hoja de ruta):
[`docs/AUDITORIA_2026-10.md`](docs/AUDITORIA_2026-10.md).

## Cómo funciona

```
Informix (ERP) ─┐
Reactor (CRM) ──┼─ scripts/sincronizar_*.py (solo SELECT) ─► data/wurth.db (SQLite)
SUN (cobranza) ─┘                                                  │
                         src/score_engine.py (score 1-10, tendencia 3 meses)
                                                                   │
            dashboard.py + pages/ (Streamlit)   ·   scripts/enviar_alertas.py (Outlook COM)
```

Las tres bases de producción son **solo lectura**. La única base que se escribe
es `data/wurth.db`, que no se commitea.

## Cómo ejecutar (Windows)

| Paso | Comando | Python |
|---|---|---|
| Crear la base / actualizar padrón de vendedores | `inicializar_db.bat` (idempotente) | 32-bit (ODBC) |
| Sincronizar fuentes a mano (padrón + 3 sync) | `sincronizar_todo.bat` | 32-bit (ODBC) |
| Dashboard | `iniciar_dashboard.bat` (`streamlit run dashboard.py`) | 64-bit |
| Automatización diaria (padrón → sync → snapshot → alertas; log en `logs\`) | `scripts\sync_y_alertas.bat` | ambos |
| Probar alertas sin enviar nada | `python scripts\enviar_alertas.py --dry-run` | 64-bit |

## Score de riesgo

`score = 1 + min(suma de pesos activos / 8, 1) × 9`, calculado sobre los últimos
3 meses **cerrados** (el mes en curso no entra). Niveles: 8-10 crítico,
6-7 alto, 4-5 medio, 1-3 bajo. Los niveles son una guía visual; la acción
operativa es **por ranking** (empezar por los de mayor score de cada zona).

Señales activas (umbrales vigentes; la clave interna `descripcion=` del motor
conserva textos viejos a propósito, ver CLAUDE.md):

| Señal | Peso | Se enciende cuando |
|---|---|---|
| Plan bajo | 2.0 | promedio % plan 3 meses (solo meses con plan) < 55 |
| Ausencias tempranas | 2.0 | > 2 días/mes no vacacionales, solo meses 1-3 (promedio sobre los meses con dato de Reactor) |
| Ventana crítica 1-3 | 1.5 | antigüedad 1-3 meses |
| Grupo con alta rotación | 1.5 | `riesgo_base` del grupo > 0.40 |
| Balanza de clientes negativa | 1.5 | 2 meses negativos y suma < −60 |
| Ventana crítica 4-6 | 1.0 | antigüedad 4-6 meses |
| Ticket cayendo | 1.0 | pendiente > 5 %/mes del promedio |
| Sin acompañamiento del supervisor | 1.0 | < 1 visita/mes, solo meses 1-6 |
| Sin clientes nuevos | 0.5 | 0 nuevos en los últimos 2 meses |

Deshabilitadas (peso 0, no suman): caída de plan, días sin venta, cartera
activa, cobranza, llamadas y visitas. No distinguían egresados de activos por
problemas de cobertura de datos (detalle en CLAUDE.md).

## Validación y diagnóstico (solo lectura sobre `data/wurth.db`)

| Script | Para qué |
|---|---|
| `scripts\chequeo_integridad.bat` | Conteos de problemas de datos: meses futuros/parciales, activos sin ventas, altas no sincronizadas, egresados sin motivo, etc. |
| `scripts\evaluar_ranking.bat` | ¿El ranking anticipa bajas a 30/60/90 días? Precisión@K, lift vs. azar, AUC, comparado con antigüedad, plan, caída de venta y grupo (sin fuga temporal) |
| `scripts\validar_pesos.bat` | Barrido de `RIESGO_REFERENCIA` y auditoría por señal (ver caveats en la auditoría) |
| `scripts\backfill_scores.bat` | Recalcula `score_historico` de los últimos 18 meses |

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Los tests usan SQLite temporales con datos sintéticos: nunca tocan producción,
`data/wurth.db` ni envían correos.

## Limitaciones conocidas (resumen)

- El ranking todavía no fue validado con el método point-in-time sobre datos
  reales: correr `evaluar_ranking.bat` antes de sacar conclusiones.
- El riesgo histórico del grupo (`riesgo_base`) usa todas las bajas, también
  las posteriores a cada mes del backfill: la validación histórica es optimista.
- `motivo_egreso` no se carga: las "bajas" mezclan renuncias y despidos.
- La identidad del usuario no está autenticada (selector + `?usuario=`).

Detalle, evidencia y propuestas: [`docs/AUDITORIA_2026-10.md`](docs/AUDITORIA_2026-10.md).
