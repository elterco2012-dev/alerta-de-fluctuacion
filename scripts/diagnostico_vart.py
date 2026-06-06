"""
diagnostico_vart.py
--------------------
Exporta un CSV con id_vendedor, nombre, vart, vgrp, nombre_grupo y tipo_actual
para todos los vendedores activos en SQLite.

Fuentes:
  - f040 en Informix (MSPA) → vart, vgrp reales del ERP
  - vendedores en SQLite     → tipo que usa el sistema hoy

Uso (Python 32-bit con ODBC):
  python scripts\\diagnostico_vart.py

Salida: scripts\\vart_diagnostico.csv
"""

import os, sys, sqlite3, csv

try:
    import pyodbc
except ImportError:
    sys.exit("ERROR: pyodbc no instalado.")

DSN_INFORMIX = "MSPA"
FIRMA        = 1
DB_PATH      = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')
OUT_CSV      = os.path.join(os.path.dirname(__file__), 'vart_diagnostico.csv')

# ── 1. Leer activos de SQLite ──────────────────────────────────────────────────
con_local = sqlite3.connect(DB_PATH)
filas_sqlite = con_local.execute(
    "SELECT id_vendedor, nombre, tipo, nombre_grupo FROM vendedores WHERE activo = 1"
).fetchall()
con_local.close()

ids_activos = {r[0] for r in filas_sqlite}
sqlite_map  = {r[0]: {"nombre": r[1], "tipo_actual": r[2], "nombre_grupo": r[3]}
               for r in filas_sqlite}

print(f"Activos en SQLite: {len(ids_activos)}")

# ── 2. Leer vart y vgrp desde Informix ────────────────────────────────────────
print("Conectando a Informix (MSPA)...", end=" ", flush=True)
try:
    con_inf = pyodbc.connect(f"DSN={DSN_INFORMIX}", autocommit=True)
except Exception as e:
    sys.exit(f"ERROR conectando a Informix: {e}")
print("OK")

in_clause = ",".join(str(v) for v in sorted(ids_activos))
cur = con_inf.cursor()
cur.execute(
    f"SELECT vertr, vart, vgrp, zone FROM f040 "
    f"WHERE firma = {FIRMA} AND vertr IN ({in_clause})"
)
informix_map = {r[0]: {"vart": r[1], "vgrp": r[2], "zone": r[3]} for r in cur.fetchall()}
con_inf.close()

print(f"Registros obtenidos de f040: {len(informix_map)}")

# ── 3. Combinar y exportar ─────────────────────────────────────────────────────
filas_out = []
for vid in sorted(ids_activos):
    s = sqlite_map[vid]
    i = informix_map.get(vid, {})
    vart = i.get("vart", "N/A")
    zona = str(i.get("zone", "") or "").strip()
    # Mismo mapeo que inicializar_db.py actualizado:
    # zone='TVTAS' tiene prioridad sobre vart.
    if zona == "TVTAS":
        tipo_erp = "Televentas"
    elif str(vart).strip() in ("2","T","TV","Televentas","I","Innendienst"):
        tipo_erp = "Televentas"
    else:
        tipo_erp = "Viajante"
    filas_out.append({
        "id_vendedor":  vid,
        "nombre":       s["nombre"],
        "nombre_grupo": s["nombre_grupo"],
        "vart_erp":     vart,
        "zone_erp":     zona,
        "tipo_erp":     tipo_erp,
        "tipo_actual":  s["tipo_actual"],
        "ok":           "OK" if tipo_erp == s["tipo_actual"] else "DISCREPANCIA",
    })

with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["id_vendedor","nombre","nombre_grupo",
                                      "vart_erp","zone_erp","tipo_erp","tipo_actual","ok"])
    w.writeheader()
    w.writerows(filas_out)

# Resumen
total      = len(filas_out)
televentas = sum(1 for r in filas_out if r["tipo_actual"] == "Televentas")
viajantes  = sum(1 for r in filas_out if r["tipo_actual"] == "Viajante")
disc       = sum(1 for r in filas_out if r["ok"] == "DISCREPANCIA")
vart_vals  = {}
for r in filas_out:
    vart_vals[r["vart_erp"]] = vart_vals.get(r["vart_erp"], 0) + 1

print(f"\n{'='*50}")
print(f"Total activos:   {total}")
print(f"Televentas:      {televentas}")
print(f"Viajantes:       {viajantes}")
print(f"Discrepancias:   {disc}")
print(f"Valores de vart: {vart_vals}")
print(f"{'='*50}")
print(f"\nCSV exportado → {OUT_CSV}")
if disc:
    print(f"\nVendedores con DISCREPANCIA (vart dice X pero SQLite tiene Y):")
    for r in filas_out:
        if r["ok"] == "DISCREPANCIA":
            print(f"  {r['id_vendedor']:5d}  {r['nombre']:<35}  vart={r['vart_erp']}  ERP→{r['tipo_erp']}  actual→{r['tipo_actual']}")
