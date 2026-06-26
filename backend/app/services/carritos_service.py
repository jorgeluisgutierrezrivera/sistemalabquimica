"""Acceso a datos y lógica del Carrito de Insumos (Módulo 5).

El carrito es un agregado: cabecera + líneas de reactivos/materiales. Se **arma
desde una Receta Maestra** copiando sus líneas al detalle editable, con snapshot
de nombres y `cantidad_total = cantidad_por_grupo × cantidad_grupos`. Editar
(PUT) reemplaza el conjunto de líneas en una transacción (el context manager
`get_db` hace commit al salir y rollback ante excepción).

Alcance M5: solo construye el carrito en estado 'Preparacion'. NO mueve
inventario (cantidad_en_uso) ni escribe Kardex; eso se difiere al Módulo 6.
"""

import sqlite3

from ..database import get_db

ESTADO_INICIAL = "Preparacion"


class CarritoDuplicado(Exception):
    """Ya existe un carrito (no cerrado) con misma materia + práctica + fecha + hora."""


class CarritoNoEliminable(Exception):
    """El carrito no está en 'Preparacion'; no se puede eliminar en M5."""


class FKInexistente(Exception):
    """Una referencia (docente/materia/ambiente/receta/insumo) no existe."""


class RecetaInactiva(Exception):
    """La receta origen está inactiva; no se puede armar un carrito desde ella."""


# ============================================================
# Validaciones de existencia (FKs)
# ============================================================
def _validar_existe(conn, tabla: str, id_: int, etiqueta: str) -> None:
    if conn.execute(f"SELECT 1 FROM {tabla} WHERE id = ?", (id_,)).fetchone() is None:
        raise FKInexistente(f"{etiqueta} id={id_} no existe.")


def _validar_cabecera(conn, datos) -> None:
    _validar_existe(conn, "docentes", datos.docente_id, "El docente")
    _validar_existe(conn, "materias", datos.materia_id, "La materia")
    if datos.ambiente_id is not None:
        _validar_existe(conn, "ambientes", datos.ambiente_id, "El ambiente")


def _validar_receta_activa(conn, receta_id: int) -> None:
    fila = conn.execute(
        "SELECT activa FROM recetas WHERE id = ?", (receta_id,)
    ).fetchone()
    if fila is None:
        raise FKInexistente(f"La receta id={receta_id} no existe.")
    if not fila["activa"]:
        raise RecetaInactiva(
            f"La receta id={receta_id} está inactiva; no se puede armar."
        )


def _validar_lineas(conn, datos) -> None:
    for r in datos.reactivos:
        _validar_existe(conn, "reactivos", r.reactivo_id, "El reactivo")
    for m in datos.materiales:
        _validar_existe(conn, "materiales", m.material_id, "El material")


def _existe_duplicado(conn, datos, excluir_id: int | None = None) -> bool:
    """True si ya hay otro carrito no cerrado con misma clave de unicidad
    (materia + práctica + fecha + hora_inicio). `IS` maneja hora NULL."""
    sql = (
        "SELECT 1 FROM carritos_cabecera "
        "WHERE materia_id = ? AND lower(nombre_numero_practica) = lower(?) "
        "AND fecha_realizacion = ? AND hora_inicio IS ? "
        "AND estado_carrito <> 'Cerrado'"
    )
    params: list = [
        datos.materia_id,
        datos.nombre_numero_practica.strip(),
        datos.fecha_realizacion,
        datos.hora_inicio,
    ]
    if excluir_id is not None:
        sql += " AND id <> ?"
        params.append(excluir_id)
    return conn.execute(sql, params).fetchone() is not None


