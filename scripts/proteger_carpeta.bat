@echo off
:: proteger_carpeta.bat — cierra la carpeta del proyecto: quedan solo Administradores, SYSTEM y la cuenta con la que
:: corren las tareas (la de WurthAlertas). Por herencia de C:\, "Usuarios" podia leer todo (la base con datos de
:: vendedores, las claves del tablero, el .env) y "Usuarios autentificados" podia cambiar los scripts que corren
:: las tareas programadas. Lo de LOCAL SERVICE (el tablero) no lo toca: lo da programar_dashboard.bat.
::
:: Con la cuenta de Claude (decision del usuario del 25/11, guia sesion-en-la-vm de conocimiento-wurth):
::     scripts\proteger_carpeta.bat EQUIPO\cuenta     (el nombre como lo muestra Windows; no va en el repositorio)
:: esa cuenta queda con leer y ejecutar, nunca escribir, y con "Denegar" la lectura en lo que tiene claves o datos de
:: personas: el .env, .git\config, data\ (la base con los puntajes de los vendedores, las claves del tablero, los
:: registros) y las salidas viejas de los diagnosticos que quedaron fuera de data\. Lo nuevo con datos va a data\:
:: lo que se crea adentro hereda el "Denegar". Si despues se crea el .env, volver a correrlo.
:: No acepta como cuenta de Claude una que necesitan el tablero, las tareas o Windows: el "Denegar" las frenaria.
::
:: Ejecutar como administrador (clic derecho > Ejecutar como administrador). Se puede repetir.
:: Cierra la carpeta donde esta: C:\alerta-de-fluctuacion o la copia de prueba, C:\alerta-test. Para las dos, correr el
:: de cada una; con la cuenta de Claude, primero el de la copia de prueba.
:: Para volver atras: icacls C:\ /restore C:\alerta-de-fluctuacion_permisos_antes.txt (o el de alerta-test)
setlocal

net session >NUL 2>&1
if errorlevel 1 (
    echo  Hay que ejecutarlo como administrador: clic derecho ^> Ejecutar como administrador.
    goto :fin
)

for %%d in ("%~dp0..") do set "CARPETA_PROPIA=%%~fd"
if /i not "%CARPETA_PROPIA%"=="C:\alerta-de-fluctuacion" if /i not "%CARPETA_PROPIA%"=="C:\alerta-test" (
    echo  Este script cierra C:\alerta-de-fluctuacion o C:\alerta-test, la carpeta donde esta. Esta en otra. No cambie nada.
    goto :fin
)

set "CUENTA="
for /f "usebackq delims=" %%u in (`powershell -NoProfile -Command "(Get-ScheduledTask -TaskName 'WurthAlertas' -ErrorAction SilentlyContinue).Principal.UserId"`) do set "CUENTA=%%u"
if not defined CUENTA (
    echo  No encontre la tarea WurthAlertas, asi que no se con que cuenta corren las tareas. No cambie nada.
    goto :fin
)
echo  Las tareas corren con la cuenta: %CUENTA%

set "CLAUDE=%~1"
set "CLAUDE_SID="
if not defined CLAUDE goto :carpetas
call :revisar_claude
if errorlevel 1 goto :fin

:carpetas
echo.
call :cerrar "%CARPETA_PROPIA%"
goto :fin

:revisar_claude
:: El SID de la cuenta de Claude. No puede ser una de las que necesitan la carpeta.
for /f "usebackq delims=" %%s in (`powershell -NoProfile -Command "try { (New-Object System.Security.Principal.NTAccount($env:CLAUDE)).Translate([System.Security.Principal.SecurityIdentifier]).Value } catch {}"`) do set "CLAUDE_SID=%%s"
if not defined CLAUDE_SID (
    echo  No encontre la cuenta "%CLAUDE%". Escribila como la muestra Windows: EQUIPO\cuenta. No cambie nada.
    exit /b 1
)
set "CUENTA_SID="
for /f "usebackq delims=" %%s in (`powershell -NoProfile -Command "try { (New-Object System.Security.Principal.NTAccount($env:CUENTA)).Translate([System.Security.Principal.SecurityIdentifier]).Value } catch {}"`) do set "CUENTA_SID=%%s"
for %%p in (S-1-5-18 S-1-5-19 S-1-5-20 S-1-5-32-544 S-1-5-32-545 S-1-5-11 S-1-1-0 "%CUENTA_SID%") do (
    if /i "%%~p"=="%CLAUDE_SID%" (
        echo  "%CLAUDE%" no puede ser la cuenta de Claude: la necesitan el tablero, las tareas o Windows. No cambie nada.
        exit /b 1
    )
)
echo  La cuenta de Claude: %CLAUDE% [%CLAUDE_SID%]
exit /b 0

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
if defined CLAUDE_SID (
    call :leer_claude
    if errorlevel 1 exit /b 1
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

:leer_claude
:: Leer y ejecutar en toda la carpeta, nunca escribir.
icacls "%CARPETA%" /grant:r "*%CLAUDE_SID%:(OI)(CI)RX" /Q >NUL
if errorlevel 1 (
    echo  ERROR: no se pudo dar la lectura a la cuenta de Claude en %CARPETA%.
    exit /b 1
)
:: "Denegar" la lectura en lo que tiene claves o datos de personas. En data\, con herencia.
set "FALLO="
if exist "%CARPETA%\data\" (
    icacls "%CARPETA%\data" /deny "*%CLAUDE_SID%:(OI)(CI)R" /Q >NUL
    if errorlevel 1 set "FALLO=1"
)
for %%f in (".env" ".git\config" "scripts\vart_diagnostico.csv") do (
    if exist "%CARPETA%\%%~f" (
        icacls "%CARPETA%\%%~f" /deny "*%CLAUDE_SID%:R" /Q >NUL
        if errorlevel 1 set "FALLO=1"
    )
)
:: Las salidas viejas de los scripts de exploracion (traen filas de muestra); las nuevas van a data\.
if exist "%CARPETA%\*_estructura.txt" (
    icacls "%CARPETA%\*_estructura.txt" /deny "*%CLAUDE_SID%:R" /Q >NUL
    if errorlevel 1 set "FALLO=1"
)
if exist "%CARPETA%\scripts\*_estructura.txt" (
    icacls "%CARPETA%\scripts\*_estructura.txt" /deny "*%CLAUDE_SID%:R" /Q >NUL
    if errorlevel 1 set "FALLO=1"
)
if defined FALLO (
    echo  ERROR: no se pudo denegar algo a la cuenta de Claude en %CARPETA%. Revisalo antes de prender la lectura.
    exit /b 1
)
echo  Cuenta de Claude en %CARPETA%: leer y ejecutar; denegado en .env, .git\config, data\ y las salidas viejas.
if not exist "%CARPETA%\.env" echo  No hay .env: si lo creas despues, volve a correr este script.
exit /b 0

:fin
echo.
pause
