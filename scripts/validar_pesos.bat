@echo off
cd /d C:\alerta-de-fluctuacion

echo Validando pesos propuestos (holdout temporal, solo lectura SQLite)...
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" -B scripts\validar_pesos.py
if errorlevel 1 (
    echo ERROR en la validacion. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
