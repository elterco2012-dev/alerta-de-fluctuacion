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
import glob
import time
import subprocess
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
    "En ventana crítica mes 1-3":         "onboarding",
    "En ventana crítica mes 4-6":         "mes 4-6",
    "Grupo con alta rotación histórica":  "zona quemada",
    "Sin clientes nuevos últimos 2 meses":"sin nuevos",
    "Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3": "ausencias↑",
    "Balanza clientes negativa 2+ meses consecutivos": "balanza−",
    "Ticket promedio cae > 5% por mes":   "ticket↓",
    "Supervisor no acompañó en ventana crítica 1-6": "sin acomp.",
}


# ── Estado persistido ──────────────────────────────────────────────────────────
# Formato: {"criticos": {"1234": "2026-06-04T10:00:00", ...}, "ultima_ejecucion": "..."}
# La clave es el id_vendedor (str), el valor es el timestamp de la ÚLTIMA alerta enviada.

def cargar_estado() -> dict:
    """Lee el estado de la última ejecución."""
    if not os.path.exists(ESTADO_PATH):
        return {"criticos": {}, "ultima_ejecucion": None}
    with open(ESTADO_PATH) as f:
        estado = json.load(f)
    # Migración: formato viejo era una lista, nuevo es un dict con timestamps.
    if isinstance(estado.get("criticos"), list):
        estado["criticos"] = {str(v): None for v in estado["criticos"]}
    return estado


def guardar_estado(scores: pd.DataFrame, alertados_ids: set) -> None:
    """
    Persiste el estado después del run.
    - Vendedores que siguen críticos pero NO se alertaron esta vez → mantener timestamp anterior
    - Vendedores que se alertaron → actualizar timestamp a ahora
    - Vendedores que bajaron de crítico → eliminar
    """
    estado_prev = cargar_estado()
    prev        = estado_prev.get("criticos", {})
    ahora_ts    = datetime.now().isoformat(timespec="seconds")

    criticos_ids = set(
        str(int(v)) for v in scores.loc[scores.nivel_riesgo == "critico", "id_vendedor"]
    )
    nuevo_estado: dict[str, str | None] = {}
    for vid in criticos_ids:
        if vid in alertados_ids:
            nuevo_estado[vid] = ahora_ts        # se alertó ahora → actualizar
        else:
            nuevo_estado[vid] = prev.get(vid)   # sigue crítico pero no se alertó → conservar

    estado = {
        "criticos": nuevo_estado,
        "ultima_ejecucion": ahora_ts,
    }
    os.makedirs(os.path.dirname(ESTADO_PATH), exist_ok=True)
    with open(ESTADO_PATH, "w") as f:
        json.dump(estado, f, indent=2)


# ── Detección ──────────────────────────────────────────────────────────────────

def detectar_nuevos_criticos(scores: pd.DataFrame, estado: dict,
                             dias_realerta: int = 7) -> pd.DataFrame:
    """
    Retorna los vendors que hay que alertar en este run:
    - Vendedores que acaban de llegar a crítico (no estaban en estado previo)
    - Vendedores que siguen críticos y pasaron `dias_realerta` días desde la última alerta

    Si no hay estado previo (primer run), alerta sobre todos los críticos actuales.
    """
    criticos_prev = estado.get("criticos", {})   # {str(id): "ISO datetime" | None}
    criticos_ahora = scores[scores.nivel_riesgo == "critico"].copy()
    ahora = datetime.now()

    def _debe_alertar(vid: int) -> bool:
        key = str(vid)
        if key not in criticos_prev:
            return True   # nuevo crítico
        ultima_str = criticos_prev[key]
        if ultima_str is None:
            return True   # estado migrado sin timestamp → alertar
        ultima = datetime.fromisoformat(ultima_str)
        return (ahora - ultima).days >= dias_realerta

    mask = criticos_ahora["id_vendedor"].apply(lambda v: _debe_alertar(int(v)))
    return criticos_ahora[mask].copy()


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


