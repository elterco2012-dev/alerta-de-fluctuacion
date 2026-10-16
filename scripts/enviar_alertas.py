"""
enviar_alertas.py
-----------------
Detecta vendedores que subieron a nivel crítico (o siguen críticos hace 7+ días)
y envía email. Requiere Python 64-bit. Ejecutar DESPUÉS de sincronizar_informix.py.

Configuración: crear un archivo .env en la raíz del proyecto (ver .env.example).
"""

import os
import sys

# Cargar .env si existe (acepta tanto python-dotenv instalado como carga manual)
_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(_env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        for _line in open(_env_path, encoding="utf-8"):
            if "=" in _line and not _line.strip().startswith("#"):
                _k, _v = _line.strip().split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from score_engine import calcular_scores
from alertas import (cargar_estado, detectar_nuevos_criticos,
                     guardar_estado, enviar_email)

DIAS_REALERTA = 7   # re-alertar si sigue crítico después de N días

# Máximo de vendedores por email. El scoring ya es un ranking: se toman los N
# peores por score. El resto sigue en estado "crítico" en el dashboard pero no
# genera ruido de email. Alineado con FOCO_SEMANA del dashboard (~20).
MAX_ALERTAS = 20

smtp_user     = os.getenv("SMTP_USER", "")
smtp_pwd      = os.getenv("SMTP_PWD", "")
alert_to      = [e.strip() for e in os.getenv("ALERT_TO", "").split(",") if e.strip()]
teams_webhook = os.getenv("TEAMS_WEBHOOK", "").strip()

# --dry-run: calcula y muestra a quién se alertaría, sin enviar nada ni tocar
# data/estado_alertas.json. Usarlo para probar (nunca mandar correos reales en pruebas).
DRY_RUN = "--dry-run" in sys.argv

try:
    import win32com.client  # noqa: F401 — Outlook COM no necesita contraseña
    _hay_com = True
except ImportError:
    _hay_com = False

# Con Outlook COM la contraseña no se usa (y no conviene guardarla en .env).
tiene_email  = bool(alert_to and (_hay_com or (smtp_user and smtp_pwd)))
tiene_teams  = bool(teams_webhook)

if not DRY_RUN and not tiene_email and not tiene_teams:
    print("Sin canales de alerta configurados.")
    print("Creá el archivo .env (ver .env.example) con ALERT_TO (y SMTP_USER/SMTP_PWD "
          "solo si no hay Outlook COM).")
    sys.exit(0)

print("=" * 55)
print("ALERTAS — Wurth Argentina" + ("  [DRY RUN: no se envía nada]" if DRY_RUN else ""))
print("=" * 55)

scores = calcular_scores(meses_tendencia=3)
estado = cargar_estado()
nuevos = detectar_nuevos_criticos(scores, estado, dias_realerta=DIAS_REALERTA)

if nuevos.empty:
    print("Sin alertas nuevas (ningún crítico nuevo ni re-alerta pendiente).")
else:
    total_criticos = len(nuevos)

    # Limitar al top N por score (ya viene ordenado desc del calcular_scores)
    if len(nuevos) > MAX_ALERTAS:
        print(f"{total_criticos} vendedores críticos detectados — "
              f"se alertan los top {MAX_ALERTAS} por score (ver dashboard para el resto).")
        nuevos = nuevos.head(MAX_ALERTAS)
    else:
        print(f"{len(nuevos)} vendedor(es) a alertar:")

    for _, r in nuevos.iterrows():
        nombre = r.get("nombre") or f"ID {int(r['id_vendedor'])}"
        print(f"  · {nombre} ({int(r['id_vendedor'])}) — Score {r['score']:.1f} — {r['supervisor']}")

    alertados_ids = set()

    if DRY_RUN:
        print("\nDRY RUN: no se envió ningún mensaje ni se actualizó el estado.")
        sys.exit(0)

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
            alertados_ids = set(str(int(v)) for v in nuevos["id_vendedor"])
        except Exception as e:
            print(f"ERROR email: {e}")
            print("  No se actualiza el estado — el próximo run lo reintentará.")
            sys.exit(1)

    guardar_estado(scores, alertados_ids)

print("\nListo.")
