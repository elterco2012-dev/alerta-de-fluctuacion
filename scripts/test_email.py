"""test_email.py — Envía un email de prueba para verificar SMTP."""
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
from alertas import enviar_email
import pandas as pd

smtp_user = os.getenv("SMTP_USER", "")
smtp_pwd  = os.getenv("SMTP_PWD", "")
alert_to  = [e.strip() for e in os.getenv("ALERT_TO", "").split(",") if e.strip()]

if not (smtp_user and smtp_pwd and alert_to):
    print("Faltan SMTP_USER, SMTP_PWD o ALERT_TO en el .env")
    print(f"  SMTP_USER={'OK' if smtp_user else 'FALTA'}  "
          f"SMTP_PWD={'OK' if smtp_pwd else 'FALTA'}  "
          f"ALERT_TO={'OK' if alert_to else 'FALTA'}")
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

print(f"Enviando email de prueba a {alert_to}...")
try:
    enviar_email({
        "host":     "smtp.office365.com",
        "port":     587,
        "user":     smtp_user,
        "password": smtp_pwd,
        "to":       alert_to,
    }, vendedor_prueba)
    print("Email enviado OK. Revisá tu bandeja de entrada.")
except Exception as e:
    print(f"ERROR: {e}")
