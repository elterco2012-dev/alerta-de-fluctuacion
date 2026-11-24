@echo off
REM Gestion de usuarios del tablero. La clave se pide en pantalla: nunca va escrita en el comando.
REM Uso:
REM   usuarios.bat alta <usuario> "<clave_acceso>"
REM   usuarios.bat baja <usuario>
REM   usuarios.bat clave <usuario>
REM   usuarios.bat lista
REM
REM Ejemplos:
REM   usuarios.bat alta daniel "Gerencia"
REM   usuarios.bat alta jsup "Zerbatto Jose Luis"
REM   usuarios.bat lista

CALL "%~dp0python_paths.bat"
%PY64% "%~dp0usuarios.py" %*
