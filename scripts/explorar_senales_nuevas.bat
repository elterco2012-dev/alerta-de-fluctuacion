@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion

echo Explorando senales nuevas (lift con holdout, solo lectura SQLite)...
echo.
%PY64% scripts\explorar_senales_nuevas.py
if errorlevel 1 (
    echo ERROR en la exploracion. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
