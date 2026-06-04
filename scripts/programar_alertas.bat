@echo off
REM ============================================================
REM  programar_alertas.bat
REM  Registra una tarea programada de Windows que corre
REM  sync_y_alertas.bat todos los dias a las 08:00.
REM
REM  Ejecutar UNA SOLA VEZ (doble clic). Si dice "Acceso
REM  denegado", clic derecho > Ejecutar como administrador.
REM ============================================================

echo ============================================================
echo  Registrando tarea programada de Windows
echo ============================================================
echo  Nombre : WurthAlertas
echo  Script : C:\alerta-de-fluctuacion\scripts\sync_y_alertas.bat
echo  Horario: todos los dias a las 08:00
echo ============================================================
echo.

REM NOTA: hay que abrir este .bat como Administrador (clic derecho > Ejecutar como admin).
REM Se usa "cmd /c" para lanzar el .bat porque schtasks no acepta .bat directo.
REM /F = sobrescribe si ya existe
schtasks /Create /TN WurthAlertas /TR "cmd /c C:\alerta-de-fluctuacion\scripts\sync_y_alertas.bat" /SC DAILY /ST 08:00 /F

echo.
if errorlevel 1 goto :error

echo ============================================================
echo  Tarea creada OK.
echo.
echo  IMPORTANTE: la tarea corre solo cuando estas logueado en
echo  Windows (lo necesita Outlook COM). Si la PC esta apagada o
echo  con sesion cerrada a las 08:00, no se ejecuta.
echo.
echo  Probarla ahora:   schtasks /Run /TN "WurthAlertas"
echo  Verla:            schtasks /Query /TN "WurthAlertas"
echo  Borrarla:         schtasks /Delete /TN "WurthAlertas" /F
echo ============================================================
goto :fin

:error
echo ============================================================
echo  ERROR al crear la tarea.
echo  Proba de nuevo con clic derecho ^> Ejecutar como administrador.
echo ============================================================

:fin
echo.
pause
