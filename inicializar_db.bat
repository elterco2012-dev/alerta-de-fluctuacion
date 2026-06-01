@echo off
echo ============================================================
echo  INICIALIZACION wurth.db (ejecutar solo cuando la base
echo  esta vacia o fue borrada)
echo ============================================================
echo.
C:\Users\aarmoa\AppData\Local\Programs\Python\Python312-32\python.exe scripts\inicializar_db.py
echo.
echo ============================================================
echo  Si el script termino sin errores, ejecutar sincronizar_todo.bat
echo ============================================================
pause
