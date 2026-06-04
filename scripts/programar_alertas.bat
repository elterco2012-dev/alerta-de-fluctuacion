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
echo  Nombre : Wurth - Alertas Rotacion
echo  Script : C:\alerta-de-fluctuacion\scripts\sync_y_alertas.bat
echo  Horario: todos los dias a las 08:00
echo ============================================================
echo.

REM /IT = corre en la sesion interactiva (necesario para Outlook COM y DSN ODBC)
REM /RL LIMITED = privilegios normales (misma integridad que Outlook)
REM /F = sobrescribe si ya existe
schtasks /Create /TN "Wurth - Alertas Rotacion" /TR "\"C:\alerta-de-fluctuacion\scripts\sync_y_alertas.bat\"" /SC DAILY /ST 08:00 /IT /RL LIMITED /F

echo.
if errorlevel 1 goto :error

echo ============================================================
echo  Tarea creada OK.
echo.
echo  IMPORTANTE: la tarea corre solo cuando estas logueado en
echo  Windows (lo necesita Outlook COM). Si la PC esta apagada o
echo  con sesion cerrada a las 08:00, no se ejecuta.
echo.
echo  Probarla ahora:   schtasks /Run /TN "Wurth - Alertas Rotacion"
echo  Verla:            schtasks /Query /TN "Wurth - Alertas Rotacion"
echo  Borrarla:         schtasks /Delete /TN "Wurth - Alertas Rotacion" /F
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
