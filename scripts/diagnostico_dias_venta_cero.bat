@echo off
cd /d C:\alerta-de-fluctuacion

echo Diagnostico de dias venta cero (Informix, solo lectura)...
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\diagnostico_dias_venta_cero.py
if errorlevel 1 (
    echo ERROR en el diagnostico. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
