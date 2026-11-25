@echo off
:: cerrar_claves.bat <carpeta> - la subcarpeta claves\ del proyecto, donde vive el .env desde el 25/11 (decision del
:: usuario). Le niega la lectura a LOCAL SERVICE (el tablero) con herencia: asi un editor que reescribe el .env con un
:: temporal no le saca el "Denegar". Si el .env todavia esta en la raiz, lo copia ahi; el de la raiz se borra a mano
:: cuando la tarea diaria corrio bien con el nuevo. La cuenta de Claude se la niega proteger_carpeta.bat.
:: Lo llaman proteger_carpeta.bat y programar_dashboard.bat, como administrador. Sale con 1 si algo falla.
setlocal
set "CARPETA=%~1"
if not defined CARPETA exit /b 1
if not exist "%CARPETA%\claves\" (
    mkdir "%CARPETA%\claves"
    if errorlevel 1 exit /b 1
)
icacls "%CARPETA%\claves" /deny "*S-1-5-19:(OI)(CI)R" /Q >NUL
if errorlevel 1 exit /b 1
if exist "%CARPETA%\.env" if not exist "%CARPETA%\claves\.env" (
    copy /Y "%CARPETA%\.env" "%CARPETA%\claves\.env" >NUL
    if errorlevel 1 exit /b 1
    echo  [OK] Copie el .env a claves\.env. El de la raiz se borra cuando la tarea diaria ande con el nuevo.
)
if exist "%CARPETA%\.env" (
    icacls "%CARPETA%\.env" /deny "*S-1-5-19:R" /Q >NUL
    if errorlevel 1 exit /b 1
)
echo  [OK] %CARPETA%\claves: LOCAL SERVICE no lo puede leer
exit /b 0
