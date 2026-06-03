@echo off
cd /d C:\alerta-de-fluctuacion

echo Explorando senales nuevas (lift con holdout, solo lectura SQLite)...
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\explorar_senales_nuevas.py
if errorlevel 1 (
    echo ERROR en la exploracion. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