def _buscar_outlook_clasico() -> str | None:
    """
    Devuelve la ruta del OUTLOOK.EXE clásico de Office, o None si no lo encuentra.
    El 'nuevo Outlook' no soporta COM; necesitamos el OUTLOOK.EXE del Office clásico.

    IMPORTANTE: no usa App Paths del registro porque puede apuntar al nuevo Outlook.
    Busca directamente en los directorios de instalación de Office.
    """
    # Rutas de Office clásico (Office 2016/2019/365, 32 y 64 bits)
    patrones = [
        r"C:\Program Files\Microsoft Office\root\Office*\OUTLOOK.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office*\OUTLOOK.EXE",
        r"C:\Program Files\Microsoft Office\Office*\OUTLOOK.EXE",
        r"C:\Program Files (x86)\Microsoft Office\Office*\OUTLOOK.EXE",
    ]
    for patron in patrones:
        for ruta in glob.glob(patron):
            if os.path.exists(ruta):
                return ruta

    # Fallback: registro (podría apuntar al nuevo, pero vale intentar)
    try:
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(
                    hive,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE",
                ) as k:
                    ruta = winreg.QueryValue(k, None).strip('"')
                    if ruta and os.path.exists(ruta):
                        return ruta
            except OSError:
                continue
    except Exception:
        pass
    return None


def _obtener_outlook(timeout: int = 90, _verbose: bool = False):
    """
    Devuelve un objeto COM de Outlook clásico listo para usar.

    Estrategia:
      1. Conectar a una instancia ya corriendo (GetActiveObject).
      2. Si no hay, localizar OUTLOOK.EXE clásico, lanzarlo SIN flags y esperar
         hasta `timeout` segundos a que registre el servidor COM.
         (No usamos /recycle: ese flag puede ceder el control al nuevo Outlook.)
    """
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()

    # 1. ¿Hay un Outlook clásico ya corriendo?
    try:
        return win32com.client.GetActiveObject("Outlook.Application")
    except Exception:
        pass

    # 2. Lanzar el clásico explícitamente
    exe = _buscar_outlook_clasico()
    if not exe:
        raise RuntimeError(
            "No se encontró el Outlook clásico (OUTLOOK.EXE). El 'nuevo Outlook' "
            "no soporta automatización COM."
        )
    if _verbose:
        print(f"  Lanzando: {exe}")
    # DETACHED_PROCESS: corre en segundo plano sin consola propia
    subprocess.Popen([exe], creationflags=0x00000008)  # DETACHED_PROCESS
    # Outlook tarda ~15s en registrar el servidor COM; esperamos con backoff
    esperas = [5, 5, 5, 5, 5, 10, 10, 10, 10, 10, 15]  # suma = 90s
    ultimo_err = None
    for espera in esperas:
        time.sleep(espera)
        try:
            ol = win32com.client.GetActiveObject("Outlook.Application")
            return ol
        except Exception as e:
            ultimo_err = e
    raise RuntimeError(
        f"Se lanzó el Outlook clásico ({exe}) pero no respondió en {timeout}s. "
        f"Último error: {ultimo_err}"
    )


def enviar_email_outlook(to: list, nuevos: pd.DataFrame) -> bool:
    """
    Envía alerta usando el Outlook clásico via COM (win32com).
    No requiere contraseña ni SMTP AUTH. Si el clásico no está abierto, lo
    levanta solo en segundo plano (ver `_obtener_outlook`).
    """
    n = len(nuevos)
    outlook = _obtener_outlook()
    mail = outlook.CreateItem(0)
    mail.To = "; ".join(to)
    mail.Subject = f"[Wurth] 🔴 {n} vendedor{'es' if n > 1 else ''} en nivel crítico — {datetime.now().strftime('%d/%m/%Y')}"
    mail.HTMLBody = _email_html(nuevos)
    mail.Send()
    return True


def enviar_email(smtp_config: dict, nuevos: pd.DataFrame) -> bool:
    """
    Envía alerta por email. Intenta primero via Outlook COM (sin SMTP AUTH),
    con fallback a SMTP solo si pywin32 no está instalado.

    Si win32com está instalado pero Outlook falla (ej: no está abierto), el error
    se propaga — no se intenta SMTP porque el tenant tiene SMTP AUTH deshabilitado.
    """
    to = smtp_config.get("to", [])
    try:
        import win32com.client  # noqa: F401 — solo para detectar si está instalado
        return enviar_email_outlook(to, nuevos)
    except ImportError:
        pass   # pywin32 no instalado → caer a SMTP

    # Fallback SMTP (solo cuando win32com no está disponible)
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
