"""Supervisor del tablero de producción (puerto 8501).

Lo arranca la tarea WurthAlertasTablero con pythonw.exe (sin ventana) y con la cuenta LOCAL SERVICE, sin
privilegios y nunca como SYSTEM. Levanta el tablero, comprueba cada 2 minutos que responda y, si no, lo reinicia.
Solo cierra sus propios procesos: los que tienen C:\\alerta-de-fluctuacion\\dashboard.py en la línea de comando
(regla de la VM: nunca por nombre ni por puerto). Si el puerto lo ocupa otro proceso, lo anota y no lo toca.
Lo que hace queda en data/vigilante.log y la salida de Streamlit en data/streamlit.log.
Cada 30 minutos revisa también que las tareas de alerta sigan siendo suyas (tareas_propias.py) y anota lo que cambie.
"""
import ctypes
import os
import subprocess
import sys
import time
import traceback
import urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TABLERO = RAIZ / "dashboard.py"
PUERTO = 8501
CADA_SEG = 120
FALLAS_PARA_REINICIAR = 2
CADA_SEG_TAREAS = 30 * 60
LOG = RAIZ / "data" / "vigilante.log"
SALIDA_STREAMLIT = RAIZ / "data" / "streamlit.log"
SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Busca los procesos por la ruta completa del tablero en su línea de comando. La ruta va por variable de entorno
# para no tener que escaparla.
_BUSCAR_PROPIOS = (
    "Get-CimInstance Win32_Process | "
    "Where-Object { ($_.Name -eq 'python.exe' -or $_.Name -eq 'pythonw.exe') -and "
    "$_.CommandLine -like ('*' + $env:ALERTA_TABLERO + '*') } | "
    "ForEach-Object { $_.ProcessId }"
)


def anotar(texto: str) -> None:
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {texto}\n")


def responde() -> bool:
    sin_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with sin_proxy.open(f"http://127.0.0.1:{PUERTO}/_stcore/health", timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def pids_del_tablero() -> set[int]:
    """Procesos de este tablero: los que tienen su dashboard.py, con la ruta completa, en la línea de comando."""
    salida = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", _BUSCAR_PROPIOS],
        capture_output=True, text=True, errors="replace", creationflags=SIN_VENTANA,
        env={**os.environ, "ALERTA_TABLERO": str(TABLERO)}).stdout
    return {int(x) for x in salida.split() if x.isdigit()}


def pids_escuchando(salida_netstat: str, puerto: int) -> set[int]:
    """PIDs que escuchan en el puerto según `netstat -ano`. No mira el estado, que viene traducido."""
    pids = set()
    for linea in salida_netstat.splitlines():
        partes = linea.split()
        if (len(partes) == 5 and partes[0].upper().startswith("TCP")
                and partes[1].rsplit(":", 1)[-1] == str(puerto)
                and partes[2] in ("0.0.0.0:0", "[::]:0")
                and partes[4].isdigit() and int(partes[4]) > 4):
            pids.add(int(partes[4]))
    return pids


def pids_en_el_puerto() -> set[int]:
    salida = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, errors="replace",
                            creationflags=SIN_VENTANA).stdout
    return pids_escuchando(salida, PUERTO)


def detener(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=SIN_VENTANA)


def python_de_consola() -> str:
    # pythonw.exe no tiene salida de consola: Streamlit corre con el python.exe de la misma instalación
    exe = Path(sys.executable)
    candidato = exe.with_name("python.exe")
    return str(candidato if candidato.exists() else exe)


def iniciar() -> None:
    entorno = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    with open(SALIDA_STREAMLIT, "a", encoding="utf-8") as salida:
        proceso = subprocess.Popen(
            [python_de_consola(), "-m", "streamlit", "run", str(TABLERO),
             "--server.port", str(PUERTO), "--server.headless", "true",
             "--server.address", "0.0.0.0", "--browser.gatherUsageStats", "false"],
            cwd=RAIZ, env=entorno, stdin=subprocess.DEVNULL, stdout=salida, stderr=subprocess.STDOUT,
            creationflags=SIN_VENTANA)
    anotar(f"tablero iniciado (proceso {proceso.pid})")


def reiniciar(motivo: str) -> None:
    anotar(motivo)
    for pid in pids_del_tablero():
        detener(pid)
        anotar(f"detenido el proceso {pid} del tablero")
    time.sleep(5)
    ajenos = pids_en_el_puerto()
    if ajenos:
        anotar(f"el puerto {PUERTO} lo ocupa otro proceso ({', '.join(map(str, sorted(ajenos)))}), "
               "que no es de este tablero: no lo toco")
    iniciar()


def revisar_tareas(anterior: str) -> str:
    """Revisa que las tareas de alerta sigan siendo suyas; anota solo cuando el resultado cambia."""
    try:
        import tareas_propias
        resultados = tareas_propias.revisar(propia="WurthAlertasTablero")
        tareas_propias.guardar(resultados)
        actual = tareas_propias.resumen(resultados)
    except Exception as e:
        actual = f"no pude revisar las tareas ({e})"
    if actual != anterior:
        anotar("tareas de alerta: " + actual)
    return actual


def es_el_unico_supervisor() -> bool:
    # Si alguien lo corre a mano con la tarea andando, el segundo se va sin hacer nada.
    if os.name != "nt":
        return True
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW(None, False, "Local\\WurthAlertaSupervisor")
    return ctypes.get_last_error() != 183  # ERROR_ALREADY_EXISTS


def main() -> None:
    if not es_el_unico_supervisor():
        return
    anotar("supervisor iniciado")
    if not responde():
        reiniciar("el tablero no respondía al iniciar el supervisor; lo levanto")
    fallas = 0
    tareas = revisar_tareas("")
    proxima_revision = time.monotonic() + CADA_SEG_TAREAS
    while True:
        time.sleep(CADA_SEG)
        try:
            if time.monotonic() >= proxima_revision:
                proxima_revision = time.monotonic() + CADA_SEG_TAREAS
                tareas = revisar_tareas(tareas)
            if responde():
                fallas = 0
                continue
            fallas += 1
            anotar(f"el tablero no respondió ({fallas} control(es) seguido(s))")
            if not pids_del_tablero():
                reiniciar("el tablero no estaba corriendo; lo levanto")
                fallas = 0
            elif fallas >= FALLAS_PARA_REINICIAR:
                reiniciar("el tablero sigue sin responder; lo reinicio")
                fallas = 0
        except Exception:
            anotar("error en el supervisor:\n" + traceback.format_exc())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        anotar("el supervisor se detuvo por un error:\n" + traceback.format_exc())
        raise
