"""
alertas.py
----------
Detección y envío de alertas cuando un vendedor sube a nivel crítico.
Soporta Teams (webhook) y email (SMTP).

Uso típico (desde enviar_alertas.py):
    estado = cargar_estado()
    nuevos = detectar_nuevos_criticos(scores_df, estado)
    if not nuevos.empty:
        enviar_teams(webhook_url, nuevos)
        guardar_estado(scores_df)
"""

import json
import smtplib
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
import pandas as pd

ESTADO_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'estado_alertas.json')

def _fmt_ant(m):
    if m < 12:
        return f"{m} mes{'es' if m != 1 else ''}"
    a = m // 12; r = m % 12
    s = f"{a} año{'s' if a != 1 else ''}"
    return s + (f" y {r} mes{'es' if r != 1 else ''}" if r else "")


SEÑAL_CORTA = {
    "% Plan cayendo 3 meses seguidos":    "caída 3m",
    "% Plan < 80% promedio últimos meses":"plan<80%",
    "Días sin venta > 3 en promedio":     "días cero↑",
    "< 60% de cartera activa":            "inactivos↑",
    "Cobranza real < 90% de teórica":     "cobranza baja",
    "En ventana crítica mes 1-3":         "onboarding",
    "En ventana crítica mes 4-6":         "mes 4-6",
    "Grupo con alta rotación histórica":  "zona quemada",
    "Sin clientes nuevos últimos 2 meses":"clientes L:0",
}


# ── Estado persistido ──────────────────────────────────────────────────────────

def cargar_estado() -> dict:
    """Lee el estado de la última ejecución (qué vendors ya eran críticos)."""
    if not os.path.exists(ESTADO_PATH):
        return {"criticos": [], "ultima_ejecucion": None}
    with open(ESTADO_PATH) as f:
        return json.load(f)


def guardar_estado(scores: pd.DataFrame) -> None:
    """Persiste el conjunto de vendors críticos del run actual."""
    criticos = scores[scores.nivel_riesgo == "critico"]["id_vendedor"].astype(int).tolist()
    estado = {
        "criticos": criticos,
        "ultima_ejecucion": datetime.now().isoformat(timespec="seconds"),
    }
    os.makedirs(os.path.dirname(ESTADO_PATH), exist_ok=True)
    with open(ESTADO_PATH, "w") as f:
        json.dump(estado, f, indent=2)


# ── Detección ──────────────────────────────────────────────────────────────────

def detectar_nuevos_criticos(scores: pd.DataFrame, estado: dict) -> pd.DataFrame:
    """
    Retorna los vendors que pasaron a crítico desde el último chequeo.
    Si no hay estado previo (primer run), alerta sobre todos los críticos actuales.
    """
    criticos_previos = set(estado.get("criticos", []))
    criticos_ahora   = scores[scores.nivel_riesgo == "critico"]
    return criticos_ahora[~criticos_ahora["id_vendedor"].isin(criticos_previos)].copy()


# ── Formato Teams ──────────────────────────────────────────────────────────────

def _teams_payload(nuevos: pd.DataFrame) -> dict:
    """
    Genera payload Adaptive Card para Teams (compatible con Workflows / Power Automate).
    También funciona con webhooks legacy de Teams.
    """
    n = len(nuevos)
    titulo = f"🔴 {n} vendedor{'es' if n > 1 else ''} nuevo{'s' if n > 1 else ''} en nivel CRÍTICO"

    facts = []
    for _, r in nuevos.iterrows():
        señales = " · ".join(
            SEÑAL_CORTA.get(s, s) for s in r["señales_activas"][:4]
        ) or "sin señales registradas"
        nombre = r.get("nombre") or f"ID {int(r['id_vendedor'])}"
        facts.append({
            "title": f"{nombre} ({int(r['id_vendedor'])}) — {r['nombre_grupo']}",
            "value": f"{r['tipo']} · {_fmt_ant(r['meses_activo'])} · Score {r['score']}/10 | {señales}",
        })

    return {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": titulo,
                        "weight": "Bolder",
                        "size": "Medium",
                        "color": "Attention",
                        "wrap": True,
                    },
                    {
                        "type": "TextBlock",
                        "text": f"Wurth Argentina · {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                        "isSubtle": True,
                        "size": "Small",
                        "spacing": "None",
                    },
                    {"type": "Separator"},
                    {
                        "type": "FactSet",
                        "facts": facts,
                    },
                    {
                        "type": "TextBlock",
                        "text": "Acción recomendada: contactar al supervisor de cada zona hoy.",
                        "wrap": True,
                        "spacing": "Medium",
                        "isSubtle": True,
                    },
                ],
            },
        }],
    }


