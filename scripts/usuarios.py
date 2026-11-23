"""
scripts/usuarios.py
-------------------
Gestión de usuarios del dashboard desde la línea de comando.

Uso (con Python 64 bits desde la raíz del proyecto):
    python scripts\\usuarios.py alta <usuario> <clave> "<clave_acceso>"
    python scripts\\usuarios.py baja <usuario>
    python scripts\\usuarios.py clave <usuario> <nueva_clave>
    python scripts\\usuarios.py lista

`clave_acceso` debe ser exactamente el nombre que aparece en acceso.py:
  - "Gerencia"              → acceso total (gerencia y RRHH)
  - "Daniel Fernandez"      → director (nombre exacto de f040)
  - "Zerbatto Jose Luis"    → supervisor (nombre exacto de f040)

Ejemplos:
    python scripts\\usuarios.py alta daniel MiClave123 "Gerencia"
    python scripts\\usuarios.py alta jsup ClaveSegura "Zerbatto Jose Luis"
    python scripts\\usuarios.py lista
    python scripts\\usuarios.py clave daniel NuevaClave456
    python scripts\\usuarios.py baja daniel
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.auth import crear_usuario, cambiar_clave, desactivar_usuario, listar_usuarios


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == "alta":
        if len(args) < 4:
            print("Uso: usuarios.py alta <usuario> <clave> <clave_acceso>")
            sys.exit(1)
        usuario, clave, clave_acceso = args[1], args[2], args[3]
        try:
            crear_usuario(usuario, clave, clave_acceso)
            print(f"Usuario '{usuario}' creado → acceso como '{clave_acceso}'.")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif cmd == "baja":
        if len(args) < 2:
            print("Uso: usuarios.py baja <usuario>")
            sys.exit(1)
        try:
            desactivar_usuario(args[1])
            print(f"Usuario '{args[1]}' desactivado.")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif cmd == "clave":
        if len(args) < 3:
            print("Uso: usuarios.py clave <usuario> <nueva_clave>")
            sys.exit(1)
        try:
            cambiar_clave(args[1], args[2])
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
