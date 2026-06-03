@echo off
cd /d C:\alerta-de-fluctuacion

echo Diagnostico de grupos quemados (hipotesis central, solo lectura SQLite)...
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\diagnostico_grupos_quemados.py
if errorlevel 1 (
    echo ERROR en el diagnostico. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
