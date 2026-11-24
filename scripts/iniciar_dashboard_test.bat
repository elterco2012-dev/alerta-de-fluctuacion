@echo off
:: iniciar_dashboard_test.bat — arranca el tablero en modo TESTING (puerto 8502).
:: Usa C:\alerta-test (copia del repo para probar antes de pasar a producción).
:: No interfiere con el tablero de producción (8501).
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-test
start "" /B %PY64% -m streamlit run C:\alerta-test\dashboard.py ^
    --server.port 8502 ^
    --server.headless true ^
    --server.address 0.0.0.0 ^
    --browser.gatherUsageStats false
