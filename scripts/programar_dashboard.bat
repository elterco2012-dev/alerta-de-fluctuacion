@echo off
:: programar_dashboard.bat — registra la tarea WurthAlertasTablero, que deja el tablero de produccion (puerto 8501)
:: siempre andando: corre scripts\supervisor_dashboard.py con pythonw y con la misma cuenta que WurthAlertas,
:: sin guardar su contrasena (S4U). Corre aunque nadie tenga la sesion iniciada en la VM, tambien despues de un
:: reinicio. Nada corre como SYSTEM. Se dispara al arrancar la VM y cada 15 minutos: si el supervisor ya esta
:: andando el disparo se ignora, y si se cayo lo vuelve a levantar.
:: La cuenta necesita el derecho "Iniciar sesion como proceso por lotes" (los administradores lo tienen).
::
:: Solo toca su propia tarea. Si ya existe una tarea WurthAlertasTablero que no corre este supervisor, no hace
:: nada: en la VM hay tareas de otros proyectos (el 23/11 este script uso el nombre WurthDashboard, que es de
:: taginfo, y la piso). Antes de crear una tarea nueva, mirar inventario.md de conocimiento-wurth.
::
:: Ejecutar como administrador (clic derecho > Ejecutar como administrador), despues de proteger_carpeta.bat.
setlocal
set "RAIZ=C:\alerta-de-fluctuacion"
set "SUPERVISOR=%RAIZ%\scripts\supervisor_dashboard.py"
set "TAREA=WurthAlertasTablero"

net session >NUL 2>&1
if errorlevel 1 (
    echo  Hay que ejecutarlo como administrador: clic derecho ^> Ejecutar como administrador.
    goto :fin
)

CALL "%RAIZ%\scripts\python_paths.bat"
set "PYEXE="
for /f "delims=" %%p in ('%PY64% -c "import sys; print(sys.executable)"') do set "PYEXE=%%p"
if not defined PYEXE (
    echo  No encontre el Python de 64 bits ^(py -3.12-64^).
    goto :fin
)
set "PYW=%PYEXE:python.exe=pythonw.exe%"
if not exist "%PYW%" (
    echo  No encontre el Python de 64 bits sin ventana: "%PYW%"
    goto :fin
)

echo ============================================================
echo  Registrando el tablero de Alertas de Rotacion (%TAREA%)
echo ============================================================
echo.

powershell -NoProfile -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "$existente = Get-ScheduledTask -TaskName $env:TAREA -ErrorAction SilentlyContinue;" ^
  "if ($existente -and -not (($existente.Actions.Arguments -join ' ') -like '*supervisor_dashboard.py*')) { throw ('Ya existe una tarea ' + $env:TAREA + ' que no es de este proyecto. No la toque.') };" ^
  "if ($existente) { Stop-ScheduledTask -TaskName $env:TAREA };" ^
  "Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue };" ^
  "$cuenta = (Get-ScheduledTask -TaskName 'WurthAlertas').Principal.UserId;" ^
  "$q = [char]34;" ^
  "$a = New-ScheduledTaskAction -Execute ($q + $env:PYW + $q) -Argument ($q + $env:SUPERVISOR + $q) -WorkingDirectory $env:RAIZ;" ^
  "$t1 = New-ScheduledTaskTrigger -AtStartup; $t1.Delay = 'PT1M';" ^
  "$t2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650);" ^
  "$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries;" ^
  "$p = New-ScheduledTaskPrincipal -UserId $cuenta -LogonType S4U -RunLevel Limited;" ^
  "Register-ScheduledTask -TaskName $env:TAREA -Action $a -Trigger $t1,$t2 -Settings $s -Principal $p -Force | Out-Null;" ^
  "Write-Host (' [OK] ' + $env:TAREA + ', con la cuenta ' + $cuenta + ' (sin SYSTEM)')"
if errorlevel 1 goto :error

schtasks /Run /TN "%TAREA%" >NUL
echo  Arrancando el tablero (puede tardar hasta un minuto)...
set INTENTOS=0
:esperar
ping -n 11 127.0.0.1 >NUL
curl.exe --noproxy "*" -sf -o NUL --max-time 10 http://127.0.0.1:8501/_stcore/health
if not errorlevel 1 goto :responde
set /a INTENTOS+=1
if %INTENTOS% LSS 6 goto :esperar

echo  El tablero todavia no responde. Mira %RAIZ%\data\vigilante.log y %RAIZ%\data\streamlit.log
powershell -NoProfile -Command "$h = '{0:X8}' -f (Get-ScheduledTaskInfo -TaskName $env:TAREA).LastTaskResult; Write-Host (' Estado de la tarea: ' + (Get-ScheduledTask -TaskName $env:TAREA).State + ', resultado 0x' + $h); if ($h -eq '80070569') { Write-Host ' A la cuenta le falta el derecho Iniciar sesion como proceso por lotes.' }"
goto :final

:responde
echo  [OK] El tablero responde en el puerto 8501.

:final
echo.
echo  Lo que hace el supervisor queda en %RAIZ%\data\vigilante.log
goto :fin

:error
echo.
echo  ERROR. Lee el mensaje de arriba. Revisa tambien que exista la tarea WurthAlertas y que lo hayas corrido como administrador.

:fin
echo.
pause
