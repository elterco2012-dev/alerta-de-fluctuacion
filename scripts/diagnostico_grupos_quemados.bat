@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion

echo Diagnostico de grupos quemados (hipotesis central, solo lectura SQLite)...
echo.
%PY64% scripts\diagnostico_grupos_quemados.py
if errorlevel 1 (
    echo ERROR en el diagnostico. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
