"""Acceso a datos y lógica del módulo de usuarios / autenticación."""

import sqlite3

from ..database import get_db
from ..security import hash_password, verify_password


def obtener_por_id(usuario_id: int) -> sqlite3.Row | None:
    """Devuelve un usuario activo por su id, o None."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM usuarios WHERE id = ? AND activo = 1",
            (usuario_id,),
        ).fetchone()


def obtener_por_usuario(nombre_usuario: str) -> sqlite3.Row | None:
    """Devuelve un usuario activo por su nombre de login, o None."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM usuarios WHERE nombre_usuario = ? AND activo = 1",
            (nombre_usuario,),
        ).fetchone()


def contar_usuarios() -> int:
    """Total de usuarios registrados (para saber si hay que crear el admin)."""
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]


def crear_usuario(
    nombre_usuario: str,
    password: str,
    nombre_completo: str | None = None,
    rol: str = "administrador",
) -> int:
    """Crea un usuario con la contraseña ya hasheada. Devuelve su id.

    Lanza ValueError si el nombre de usuario ya existe.
    """
    try:
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO usuarios (nombre_usuario, nombre_completo, password_hash, rol) "
                "VALUES (?, ?, ?, ?)",
                (nombre_usuario, nombre_completo, hash_password(password), rol),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"El usuario '{nombre_usuario}' ya existe.") from exc


def autenticar(nombre_usuario: str, password: str) -> sqlite3.Row | None:
    """Valida credenciales. Devuelve la fila del usuario o None si fallan."""
    usuario = obtener_por_usuario(nombre_usuario)
    if usuario and verify_password(password, usuario["password_hash"]):
        return usuario
    return None
