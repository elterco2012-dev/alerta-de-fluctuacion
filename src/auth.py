"""
src/auth.py
-----------
Autenticación con usuario + contraseña para el dashboard.

Almacena los usuarios en data/auth.json (gitignoreado).
Contraseñas hasheadas con PBKDF2-SHA256 (200.000 iteraciones).
Bloqueo por usuario tras 5 intentos fallidos (15 minutos).

Gestión de usuarios desde la línea de comando (la clave se pide en pantalla):
    scripts/usuarios.bat alta <usuario> "<clave_acceso>"
    scripts/usuarios.bat baja <usuario>
    scripts/usuarios.bat lista
    scripts/usuarios.bat clave <usuario>

`clave_acceso` es el nombre tal como aparece en acceso.py (ej. "Gerencia",
"Zerbatto Jose Luis"). Define el rol y el alcance del usuario.

La sesión sobrevive a la navegación entre páginas (cada enlace abre una sesión nueva de Streamlit) con una
cookie firmada con HMAC: dura 8 horas y deja de valer si al usuario lo dan de baja, le cambian el acceso o la clave.
"""

from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional

_BASE = os.path.join(os.path.dirname(__file__), "..", "data")
_AUTH_FILE = os.path.join(_BASE, "auth.json")
_FAILS_FILE = os.path.join(_BASE, "auth_fails.json")
_CLAVE_SESION_FILE = os.path.join(_BASE, "sesion.key")

ITERACIONES  = 200_000
MAX_FALLOS   = 5
VENTANA_LOCK = 15 * 60   # segundos
COOKIE_SESION = "alerta_sesion"
HORAS_SESION  = 8

# ── Hashing ───────────────────────────────────────────────────────────────────

def _hash(clave: str) -> str:
    sal = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), ITERACIONES).hex()
    return f"pbkdf2_sha256${ITERACIONES}${sal}${h}"


def _verificar(clave: str, guardado: str) -> bool:
    try:
        _, it, sal, h = guardado.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), int(it)).hex()
        return hmac.compare_digest(calc, h)
    except Exception:
        return False


# ── Persistencia ──────────────────────────────────────────────────────────────

