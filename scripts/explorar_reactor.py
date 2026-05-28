"""
explorar_reactor.py
--------------------
Explora la estructura de Reactor CRM (MySQL, DSN "Wurth Reactor Produccion").
No modifica nada. Solo lectura.

Probar primero con Python 64 bits:
    python scripts\\explorar_reactor.py

Si falla con error de arquitectura, usar Python 32 bits:
    C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe scripts\\explorar_reactor.py

Genera: reactor_estructura.txt en la carpeta actual.
"""

import pyodbc
import sys

DSN = "Wurth Reactor Produccion"
OUTPUT = "reactor_estructura.txt"

KEYWORDS = [
    "llamad", "visita", "call", "visit", "actividad", "activity",
    "contact", "agenda", "task", "tarea", "evento", "event",
    "seguimiento", "nota", "note", "log", "histor", "interac",
    "vend", "seller", "comerci", "client", "customer",
]

print(f"Conectando a '{DSN}'...", end=" ", flush=True)
try:
    con = pyodbc.connect(f"DSN={DSN}", timeout=10)
    print("OK")
except Exception as e:
    print(f"\nERROR: {e}")
    print("\nSi ves 'arquitectura no coincide', probá con Python 32 bits.")
    sys.exit(1)

cur = con.cursor()
lines = []

# ── Todas las tablas ──────────────────────────────────────────────────────────
cur.execute("SHOW TABLES")
tablas = [r[0] for r in cur.fetchall()]
lines.append(f"=== {len(tablas)} TABLAS EN wurth_ar_reactor_prod ===\n")
print(f"\n{len(tablas)} tablas encontradas.")

for t in tablas:
    lines.append(f"  {t}")

# ── Tablas posiblemente relevantes ───────────────────────────────────────────
relevantes = [t for t in tablas if any(kw in t.lower() for kw in KEYWORDS)]
lines.append(f"\n\n=== TABLAS POSIBLEMENTE RELEVANTES ({len(relevantes)}) ===\n")
print(f"\nTablas posiblemente relevantes ({len(relevantes)}):")
for t in relevantes:
    lines.append(f"  {t}")
    print(f"  {t}")

# ── Detalle de tablas relevantes ─────────────────────────────────────────────
lines.append("\n\n=== DETALLE DE TABLAS RELEVANTES ===\n")
for tabla in relevantes:
    lines.append(f"\n--- {tabla} ---")
    try:
        cur.execute(f"DESCRIBE `{tabla}`")
        cols = cur.fetchall()
        col_names = [c[0] for c in cols]
        for c in cols:
            lines.append(f"  {c[0]:<40} {c[1]}")
        cur.execute(f"SELECT * FROM `{tabla}` LIMIT 2")
        rows = cur.fetchall()
        for r in rows:
            lines.append(f"  MUESTRA: {dict(zip(col_names, list(r)))}")
    except Exception as e:
        lines.append(f"  (error: {e})")

# ── Todas las tablas con estructura (para referencia completa) ────────────────
lines.append("\n\n=== ESTRUCTURA COMPLETA DE TODAS LAS TABLAS ===\n")
for tabla in tablas:
    if tabla in relevantes:
        continue  # ya está arriba
    lines.append(f"\n--- {tabla} ---")
    try:
        cur.execute(f"DESCRIBE `{tabla}`")
        cols = cur.fetchall()
        for c in cols:
            lines.append(f"  {c[0]:<40} {c[1]}")
    except Exception as e:
        lines.append(f"  (error: {e})")

con.close()

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\nListo. Estructura guardada en: {OUTPUT}")
print("Pegá el contenido del archivo acá para continuar con el ETL.")
