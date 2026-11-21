@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion

echo Guardando snapshot de scores del mes anterior...
%PY64% scripts\snapshot_mensual.py
if errorlevel 1 (
    echo ERROR en snapshot_mensual.py
    exit /b 1
)

echo.
echo Snapshot completado. El historial de scores se actualizó en data\wurth.db
