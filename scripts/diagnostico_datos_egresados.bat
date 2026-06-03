@echo off
cd /d C:\alerta-de-fluctuacion

echo Diagnostico de completitud de datos (activos vs egresados)...
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\diagnostico_datos_egresados.py
if errorlevel 1 (
    echo ERROR en el diagnostico. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
