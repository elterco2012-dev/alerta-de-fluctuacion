"""
diagnostico_distribucion.py
---------------------------
Corre el motor de scoring EN VIVO sobre data/wurth.db (solo lectura) y muestra:
  1. La distribución de scores y niveles entre los activos
  2. Cada cuánto dispara CADA señal entre los activos (la que más dispara es la
     que más infla los scores)

Sirve para entender por qué hay tantos críticos y decidir qué señal ajustar.
No toca ninguna base externa. Correr con Python 64-bit:
    python scripts\\diagnostico_distribucion.py
"""

import os
import sys
import collections

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from score_engine import calcular_scores

df = calcular_scores(meses_tendencia=3)
n = len(df)

print("=" * 60)
print("DISTRIBUCIÓN DE SCORES — vendedores activos")
print("=" * 60)
print(f"Total activos evaluados: {n}\n")

niveles = [("critico", ">=8"), ("alto", "6-7"), ("medio", "4-5"), ("bajo", "1-3")]
for nivel, rango in niveles:
    cnt = len(df[df.nivel_riesgo == nivel])
    pct = cnt / n * 100 if n else 0
    print(f"  {nivel:8} ({rango:>4}): {cnt:4}  ({pct:4.0f}%)")

print("\nHistograma de score (redondeado):")
c = collections.Counter(df["score"].round().astype(int))
for s in range(10, 0, -1):
    cnt = c.get(s, 0)
    print(f"  score {s:2}: {'#' * cnt} ({cnt})")

# ── Frecuencia de cada señal entre los activos ──────────────────────────────
print("\n" + "=" * 60)
print("FRECUENCIA DE CADA SEÑAL — entre los activos")
print("=" * 60)
print("La señal que dispara en más activos es la que más infla los scores.\n")

cont = collections.Counter()
for _, r in df.iterrows():
    for s in r["señales_activas"]:
        cont[s] += 1

print(f"  {'SEÑAL':52} {'activos':>8} {'%':>5}")
print("  " + "-" * 68)
for s, cnt in cont.most_common():
    pct = cnt / n * 100 if n else 0
    nombre = (s[:50] + "..") if len(s) > 52 else s
    print(f"  {nombre:52} {cnt:>8} {pct:>4.0f}%")

print("\n" + "=" * 60)
print("CÓMO LEERLO:")
print("  Si una señal dispara en >60% de los activos, no está distinguiendo")
print("  riesgo: está inflando el score de casi todos por igual. Esas son")
print("  candidatas a bajar de peso o subir el umbral.")
print("=" * 60)
