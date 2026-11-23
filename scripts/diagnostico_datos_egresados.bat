@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion

echo Diagnostico de completitud de datos (activos vs egresados)...
echo.
%PY64% scripts\diagnostico_datos_egresados.py
if errorlevel 1 (
    echo ERROR en el diagnostico. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
