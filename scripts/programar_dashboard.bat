@echo off
:: programar_dashboard.bat — registra dos tareas en el Programador de Windows:
::   WurthDashboard        : arranca el tablero cuando el usuario inicia sesión
::   WurthDashboard-Vigilante : comprueba cada 2 minutos que el tablero sigue vivo
::
:: Ejecutar UNA SOLA VEZ (clic derecho > Ejecutar como administrador).

echo ============================================================
echo  Registrando tareas del tablero de Alertas de Rotación
echo ============================================================
echo.

:: ── Tarea 1: arranque al iniciar sesión ──────────────────────
schtasks /Create /TN "WurthDashboard" ^
    /TR "cmd /c C:\alerta-de-fluctuacion\scripts\iniciar_dashboard.bat" ^
    /SC ONLOGON /DELAY 0001:00 /F
if errorlevel 1 goto :error
echo  [OK] WurthDashboard — arranca al iniciar sesión (con 1 min de demora)
echo.

:: ── Tarea 2: vigilante cada 2 minutos ────────────────────────
:: Se usa Register-ScheduledTask (PowerShell) porque schtasks no tiene
:: ExecutionTimeLimit=0 ni repetición cada 2 min en una sola línea.
powershell -NoProfile -Command ^
  "$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c C:\alerta-de-fluctuacion\scripts\vigilante_dashboard.bat';" ^
  "$t = New-ScheduledTaskTrigger -RepetitionInterval ([TimeSpan]::FromMinutes(2)) -Once -At (Get-Date);" ^
  "$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::FromDays(3650)) -MultipleInstances IgnoreNew;" ^
  "$p = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest;" ^
  "Register-ScheduledTask -TaskName 'WurthDashboard-Vigilante' -Action $a -Trigger $t -Settings $s -Principal $p -Force | Out-Null;" ^
  "Write-Host ' [OK] WurthDashboard-Vigilante — cada 2 minutos como SYSTEM'"
if errorlevel 1 goto :error

echo.
echo ============================================================
echo  Tareas creadas.
echo.
echo  Iniciar el tablero ahora:
echo    schtasks /Run /TN "WurthDashboard"
echo.
echo  Ver estado:
echo    schtasks /Query /TN "WurthDashboard"
echo    schtasks /Query /TN "WurthDashboard-Vigilante"
echo.
echo  Log del vigilante: C:\alerta-de-fluctuacion\data\vigilante.log
echo ============================================================
goto :fin

:error
echo.
echo ============================================================
echo  ERROR. Intentá de nuevo con clic derecho > Ejecutar como administrador.
echo ============================================================

:fin
echo.
pause
