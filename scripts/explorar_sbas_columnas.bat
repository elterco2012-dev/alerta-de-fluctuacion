@echo off
cd /d C:\alerta-de-fluctuacion

echo Explorando columnas reales de sbas (Informix, solo lectura)...
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe" scripts\explorar_sbas_columnas.py
if errorlevel 1 (
    echo ERROR. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
