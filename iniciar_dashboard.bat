@echo off
CALL "%~dp0scripts\python_paths.bat"
cd /d "%~dp0"

:: Puerto fijo 8501 (coordinado con los demás proyectos de la VM).
:: Escucha en todas las interfaces de la red interna — gerencia y supervisores
:: se conectan desde sus PCs.
:: NUNCA publicar en internet: el firewall debe tener el 8501 abierto solo
:: para la red interna de Würth (solicitarlo a Sistemas).
%PY64% -m streamlit run "%~dp0dashboard.py" ^
  --server.port 8501 ^
  --server.headless true

pause
