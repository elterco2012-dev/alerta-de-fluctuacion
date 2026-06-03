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

smtp_user     = os.getenv("SMTP_USER", "")
smtp_pwd      = os.getenv("SMTP_PWD", "")
alert_to      = [e.strip() for e in os.getenv("ALERT_TO", "").split(",") if e.strip()]
teams_webhook = os.getenv("TEAMS_WEBHOOK", "").strip()

tiene_email  = bool(smtp_user and smtp_pwd and alert_to)
tiene_teams  = bool(teams_webhook)

if not tiene_email and not tiene_teams:
    print("Sin canales de alerta configurados.")
    print("Agregá TEAMS_WEBHOOK y/o SMTP_USER + SMTP_PWD + ALERT_TO al .env")
    sys.exit(0)

print("=" * 55)
print("ALERTAS — Wurth Argentina")
print("=" * 55)

scores = calcular_scores(meses_tendencia=3)
estado = cargar_estado()
nuevos = detectar_nuevos_criticos(scores, estado)

if nuevos.empty:
    print("Sin nuevos vendedores críticos — no se envían alertas.")
else:
    print(f"{len(nuevos)} nuevo(s) en nivel crítico:")
    for _, r in nuevos.iterrows():
        nombre = r.get("nombre") or f"ID {int(r['id_vendedor'])}"
        print(f"  · {nombre} ({int(r['id_vendedor'])}) — Score {r['score']} — {r['supervisor']}")

    if tiene_teams:
        from alertas import enviar_teams
        print(f"\nEnviando alerta a Teams...")
        try:
            enviar_teams(teams_webhook, nuevos)
            print("Teams OK.")
        except Exception as e:
            print(f"ERROR Teams: {e}")

    if tiene_email:
        print(f"\nEnviando email a {alert_to}...")
        try:
            enviar_email({
                "host":     "smtp.office365.com",
                "port":     587,
                "user":     smtp_user,
                "password": smtp_pwd,
                "to":       alert_to,
            }, nuevos)
            print("Email OK.")
        except Exception as e:
            print(f"ERROR email: {e}")
            sys.exit(1)

guardar_estado(scores)
print("\nListo.")
