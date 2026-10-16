@echo off
REM ============================================================================
REM  Automatizacion diaria: padron + sync (Python 32-bit, ODBC) -> snapshot -> alertas
REM  (Python 64-bit). Corta ante el PRIMER error: si una fuente falla, ese dia
REM  no salen alertas (mejor sin alertas que alertas con datos rotos o viejos).
REM  Toda la salida queda en logs\sync_y_alertas_AAAAMMDD_HHMM.log
REM ============================================================================
setlocal
cd /d C:\alerta-de-fluctuacion

set "PY32=C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe"
set "PY64=C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe"
REM Sin esto, los caracteres no ASCII de los print rompen al redirigir a archivo.
set "PYTHONUTF8=1"

if not exist logs mkdir logs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmm"') do set "TS=%%i"
set "LOG=logs\sync_y_alertas_%TS%.log"

echo Corriendo... log en %LOG%
call :pipeline > "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
    echo Proceso completo. Ver %LOG%
) else (
    echo ERROR: el proceso se corto en el paso %RC%. No se enviaron alertas. Ver %LOG%
)
exit /b %RC%

:pipeline
echo [%date% %time%] Inicio

echo [1/6] Padron de vendedores desde f040 - altas, bajas, cambios de grupo y supervisor...
"%PY32%" scripts\inicializar_db.py || (echo ERROR actualizando el padron de vendedores & exit /b 1)

echo.
echo [2/6] Sincronizando Informix...
"%PY32%" scripts\sincronizar_informix.py || (echo ERROR en sincronizacion Informix & exit /b 2)

echo.
echo [3/6] Sincronizando Reactor CRM - actividad, ausencias, acompanamiento...
"%PY32%" scripts\sincronizar_reactor.py || (echo ERROR en sincronizacion Reactor & exit /b 3)

echo.
echo [4/6] Sincronizando SUNDB - cobranza real...
"%PY32%" scripts\sincronizar_sundb.py || (echo ERROR en sincronizacion SUNDB & exit /b 4)

echo.
echo [5/6] Guardando snapshot de scores del mes - Python 64-bit, solo lee SQLite...
"%PY64%" scripts\snapshot_mensual.py || (echo ERROR en snapshot_mensual & exit /b 5)

echo.
echo [6/6] Verificando alertas email...
"%PY64%" scripts\enviar_alertas.py || (echo ERROR en enviar_alertas & exit /b 6)

echo.
echo [%date% %time%] Fin OK
exit /b 0
