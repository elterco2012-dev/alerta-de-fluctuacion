"""
explorar_informix_balance.py
-----------------------------
Explora las tablas de Informix que alimentarán la balanza de clientes
y la variedad de productos:
  - adrchr   (clientes nuevos por vendedor)
  - sbas     (historial de ventas por cliente — para reactivados/perdidos y productos)

Ejecutar con Python 32 bits:
    C:\\Users\\aarmoa\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe scripts\\explorar_informix_balance.py

Genera: informix_balance_estructura.txt
"""

import pyodbc, sys, datetime

DSN    = "MSPA"
OUTPUT = "informix_balance_estructura.txt"
FIRMA  = 1

print(f"Conectando a '{DSN}'...", end=" ", flush=True)
try:
    con = pyodbc.connect(f"DSN={DSN}", timeout=10)
    print("OK")
except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)

cur = con.cursor()
lines = []

HOY = datetime.date.today()
HACE_3M_STR = (HOY - datetime.timedelta(days=90)).strftime("%Y-%m-%d")

# ── Buscar tablas con nombres parecidos a adrchr/sbas en systables ────────────
lines.append("=== TABLAS CON NOMBRES SIMILARES A adrchr / sbas ===\n")
try:
    cur.execute("""
        SELECT tabname FROM systables
        WHERE tabtype = 'T'
          AND (tabname LIKE '%adr%' OR tabname LIKE '%sbas%'
               OR tabname LIKE '%kund%' OR tabname LIKE '%clie%'
               OR tabname LIKE '%client%' OR tabname LIKE '%alta%'
               OR tabname LIKE '%venta%' OR tabname LIKE '%sale%')
        ORDER BY tabname
    """)
    for r in cur.fetchall():
        lines.append(f"  {r[0].strip()}")
    lines.append("")
except Exception as e:
    lines.append(f"  (error buscando tablas: {e})\n")

# ── adrchr ────────────────────────────────────────────────────────────────────
lines.append("=" * 60)
lines.append("TABLA: adrchr  (altas de clientes / direcciones)")
lines.append("=" * 60)
try:
    # Usar API ODBC de metadatos (no requiere SQL — evita problemas de sintaxis Informix)
    cur.columns(table="adrchr")
    cols_adrchr = [r.column_name for r in cur.fetchall()]
    lines.append(f"Columnas ({len(cols_adrchr)}):")
    for c in cols_adrchr:
        lines.append(f"  {c}")

    cur.execute("SELECT COUNT(*) FROM adrchr")
    lines.append(f"\nTotal filas: {cur.fetchone()[0]:,}")

    lines.append("\nMuestra 3 filas:")
    cur.execute("SELECT FIRST 3 * FROM adrchr")
    for r in cur.fetchall():
        lines.append(f"  {dict(zip(cols_adrchr, list(r)))}")

    # Buscar columnas de fecha y vendedor
    posibles_fecha  = [c for c in cols_adrchr if any(k in c.lower() for k in ["dat","fec","date","dte"])]
    posibles_vend   = [c for c in cols_adrchr if any(k in c.lower() for k in ["vert","vend","verk","user","vertr"])]
    posibles_client = [c for c in cols_adrchr if any(k in c.lower() for k in ["kund","clie","client","adr"])]
    lines.append(f"\nPosibles columnas fecha:    {posibles_fecha}")
    lines.append(f"Posibles columnas vendedor: {posibles_vend}")
    lines.append(f"Posibles columnas cliente:  {posibles_client}")

    # Contar por mes si hay columna de fecha clara
    if posibles_fecha:
        fc = posibles_fecha[0]
        try:
            cur.execute(f"""
                SELECT YEAR({fc}), MONTH({fc}), COUNT(*)
                FROM adrchr
                WHERE {fc} >= '{HACE_3M_STR}'
                GROUP BY 1, 2
                ORDER BY 1 DESC, 2 DESC
            """)
            lines.append(f"\nAltas por mes (campo {fc}, últimos 3 meses):")
            for r in cur.fetchall():
                lines.append(f"  {r[0]}-{r[1]:02d}: {r[2]:,}")
        except Exception as e:
            lines.append(f"  (error conteo por mes: {e})")

except Exception as e:
    lines.append(f"ERROR: {e}")

# ── sbas ──────────────────────────────────────────────────────────────────────
lines.append("\n" + "=" * 60)
lines.append("TABLA: sbas  (historial de ventas/posiciones por cliente)")
lines.append("=" * 60)
try:
    cur.columns(table="sbas")
    cols_sbas = [r.column_name for r in cur.fetchall()]
    lines.append(f"Columnas ({len(cols_sbas)}):")
    for c in cols_sbas:
        lines.append(f"  {c}")

    cur.execute("SELECT COUNT(*) FROM sbas")
    lines.append(f"\nTotal filas: {cur.fetchone()[0]:,}")

    lines.append("\nMuestra 3 filas:")
    cur.execute("SELECT FIRST 3 * FROM sbas")
    for r in cur.fetchall():
        lines.append(f"  {dict(zip(cols_sbas, list(r)))}")

    posibles_fecha  = [c for c in cols_sbas if any(k in c.lower() for k in ["dat","fec","date","dte","monat","year","anio","mes"])]
    posibles_vend   = [c for c in cols_sbas if any(k in c.lower() for k in ["vert","vend","verk","vertr"])]
    posibles_client = [c for c in cols_sbas if any(k in c.lower() for k in ["kund","clie","client"])]
    posibles_prod   = [c for c in cols_sbas if any(k in c.lower() for k in ["art","prod","mater","item","artnr"])]
    posibles_importe = [c for c in cols_sbas if any(k in c.lower() for k in ["netto","brut","import","wert","monto","total","umsatz"])]
    lines.append(f"\nPosibles columnas fecha:    {posibles_fecha}")
    lines.append(f"Posibles columnas vendedor: {posibles_vend}")
    lines.append(f"Posibles columnas cliente:  {posibles_client}")
    lines.append(f"Posibles columnas producto: {posibles_prod}")
    lines.append(f"Posibles columnas importe:  {posibles_importe}")

    # Conteo por mes
    if posibles_fecha:
        fc = posibles_fecha[0]
        try:
            cur.execute(f"""
                SELECT YEAR({fc}), MONTH({fc}), COUNT(*), COUNT(DISTINCT {posibles_client[0] if posibles_client else '1'})
                FROM sbas
                WHERE {fc} >= '{HACE_3M_STR}'
                GROUP BY 1, 2
                ORDER BY 1 DESC, 2 DESC
            """)
            lines.append(f"\nActividad por mes (campo {fc}, últimos 3 meses):")
            for r in cur.fetchall():
                lines.append(f"  {r[0]}-{r[1]:02d}: {r[2]:,} filas, {r[3]:,} clientes distintos")
        except Exception as e:
            lines.append(f"  (error conteo: {e})")

except Exception as e:
    lines.append(f"ERROR: {e}")

con.close()

output = "\n".join(lines)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(output)

print(f"\nListo. Guardado en: {OUTPUT}")
print("Pegá el contenido acá para continuar con el ETL.")
