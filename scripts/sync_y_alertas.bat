@echo off
cd /d C:\alerta-de-fluctuacion

echo [1/3] Sincronizando Informix...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\sincronizar_informix.py
if errorlevel 1 (
    echo ERROR en sincronizacion. Abortando.
    exit /b 1
)

echo.
echo [2/3] Guardando snapshot de scores del mes...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\snapshot_mensual.py

echo.
echo [3/3] Verificando alertas email...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\enviar_alertas.py

echo.
echo Proceso completo.
