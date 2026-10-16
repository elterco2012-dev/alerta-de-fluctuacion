@echo off
cd /d C:\alerta-de-fluctuacion

echo Evaluando el ranking point-in-time (precision@K, lift vs azar; solo lectura SQLite)...
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" -B scripts\evaluar_ranking.py %*
if errorlevel 1 (
    echo ERROR. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
