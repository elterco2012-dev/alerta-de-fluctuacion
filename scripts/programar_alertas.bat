@echo off
REM ============================================================
REM  programar_alertas.bat
REM  Registra una tarea programada de Windows que corre
REM  sync_y_alertas.bat todos los dias a las 08:00.
REM
REM  Ejecutar UNA SOLA VEZ (doble clic). Si dice "Acceso
REM  denegado", clic derecho > Ejecutar como administrador.
REM ============================================================

set TAREA=Wurth - Alertas Rotacion
set SCRIPT=C:\alerta-de-fluctuacion\scripts\sync_y_alertas.bat
set HORA=08:00

echo ============================================================
echo  Registrando tarea programada de Windows
echo ============================================================
echo  Nombre : %TAREA%
echo  Script : %SCRIPT%
echo  Horario: todos los dias a las %HORA%
echo ============================================================
echo.

REM /IT  = corre en la sesion interactiva del usuario (NECESARIO para
REM        que Outlook COM y los DSN ODBC del usuario funcionen).
REM /RL LIMITED = privilegios normales (misma integridad que Outlook).
REM /F   = sobrescribe si ya existe.
schtasks /Create ^
  /TN "%TAREA%" ^
  /TR "\"%SCRIPT%\"" ^
  /SC DAILY ^
  /ST %HORA% ^
  /IT ^
  /RL LIMITED ^
  /F

echo.
if errorlevel 1 (
  echo ============================================================
  echo  ERROR al crear la tarea.
  echo  Proba de nuevo con clic derecho ^> Ejecutar como administrador.
  echo ============================================================
) else (
  echo ============================================================
  echo  Tarea creada OK.
  echo
  echo  IMPORTANTE: la tarea corre solo cuando estas logueado en
  echo  Windows (lo necesita Outlook COM). Si la PC esta apagada o
  echo  con sesion cerrada a las %HORA%, no se ejecuta.
  echo
  echo  Para verla / editar la hora:
  echo    Programador de tareas ^> Biblioteca ^> "%TAREA%"
  echo
  echo  Para probarla ahora mismo sin esperar:
  echo    schtasks /Run /TN "%TAREA%"
  echo
  echo  Para borrarla:
  echo    schtasks /Delete /TN "%TAREA%" /F
  echo ============================================================
)
echo.
pause
