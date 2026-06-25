"""Acceso a datos y lógica del catálogo de Ambientes.

Catálogo simple (nombre único). La integridad referencial al borrar se valida
aquí: un ambiente referenciado por horarios o carritos no puede eliminarse.
"""

import sqlite3

from ..database import get_db


class AmbienteEnUso(Exception):
    """El ambiente está referenciado por un horario o carrito (no se puede borrar)."""


class AmbienteDuplicado(Exception):
    """Ya existe un ambiente con el mismo nombre."""


def _existe_duplicado(
    conn: sqlite3.Connection, nombre: str, excluir_id: int | None = None
) -> bool:
    """True si ya hay otro ambiente con el mismo nombre (case-insensitive)."""
    sql = "SELECT 1 FROM ambientes WHERE lower(nombre) = lower(?)"
    params: list = [nombre.strip()]
    if excluir_id is not None:
        sql += " AND id <> ?"
        params.append(excluir_id)
    return conn.execute(sql, params).fetchone() is not None


def listar(q: str | None = None) -> list[sqlite3.Row]:
    """Lista ambientes; si `q`, filtra por nombre (LIKE, case-insensitive)."""
    with get_db() as conn:
        if q:
            patron = f"%{q.strip()}%"
            return conn.execute(
                "SELECT * FROM ambientes WHERE nombre LIKE ? COLLATE NOCASE "
                "ORDER BY nombre",
                (patron,),
            ).fetchall()
        return conn.execute("SELECT * FROM ambientes ORDER BY nombre").fetchall()


def obtener(ambiente_id: int) -> sqlite3.Row | None:
    """Devuelve un ambiente por id, o None."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM ambientes WHERE id = ?", (ambiente_id,)
        ).fetchone()


def crear(nombre: str) -> int:
    """Crea un ambiente y devuelve su id. Lanza AmbienteDuplicado si ya existe."""
    with get_db() as conn:
        if _existe_duplicado(conn, nombre):
            raise AmbienteDuplicado(f"Ya existe un ambiente llamado '{nombre}'.")
        cur = conn.execute(
            "INSERT INTO ambientes (nombre) VALUES (?)", (nombre.strip(),)
        )
        return cur.lastrowid


def actualizar(ambiente_id: int, nombre: str) -> bool:
    """Actualiza un ambiente. False si no existe; AmbienteDuplicado si choca."""
    with get_db() as conn:
        existe = conn.execute(
            "SELECT 1 FROM ambientes WHERE id = ?", (ambiente_id,)
        ).fetchone()
        if existe is None:
            return False
        if _existe_duplicado(conn, nombre, excluir_id=ambiente_id):
            raise AmbienteDuplicado(f"Ya existe un ambiente llamado '{nombre}'.")
        conn.execute(
            "UPDATE ambientes SET nombre = ? WHERE id = ?",
            (nombre.strip(), ambiente_id),
        )
        return True


def _referencias(conn: sqlite3.Connection, ambiente_id: int) -> int:
    """Cuenta referencias del ambiente en horarios y carritos."""
    en_horarios = conn.execute(
        "SELECT COUNT(*) FROM horarios_semestre WHERE ambiente_id = ?",
        (ambiente_id,),
    ).fetchone()[0]
    en_carritos = conn.execute(
        "SELECT COUNT(*) FROM carritos_cabecera WHERE ambiente_id = ?",
        (ambiente_id,),
    ).fetchone()[0]
    return en_horarios + en_carritos


def eliminar(ambiente_id: int) -> bool:
    """Elimina un ambiente. False si no existe; AmbienteEnUso si está referenciado."""
    with get_db() as conn:
        existe = conn.execute(
            "SELECT 1 FROM ambientes WHERE id = ?", (ambiente_id,)
        ).fetchone()
        if existe is None:
            return False
        if _referencias(conn, ambiente_id) > 0:
            raise AmbienteEnUso(
                "El ambiente está en uso por un horario o carrito; no se puede eliminar."
            )
        conn.execute("DELETE FROM ambientes WHERE id = ?", (ambiente_id,))
        return True
