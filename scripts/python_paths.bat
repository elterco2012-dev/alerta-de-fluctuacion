@echo off
:: python_paths.bat — detecta Python 64-bit y Python 32-bit para este proyecto.
:: Incluirlo con  CALL "%~dp0python_paths.bat"  al inicio de cada script.
::
:: Prioridad para PYTHON64:
::   1. Variable de entorno PY64 si ya está definida
::   2. Subdirectorio local  .python\64\python.exe  (para equipos sin Python global)
::   3. py -3.12-64  (Python Launcher de Windows, busca cualquier 64-bit)
::   4. python  del PATH (asume que el Python del PATH es 64-bit)
::
:: Prioridad para PYTHON32:
::   1. Variable de entorno PY32 si ya está definida
::   2. Subdirectorio local  .python\32\python.exe
::   3. py -3.12-32  (Python Launcher)
::   4. Ruta fija de fallback (Python 3.12 32-bit en la ubicación habitual)

if defined PY64 goto :done_64
if exist "%~dp0..\.python\64\python.exe" (
    set "PY64=%~dp0..\.python\64\python.exe"
    goto :done_64
)
py -3.12-64 --version >nul 2>&1
if not errorlevel 1 (
    set PY64=py -3.12-64
    goto :done_64
)
set PY64=python
:done_64

if defined PY32 goto :done_32
if exist "%~dp0..\.python\32\python.exe" (
    set "PY32=%~dp0..\.python\32\python.exe"
    goto :done_32
)
py -3.12-32 --version >nul 2>&1
if not errorlevel 1 (
    set PY32=py -3.12-32
    goto :done_32
)
:: Fallback: ubicación estándar de Python 32-bit (ajustar si difiere)
set "PY32=C:\Program Files (x86)\Python312-32\python.exe"
:done_32
