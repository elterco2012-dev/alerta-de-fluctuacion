@echo off
cd /d C:\alerta-de-fluctuacion
echo ============================================================
echo  DISTRIBUCION DE VALORES DE SEÑALES — para calibrar umbrales
echo  Muestra en que valor esta cada vendedor y que % dispara
echo  a distintos umbrales.
echo ============================================================
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\diagnostico_valores.py
echo.
pause
