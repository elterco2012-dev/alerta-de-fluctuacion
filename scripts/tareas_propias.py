"""
Vigila que las tareas programadas de alerta sigan siendo suyas (regla 4 de la VM, 24/11).

Para cada tarea de alerta mira qué ejecuta y con qué cuenta corre, y lo compara con lo que tiene que
ser (lo que declara PROYECTO.json). Solo lee: nunca crea, cambia, para ni borra una tarea.

Quién la corre y cómo avisa:
- la corrida diaria (sync_y_alertas.bat, en la sesión del usuario), con --avisar: si una tarea cambió o
  no está, manda un mail a Sistemas (AVISOS_TO en .env) con el Outlook de esa sesión;
- el supervisor del tablero (LOCAL SERVICE), cada 30 minutos: lo anota en data/vigilante.log. Todavía no
  tiene cómo mandar un mail (lo va a tener con Microsoft Graph).
El último resultado queda en data/tareas_propias.json.

Uso, desde la carpeta del proyecto:
    py scripts\\tareas_propias.py            muestra cómo están
    py scripts\\tareas_propias.py --avisar   y si alguna no está bien, manda el mail
Sale con 0 si están bien, 1 si alguna cambió o no está, 2 si alguna no se pudo leer.
"""

import base64
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RESULTADO = RAIZ / "data" / "tareas_propias.json"
SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Las tareas son de producción: van siempre contra esta carpeta, también si esto corre desde la de testing.
PRODUCCION = r"C:\alerta-de-fluctuacion"
LOCAL_SERVICE = "S-1-5-19"
CUENTAS_DE_SERVICIO = {"S-1-5-18", "S-1-5-19", "S-1-5-20"}  # SYSTEM, LOCAL SERVICE, NETWORK SERVICE
NOMBRES_LOCAL_SERVICE = {"local service", "servicio local", "localservice",
                         r"nt authority\local service", r"nt authority\servicio local"}

TAREAS = {
    "WurthAlertasTablero": {
        "ejecuta": PRODUCCION + r"\scripts\supervisor_dashboard.py",
        "cuenta": LOCAL_SERVICE,
    },
    "WurthAlertas": {
        "ejecuta": PRODUCCION + r"\scripts\sync_y_alertas.bat",
        "cuenta": "usuario",  # la del usuario, con su sesión: nunca SYSTEM ni una cuenta de servicio
    },
}

# Lee una tarea de la carpeta raíz del Programador (el nombre va por variable de entorno, sin escaparlo).
# Responde un JSON; si la tarea no existe, existe = false; si no la puede leer, sale con 3.
# Va con -EncodedCommand: así no hay comillas ni saltos de línea que escapar.
_LEER_TAREA = r"""
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try { $t = Get-ScheduledTask -TaskPath '\' -TaskName $env:ALERTA_TAREA }
catch {
    if ($_.CategoryInfo.Category -eq 'ObjectNotFound') {
        [pscustomobject]@{ existe = $false } | ConvertTo-Json -Compress
        exit 0
    }
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 3
}
$usuario = [string]$t.Principal.UserId
$sid = $null
if ($usuario -match '^S-1-') { $sid = $usuario }
else { try { $sid = (New-Object System.Security.Principal.NTAccount($usuario)).Translate([System.Security.Principal.SecurityIdentifier]).Value } catch {} }
[pscustomobject]@{
    existe   = $true
    acciones = @($t.Actions | ForEach-Object { ([string]$_.Execute + ' ' + [string]$_.Arguments).Trim() })
    cuenta   = $usuario
    sid      = $sid
    inicio   = [string]$t.Principal.LogonType
    nivel    = [string]$t.Principal.RunLevel
} | ConvertTo-Json -Compress
"""


class NoSePudoLeer(RuntimeError):
    pass


def leer(nombre: str) -> dict:
    codificado = base64.b64encode(_LEER_TAREA.encode("utf-16-le")).decode("ascii")
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", codificado],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
            creationflags=SIN_VENTANA, env={**os.environ, "ALERTA_TAREA": nombre})
    except (OSError, subprocess.TimeoutExpired) as e:
        raise NoSePudoLeer(str(e)) from e
    if r.returncode != 0:
        raise NoSePudoLeer((r.stderr or r.stdout).strip()[:300] or f"PowerShell salió con {r.returncode}")
    try:
        return json.loads(r.stdout)
    except ValueError as e:
        raise NoSePudoLeer(f"respuesta inesperada de PowerShell: {r.stdout.strip()[:200]}") from e


def _es_local_service(leida: dict) -> bool:
    return leida.get("sid") == LOCAL_SERVICE or str(leida.get("cuenta", "")).strip().lower() in NOMBRES_LOCAL_SERVICE


