"""
explorar_taginfo.py
--------------------
Busca en Informix (DSN=MSPA) las tablas y campos que alimentan
la pantalla Tag Info 2 (Daily Info 2 Sales):

  - Backorders (pedidos vencidos)
  - Bloqueados por límite de crédito
  - Bloqueados por status < -1
  - Pedidos abiertos (plazos futuros)
  - Órdenes de producción abiertas
  - Remitos/Facturas abiertas
  - Venta diaria

Ejecutar con Python 32 bits (mismo DSN que Informix):
    C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe scripts\\explorar_taginfo.py

Genera: taginfo_estructura.txt
"""

import pyodbc
import sys

DSN    = "MSPA"
OUTPUT = "taginfo_estructura.txt"
FIRMA  = 1  # ajustar si la firma es distinta

KEYWORDS_PEDIDOS = [
    "auftr", "order", "pedid", "aukop", "aupos",
    "lauf",  "llauf", "liefe", "remit",
    "faktu", "factu", "rech",
    "prod",  "fert",  "werk",
    "sperr", "block", "credi", "limit",
    "venta", "verk",  "sale",
    "kred",  "debit",
]

print(f"Conectando a '{DSN}'...", end=" ", flush=True)
try:
    con = pyodbc.connect(f"DSN={DSN}", timeout=10)
    print("OK")
except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)

cur = con.cursor()
lines = []

# ── Todas las tablas ──────────────────────────────────────────────────────────
cur.execute("SELECT tabname FROM systables WHERE tabtype = 'T' ORDER BY tabname")
tablas = [r[0].strip() for r in cur.fetchall()]
lines.append(f"=== {len(tablas)} TABLAS EN MSPA ===\n")
print(f"\n{len(tablas)} tablas encontradas.")
for t in tablas:
    lines.append(f"  {t}")

# ── Tablas posiblemente relevantes para Tag Info ───────────────────────────────
relevantes = [t for t in tablas if any(kw in t.lower() for kw in KEYWORDS_PEDIDOS)]
lines.append(f"\n\n=== TABLAS POSIBLEMENTE RELEVANTES ({len(relevantes)}) ===\n")
print(f"\nTablas posiblemente relevantes ({len(relevantes)}):")
for t in relevantes:
    lines.append(f"  {t}")
    print(f"  {t}")

# ── Detalle de tablas relevantes ──────────────────────────────────────────────
lines.append("\n\n=== DETALLE DE TABLAS RELEVANTES ===\n")
for tabla in relevantes:
    lines.append(f"\n--- {tabla} ---")
    try:
        cur.execute(f"SELECT * FROM {tabla} WHERE 1=0")
        cols = [d[0] for d in cur.description]
        for c in cols:
            lines.append(f"  {c}")

        # Muestra 2 filas de las tablas pequeñas para entender el contenido
        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        total = cur.fetchone()[0]
        lines.append(f"  [total filas: {total}]")
        if 0 < total <= 500:
            cur.execute(f"SELECT FIRST 2 * FROM {tabla}")
            rows = cur.fetchall()
            for r in rows:
                lines.append(f"  MUESTRA: {dict(zip(cols, list(r)))}")
        elif total > 500:
            cur.execute(f"SELECT FIRST 2 * FROM {tabla}")
            rows = cur.fetchall()
            for r in rows:
                lines.append(f"  MUESTRA: {dict(zip(cols, list(r)))}")
    except Exception as e:
        lines.append(f"  (error: {e})")

# ── Búsqueda específica por campos clave de Tag Info ──────────────────────────
lines.append("\n\n=== BÚSQUEDA DE CAMPOS CLAVE (status, plazo, vencimiento, bloqueo) ===\n")
CAMPOS_CLAVE = ["status", "liefdat", "lieferdat", "plazo", "sperr",
                "block", "kred", "posit", "netto", "brutto", "wert"]

for tabla in tablas:
    try:
        cur.execute(f"SELECT * FROM {tabla} WHERE 1=0")
        cols = [d[0].lower() for d in cur.description]
        matches = [c for c in cols if any(kw in c for kw in CAMPOS_CLAVE)]
        if len(matches) >= 2:
            lines.append(f"  {tabla}: {matches}")
    except Exception:
        pass

con.close()

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\nListo. Guardado en: {OUTPUT}")
print("Pegá el contenido del archivo acá para continuar.")