def enviar_teams(webhook_url: str, nuevos: pd.DataFrame) -> bool:
    """
    Envía alerta a Teams via webhook.
    webhook_url: URL del conector "Incoming Webhook" o flujo de Power Automate.
    Retorna True si el envío fue exitoso.
    """
    payload = _teams_payload(nuevos)
    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()
    return True


# ── Formato Email ──────────────────────────────────────────────────────────────

def _email_html(nuevos: pd.DataFrame) -> str:
    n = len(nuevos)
    filas = ""
    for _, r in nuevos.iterrows():
        señales = ", ".join(SEÑAL_CORTA.get(s, s) for s in r["señales_activas"][:4]) or "—"
        nombre = r.get("nombre") or f"ID {int(r['id_vendedor'])}"
        filas += f"""
        <tr>
          <td style="padding:10px 14px;font-weight:bold;">{nombre}<br>
              <span style="font-weight:normal;font-size:11px;color:#999;">({int(r['id_vendedor'])})</span></td>
          <td style="padding:10px 14px;">{r['tipo']}</td>
          <td style="padding:10px 14px;">{r['nombre_grupo']}</td>
          <td style="padding:10px 14px;">{r['supervisor']}</td>
          <td style="padding:10px 14px;">{_fmt_ant(r['meses_activo'])}</td>
          <td style="padding:10px 14px;background:#FDECEA;font-weight:bold;text-align:center;">
            {r['score']}/10
          </td>
          <td style="padding:10px 14px;font-size:12px;color:#666;">{señales}</td>
        </tr>"""

    return f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:800px;margin:0 auto;">
      <div style="background:#E24B4A;color:white;padding:20px 24px;border-radius:8px 8px 0 0;">
        <h2 style="margin:0;">🔴 Alerta de rotación — Wurth Argentina</h2>
        <p style="margin:6px 0 0;opacity:.85;">
          {n} vendedor{'es' if n > 1 else ''} {'alcanzaron' if n > 1 else 'alcanzó'} nivel CRÍTICO
          · {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
      </div>
      <div style="background:white;border:1px solid #eee;border-top:none;
                  border-radius:0 0 8px 8px;padding:20px 24px;">
        <table style="width:100%;border-collapse:collapse;">
          <thead>
            <tr style="background:#f8f9fa;font-size:12px;color:#666;">
              <th style="padding:10px 14px;text-align:left;">ID</th>
              <th style="padding:10px 14px;text-align:left;">Tipo</th>
              <th style="padding:10px 14px;text-align:left;">Zona</th>
              <th style="padding:10px 14px;text-align:left;">Supervisor</th>
              <th style="padding:10px 14px;text-align:left;">Antigüedad</th>
              <th style="padding:10px 14px;text-align:left;">Score</th>
              <th style="padding:10px 14px;text-align:left;">Señales</th>
            </tr>
          </thead>
          <tbody>{filas}</tbody>
        </table>
        <p style="margin-top:20px;font-size:13px;color:#888;border-top:1px solid #eee;padding-top:16px;">
          Acción recomendada: contactar al supervisor de cada zona hoy.<br>
          Este mensaje es generado automáticamente por el sistema de alertas de Wurth Argentina.
        </p>
      </div>
    </body></html>"""


def enviar_email_outlook(to: list, nuevos: pd.DataFrame) -> bool:
    """
    Envía alerta usando Outlook instalado via COM (win32com).
    No requiere contraseña ni SMTP AUTH — usa la sesión de Outlook activa.
    """
    import win32com.client
    n = len(nuevos)
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = "; ".join(to)
    mail.Subject = f"[Wurth] 🔴 {n} vendedor{'es' if n > 1 else ''} en nivel crítico — {datetime.now().strftime('%d/%m/%Y')}"
    mail.HTMLBody = _email_html(nuevos)
    mail.Send()
    return True


def enviar_email(smtp_config: dict, nuevos: pd.DataFrame) -> bool:
    """
    Envía alerta por email. Intenta primero via Outlook COM (sin SMTP AUTH),
    con fallback a SMTP si Outlook no está disponible.
    """
    to = smtp_config.get("to", [])
    try:
        return enviar_email_outlook(to, nuevos)
    except Exception:
        pass

    # Fallback SMTP
    n = len(nuevos)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Wurth] 🔴 {n} vendedor{'es' if n > 1 else ''} en nivel crítico — {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"]    = smtp_config["user"]
    msg["To"]      = ", ".join(to)
    msg.attach(MIMEText(_email_html(nuevos), "html", "utf-8"))

    with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
        server.starttls()
        server.login(smtp_config["user"], smtp_config["password"])
        server.sendmail(smtp_config["user"], to, msg.as_string())
    return True