def comparar(esperado: dict, leida: dict) -> tuple[str, str]:
    """Devuelve (estado, detalle). Estado: «bien», «cambió» o «no está»."""
    if not leida.get("existe"):
        return "no está", "no existe en el Programador de tareas"
    problemas = []
    acciones = leida.get("acciones") or []
    if isinstance(acciones, str):
        acciones = [acciones]
    if len(acciones) != 1 or esperado["ejecuta"].lower() not in acciones[0].lower():
        problemas.append("ejecuta " + " | ".join(acciones) if acciones else "no ejecuta nada")
    cuenta = f"{leida.get('cuenta')} ({leida.get('inicio')})"
    if esperado["cuenta"] == "usuario":
        if leida.get("sid") in CUENTAS_DE_SERVICIO or _es_local_service(leida) or leida.get("inicio") != "Interactive":
            problemas.append(f"corre con {cuenta}, no con la sesión del usuario")
    elif esperado["cuenta"] == LOCAL_SERVICE and not _es_local_service(leida):
        problemas.append(f"corre con {cuenta}, no con LOCAL SERVICE")
    if leida.get("nivel") != "Limited":
        problemas.append(f"con privilegios «{leida.get('nivel')}»")
    return ("cambió", "; ".join(problemas)) if problemas else ("bien", "")


def revisar(propia: str | None = None) -> list[dict]:
    """Revisa las tareas. `propia` es la tarea que está corriendo esto (el supervisor pasa la suya).

    Windows no le muestra a una cuenta las tareas que no puede leer: si quien revisa no ve ni su propia
    tarea, que sí existe, un «no está» no dice nada y queda como «no se pudo leer».
    """
    resultados = []
    for nombre, esperado in TAREAS.items():
        try:
            estado, detalle = comparar(esperado, leer(nombre))
        except NoSePudoLeer as e:
            estado, detalle = "no se pudo leer", str(e)
        resultados.append({"tarea": nombre, "estado": estado, "detalle": detalle})
    if propia and any(r["tarea"] == propia and r["estado"] == "no está" for r in resultados):
        for r in resultados:
            if r["estado"] == "no está":
                r["estado"], r["detalle"] = "no se pudo leer", "esta cuenta no ve las tareas del Programador"
    return resultados


def resumen(resultados: list[dict]) -> str:
    return "; ".join(f"{r['tarea']}: {r['estado']}" + (f" ({r['detalle']})" if r["detalle"] else "")
                     for r in resultados)


def guardar(resultados: list[dict]) -> None:
    RESULTADO.parent.mkdir(exist_ok=True)
    datos = {"revisado": f"{datetime.now():%Y-%m-%d %H:%M:%S}", "tareas": resultados}
    RESULTADO.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def _cargar_env() -> None:
    env = RAIZ / ".env"
    if not env.exists():
        return
    try:
        texto = env.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return
    for linea in texto.splitlines():
        if "=" in linea and not linea.strip().startswith("#"):
            clave, valor = linea.strip().split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())


def avisar(malas: list[dict]) -> None:
    _cargar_env()
    destinatarios = [d.strip() for d in os.getenv("AVISOS_TO", "").split(",") if d.strip()]
    if not destinatarios:
        print("  No hay a quién avisar: falta AVISOS_TO en .env (el mail de Sistemas).")
        return
    sys.path.insert(0, str(RAIZ / "src"))
    from alertas import enviar_aviso_outlook

    lineas = [f"- {r['tarea']}: {r['estado']}. {r['detalle']}" for r in malas]
    texto = (
        "Una tarea programada de alerta de fluctuación ya no es como la dejó el proyecto:\n\n"
        + "\n".join(lineas)
        + "\n\nPuede ser que otra instalación la haya pisado. No la toques con -Force ni /F: mirá en la VM qué "
          "ejecuta y con qué cuenta (Get-ScheduledTask), y avisá por el buzón de conocimiento-wurth. Para "
          "volver a crearla: scripts\\programar_dashboard.bat (WurthAlertasTablero) o scripts\\programar_alertas.bat "
          "(WurthAlertas), que no tocan una tarea ajena.\n"
    )
    enviar_aviso_outlook(destinatarios, "[Wurth] Aviso: una tarea de alerta de fluctuación cambió", texto)
    print(f"  Aviso mandado a {len(destinatarios)} destinatario(s).")


def main() -> int:
    resultados = revisar()
    for r in resultados:
        print(f"  {r['tarea']}: {r['estado']}" + (f" ({r['detalle']})" if r["detalle"] else ""))
    guardar(resultados)
    malas = [r for r in resultados if r["estado"] in ("cambió", "no está")]
    if malas and "--avisar" in sys.argv[1:]:
        try:
            avisar(malas)
        except Exception as e:  # el aviso nunca hace fallar la corrida diaria
            print(f"  No se pudo mandar el aviso: {e}")
    if malas:
        return 1
    return 2 if any(r["estado"] == "no se pudo leer" for r in resultados) else 0


if __name__ == "__main__":
    sys.exit(main())
