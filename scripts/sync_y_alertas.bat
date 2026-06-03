@echo off
cd /d C:\alerta-de-fluctuacion

echo [1/5] Sincronizando Informix...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\sincronizar_informix.py
if errorlevel 1 (
    echo ERROR en sincronizacion Informix. Abortando.
    exit /b 1
)

echo.
echo [2/5] Sincronizando Reactor CRM (actividad, ausencias, acompanamiento)...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\sincronizar_reactor.py
if errorlevel 1 (
    echo AVISO: fallo el sync de Reactor. Continuo con el resto.
)

echo.
echo [3/5] Sincronizando SUNDB (cobranza real)...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\sincronizar_sundb.py
if errorlevel 1 (
    echo AVISO: fallo el sync de SUNDB. Continuo con el resto.
)

echo.
echo [4/5] Guardando snapshot de scores del mes...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\snapshot_mensual.py

echo.
echo [5/5] Verificando alertas email...
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\enviar_alertas.py

echo.
echo Proceso completo.
