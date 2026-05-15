"""
enviar_alertas.py
-----------------
Runner de alertas de rotación. Detecta nuevos críticos y notifica via Teams y/o email.

Configuración via variables de entorno (ver .env.example):
    WURTH_TEAMS_WEBHOOK_URL   → Teams Incoming Webhook o Power Automate
    WURTH_SMTP_HOST           → servidor SMTP
    WURTH_SMTP_PORT           → puerto (default 587)
    WURTH_SMTP_USER           → usuario/remitente
    WURTH_SMTP_PASSWORD       → contraseña
    WURTH_EMAIL_TO            → destinatarios separados por coma

Uso:
    python scripts/enviar_alertas.py              # detecta y envía
    python scripts/enviar_alertas.py --dry-run    # muestra qué enviaría sin enviar
    python scripts/enviar_alertas.py --reset      # borra estado (alerta todos los críticos)

Cron/Tarea programada recomendada: ejecutar una vez por día (ej: lunes a las 8am).
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from score_engine import calcular_scores
from alertas import (
    cargar_estado, guardar_estado, detectar_nuevos_criticos,
    enviar_teams, enviar_email, ESTADO_PATH,
)


def main():
    parser = argparse.ArgumentParser(description="Envía alertas de rotación Wurth")
    parser.add_argument("--dry-run", action="store_true",
                        help="Muestra qué enviaría sin enviar nada")
    parser.add_argument("--reset", action="store_true",
                        help="Borra el estado guardado (próxima ejecución alerta todos los críticos)")
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(ESTADO_PATH):
            os.remove(ESTADO_PATH)
            print("✓ Estado borrado. El próximo run alertará sobre todos los críticos actuales.")
        else:
            print("No había estado guardado.")
        return

    # ── Calcular scores ────────────────────────────────────────────────────────
    print("Calculando scores...")
    scores = calcular_scores()
    estado = cargar_estado()

    ultima = estado.get("ultima_ejecucion", "nunca")
    print(f"Última ejecución: {ultima}")
    print(f"Críticos actuales: {len(scores[scores.nivel_riesgo == 'critico'])}")

    nuevos = detectar_nuevos_criticos(scores, estado)

    if nuevos.empty:
        print("✓ Sin nuevos críticos desde la última ejecución.")
        guardar_estado(scores)
        return

    print(f"\n⚠️  {len(nuevos)} nuevo(s) en nivel crítico:")
    for _, r in nuevos.iterrows():
        señales = " · ".join(r["señales_activas"][:3]) or "—"
        print(f"   ID {int(r['id_vendedor'])} | {r['nombre_grupo']} | "
              f"Score {r['score']} | {señales}")

    if args.dry_run:
        print("\n[dry-run] No se envió nada.")
        return

    # ── Teams ──────────────────────────────────────────────────────────────────
    teams_url = os.getenv("WURTH_TEAMS_WEBHOOK_URL", "").strip()
    if teams_url:
        try:
            enviar_teams(teams_url, nuevos)
            print("✓ Alerta enviada a Teams.")
        except Exception as e:
            print(f"✗ Error enviando a Teams: {e}", file=sys.stderr)
    else:
        print("  Teams: WURTH_TEAMS_WEBHOOK_URL no configurado, saltando.")

    # ── Email ──────────────────────────────────────────────────────────────────
    smtp_host = os.getenv("WURTH_SMTP_HOST", "").strip()
    email_to  = os.getenv("WURTH_EMAIL_TO", "").strip()
    if smtp_host and email_to:
        smtp_config = {
            "host":     smtp_host,
            "port":     int(os.getenv("WURTH_SMTP_PORT", "587")),
            "user":     os.getenv("WURTH_SMTP_USER", ""),
            "password": os.getenv("WURTH_SMTP_PASSWORD", ""),
            "to":       [e.strip() for e in email_to.split(",")],
        }
        try:
            enviar_email(smtp_config, nuevos)
            print(f"✓ Alerta enviada por email a: {email_to}")
        except Exception as e:
            print(f"✗ Error enviando email: {e}", file=sys.stderr)
    else:
        print("  Email: WURTH_SMTP_HOST / WURTH_EMAIL_TO no configurados, saltando.")

    # ── Guardar estado ─────────────────────────────────────────────────────────
    guardar_estado(scores)
    print("\nEstado actualizado.")


if __name__ == "__main__":
    main()
