@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion

echo Explorando columnas reales de sbas (Informix, solo lectura)...
echo.
%PY32% scripts\explorar_sbas_columnas.py
if errorlevel 1 (
    echo ERROR. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
