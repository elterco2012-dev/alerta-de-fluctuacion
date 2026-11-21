@echo off
CALL "%~dp0python_paths.bat"
cd /d C:\alerta-de-fluctuacion
echo ============================================================
echo  DIAGNOSTICO DEL [chequeo] de validar_pesos
echo  Encuentra la fila que no reconstruye y por que.
echo ============================================================
echo.
%PY64% -B scripts\diagnostico_chequeo.py
echo.
pause
