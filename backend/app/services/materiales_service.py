"""Acceso a datos y lógica del catálogo + inventario de Materiales (retornables).

A diferencia de los reactivos, los materiales SÍ llevan inventario:
`cantidad_total` (patrimonio) y `cantidad_en_uso` (en carritos activos). El
campo `cantidad_en_uso` NO se toca desde este módulo: solo lo mueve la lógica de
carritos (Módulo 5). Aquí se usa para validar reglas de conciliación.
"""

import sqlite3

from ..database import get_db


class MaterialEnUso(Exception):
    """El material está en uso (en_uso > 0) o referenciado; no se puede borrar."""


class MaterialDuplicado(Exception):
    """Ya existe un material con el mismo nombre + capacidad."""


class TotalMenorAEnUso(Exception):
    """El nuevo cantidad_total dejaría el inventario por debajo de lo ya en uso."""


def _existe_duplicado(
    conn: sqlite3.Connection,
    nombre: str,
    capacidad: str | None,
    excluir_id: int | None = None,
) -> bool:
    """True si ya hay otro material con el mismo nombre + capacidad (case-insensitive).

    `capacidad` NULL se compara con NULL (mismo material sin capacidad definida).
    """
    sql = (
        "SELECT 1 FROM materiales "
        "WHERE lower(nombre) = lower(?) "
        "AND IFNULL(lower(capacidad), '') = IFNULL(lower(?), '')"
    )
    params: list = [nombre.strip(), capacidad]
    if excluir_id is not None:
        sql += " AND id <> ?"
        params.append(excluir_id)
    return conn.execute(sql, params).fetchone() is not None


def listar(q: str | None = None) -> list[sqlite3.Row]:
    """Lista materiales; si `q`, filtra por nombre o código (LIKE, case-insensitive)."""
    with get_db() as conn:
        if q:
            patron = f"%{q.strip()}%"
            return conn.execute(
                "SELECT * FROM materiales "
                "WHERE nombre LIKE ? COLLATE NOCASE OR codigo LIKE ? COLLATE NOCASE "
                "ORDER BY nombre",
                (patron, patron),
            ).fetchall()
        return conn.execute("SELECT * FROM materiales ORDER BY nombre").fetchall()


def obtener(material_id: int) -> sqlite3.Row | None:
    """Devuelve un material por id, o None."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM materiales WHERE id = ?", (material_id,)
        ).fetchone()


def crear(
    nombre: str, codigo: str | None, capacidad: str | None, cantidad_total: int
) -> int:
    """Crea un material (en_uso = 0). Devuelve su id; MaterialDuplicado si choca."""
    with get_db() as conn:
        if _existe_duplicado(conn, nombre, capacidad):
            raise MaterialDuplicado(
                f"Ya existe el material '{nombre}' con esa capacidad."
            )
        cur = conn.execute(
            "INSERT INTO materiales (codigo, nombre, capacidad, cantidad_total, "
            "cantidad_en_uso) VALUES (?, ?, ?, ?, 0)",
            (codigo, nombre.strip(), capacidad, cantidad_total),
        )
        return cur.lastrowid


def actualizar(
    material_id: int,
    nombre: str,
    codigo: str | None,
    capacidad: str | None,
    cantidad_total: int,
) -> bool:
    """Actualiza un material (sin tocar cantidad_en_uso).

    Devuelve False si no existe. Lanza MaterialDuplicado si choca el nombre, o
    TotalMenorAEnUso si el nuevo total quedaría por debajo de lo ya en uso.
    """
    with get_db() as conn:
        fila = conn.execute(
            "SELECT cantidad_en_uso FROM materiales WHERE id = ?", (material_id,)
        ).fetchone()
        if fila is None:
            return False
        if _existe_duplicado(conn, nombre, capacidad, excluir_id=material_id):
            raise MaterialDuplicado(
                f"Ya existe el material '{nombre}' con esa capacidad."
            )
        if cantidad_total < fila["cantidad_en_uso"]:
            raise TotalMenorAEnUso(
                f"El total ({cantidad_total}) no puede ser menor que las unidades "
                f"en uso ({fila['cantidad_en_uso']})."
            )
        conn.execute(
            "UPDATE materiales SET codigo = ?, nombre = ?, capacidad = ?, "
            "cantidad_total = ? WHERE id = ?",
            (codigo, nombre.strip(), capacidad, cantidad_total, material_id),
        )
        return True


def _referencias(conn: sqlite3.Connection, material_id: int) -> int:
    """Cuenta referencias del material en recetas y carritos."""
    en_recetas = conn.execute(
        "SELECT COUNT(*) FROM receta_detalle_materiales WHERE material_id = ?",
        (material_id,),
    ).fetchone()[0]
    en_carritos = conn.execute(
        "SELECT COUNT(*) FROM carrito_detalle_materiales WHERE material_id = ?",
        (material_id,),
    ).fetchone()[0]
    return en_recetas + en_carritos


def eliminar(material_id: int) -> bool:
    """Elimina un material. False si no existe; MaterialEnUso si en_uso>0 o referenciado."""
    with get_db() as conn:
        fila = conn.execute(
            "SELECT cantidad_en_uso FROM materiales WHERE id = ?", (material_id,)
        ).fetchone()
        if fila is None:
            return False
        if fila["cantidad_en_uso"] > 0:
            raise MaterialEnUso(
                "El material tiene unidades en uso; no se puede eliminar."
            )
        if _referencias(conn, material_id) > 0:
            raise MaterialEnUso(
                "El material está en uso por una receta o carrito; no se puede eliminar."
            )
        conn.execute("DELETE FROM materiales WHERE id = ?", (material_id,))
        return True
