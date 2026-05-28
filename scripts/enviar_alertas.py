"""
enviar_alertas.py
-----------------
Detecta vendedores que subieron a nivel crítico y envía email.
Requiere Python 64-bit (tiene pandas). Ejecutar DESPUÉS de sincronizar_informix.py.
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from score_engine import calcular_scores
from alertas import (cargar_estado, detectar_nuevos_criticos,
                     guardar_estado, enviar_email)

smtp_user = os.getenv("SMTP_USER", "")
smtp_pwd  = os.getenv("SMTP_PWD", "")
alert_to  = [e.strip() for e in os.getenv("ALERT_TO", "").split(",") if e.strip()]

if not (smtp_user and smtp_pwd and alert_to):
    print("Alertas email no configuradas. Agregá SMTP_USER, SMTP_PWD y ALERT_TO al .env")
    sys.exit(0)

print("=" * 55)
print("ALERTAS EMAIL — Wurth Argentina")
print("=" * 55)

scores = calcular_scores(meses_tendencia=3)
estado = cargar_estado()
nuevos = detectar_nuevos_criticos(scores, estado)

if nuevos.empty:
    print("Sin nuevos vendedores críticos — no se envía email.")
else:
    print(f"{len(nuevos)} nuevo(s) en nivel crítico:")
    for _, r in nuevos.iterrows():
        nombre = r.get("nombre") or f"ID {int(r['id_vendedor'])}"
        print(f"  · {nombre} ({int(r['id_vendedor'])}) — Score {r['score']} — {r['supervisor']}")
    print(f"\nEnviando email a {alert_to}...")
    try:
        enviar_email({
            "host":     "smtp.office365.com",
            "port":     587,
            "user":     smtp_user,
            "password": smtp_pwd,
            "to":       alert_to,
        }, nuevos)
        print("Email enviado OK.")
    except Exception as e:
        print(f"ERROR enviando email: {e}")
        sys.exit(1)

guardar_estado(scores)
print("\nListo.")
