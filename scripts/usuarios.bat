@echo off
REM Gestión de usuarios del dashboard.
REM Uso:
REM   usuarios.bat alta <usuario> <clave> "<clave_acceso>"
REM   usuarios.bat baja <usuario>
REM   usuarios.bat clave <usuario> <nueva_clave>
REM   usuarios.bat lista
REM
REM Ejemplos:
REM   usuarios.bat alta daniel MiClave123 "Gerencia"
REM   usuarios.bat alta jsup ClaveSegura "Zerbatto Jose Luis"
REM   usuarios.bat lista

python "%~dp0..\scripts\usuarios.py" %*
