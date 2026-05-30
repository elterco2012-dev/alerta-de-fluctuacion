@echo off
echo ============================================================
echo  SINCRONIZACION MENSUAL - Wurth Alertas
echo ============================================================
echo.
echo [1/2] Sincronizando Reactor CRM (llamadas, visitas, ausencias)...
C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe scripts\sincronizar_reactor.py
echo.
echo [2/2] Sincronizando Informix (balanza de clientes)...
C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe scripts\sincronizar_informix.py
echo.
echo ============================================================
echo  Listo. Podés abrir el dashboard con iniciar_dashboard.bat
echo ============================================================
pause
