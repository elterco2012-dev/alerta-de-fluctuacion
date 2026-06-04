@echo off
cd /d C:\alerta-de-fluctuacion
echo ============================================================
echo  DIAGNOSTICO DEL [chequeo] de validar_pesos
echo  Encuentra la fila que no reconstruye y por que.
echo ============================================================
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" -B scripts\diagnostico_chequeo.py
echo.
pause