def _leer_auth() -> dict:
    try:
        with open(_AUTH_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {"usuarios": {}}


def _guardar_auth(data: dict) -> None:
    os.makedirs(_BASE, exist_ok=True)
    with open(_AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _leer_fails() -> dict:
    try:
        with open(_FAILS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}


def _guardar_fails(data: dict) -> None:
    os.makedirs(_BASE, exist_ok=True)
    with open(_FAILS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


# ── Sesión firmada (cookie) ───────────────────────────────────────────────────

def _clave_sesion() -> bytes:
    """Clave secreta para firmar las sesiones. Se crea la primera vez en data/ (que no se sube al repo)."""
    try:
        with open(_CLAVE_SESION_FILE, "rb") as f:
            clave = f.read()
        if len(clave) >= 32:
            return clave
    except FileNotFoundError:
        pass
    os.makedirs(_BASE, exist_ok=True)
    try:
        with open(_CLAVE_SESION_FILE, "xb") as f:
            f.write(secrets.token_bytes(32))
    except FileExistsError:
        pass  # otra sesión la creó recién
    with open(_CLAVE_SESION_FILE, "rb") as f:
        return f.read()


def _huella(hash_clave: str) -> str:
    # Cambia si cambia la clave, sin exponer el hash.
    return hashlib.sha256(hash_clave.encode()).hexdigest()[:16]


def _firmar(cuerpo: str) -> str:
    return hmac.new(_clave_sesion(), cuerpo.encode(), hashlib.sha256).hexdigest()


def crear_token_sesion(usuario: str) -> Optional[str]:
    u = _leer_auth().get("usuarios", {}).get(usuario.lower())
    if not u:
        return None
    datos = {"u": usuario.lower(), "a": u["clave_acceso"], "h": _huella(u["hash"]),
             "exp": int(time.time()) + HORAS_SESION * 3600}
    cuerpo = base64.urlsafe_b64encode(json.dumps(datos, separators=(",", ":")).encode()).decode().rstrip("=")
    return f"{cuerpo}.{_firmar(cuerpo)}"


def usuario_de_token(token: Optional[str]) -> Optional[tuple[str, str]]:
    """(usuario, clave_acceso) si el token es auténtico, no venció y el usuario sigue igual; si no, None."""
    if not token or "." not in token:
        return None
    cuerpo, firma = token.rsplit(".", 1)
    if not hmac.compare_digest(firma, _firmar(cuerpo)):
        return None
    try:
        datos = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
    except ValueError:
        return None
    if datos.get("exp", 0) < time.time():
        return None
    u = _leer_auth().get("usuarios", {}).get(datos.get("u", ""))
    if (not u or not u.get("activo", True) or u.get("clave_acceso") != datos.get("a")
            or _huella(u["hash"]) != datos.get("h")):
        return None
    return datos["u"], datos["a"]


# ── Brute-force ───────────────────────────────────────────────────────────────

def _esta_bloqueado(usuario: str) -> tuple[bool, int]:
    """Devuelve (bloqueado, segundos_restantes)."""
    fails = _leer_fails()
    entrada = fails.get(usuario.lower())
    if not entrada:
        return False, 0
    if entrada["count"] < MAX_FALLOS:
        return False, 0
    restante = int(VENTANA_LOCK - (time.time() - entrada["ts"]))
    if restante <= 0:
        return False, 0
    return True, restante


def _registrar_fallo(usuario: str) -> int:
    """Registra un intento fallido. Devuelve el conteo actual."""
    fails = _leer_fails()
    clave = usuario.lower()
    ahora = time.time()
    entrada = fails.get(clave, {"count": 0, "ts": ahora})
    if ahora - entrada["ts"] > VENTANA_LOCK:
        entrada = {"count": 0, "ts": ahora}
    entrada["count"] += 1
    entrada["ts"] = ahora
    fails[clave] = entrada
    _guardar_fails(fails)
    return entrada["count"]


def _limpiar_fallo(usuario: str) -> None:
    fails = _leer_fails()
    fails.pop(usuario.lower(), None)
    _guardar_fails(fails)


# ── API pública ───────────────────────────────────────────────────────────────

def autenticar(usuario: str, clave: str) -> Optional[str]:
    """
    Verifica usuario y contraseña.
    Retorna la `clave_acceso` si es correcto (para pasarla a acceso.resolver()),
    o None si falla. Aplica bloqueo por intentos fallidos.
    """
    bloqueado, restante = _esta_bloqueado(usuario)
    if bloqueado:
        raise ValueError(f"Usuario bloqueado. Intentá en {restante // 60 + 1} minutos.")

    data = _leer_auth()
    u = data.get("usuarios", {}).get(usuario.lower())
    if not u or not u.get("activo", True):
        _registrar_fallo(usuario)
        return None

    if not _verificar(clave, u["hash"]):
        count = _registrar_fallo(usuario)
        restantes = MAX_FALLOS - count
        if restantes <= 0:
            raise ValueError(f"Demasiados intentos fallidos. Usuario bloqueado 15 minutos.")
        return None

    _limpiar_fallo(usuario)
    return u["clave_acceso"]


def crear_usuario(usuario: str, clave: str, clave_acceso: str) -> None:
    """Alta de usuario. Lanza ValueError si ya existe."""
    data = _leer_auth()
    if usuario.lower() in data["usuarios"]:
        raise ValueError(f"El usuario '{usuario}' ya existe.")
    data["usuarios"][usuario.lower()] = {
        "hash": _hash(clave),
        "clave_acceso": clave_acceso,
        "activo": True,
    }
    _guardar_auth(data)


def cambiar_clave(usuario: str, nueva_clave: str) -> None:
    data = _leer_auth()
    u = data["usuarios"].get(usuario.lower())
    if not u:
        raise ValueError(f"Usuario '{usuario}' no encontrado.")
    u["hash"] = _hash(nueva_clave)
    _guardar_auth(data)


def desactivar_usuario(usuario: str) -> None:
    data = _leer_auth()
    u = data["usuarios"].get(usuario.lower())
    if not u:
        raise ValueError(f"Usuario '{usuario}' no encontrado.")
    u["activo"] = False
    _guardar_auth(data)


def listar_usuarios() -> list[dict]:
    data = _leer_auth()
    return [
        {"usuario": k, "clave_acceso": v["clave_acceso"], "activo": v.get("activo", True)}
        for k, v in data.get("usuarios", {}).items()
    ]


# ── Helpers de UI (Streamlit) ──────────────────────────────────────────────────

_LS_KEY = "wurth_auth_usuario"   # solo guarda el nombre de usuario, nunca la clave


def _js_guardar_usuario(usuario: str) -> str:
    import json as _json
    return f"""<script>
(function(){{
  localStorage.setItem({_json.dumps(_LS_KEY)}, {_json.dumps(usuario)});
}})();
</script>"""


def _js_leer_usuario_prefill() -> str:
    """Inyecta JS que lee localStorage y pone el usuario en el campo si existe."""
    import json as _json
    return f"""<script>
(function(){{
  var u = localStorage.getItem({_json.dumps(_LS_KEY)});
  if (!u) return;
  // Poner el valor en el input de Streamlit con el label "Usuario"
  var inputs = window.parent.document.querySelectorAll('input[type="text"]');
  for (var i = 0; i < inputs.length; i++) {{
    var label = inputs[i].closest('[data-testid="stTextInputRootElement"]');
    if (label && label.textContent.indexOf('Usuario') >= 0) {{
      var nativeInput = inputs[i];
      var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(nativeInput, u);
      nativeInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
      break;
    }}
  }}
}})();
</script>"""


def _js_cookie(valor: str, segundos: int) -> str:
    """Pone (o borra, con 0 segundos) la cookie de sesión en el documento del tablero."""
    import json as _json
    return f"""<script>
(function(){{
  var seguro = window.parent.location.protocol === 'https:' ? '; Secure' : '';
  window.parent.document.cookie = {_json.dumps(COOKIE_SESION)} + '=' + {_json.dumps(valor)} +
    '; Path=/; Max-Age={segundos}; SameSite=Strict' + seguro;
}})();
</script>"""


def formulario_login_st() -> None:
    """
    Muestra el formulario de login y detiene la ejecución hasta autenticar.
    Si el login es exitoso, guarda en session_state["_auth_clave_acceso"]
    el valor para pasar a acceso.resolver().
    Antes de mostrar el formulario, recupera la sesión de la cookie firmada si es válida.
    """
    import streamlit as st
    import streamlit.components.v1 as components

    # Si ya está autenticado en esta sesión, no mostrar el formulario.
    if st.session_state.get("_auth_ok"):
        token = st.session_state.pop("_auth_cookie_pendiente", None)
        if token:
            components.html(_js_cookie(token, HORAS_SESION * 3600), height=0)
        return

    if st.session_state.get("_auth_salio"):
        components.html(_js_cookie("", 0), height=0)
    else:
        recuperada = usuario_de_token(st.context.cookies.get(COOKIE_SESION))
        if recuperada:
            st.session_state["_auth_ok"] = True
            st.session_state["_auth_usuario_login"], st.session_state["_auth_clave_acceso"] = recuperada
            return

    st.markdown("""
<div style="max-width:400px;margin:40px auto 0;">
  <div style="font-size:22px;font-weight:800;color:#1a1a2e;margin-bottom:4px;">Würth Argentina</div>
  <div style="font-size:14px;color:#666;margin-bottom:24px;">Sistema de Alertas de Rotación</div>
</div>
""", unsafe_allow_html=True)

    # Intentar pre-rellenar el usuario desde localStorage
    components.html(_js_leer_usuario_prefill(), height=0)

    with st.form("login_form", clear_on_submit=False):
        st.markdown(
            "<div style='max-width:400px;margin:0 auto;'>",
            unsafe_allow_html=True,
        )
        usuario = st.text_input("Usuario", placeholder="tu.usuario")
        clave   = st.text_input("Contraseña", type="password", placeholder="••••••••")
        enviar  = st.form_submit_button("Ingresar →", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if enviar:
        if not usuario or not clave:
            st.error("Ingresá usuario y contraseña.")
            st.stop()
        try:
            clave_acceso = autenticar(usuario.strip(), clave)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        if clave_acceso is None:
            st.error("Usuario o contraseña incorrectos.")
            st.stop()

        # Login exitoso. La cookie se pone en la próxima corrida: con st.rerun() acá, el script no llegaría a correr.
        login = usuario.strip().lower()
        st.session_state.pop("_auth_salio", None)
        st.session_state["_auth_ok"] = True
        st.session_state["_auth_usuario_login"] = login
        st.session_state["_auth_clave_acceso"] = clave_acceso
        st.session_state["_auth_cookie_pendiente"] = crear_token_sesion(login)
        # Guardar nombre de usuario en localStorage (nunca la contraseña)
        components.html(_js_guardar_usuario(login), height=0)
        st.rerun()

    st.stop()


def cerrar_sesion_st() -> None:
    """Limpia la sesión y la cookie, y vuelve al formulario de ingreso."""
    import streamlit as st
    for k in ("_auth_ok", "_auth_clave_acceso", "_auth_usuario_login", "_acc_usuario", "_auth_cookie_pendiente"):
        st.session_state.pop(k, None)
    st.session_state["_auth_salio"] = True   # el formulario borra la cookie y no la vuelve a leer
    st.rerun()
