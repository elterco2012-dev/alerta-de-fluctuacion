# Wurth — Sistema de Alertas Tempranas de Rotación

## Estructura del proyecto
```
wurth_rotacion/
├── data/
│   └── wurth.db              ← SQLite simulada (reemplazar por Informix el lunes)
├── src/
│   └── score_engine.py       ← Motor de scoring (score 1-10 por vendedor)
├── scripts/
│   └── generar_datos_simulados.py
├── dashboard.py              ← App Streamlit
└── requirements.txt
```

## Cómo ejecutar
```bash
pip install -r requirements.txt
python scripts/generar_datos_simulados.py   # solo primera vez
streamlit run dashboard.py
```

## El lunes — conectar Informix
En `src/score_engine.py`, función `get_connection()`:
```python
import pyodbc
conn_str = (
    "DRIVER={IBM INFORMIX ODBC DRIVER};"
    "SERVER=<servidor>;"
    "DATABASE=<base>;"
    "HOST=<host>;"
    "UID=<usuario>;"
    "PWD=<password>;"
)
return pyodbc.connect(conn_str)
```
Reemplazar también las queries SQL con los nombres reales de tablas de Informix.

## Score de riesgo (1-10)
| Score | Nivel    | Acción sugerida              |
|-------|----------|------------------------------|
| 8-10  | Crítico  | Reunión supervisor esta semana |
| 6-7   | Alto     | Seguimiento activo           |
| 4-5   | Medio    | Monitoreo mensual            |
| 1-3   | Bajo     | Seguimiento normal           |

## Señales que componen el score
- % Plan cayendo 3 meses seguidos (peso 2.5)
- % Plan < 80% promedio (peso 2.0)
- Días venta cero > 3 (peso 1.5)
- < 60% cartera activa (peso 1.5)
- Grupo con alta rotación histórica (peso 1.5)
- Ventana crítica mes 1-3 (peso 1.5)
- Ventana crítica mes 4-6 (peso 1.0)
- Cobranza real < 90% teórica (peso 1.0)
- Sin clientes nuevos 2 meses (peso 0.5)