# ============================================================
# Inserción de líneas (dentro de una transacción abierta)
# ============================================================
def _insertar_desde_receta(conn, carrito_id: int, receta_id: int, grupos: int) -> None:
    """Copia las líneas de la receta al detalle del carrito (snapshot + totales)."""
    reactivos = conn.execute(
        "SELECT d.reactivo_id, d.concentracion_unidad, d.cantidad_por_grupo, "
        "x.nombre FROM receta_detalle_reactivos d "
        "JOIN reactivos x ON x.id = d.reactivo_id WHERE d.receta_id = ? ORDER BY d.id",
        (receta_id,),
    ).fetchall()
    for r in reactivos:
        conn.execute(
            "INSERT INTO carrito_detalle_reactivos (carrito_id, reactivo_id, "
            "nombre_reactivo, concentracion_unidad, cantidad_por_grupo, "
            "cantidad_total, es_extra) VALUES (?, ?, ?, ?, ?, ?, 0)",
            (
                carrito_id,
                r["reactivo_id"],
                r["nombre"],
                r["concentracion_unidad"],
                r["cantidad_por_grupo"],
                r["cantidad_por_grupo"] * grupos,
            ),
        )
    materiales = conn.execute(
        "SELECT d.material_id, d.cantidad_por_grupo, d.observaciones, "
        "x.nombre, x.capacidad FROM receta_detalle_materiales d "
        "JOIN materiales x ON x.id = d.material_id WHERE d.receta_id = ? ORDER BY d.id",
        (receta_id,),
    ).fetchall()
    for m in materiales:
        conn.execute(
            "INSERT INTO carrito_detalle_materiales (carrito_id, material_id, "
            "nombre_material, capacidad, cantidad_entregada, es_extra, observaciones) "
            "VALUES (?, ?, ?, ?, ?, 0, ?)",
            (
                carrito_id,
                m["material_id"],
                m["nombre"],
                m["capacidad"],
                m["cantidad_por_grupo"] * grupos,
                m["observaciones"],
            ),
        )


def _insertar_desde_lineas(conn, carrito_id: int, datos) -> None:
    """Inserta el detalle desde las líneas editadas (PUT), con snapshot de nombres."""
    for r in datos.reactivos:
        nombre = conn.execute(
            "SELECT nombre FROM reactivos WHERE id = ?", (r.reactivo_id,)
        ).fetchone()["nombre"]
        conn.execute(
            "INSERT INTO carrito_detalle_reactivos (carrito_id, reactivo_id, "
            "nombre_reactivo, concentracion_unidad, cantidad_por_grupo, "
            "cantidad_total, es_extra) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                carrito_id,
                r.reactivo_id,
                nombre,
                r.concentracion_unidad,
                r.cantidad_por_grupo,
                r.cantidad_por_grupo * datos.cantidad_grupos,
                1 if r.es_extra else 0,
            ),
        )
    for m in datos.materiales:
        fila = conn.execute(
            "SELECT nombre, capacidad FROM materiales WHERE id = ?", (m.material_id,)
        ).fetchone()
        conn.execute(
            "INSERT INTO carrito_detalle_materiales (carrito_id, material_id, "
            "nombre_material, capacidad, cantidad_entregada, es_extra, observaciones) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                carrito_id,
                m.material_id,
                fila["nombre"],
                fila["capacidad"],
                m.cantidad_entregada,
                1 if m.es_extra else 0,
                m.observaciones,
            ),
        )


def _insertar_cabecera(conn, datos, receta_id) -> int:
    cur = conn.execute(
        "INSERT INTO carritos_cabecera (docente_id, materia_id, receta_id, "
        "nombre_numero_practica, fecha_realizacion, ambiente_id, hora_inicio, "
        "hora_fin, numero_pedido, numero_grupos, codigo_lab_qmc, estado_carrito) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            datos.docente_id,
            datos.materia_id,
            receta_id,
            datos.nombre_numero_practica.strip(),
            datos.fecha_realizacion,
            datos.ambiente_id,
            datos.hora_inicio,
            datos.hora_fin,
            datos.numero_pedido,
            datos.numero_grupos,
            datos.codigo_lab_qmc,
            ESTADO_INICIAL,
        ),
    )
    return cur.lastrowid


# ============================================================
# Lectura
# ============================================================
def listar(
    q: str | None = None,
    materia_id: int | None = None,
    fecha: str | None = None,
    estado: str | None = None,
) -> list[sqlite3.Row]:
    """Lista cabeceras de carrito con docente y materia resueltos."""
    sql = (
        "SELECT c.*, d.nombre AS docente_nombre, "
        "m.sigla AS materia_sigla, m.nombre AS materia_nombre "
        "FROM carritos_cabecera c "
        "JOIN docentes d ON d.id = c.docente_id "
        "JOIN materias m ON m.id = c.materia_id WHERE 1=1"
    )
    params: list = []
    if q:
        sql += " AND c.nombre_numero_practica LIKE ? COLLATE NOCASE"
        params.append(f"%{q.strip()}%")
    if materia_id is not None:
        sql += " AND c.materia_id = ?"
        params.append(materia_id)
    if fecha:
        sql += " AND c.fecha_realizacion = ?"
        params.append(fecha)
    if estado:
        sql += " AND c.estado_carrito = ?"
        params.append(estado)
    sql += " ORDER BY c.fecha_realizacion DESC, c.id DESC"
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()


