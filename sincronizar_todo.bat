@echo off
REM Sincronizacion manual de las 3 fuentes. Corta ante el primer error.
setlocal
cd /d C:\alerta-de-fluctuacion
set "PY32=C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe"
set "PYTHONUTF8=1"
echo ============================================================
echo  SINCRONIZACION - Wurth Alertas
echo ============================================================
echo.
echo [1/3] Sincronizando Informix (balanza clientes + ventas + plan)...
"%PY32%" scripts\sincronizar_informix.py || goto :error
echo.
echo [2/3] Sincronizando Reactor CRM (llamadas, visitas, ausencias)...
"%PY32%" scripts\sincronizar_reactor.py || goto :error
echo.
echo [3/3] Sincronizando SUN DB (cobranza real)...
"%PY32%" scripts\sincronizar_sundb.py || goto :error
echo.
echo ============================================================
echo  Listo. Podes abrir el dashboard con iniciar_dashboard.bat
echo ============================================================
pause
exit /b 0

:error
echo.
echo ============================================================
echo  ERROR: la sincronizacion se corto. Revisa el mensaje de arriba.
echo  Los pasos siguientes NO se ejecutaron.
echo ============================================================
pause
exit /b 1
