@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion

echo Validando pesos propuestos (holdout temporal, solo lectura SQLite)...
echo.
%PY64% -B scripts\validar_pesos.py
if errorlevel 1 (
    echo ERROR en la validacion. Revisa el output de arriba.
    pause
    exit /b 1
)

echo.
pause