def obtener(carrito_id: int) -> dict | None:
    """Devuelve el carrito con sus detalles anidados (dict), o None."""
    with get_db() as conn:
        cab = conn.execute(
            "SELECT c.*, d.nombre AS docente_nombre, "
            "m.sigla AS materia_sigla, m.nombre AS materia_nombre, "
            "a.nombre AS ambiente_nombre "
            "FROM carritos_cabecera c "
            "JOIN docentes d ON d.id = c.docente_id "
            "JOIN materias m ON m.id = c.materia_id "
            "LEFT JOIN ambientes a ON a.id = c.ambiente_id "
            "WHERE c.id = ?",
            (carrito_id,),
        ).fetchone()
        if cab is None:
            return None
        reactivos = conn.execute(
            "SELECT * FROM carrito_detalle_reactivos WHERE carrito_id = ? ORDER BY id",
            (carrito_id,),
        ).fetchall()
        materiales = conn.execute(
            "SELECT * FROM carrito_detalle_materiales WHERE carrito_id = ? ORDER BY id",
            (carrito_id,),
        ).fetchall()
    return {"cabecera": cab, "reactivos": reactivos, "materiales": materiales}


# ============================================================
# Escritura
# ============================================================
def armar(datos) -> int:
    """Arma un carrito desde una receta (copia líneas + calcula totales).

    Lanza FKInexistente / RecetaInactiva / CarritoDuplicado según corresponda.
    """
    with get_db() as conn:
        _validar_cabecera(conn, datos)
        _validar_receta_activa(conn, datos.receta_id)
        if _existe_duplicado(conn, datos):
            raise CarritoDuplicado(
                "Ya existe un carrito para esa materia + práctica en esa fecha y hora."
            )
        carrito_id = _insertar_cabecera(conn, datos, datos.receta_id)
        _insertar_desde_receta(conn, carrito_id, datos.receta_id, datos.cantidad_grupos)
        return carrito_id


def actualizar(carrito_id: int, datos) -> bool:
    """Edita cabecera y REEMPLAZA las líneas. False si el carrito no existe."""
    with get_db() as conn:
        actual = conn.execute(
            "SELECT receta_id FROM carritos_cabecera WHERE id = ?", (carrito_id,)
        ).fetchone()
        if actual is None:
            return False
        _validar_cabecera(conn, datos)
        _validar_lineas(conn, datos)
        if _existe_duplicado(conn, datos, excluir_id=carrito_id):
            raise CarritoDuplicado(
                "Ya existe un carrito para esa materia + práctica en esa fecha y hora."
            )
        conn.execute(
            "UPDATE carritos_cabecera SET docente_id = ?, materia_id = ?, "
            "nombre_numero_practica = ?, fecha_realizacion = ?, ambiente_id = ?, "
            "hora_inicio = ?, hora_fin = ?, numero_pedido = ?, numero_grupos = ?, "
            "codigo_lab_qmc = ? WHERE id = ?",
            (
                datos.docente_id,
                datos.materia_id,
                datos.nombre_numero_practica.strip(),
                datos.fecha_realizacion,
                datos.ambiente_id,
                datos.hora_inicio,
                datos.hora_fin,
                datos.numero_pedido,
                datos.numero_grupos,
                datos.codigo_lab_qmc,
                carrito_id,
            ),
        )
        # Reemplazo de líneas.
        conn.execute(
            "DELETE FROM carrito_detalle_reactivos WHERE carrito_id = ?", (carrito_id,)
        )
        conn.execute(
            "DELETE FROM carrito_detalle_materiales WHERE carrito_id = ?", (carrito_id,)
        )
        _insertar_desde_lineas(conn, carrito_id, datos)
        return True


def eliminar(carrito_id: int) -> bool:
    """Elimina el carrito (líneas en cascada). False si no existe;
    CarritoNoEliminable si no está en 'Preparacion'."""
    with get_db() as conn:
        fila = conn.execute(
            "SELECT estado_carrito FROM carritos_cabecera WHERE id = ?", (carrito_id,)
        ).fetchone()
        if fila is None:
            return False
        if fila["estado_carrito"] != ESTADO_INICIAL:
            raise CarritoNoEliminable(
                "Solo se pueden eliminar carritos en estado 'Preparacion'."
            )
        conn.execute("DELETE FROM carritos_cabecera WHERE id = ?", (carrito_id,))
        return True
