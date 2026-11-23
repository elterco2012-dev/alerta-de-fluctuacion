@echo off
CALL "%~dp0python_paths.bat"
:: %~dp0 es la carpeta donde está este .bat (scripts\)
:: Subimos un nivel para quedar en la raíz del proyecto
cd /d "%~dp0.."
echo Directorio de trabajo: %CD%
echo ============================================================
echo  INICIALIZACION wurth.db (ejecutar solo cuando la base
echo  esta vacia o fue borrada)
echo ============================================================
echo.
%PY32% scripts\inicializar_db.py
echo.
echo ============================================================
echo  Si el script termino sin errores, ejecutar sincronizar_todo.bat
echo ============================================================
pause
