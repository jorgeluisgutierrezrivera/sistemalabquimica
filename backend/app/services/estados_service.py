"""Máquina de estados del carrito y efectos de inventario (Módulo 6).

Transiciones **solo hacia adelante**:
    Preparacion → Activo → (Custodia) → Proximo_Cierre   [→ Cerrado = M7]

Al entrar a `Activo` (una sola vez) se mueve el inventario diferido de M5:
- Materiales: `cantidad_en_uso += cantidad_entregada` + Kardex `entrada_uso`.
- Reactivos: Kardex `salida_consumo` (informativo; sin stock que descontar).
Todo dentro de la transacción de la transición (commit/rollback en `get_db`).
"""

from ..database import get_db

# Estados destino permitidos desde cada estado (forward-only).
# La transición a 'Cerrado' pertenece al Módulo 7 (conciliación).
TRANSICIONES: dict[str, set[str]] = {
    "Preparacion": {"Activo"},
    "Activo": {"Custodia", "Proximo_Cierre"},
    "Custodia": {"Proximo_Cierre"},
    "Proximo_Cierre": set(),
    "Cerrado": set(),
}


class TransicionInvalida(Exception):
    """El cambio de estado solicitado no está permitido desde el estado actual."""


class StockInsuficiente(Exception):
    """No hay material disponible suficiente para poner el carrito en uso."""


def _aplicar_entrada_uso(conn, carrito_id: int) -> None:
    """Mueve materiales a 'en uso' y registra el Kardex. Valida disponibilidad
    de TODOS los materiales antes de aplicar (rollback limpio si falla)."""
    materiales = conn.execute(
        "SELECT material_id, nombre_material, cantidad_entregada "
        "FROM carrito_detalle_materiales "
        "WHERE carrito_id = ? AND material_id IS NOT NULL",
        (carrito_id,),
    ).fetchall()

    # Paso 1: validar disponibilidad de todos los materiales.
    for m in materiales:
        mat = conn.execute(
            "SELECT cantidad_total, cantidad_en_uso FROM materiales WHERE id = ?",
            (m["material_id"],),
        ).fetchone()
        disponible = mat["cantidad_total"] - mat["cantidad_en_uso"]
        if m["cantidad_entregada"] > disponible:
            raise StockInsuficiente(
                f"Material '{m['nombre_material']}': se necesitan "
                f"{m['cantidad_entregada']} y solo hay {disponible} disponibles."
            )

    # Paso 2: aplicar incrementos + Kardex de materiales.
    for m in materiales:
        conn.execute(
            "UPDATE materiales SET cantidad_en_uso = cantidad_en_uso + ? WHERE id = ?",
            (m["cantidad_entregada"], m["material_id"]),
        )
        conn.execute(
            "INSERT INTO movimientos_inventario "
            "(carrito_id, tipo_insumo, insumo_id, tipo_movimiento, cantidad) "
            "VALUES (?, 'material', ?, 'entrada_uso', ?)",
            (carrito_id, m["material_id"], m["cantidad_entregada"]),
        )

    # Reactivos: Kardex informativo (consumibles sin stock).
    reactivos = conn.execute(
        "SELECT reactivo_id, cantidad_total FROM carrito_detalle_reactivos "
        "WHERE carrito_id = ? AND reactivo_id IS NOT NULL",
        (carrito_id,),
    ).fetchall()
    for r in reactivos:
        conn.execute(
            "INSERT INTO movimientos_inventario "
            "(carrito_id, tipo_insumo, insumo_id, tipo_movimiento, cantidad) "
            "VALUES (?, 'reactivo', ?, 'salida_consumo', ?)",
            (carrito_id, r["reactivo_id"], r["cantidad_total"]),
        )


def transicionar(carrito_id: int, nuevo_estado: str) -> bool:
    """Aplica una transición de estado válida. False si el carrito no existe.

    Lanza TransicionInvalida / StockInsuficiente según corresponda.
    """
    with get_db() as conn:
        fila = conn.execute(
            "SELECT estado_carrito FROM carritos_cabecera WHERE id = ?", (carrito_id,)
        ).fetchone()
        if fila is None:
            return False
        actual = fila["estado_carrito"]
        if nuevo_estado not in TRANSICIONES.get(actual, set()):
            raise TransicionInvalida(
                f"No se puede pasar de '{actual}' a '{nuevo_estado}'."
            )
        if nuevo_estado == "Activo":
            _aplicar_entrada_uso(conn, carrito_id)
        conn.execute(
            "UPDATE carritos_cabecera SET estado_carrito = ? WHERE id = ?",
            (nuevo_estado, carrito_id),
        )
        return True
