"""
test_conexion_informix.py
-------------------------
Paso 1: verificar que la conexión a Informix funciona.
Paso 2: explorar qué tablas existen y qué columnas tienen.

Ejecutar desde la carpeta del proyecto:
    python scripts/test_conexion_informix.py
"""

import sys
import os

# Cargar credenciales desde .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # sin python-dotenv, usar variables de entorno directas

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc no está instalado.")
    print("Ejecutá: pip install pyodbc")
    sys.exit(1)

# ── Configuración de conexión ──────────────────────────────────────────────────
# Usando el DSN ya configurado en Windows (el más simple)
DSN      = os.getenv("INFORMIX_DSN", "MSPA")
UID      = os.getenv("INFORMIX_UID", "aarmoa")
PWD      = os.getenv("INFORMIX_PWD", "")         # cargar desde .env, no hardcodear

CONN_STR = f"DSN={DSN};UID={UID};PWD={PWD};"

# ── Test de conexión ───────────────────────────────────────────────────────────
print("=" * 60)
print("TEST DE CONEXIÓN — Informix Wurth")
print("=" * 60)
print(f"DSN:      {DSN}")
print(f"Usuario:  {UID}")
print(f"Host:     10.60.20.2  (configurado en el DSN)")
print()

try:
    print("Conectando...", end=" ")
    con = pyodbc.connect(CONN_STR, timeout=10)
    print("✓ CONEXIÓN EXITOSA")
except Exception as e:
    print(f"✗ FALLÓ")
    print(f"\nError: {e}")
    print("\nVerificá:")
    print("  1. Que el DSN 'MSPA' esté configurado en el Administrador ODBC")
    print("  2. Que el servidor 10.60.20.2 esté accesible desde tu PC")
    print("  3. Que usuario/contraseña sean correctos")
    sys.exit(1)

# ── Explorar tablas disponibles ────────────────────────────────────────────────
print()
print("─" * 60)
print("TABLAS DISPONIBLES EN LA BASE DE DATOS")
print("─" * 60)

cur = con.cursor()

try:
    tablas = [row.table_name for row in cur.tables(tableType="TABLE")]
    tablas_lower = [t.lower() for t in tablas]

    if not tablas:
        print("No se encontraron tablas (puede ser un tema de permisos).")
    else:
        print(f"Total: {len(tablas)} tablas\n")
        for t in sorted(tablas):
            print(f"  - {t}")
except Exception as e:
    print(f"No se pudo listar tablas: {e}")
    tablas_lower = []

# ── Buscar tablas que probablemente necesitamos ────────────────────────────────
print()
print("─" * 60)
print("BUSCANDO TABLAS RELEVANTES PARA EL SISTEMA")
print("─" * 60)

CANDIDATAS = [
    "vendedor", "vendor", "seller", "comercial",
    "venta", "sale", "pedido", "orden",
    "cliente", "customer",
    "cobranza", "cobro", "factura",
    "grupo", "zona", "region",
    "rrhh", "personal", "empleado", "legajo",
]

encontradas = []
for tabla in tablas_lower:
    for candidata in CANDIDATAS:
        if candidata in tabla:
            encontradas.append(tabla)
            break

if encontradas:
    print(f"Tablas que podrían ser relevantes:\n")
    for t in sorted(set(encontradas)):
        print(f"  → {t}")
        try:
            cols = [(col.column_name, col.type_name) for col in cur.columns(table=t)]
            for col_name, col_type in cols[:15]:
                print(f"       {col_name:<30} {col_type}")
            if len(cols) > 15:
                print(f"       ... y {len(cols)-15} columnas más")
        except Exception as e:
            print(f"       (no se pudieron leer columnas: {e})")
        print()
else:
    print("No se encontraron tablas con nombres conocidos.")
    print("Mostrando primeras 20 tablas para exploración manual:")
    for t in sorted(tablas)[:20]:
        print(f"  - {t}")

# ── Test de query simple ───────────────────────────────────────────────────────
print()
print("─" * 60)
print("TEST DE QUERY")
print("─" * 60)

try:
    cur.execute("SELECT COUNT(*) FROM systables WHERE tabtype = 'T'")
    n = cur.fetchone()[0]
    print(f"✓ Queries funcionan. Tablas del sistema: {n}")
except Exception as e:
    print(f"✗ Error ejecutando query: {e}")

con.close()

print()
print("=" * 60)
print("Guardá la salida de este script y compartila.")
print("Con eso sabemos cómo se llaman las tablas reales y")
print("adaptamos las queries del sistema.")
print("=" * 60)
