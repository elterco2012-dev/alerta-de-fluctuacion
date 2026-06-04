@echo off
cd /d C:\alerta-de-fluctuacion
echo ============================================================
echo  DIAGNOSTICO DE DISTRIBUCION DE SCORES
echo  Muestra cuantos criticos hay y que senal dispara mas.
echo ============================================================
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\diagnostico_distribucion.py
echo.
pause
