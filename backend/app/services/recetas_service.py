"""Acceso a datos y lógica de Recetas Maestras (Módulo 4).

La receta es un agregado: cabecera + líneas de reactivos/materiales. Crear y
editar manejan todo en una transacción (el context manager `get_db` hace commit
al salir y rollback ante excepción). Editar **reemplaza** el conjunto de líneas.
"""

import sqlite3

from ..database import get_db


class RecetaDuplicada(Exception):
    """Ya existe una receta con la misma materia + nombre de práctica."""


class RecetaEnUso(Exception):
    """La receta está referenciada por un carrito; no se puede borrar."""


class FKInexistente(Exception):
    """Una referencia (materia/reactivo/material) no existe."""


# ============================================================
# Validaciones de existencia (FKs)
# ============================================================
def _validar_materia(conn: sqlite3.Connection, materia_id: int) -> None:
    if conn.execute(
        "SELECT 1 FROM materias WHERE id = ?", (materia_id,)
    ).fetchone() is None:
        raise FKInexistente(f"La materia id={materia_id} no existe.")


def _validar_reactivos(conn: sqlite3.Connection, reactivos) -> None:
    for r in reactivos:
        if conn.execute(
            "SELECT 1 FROM reactivos WHERE id = ?", (r.reactivo_id,)
        ).fetchone() is None:
            raise FKInexistente(f"El reactivo id={r.reactivo_id} no existe.")


def _validar_materiales(conn: sqlite3.Connection, materiales) -> None:
    for m in materiales:
        if conn.execute(
            "SELECT 1 FROM materiales WHERE id = ?", (m.material_id,)
        ).fetchone() is None:
            raise FKInexistente(f"El material id={m.material_id} no existe.")


def _existe_duplicada(
    conn: sqlite3.Connection,
    materia_id: int,
    nombre_practica: str,
    excluir_id: int | None = None,
) -> bool:
    """True si ya hay otra receta con misma materia + práctica (case-insensitive)."""
    sql = (
        "SELECT 1 FROM recetas "
        "WHERE materia_id = ? AND lower(nombre_practica) = lower(?)"
    )
    params: list = [materia_id, nombre_practica.strip()]
    if excluir_id is not None:
        sql += " AND id <> ?"
        params.append(excluir_id)
    return conn.execute(sql, params).fetchone() is not None


# ============================================================
# Inserción de líneas (dentro de una transacción abierta)
# ============================================================
def _insertar_detalles(conn: sqlite3.Connection, receta_id: int, datos) -> None:
    for r in datos.reactivos:
        conn.execute(
            "INSERT INTO receta_detalle_reactivos "
            "(receta_id, reactivo_id, concentracion_unidad, cantidad_por_grupo) "
            "VALUES (?, ?, ?, ?)",
            (receta_id, r.reactivo_id, r.concentracion_unidad, r.cantidad_por_grupo),
        )
    for m in datos.materiales:
        conn.execute(
            "INSERT INTO receta_detalle_materiales "
            "(receta_id, material_id, cantidad_por_grupo, observaciones) "
            "VALUES (?, ?, ?, ?)",
            (receta_id, m.material_id, m.cantidad_por_grupo, m.observaciones),
        )


# ============================================================
# Lectura
# ============================================================
def listar(
    q: str | None = None,
    materia_id: int | None = None,
    activa: bool | None = None,
) -> list[sqlite3.Row]:
    """Lista cabeceras de receta con la materia resuelta. Filtros opcionales."""
    sql = (
        "SELECT r.*, m.sigla AS materia_sigla, m.nombre AS materia_nombre "
        "FROM recetas r JOIN materias m ON m.id = r.materia_id WHERE 1=1"
    )
    params: list = []
    if q:
        sql += " AND r.nombre_practica LIKE ? COLLATE NOCASE"
        params.append(f"%{q.strip()}%")
    if materia_id is not None:
        sql += " AND r.materia_id = ?"
        params.append(materia_id)
    if activa is not None:
        sql += " AND r.activa = ?"
        params.append(1 if activa else 0)
    sql += " ORDER BY m.sigla, r.nombre_practica"
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()


