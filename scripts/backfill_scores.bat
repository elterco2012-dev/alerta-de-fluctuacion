@echo off
cd /d C:\alerta-de-fluctuacion

echo Calculando backfill historico de scores (ultimos 18 meses)...
echo Esto puede tardar varios minutos.
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" -B scripts\backfill_scores.py
if errorlevel 1 (
    echo ERROR en backfill. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
echo Listo. Ya podes abrir la pantalla "Precision del modelo" en el dashboard.
pause
