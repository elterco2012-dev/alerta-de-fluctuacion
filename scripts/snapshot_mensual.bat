@echo off
cd /d C:\alerta-de-fluctuacion

echo Guardando snapshot de scores del mes anterior...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\snapshot_mensual.py
if errorlevel 1 (
    echo ERROR en snapshot_mensual.py
    exit /b 1
)

echo.
echo Snapshot completado. El historial de scores se actualizó en data\wurth.db
