@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion

echo [1/5] Sincronizando Informix...
%PY32% scripts\sincronizar_informix.py
if errorlevel 1 (
    echo ERROR en sincronizacion Informix. Abortando.
    exit /b 1
)

echo.
echo [2/5] Sincronizando Reactor CRM (actividad, ausencias, acompanamiento)...
%PY32% scripts\sincronizar_reactor.py
if errorlevel 1 (
    echo AVISO: fallo el sync de Reactor. Continuo con el resto.
)

echo.
echo [3/5] Sincronizando SUNDB (cobranza real)...
%PY32% scripts\sincronizar_sundb.py
if errorlevel 1 (
    echo AVISO: fallo el sync de SUNDB. Continuo con el resto.
)

echo.
echo [4/5] Guardando snapshot de scores del mes...
%PY64% scripts\snapshot_mensual.py

echo.
echo [5/5] Verificando alertas email...
%PY64% scripts\enviar_alertas.py

echo.
echo Proceso completo.
