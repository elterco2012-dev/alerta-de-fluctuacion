@echo off
:: proteger_carpeta.bat — cierra la carpeta del proyecto: quedan solo Administradores, SYSTEM y la cuenta con la que
:: corren las tareas (la de WurthAlertas). Por herencia de C:\, "Usuarios" podia leer todo (la base con datos de
:: vendedores, las claves del tablero, el .env) y "Usuarios autentificados" podia cambiar los scripts que corren
:: las tareas programadas.
:: Ejecutar como administrador (clic derecho > Ejecutar como administrador). Se puede repetir.
:: Hace lo mismo con C:\alerta-test si existe.
:: Para volver atras: icacls C:\ /restore C:\alerta-de-fluctuacion_permisos_antes.txt
setlocal

net session >NUL 2>&1
if errorlevel 1 (
    echo  Hay que ejecutarlo como administrador: clic derecho ^> Ejecutar como administrador.
    goto :fin
)

set "CUENTA="
for /f "usebackq delims=" %%u in (`powershell -NoProfile -Command "(Get-ScheduledTask -TaskName 'WurthAlertas' -ErrorAction SilentlyContinue).Principal.UserId"`) do set "CUENTA=%%u"
if not defined CUENTA (
    echo  No encontre la tarea WurthAlertas, asi que no se con que cuenta corren las tareas. No cambie nada.
    goto :fin
)
echo  Las tareas corren con la cuenta: %CUENTA%
echo.

for %%c in ("C:\alerta-de-fluctuacion" "C:\alerta-test") do (
    if exist "%%~c\" call :cerrar "%%~c"
)
goto :fin

:cerrar
set "CARPETA=%~1"
set "RESPALDO=%~1_permisos_antes.txt"
if not exist "%RESPALDO%" (
    icacls "%CARPETA%" /save "%RESPALDO%" /T /C /Q >NUL
    echo  Permisos anteriores guardados en %RESPALDO%
)
icacls "%CARPETA%" /inheritance:r /grant:r "*S-1-5-18:(OI)(CI)F" "*S-1-5-32-544:(OI)(CI)F" "%CUENTA%:(OI)(CI)M" /Q
if errorlevel 1 (
    echo  ERROR: no se pudo cerrar %CARPETA%.
    exit /b 1
)
echo  %CARPETA% quedo asi:
icacls "%CARPETA%"
icacls "%CARPETA%" /T /C /Q | findstr /i /c:"Usuarios:(" /c:"autentificados:(" /c:"Users:(" >NUL
if not errorlevel 1 (
    echo  OJO: todavia hay archivos adentro con permisos para Usuarios:
    icacls "%CARPETA%" /T /C /Q | findstr /i /c:"Usuarios:(" /c:"autentificados:(" /c:"Users:("
)
echo.
exit /b 0

:fin
echo.
pause
