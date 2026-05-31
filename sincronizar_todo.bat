@echo off
echo ============================================================
echo  SINCRONIZACION MENSUAL - Wurth Alertas
echo ============================================================
echo.
echo [1/3] Sincronizando Reactor CRM (llamadas, visitas, ausencias)...
C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe scripts\sincronizar_reactor.py
echo.
echo [2/3] Sincronizando Informix (balanza clientes + ventas + plan)...
C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe scripts\sincronizar_informix.py
echo.
echo [3/3] Sincronizando SUN DB (cobranza real)...
C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe scripts\sincronizar_sundb.py
echo.
echo ============================================================
echo  Listo. Podés abrir el dashboard con iniciar_dashboard.bat
echo ============================================================
pause
