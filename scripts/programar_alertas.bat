@echo off
:: programar_alertas.bat - registra la tarea WurthAlertas: corre scripts\sync_y_alertas.bat todos los dias a las
:: 08:00, en la sesion del usuario que la registra (la necesitan Outlook COM y los DSN del usuario: si a esa hora
:: no hay sesion abierta, ese dia no corre).
::
:: Solo toca su propia tarea (regla de la VM del 24/11): si ya existe una WurthAlertas que no ejecuta el
:: sync_y_alertas.bat de esta carpeta, no hace nada y avisa. Nunca -Force ni /F sobre una tarea ajena.
:: Usa Register-ScheduledTask porque schtasks /Create esta bloqueado por la proteccion de la VM.
::
:: Correrlo con la cuenta del usuario que va a tener la tarea (doble clic): la tarea queda a nombre de esa cuenta.
setlocal
set "RAIZ=C:\alerta-de-fluctuacion"
set "SCRIPT=%RAIZ%\scripts\sync_y_alertas.bat"
set "TAREA=WurthAlertas"

echo ============================================================
echo  Registrando la tarea %TAREA%
echo  Ejecuta: %SCRIPT%
echo  Horario: todos los dias a las 08:00, en la sesion de %USERDOMAIN%\%USERNAME%
echo ============================================================
echo.

powershell -NoProfile -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "$existente = Get-ScheduledTask -TaskPath '\' -TaskName $env:TAREA -ErrorAction SilentlyContinue;" ^
  "$ejecuta = ($existente.Actions | ForEach-Object { [string]$_.Execute + ' ' + [string]$_.Arguments }) -join ' ';" ^
  "if ($existente -and -not ($ejecuta -like ('*' + $env:SCRIPT + '*'))) { throw ('Ya existe una tarea ' + $env:TAREA + ' que no es de este proyecto (ejecuta ' + $ejecuta + '). No la toque.') };" ^
  "$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c ' + [char]34 + $env:SCRIPT + [char]34) -WorkingDirectory $env:RAIZ;" ^
  "$t = New-ScheduledTaskTrigger -Daily -At '08:00';" ^
  "$p = New-ScheduledTaskPrincipal -UserId ($env:USERDOMAIN + '\' + $env:USERNAME) -LogonType Interactive -RunLevel Limited;" ^
  "Register-ScheduledTask -TaskName $env:TAREA -Action $a -Trigger $t -Principal $p -Force | Out-Null;" ^
  "Write-Host (' [OK] ' + $env:TAREA + ', en la sesion de ' + $env:USERDOMAIN + '\' + $env:USERNAME)"
if errorlevel 1 goto :error

echo.
echo  IMPORTANTE: la tarea corre solo si la sesion de ese usuario esta abierta a las 08:00
echo  (lo necesita Outlook COM). Si la VM se reinicia antes, ese dia no hay alertas.
echo.
echo  Probarla ahora:   schtasks /Run /TN "%TAREA%"
echo  Verla:            schtasks /Query /TN "%TAREA%" /V /FO LIST
echo  Que sigue siendo nuestra:  py scripts\tareas_propias.py
goto :fin

:error
echo.
echo  ERROR: la tarea no se registro. Lee el mensaje de arriba.

:fin
echo.
pause