def obtener(receta_id: int) -> dict | None:
    """Devuelve la receta con sus detalles anidados (dict), o None."""
    with get_db() as conn:
        cab = conn.execute(
            "SELECT r.*, m.sigla AS materia_sigla, m.nombre AS materia_nombre "
            "FROM recetas r JOIN materias m ON m.id = r.materia_id "
            "WHERE r.id = ?",
            (receta_id,),
        ).fetchone()
        if cab is None:
            return None
        reactivos = conn.execute(
            "SELECT d.*, x.nombre AS insumo_nombre "
            "FROM receta_detalle_reactivos d "
            "JOIN reactivos x ON x.id = d.reactivo_id "
            "WHERE d.receta_id = ? ORDER BY d.id",
            (receta_id,),
        ).fetchall()
        materiales = conn.execute(
            "SELECT d.*, x.nombre AS insumo_nombre, x.capacidad AS insumo_capacidad "
            "FROM receta_detalle_materiales d "
            "JOIN materiales x ON x.id = d.material_id "
            "WHERE d.receta_id = ? ORDER BY d.id",
            (receta_id,),
        ).fetchall()
    return {"cabecera": cab, "reactivos": reactivos, "materiales": materiales}


# ============================================================
# Escritura
# ============================================================
def crear(datos) -> int:
    """Crea una receta con sus líneas en una transacción. Devuelve su id.

    Lanza FKInexistente / RecetaDuplicada según corresponda.
    """
    with get_db() as conn:
        _validar_materia(conn, datos.materia_id)
        _validar_reactivos(conn, datos.reactivos)
        _validar_materiales(conn, datos.materiales)
        if _existe_duplicada(conn, datos.materia_id, datos.nombre_practica):
            raise RecetaDuplicada(
                f"Ya existe la receta '{datos.nombre_practica}' para esa materia."
            )
        cur = conn.execute(
            "INSERT INTO recetas (materia_id, nombre_practica, descripcion, activa) "
            "VALUES (?, ?, ?, ?)",
            (
                datos.materia_id,
                datos.nombre_practica.strip(),
                datos.descripcion,
                1 if datos.activa else 0,
            ),
        )
        receta_id = cur.lastrowid
        _insertar_detalles(conn, receta_id, datos)
        return receta_id


def actualizar(receta_id: int, datos) -> bool:
    """Edita cabecera y REEMPLAZA las líneas. False si la receta no existe."""
    with get_db() as conn:
        if conn.execute(
            "SELECT 1 FROM recetas WHERE id = ?", (receta_id,)
        ).fetchone() is None:
            return False
        _validar_materia(conn, datos.materia_id)
        _validar_reactivos(conn, datos.reactivos)
        _validar_materiales(conn, datos.materiales)
        if _existe_duplicada(
            conn, datos.materia_id, datos.nombre_practica, excluir_id=receta_id
        ):
            raise RecetaDuplicada(
                f"Ya existe la receta '{datos.nombre_practica}' para esa materia."
            )
        conn.execute(
            "UPDATE recetas SET materia_id = ?, nombre_practica = ?, "
            "descripcion = ?, activa = ? WHERE id = ?",
            (
                datos.materia_id,
                datos.nombre_practica.strip(),
                datos.descripcion,
                1 if datos.activa else 0,
                receta_id,
            ),
        )
        # Reemplazo de líneas.
        conn.execute(
            "DELETE FROM receta_detalle_reactivos WHERE receta_id = ?", (receta_id,)
        )
        conn.execute(
            "DELETE FROM receta_detalle_materiales WHERE receta_id = ?", (receta_id,)
        )
        _insertar_detalles(conn, receta_id, datos)
        return True


def eliminar(receta_id: int) -> bool:
    """Elimina la receta (líneas en cascada). False si no existe; RecetaEnUso si
    un carrito la referencia."""
    with get_db() as conn:
        if conn.execute(
            "SELECT 1 FROM recetas WHERE id = ?", (receta_id,)
        ).fetchone() is None:
            return False
        en_carritos = conn.execute(
            "SELECT COUNT(*) FROM carritos_cabecera WHERE receta_id = ?",
            (receta_id,),
        ).fetchone()[0]
        if en_carritos > 0:
            raise RecetaEnUso(
                "La receta está en uso por un carrito; no se puede eliminar."
            )
        conn.execute("DELETE FROM recetas WHERE id = ?", (receta_id,))
        return True
