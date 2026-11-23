@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion
echo ============================================================
echo  DISTRIBUCION DE VALORES DE SEÑALES — para calibrar umbrales
echo  Muestra en que valor esta cada vendedor y que % dispara
echo  a distintos umbrales.
echo ============================================================
echo.
%PY64% scripts\diagnostico_valores.py
echo.
pause
