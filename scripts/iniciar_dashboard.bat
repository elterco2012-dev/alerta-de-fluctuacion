@echo off
:: iniciar_dashboard.bat — arranca el tablero Streamlit de alerta en el puerto 8501.
:: Lo llama la tarea WurthDashboard (al iniciar sesión) y el vigilante cuando el tablero no contesta.
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion
start "" /B %PY64% -m streamlit run dashboard.py ^
    --server.port 8501 ^
    --server.headless true ^
    --server.address 0.0.0.0 ^
    --browser.gatherUsageStats false
