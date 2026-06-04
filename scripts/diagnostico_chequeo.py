"""
diagnostico_chequeo.py
----------------------
Por qué validar_pesos.py reporta [chequeo] != 0. Reconstruye el score de cada
fila de score_historico con los pesos de validar_pesos y lo compara con el score
guardado por el backfill, mostrando la PEOR fila y el REF/pesos en uso.

Solo lectura SQLite. Correr con el Python 64-bit:
    python -B scripts\\diagnostico_chequeo.py
"""

import sys, os, json, sqlite3, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import score_engine

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wurth.db')

# ── Estado del repo y de los archivos en disco ───────────────────────────────
print("=" * 64)
print("ESTADO DEL CÓDIGO EN DISCO")
print("=" * 64)
try:
    head = subprocess.check_output(["git", "log", "--oneline", "-3"],
                                   cwd=os.path.join(os.path.dirname(__file__), '..')).decode()
    print("Últimos commits (git log):")
    print("  " + head.replace("\n", "\n  ").rstrip())
except Exception as e:
    print(f"  (no se pudo leer git log: {e})")

print(f"\nscore_engine.RIESGO_REFERENCIA = {score_engine.RIESGO_REFERENCIA}")

# Pesos que usa el motor (de la lista de Señal, leída del código en disco)
import inspect
src = inspect.getsource(score_engine.calcular_scores)
print("  (REF leído del módulo realmente importado)")

# Pesos de validar_pesos
from importlib import import_module
vp = import_module("validar_pesos")
print(f"validar_pesos.RIESGO_REFERENCIA = {vp.RIESGO_REFERENCIA}")

# ── Reconstrucción fila por fila ─────────────────────────────────────────────
con = sqlite3.connect(DB_PATH)
cur = con.cursor()
cur.execute("SELECT periodo, id_vendedor, score, señales FROM score_historico")

peor = None  # (dif, periodo, vid, stored, recon, señales)
n = 0
periodos = set()
for periodo, vid, score, sj in cur.fetchall():
    n += 1
    periodos.add(periodo)
    sen = json.loads(sj) if sj else []
    riesgo = sum(vp.PESOS_ACTUAL.get(s, 0.0) for s in sen)
    recon = round(min(10, max(1, 1 + min(riesgo / vp.RIESGO_REFERENCIA, 1.0) * 9)), 1)
    dif = abs(recon - score)
    if peor is None or dif > peor[0]:
        peor = (dif, periodo, vid, score, recon, sen)
con.close()

print("\n" + "=" * 64)
print("RESULTADO")
print("=" * 64)
print(f"Filas en score_historico: {n}")
print(f"Períodos distintos: {len(periodos)}  → {min(periodos)} .. {max(periodos)}")
print(f"\nPEOR fila (máxima diferencia = {peor[0]:.2f}):")
print(f"  período={peor[1]}  vendedor={peor[2]}")
print(f"  score guardado (backfill) = {peor[3]}")
print(f"  score reconstruido (validar_pesos) = {peor[4]}")
print(f"  señales almacenadas: {peor[5]}")
riesgo = sum(vp.PESOS_ACTUAL.get(s, 0.0) for s in peor[5])
print(f"  riesgo (suma pesos validar) = {riesgo}")
print(f"\n  Pesos que validar_pesos asigna a cada señal de esa fila:")
for s in peor[5]:
    print(f"    {vp.PESOS_ACTUAL.get(s, '??'):>5}  {s}")

print("\n" + "=" * 64)
print("CÓMO LEERLO:")
print("  - Si el score guardado es MAYOR que el reconstruido en casi todas las")
print("    filas → el backfill usó un peso/señal que validar ya no cuenta (ej.")
print("    días cero todavía activo en el motor que corrió el backfill).")
print("  - Si los dos REF de arriba no coinciden → ahí está el problema.")
print("  - Si una señal de la fila tiene peso '??' → está en score_historico")
print("    pero no en PESOS_ACTUAL (string desincronizado).")
print("=" * 64)
