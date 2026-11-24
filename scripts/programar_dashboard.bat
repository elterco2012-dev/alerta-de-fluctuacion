@echo off
:: programar_dashboard.bat — registra la tarea WurthDashboard, que deja el tablero de produccion (puerto 8501)
:: siempre andando: corre scripts\supervisor_dashboard.py con pythonw y con la misma cuenta que WurthAlertas,
:: sin guardar su contrasena (S4U). Corre aunque nadie tenga la sesion iniciada en la VM, tambien despues de un
:: reinicio. Nada corre como SYSTEM. Se dispara al arrancar la VM y cada 15 minutos: si el supervisor ya esta
:: andando el disparo se ignora, y si se cayo lo vuelve a levantar.
:: La cuenta necesita el derecho "Iniciar sesion como proceso por lotes" (los administradores lo tienen).
:: Borra tambien WurthDashboard-Vigilante, la tarea vieja que corria como SYSTEM.
::
:: Ejecutar como administrador (clic derecho > Ejecutar como administrador), despues de proteger_carpeta.bat.
setlocal
set "RAIZ=C:\alerta-de-fluctuacion"
set "SUPERVISOR=%RAIZ%\scripts\supervisor_dashboard.py"

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
echo  Registrando el tablero de Alertas de Rotacion
echo ============================================================
echo.

:: Frena el tablero actual (y cualquier otro que ocupe el 8501) antes de reemplazar la tarea
schtasks /End /TN "WurthDashboard" >NUL 2>&1

powershell -NoProfile -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "Unregister-ScheduledTask -TaskName 'WurthDashboard-Vigilante' -Confirm:$false -ErrorAction SilentlyContinue;" ^
  "Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue };" ^
  "$cuenta = (Get-ScheduledTask -TaskName 'WurthAlertas').Principal.UserId;" ^
  "$q = [char]34;" ^
  "$a = New-ScheduledTaskAction -Execute ($q + $env:PYW + $q) -Argument ($q + $env:SUPERVISOR + $q) -WorkingDirectory $env:RAIZ;" ^
  "$t1 = New-ScheduledTaskTrigger -AtStartup; $t1.Delay = 'PT1M';" ^
  "$t2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650);" ^
  "$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries;" ^
  "$p = New-ScheduledTaskPrincipal -UserId $cuenta -LogonType S4U -RunLevel Limited;" ^
  "Register-ScheduledTask -TaskName 'WurthDashboard' -Action $a -Trigger $t1,$t2 -Settings $s -Principal $p -Force | Out-Null;" ^
  "Write-Host (' [OK] WurthDashboard, con la cuenta ' + $cuenta + ' (sin SYSTEM)')"
if errorlevel 1 goto :error

schtasks /Run /TN "WurthDashboard" >NUL
echo  Arrancando el tablero (unos 20 segundos)...
ping -n 21 127.0.0.1 >NUL
curl.exe --noproxy "*" -sf -o NUL --max-time 20 http://127.0.0.1:8501/_stcore/health
if errorlevel 1 (
    echo  El tablero todavia no responde. Mira %RAIZ%\data\vigilante.log y %RAIZ%\data\streamlit.log
    powershell -NoProfile -Command "$h = '{0:X8}' -f (Get-ScheduledTaskInfo -TaskName 'WurthDashboard').LastTaskResult; Write-Host (' Resultado de la tarea: 0x' + $h); if ($h -eq '80070569') { Write-Host ' A la cuenta le falta el derecho Iniciar sesion como proceso por lotes.' }"
) else (
    echo  [OK] El tablero responde en el puerto 8501.
)
echo.
echo  Lo que hace el supervisor queda en %RAIZ%\data\vigilante.log
goto :fin

:error
echo.
echo  ERROR. Revisa que exista la tarea WurthAlertas y que lo hayas corrido como administrador.

:fin
echo.
pause
