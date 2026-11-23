@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion
echo ============================================================
echo  DIAGNOSTICO DE DISTRIBUCION DE SCORES
echo  Muestra cuantos criticos hay y que senal dispara mas.
echo ============================================================
echo.
%PY64% scripts\diagnostico_distribucion.py
echo.
pause
