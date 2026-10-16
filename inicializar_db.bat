@echo off
echo ============================================================
echo  PADRON DE VENDEDORES / INICIALIZACION wurth.db
echo  (idempotente: tambien corre a diario dentro de sync_y_alertas.bat)
echo ============================================================
echo.
C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe scripts\inicializar_db.py
echo.
echo ============================================================
echo  Si el script termino sin errores, ejecutar sincronizar_todo.bat
echo ============================================================
pause
