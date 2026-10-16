@echo off
cd /d C:\alerta-de-fluctuacion

echo Chequeo de integridad de data\\wurth.db (solo lectura, solo conteos)...
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" -B scripts\chequeo_integridad.py %*
if errorlevel 1 (
    echo ERROR. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
