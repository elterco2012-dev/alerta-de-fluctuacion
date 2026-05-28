@echo off
cd /d C:\alerta-de-fluctuacion

echo [1/2] Sincronizando Informix...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\sincronizar_informix.py
if errorlevel 1 (
    echo ERROR en sincronizacion. Abortando.
    exit /b 1
)

echo.
echo [2/2] Verificando alertas email...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\enviar_alertas.py

echo.
echo Proceso completo.
