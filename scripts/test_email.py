"""test_email.py — Envía un email de prueba para verificar el canal de alertas."""
import os, sys

# Cargar .env (acepta python-dotenv instalado o, si no está, lo lee a mano)
_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if not os.path.exists(_env_path):
    print(f"No existe el archivo .env en: {os.path.abspath(_env_path)}")
    print("Crealo en la raiz del proyecto con SMTP_USER, SMTP_PWD y ALERT_TO.")
    sys.exit(1)
try:
    from dotenv import load_dotenv
    load_dotenv(_env_path)
except ImportError:
    for _line in open(_env_path, encoding="utf-8"):
        if "=" in _line and not _line.strip().startswith("#"):
            _k, _v = _line.strip().split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from alertas import _email_html, enviar_email_outlook
import pandas as pd

alert_to  = [e.strip() for e in os.getenv("ALERT_TO", "").split(",") if e.strip()]
smtp_user = os.getenv("SMTP_USER", "")
smtp_pwd  = os.getenv("SMTP_PWD", "")

if not alert_to:
    print("Falta ALERT_TO en el .env")
    sys.exit(1)

# Vendedor ficticio de prueba
vendedor_prueba = pd.DataFrame([{
    "id_vendedor":    9999,
    "nombre":         "Prueba Juan Carlos",
    "tipo":           "Viajante",
    "nombre_grupo":   "Grupo 101",
    "supervisor":     "Supervisor Test",
    "meses_activo":   4,
    "score":          9.1,
    "nivel_riesgo":   "critico",
    "señales_activas": ["% Plan cayendo 3 meses seguidos",
                        "% Plan < 80% promedio últimos meses",
                        "En ventana crítica mes 4-6"],
}])

print("=" * 55)
print(f"Destinatario: {alert_to}")
print("=" * 55)

# ── Intento 1: Outlook COM ────────────────────────────────────────────────────
print("\n[1/2] Probando Outlook COM (win32com)...")
try:
    import win32com.client
    print("  pywin32 instalado OK.")
except ImportError:
    print("  pywin32 NO está instalado en este Python.")
    print("  Instalalo con:  pip install pywin32")
    print("  O ejecutá el script con el Python 32-bit donde ya tenés win32com.")
    win32com = None

if 'win32com' in dir() and win32com is not None:
    try:
        enviar_email_outlook(alert_to, vendedor_prueba)
        print("  Email enviado via Outlook COM. Revisa tu bandeja.")
        sys.exit(0)
    except Exception as e:
        print(f"  ERROR Outlook COM: {e}")
        print("  Asegurate de que Outlook esté abierto y con sesión activa.")

# ── Intento 2: SMTP ────────────────────────────────────────────────────────────
print("\n[2/2] Probando SMTP (smtp.office365.com:587)...")
if not (smtp_user and smtp_pwd):
    print("  Faltan SMTP_USER o SMTP_PWD en el .env — no se puede intentar SMTP.")
    print(f"  SMTP_USER={'OK' if smtp_user else 'FALTA'}  SMTP_PWD={'OK' if smtp_pwd else 'FALTA'}")
    print("\nNOTA: Si IT tiene deshabilitado SMTP AUTH para tu tenant, solo funciona")
    print("  el camino de Outlook COM. Instalá pywin32 y asegurate que Outlook esté abierto.")
    sys.exit(1)

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Wurth] 🔴 PRUEBA — alerta de rotación {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"]    = smtp_user
    msg["To"]      = ", ".join(alert_to)
    msg.attach(MIMEText(_email_html(vendedor_prueba), "html", "utf-8"))

    with smtplib.SMTP("smtp.office365.com", 587) as server:
        server.starttls()
        server.login(smtp_user, smtp_pwd)
        server.sendmail(smtp_user, alert_to, msg.as_string())
    print("  Email enviado via SMTP. Revisa tu bandeja.")
except smtplib.SMTPAuthenticationError as e:
    print(f"  ERROR SMTP 535: autenticación fallida.")
    print("  Causa probable: IT tiene SMTP AUTH deshabilitado para el tenant Office 365.")
    print("  Solución: usá el camino Outlook COM (pip install pywin32 + Outlook abierto).")
    print(f"  Detalle: {e}")
    sys.exit(1)
except Exception as e:
    print(f"  ERROR SMTP: {e}")
    sys.exit(1)
