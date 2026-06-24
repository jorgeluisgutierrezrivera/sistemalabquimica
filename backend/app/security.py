"""Primitivas de seguridad: hash de contraseñas (pbkdf2) y tokens JWT.

Decisiones (ver PROMPT MAESTRO / empaquetado con PyInstaller):
- Hash de contraseña con `hashlib.pbkdf2_hmac` (librería estándar → sin
  dependencias nativas que compliquen el .exe).
- Sesión con JWT firmado (HS256) usando PyJWT (Python puro).
- El secreto del JWT se genera al vuelo y se persiste en `data/.jwt_secret`
  (carpeta no versionada). No se hardcodea ningún secreto en el código.
"""

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from .config import DATA_DIR

# --- Parámetros de hashing ---
_HASH_NAME = "sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16

# --- Parámetros del token ---
JWT_ALGORITHM = "HS256"
TOKEN_EXP_HOURS = 12          # Una jornada laboral
_SECRET_PATH = DATA_DIR / ".jwt_secret"


# ============================================================
# Contraseñas
# ============================================================
def hash_password(password: str) -> str:
    """Devuelve un hash serializado: `pbkdf2_<alg>$<iter>$<salt_b64>$<hash_b64>`."""
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(_HASH_NAME, password.encode("utf-8"), salt, _ITERATIONS)
    return (
        f"pbkdf2_{_HASH_NAME}${_ITERATIONS}$"
        f"{base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"
    )


def verify_password(password: str, stored: str) -> bool:
    """Verifica una contraseña contra el hash almacenado (tiempo constante)."""
    try:
        algo, iters, salt_b64, hash_b64 = stored.split("$")
        hash_name = algo.split("_", 1)[1]
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac(hash_name, password.encode("utf-8"), salt, int(iters))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# ============================================================
# JWT
# ============================================================
def _get_secret() -> str:
    """Lee (o genera y persiste) el secreto de firma del JWT."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if _SECRET_PATH.exists():
        return _SECRET_PATH.read_text(encoding="utf-8").strip()
    secret = secrets.token_hex(32)
    _SECRET_PATH.write_text(secret, encoding="utf-8")
    return secret


def create_access_token(claims: dict) -> str:
    """Crea un JWT firmado con expiración de `TOKEN_EXP_HOURS` horas."""
    now = datetime.now(timezone.utc)
    payload = {**claims, "iat": now, "exp": now + timedelta(hours=TOKEN_EXP_HOURS)}
    return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza excepción si es inválido/expirado."""
    return jwt.decode(token, _get_secret(), algorithms=[JWT_ALGORITHM])
