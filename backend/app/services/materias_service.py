"""Acceso a datos y lógica del catálogo de Materias.

Catálogo con clave única compuesta (sigla + nombre). La integridad referencial
al borrar se valida aquí: una materia usada por horarios, recetas o carritos no
puede eliminarse.
"""

import sqlite3

from ..database import get_db


class MateriaEnUso(Exception):
    """La materia está referenciada por horario/receta/carrito (no se puede borrar)."""


class MateriaDuplicada(Exception):
    """Ya existe una materia con la misma sigla + nombre."""


def _existe_duplicado(
    conn: sqlite3.Connection,
    sigla: str,
    nombre: str,
    excluir_id: int | None = None,
) -> bool:
    """True si ya hay otra materia con la misma sigla + nombre (case-insensitive)."""
    sql = (
        "SELECT 1 FROM materias "
        "WHERE lower(sigla) = lower(?) AND lower(nombre) = lower(?)"
    )
    params: list = [sigla.strip(), nombre.strip()]
    if excluir_id is not None:
        sql += " AND id <> ?"
        params.append(excluir_id)
    return conn.execute(sql, params).fetchone() is not None


def listar(q: str | None = None) -> list[sqlite3.Row]:
    """Lista materias; si `q`, filtra por sigla, nombre o carrera."""
    with get_db() as conn:
        if q:
            patron = f"%{q.strip()}%"
            return conn.execute(
                "SELECT * FROM materias "
                "WHERE sigla LIKE ? COLLATE NOCASE "
                "OR nombre LIKE ? COLLATE NOCASE "
                "OR carrera LIKE ? COLLATE NOCASE "
                "ORDER BY sigla, nombre",
                (patron, patron, patron),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM materias ORDER BY sigla, nombre"
        ).fetchall()


def obtener(materia_id: int) -> sqlite3.Row | None:
    """Devuelve una materia por id, o None."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM materias WHERE id = ?", (materia_id,)
        ).fetchone()


def crear(sigla: str, nombre: str, carrera: str) -> int:
    """Crea una materia y devuelve su id. Lanza MateriaDuplicada si ya existe."""
    with get_db() as conn:
        if _existe_duplicado(conn, sigla, nombre):
            raise MateriaDuplicada(
                f"Ya existe la materia '{sigla} - {nombre}'."
            )
        cur = conn.execute(
            "INSERT INTO materias (sigla, nombre, carrera) VALUES (?, ?, ?)",
            (sigla.strip(), nombre.strip(), carrera.strip()),
        )
        return cur.lastrowid


def actualizar(materia_id: int, sigla: str, nombre: str, carrera: str) -> bool:
    """Actualiza una materia. False si no existe; MateriaDuplicada si choca."""
    with get_db() as conn:
        existe = conn.execute(
            "SELECT 1 FROM materias WHERE id = ?", (materia_id,)
        ).fetchone()
        if existe is None:
            return False
        if _existe_duplicado(conn, sigla, nombre, excluir_id=materia_id):
            raise MateriaDuplicada(
                f"Ya existe la materia '{sigla} - {nombre}'."
            )
        conn.execute(
            "UPDATE materias SET sigla = ?, nombre = ?, carrera = ? WHERE id = ?",
            (sigla.strip(), nombre.strip(), carrera.strip(), materia_id),
        )
        return True


def _referencias(conn: sqlite3.Connection, materia_id: int) -> int:
    """Cuenta referencias de la materia en horarios, recetas y carritos."""
    en_horarios = conn.execute(
        "SELECT COUNT(*) FROM horarios_semestre WHERE materia_id = ?",
        (materia_id,),
    ).fetchone()[0]
    en_recetas = conn.execute(
        "SELECT COUNT(*) FROM recetas WHERE materia_id = ?",
        (materia_id,),
    ).fetchone()[0]
    en_carritos = conn.execute(
        "SELECT COUNT(*) FROM carritos_cabecera WHERE materia_id = ?",
        (materia_id,),
    ).fetchone()[0]
    return en_horarios + en_recetas + en_carritos


def eliminar(materia_id: int) -> bool:
    """Elimina una materia. False si no existe; MateriaEnUso si está referenciada."""
    with get_db() as conn:
        existe = conn.execute(
            "SELECT 1 FROM materias WHERE id = ?", (materia_id,)
        ).fetchone()
        if existe is None:
            return False
        if _referencias(conn, materia_id) > 0:
            raise MateriaEnUso(
                "La materia está en uso por un horario, receta o carrito; "
                "no se puede eliminar."
            )
        conn.execute("DELETE FROM materias WHERE id = ?", (materia_id,))
        return True
