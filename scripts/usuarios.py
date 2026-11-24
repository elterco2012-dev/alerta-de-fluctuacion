"""
scripts/usuarios.py
-------------------
Gestión de usuarios del tablero desde la línea de comando.

La clave nunca va en el comando: se pide en pantalla y no se ve al escribirla. Escrita en el comando quedaría en
el historial de PowerShell y en los registros del antivirus, que guardan cada comando que se ejecuta.

Uso (desde la raíz del proyecto, con scripts\\usuarios.bat o con el Python de 64 bits):
    usuarios.bat alta <usuario> "<clave_acceso>"
    usuarios.bat baja <usuario>
    usuarios.bat clave <usuario>
    usuarios.bat lista

`clave_acceso` debe ser exactamente el nombre que aparece en acceso.py:
  - "Gerencia"              → acceso total (gerencia y RRHH)
  - "Daniel Fernandez"      → director (nombre exacto de f040)
  - "Zerbatto Jose Luis"    → supervisor (nombre exacto de f040)

Ejemplos:
    usuarios.bat alta daniel "Gerencia"
    usuarios.bat alta jsup "Zerbatto Jose Luis"
    usuarios.bat lista
    usuarios.bat clave daniel
    usuarios.bat baja daniel
"""

import getpass
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.auth import crear_usuario, cambiar_clave, desactivar_usuario, listar_usuarios

LARGO_MINIMO = 10


def pedir_clave(usuario: str) -> str:
    clave = getpass.getpass(f"Clave para '{usuario}' (no se ve al escribir): ")
    if len(clave) < LARGO_MINIMO:
        print(f"Error: la clave tiene que tener al menos {LARGO_MINIMO} caracteres.")
        sys.exit(1)
    if getpass.getpass("Repetila: ") != clave:
        print("Error: las dos claves no coinciden. No cambié nada.")
        sys.exit(1)
    return clave


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == "alta":
        if len(args) != 3:
            print('Uso: usuarios.bat alta <usuario> "<clave_acceso>"  (la clave se pide en pantalla)')
            sys.exit(1)
        usuario, clave_acceso = args[1], args[2]
        try:
            crear_usuario(usuario, pedir_clave(usuario), clave_acceso)
            print(f"Usuario '{usuario}' creado → acceso como '{clave_acceso}'.")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif cmd == "baja":
        if len(args) < 2:
            print("Uso: usuarios.bat baja <usuario>")
            sys.exit(1)
        try:
            desactivar_usuario(args[1])
            print(f"Usuario '{args[1]}' desactivado.")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif cmd == "clave":
        if len(args) != 2:
            print("Uso: usuarios.bat clave <usuario>  (la clave nueva se pide en pantalla)")
            sys.exit(1)
        try:
            cambiar_clave(args[1], pedir_clave(args[1]))
            print(f"Clave de '{args[1]}' actualizada.")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif cmd == "lista":
        usuarios = listar_usuarios()
        if not usuarios:
            print("No hay usuarios registrados. Usá 'alta' para crear el primero.")
            return
        print(f"\n{'Usuario':<20} {'Clave de acceso':<30} {'Estado'}")
        print("-" * 60)
        for u in usuarios:
            estado = "activo" if u["activo"] else "INACTIVO"
            print(f"{u['usuario']:<20} {u['clave_acceso']:<30} {estado}")
        print()

    else:
        print(f"Comando desconocido: '{cmd}'. Opciones: alta, baja, clave, lista.")
        sys.exit(1)


if __name__ == "__main__":
    main()
