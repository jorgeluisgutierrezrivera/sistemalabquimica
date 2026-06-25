"""Acceso a datos y lógica del catálogo de Reactivos (consumibles, sin stock).

El reactivo es solo una etiqueta reutilizable para recetas/carritos (Regla 2.B):
no se gestiona stock. La integridad referencial al borrar se valida aquí, ya que
el esquema no aplica restricciones ON DELETE sobre estas referencias.
"""

import sqlite3

from ..database import get_db


class ReactivoEnUso(Exception):
    """El reactivo está referenciado por una receta o carrito (no se puede borrar)."""


class ReactivoDuplicado(Exception):
    """Ya existe un reactivo con el mismo nombre (y código/unidad)."""


def _existe_duplicado(
    conn: sqlite3.Connection, nombre: str, excluir_id: int | None = None
) -> bool:
    """True si ya hay otro reactivo con el mismo nombre (case-insensitive)."""
    sql = "SELECT 1 FROM reactivos WHERE lower(nombre) = lower(?)"
    params: list = [nombre.strip()]
    if excluir_id is not None:
        sql += " AND id <> ?"
        params.append(excluir_id)
    return conn.execute(sql, params).fetchone() is not None


def listar(q: str | None = None) -> list[sqlite3.Row]:
    """Lista reactivos; si `q`, filtra por nombre o código (LIKE, case-insensitive)."""
    with get_db() as conn:
        if q:
            patron = f"%{q.strip()}%"
            return conn.execute(
                "SELECT * FROM reactivos "
                "WHERE nombre LIKE ? COLLATE NOCASE OR codigo LIKE ? COLLATE NOCASE "
                "ORDER BY nombre",
                (patron, patron),
            ).fetchall()
        return conn.execute("SELECT * FROM reactivos ORDER BY nombre").fetchall()


def obtener(reactivo_id: int) -> sqlite3.Row | None:
    """Devuelve un reactivo por id, o None."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM reactivos WHERE id = ?", (reactivo_id,)
        ).fetchone()


def crear(nombre: str, codigo: str | None, unidad_base: str | None) -> int:
    """Crea un reactivo y devuelve su id. Lanza ReactivoDuplicado si ya existe."""
    with get_db() as conn:
        if _existe_duplicado(conn, nombre):
            raise ReactivoDuplicado(f"Ya existe un reactivo llamado '{nombre}'.")
        cur = conn.execute(
            "INSERT INTO reactivos (codigo, nombre, unidad_base) VALUES (?, ?, ?)",
            (codigo, nombre.strip(), unidad_base),
        )
        return cur.lastrowid


def actualizar(
    reactivo_id: int, nombre: str, codigo: str | None, unidad_base: str | None
) -> bool:
    """Actualiza un reactivo. Devuelve False si no existe; ReactivoDuplicado si choca."""
    with get_db() as conn:
        existe = conn.execute(
            "SELECT 1 FROM reactivos WHERE id = ?", (reactivo_id,)
        ).fetchone()
        if existe is None:
            return False
        if _existe_duplicado(conn, nombre, excluir_id=reactivo_id):
            raise ReactivoDuplicado(f"Ya existe un reactivo llamado '{nombre}'.")
        conn.execute(
            "UPDATE reactivos SET codigo = ?, nombre = ?, unidad_base = ? WHERE id = ?",
            (codigo, nombre.strip(), unidad_base, reactivo_id),
        )
        return True


def _referencias(conn: sqlite3.Connection, reactivo_id: int) -> int:
    """Cuenta referencias del reactivo en recetas y carritos."""
    en_recetas = conn.execute(
        "SELECT COUNT(*) FROM receta_detalle_reactivos WHERE reactivo_id = ?",
        (reactivo_id,),
    ).fetchone()[0]
    en_carritos = conn.execute(
        "SELECT COUNT(*) FROM carrito_detalle_reactivos WHERE reactivo_id = ?",
        (reactivo_id,),
    ).fetchone()[0]
    return en_recetas + en_carritos


def eliminar(reactivo_id: int) -> bool:
    """Elimina un reactivo. False si no existe; ReactivoEnUso si está referenciado."""
    with get_db() as conn:
        existe = conn.execute(
            "SELECT 1 FROM reactivos WHERE id = ?", (reactivo_id,)
        ).fetchone()
        if existe is None:
            return False
        if _referencias(conn, reactivo_id) > 0:
            raise ReactivoEnUso(
                "El reactivo está en uso por una receta o carrito; no se puede eliminar."
            )
        conn.execute("DELETE FROM reactivos WHERE id = ?", (reactivo_id,))
        return True
