@echo off
:: vigilante_dashboard.bat — comprueba si el tablero en el 8501 responde.
:: Si no contesta dos veces seguidas, lo reinicia.
:: Corre como tarea programada cada 2 minutos (WurthDashboard-Vigilante).
:: No abre PowerShell si el tablero responde; así no llena el registro de eventos.

set PUERTO=8501
set CARPETA=C:\alerta-de-fluctuacion
set OK=0

:: Intentar llegar al tablero (curl.exe --noproxy para no ir por el proxy de SYSTEM)
curl.exe --noproxy "*" -s -o NUL -w "%%{http_code}" http://127.0.0.1:%PUERTO%/_stcore/health > "%TEMP%\alerta_health.tmp" 2>NUL
set /p ESTADO=<"%TEMP%\alerta_health.tmp"
del "%TEMP%\alerta_health.tmp" 2>NUL

if "%ESTADO%"=="200" set OK=1

if "%OK%"=="1" goto :fin

:: No contestó: reiniciar
echo %DATE% %TIME% — tablero no contestó (estado: %ESTADO%), reiniciando... >> C:\alerta-de-fluctuacion\data\vigilante.log 2>&1

:: Matar el proceso anterior si existe
powershell -NoProfile -Command "Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force" >NUL 2>&1

:: Esperar un momento y arrancar de nuevo
ping -n 4 127.0.0.1 >NUL
call "%~dp0iniciar_dashboard.bat"

:fin
