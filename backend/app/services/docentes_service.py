"""Acceso a datos y lógica del catálogo de Docentes.

Catálogo simple (nombre único). La integridad referencial al borrar se valida
aquí: un docente referenciado por horarios o carritos no puede eliminarse.
"""

import sqlite3

from ..database import get_db


class DocenteEnUso(Exception):
    """El docente está referenciado por un horario o carrito (no se puede borrar)."""


class DocenteDuplicado(Exception):
    """Ya existe un docente con el mismo nombre."""


def _existe_duplicado(
    conn: sqlite3.Connection, nombre: str, excluir_id: int | None = None
) -> bool:
    """True si ya hay otro docente con el mismo nombre (case-insensitive)."""
    sql = "SELECT 1 FROM docentes WHERE lower(nombre) = lower(?)"
    params: list = [nombre.strip()]
    if excluir_id is not None:
        sql += " AND id <> ?"
        params.append(excluir_id)
    return conn.execute(sql, params).fetchone() is not None


def listar(q: str | None = None) -> list[sqlite3.Row]:
    """Lista docentes; si `q`, filtra por nombre (LIKE, case-insensitive)."""
    with get_db() as conn:
        if q:
            patron = f"%{q.strip()}%"
            return conn.execute(
                "SELECT * FROM docentes WHERE nombre LIKE ? COLLATE NOCASE "
                "ORDER BY nombre",
                (patron,),
            ).fetchall()
        return conn.execute("SELECT * FROM docentes ORDER BY nombre").fetchall()


def obtener(docente_id: int) -> sqlite3.Row | None:
    """Devuelve un docente por id, o None."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM docentes WHERE id = ?", (docente_id,)
        ).fetchone()


def crear(nombre: str) -> int:
    """Crea un docente y devuelve su id. Lanza DocenteDuplicado si ya existe."""
    with get_db() as conn:
        if _existe_duplicado(conn, nombre):
            raise DocenteDuplicado(f"Ya existe un docente llamado '{nombre}'.")
        cur = conn.execute(
            "INSERT INTO docentes (nombre) VALUES (?)", (nombre.strip(),)
        )
        return cur.lastrowid


def actualizar(docente_id: int, nombre: str) -> bool:
    """Actualiza un docente. False si no existe; DocenteDuplicado si choca."""
    with get_db() as conn:
        existe = conn.execute(
            "SELECT 1 FROM docentes WHERE id = ?", (docente_id,)
        ).fetchone()
        if existe is None:
            return False
        if _existe_duplicado(conn, nombre, excluir_id=docente_id):
            raise DocenteDuplicado(f"Ya existe un docente llamado '{nombre}'.")
        conn.execute(
            "UPDATE docentes SET nombre = ? WHERE id = ?",
            (nombre.strip(), docente_id),
        )
        return True


def _referencias(conn: sqlite3.Connection, docente_id: int) -> int:
    """Cuenta referencias del docente en horarios y carritos."""
    en_horarios = conn.execute(
        "SELECT COUNT(*) FROM horarios_semestre WHERE docente_id = ?",
        (docente_id,),
    ).fetchone()[0]
    en_carritos = conn.execute(
        "SELECT COUNT(*) FROM carritos_cabecera WHERE docente_id = ?",
        (docente_id,),
    ).fetchone()[0]
    return en_horarios + en_carritos


def eliminar(docente_id: int) -> bool:
    """Elimina un docente. False si no existe; DocenteEnUso si está referenciado."""
    with get_db() as conn:
        existe = conn.execute(
            "SELECT 1 FROM docentes WHERE id = ?", (docente_id,)
        ).fetchone()
        if existe is None:
            return False
        if _referencias(conn, docente_id) > 0:
            raise DocenteEnUso(
                "El docente está en uso por un horario o carrito; no se puede eliminar."
            )
        conn.execute("DELETE FROM docentes WHERE id = ?", (docente_id,))
        return True
