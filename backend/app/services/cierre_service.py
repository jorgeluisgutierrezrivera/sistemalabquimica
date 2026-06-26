"""Cierre y conciliación del carrito (Módulo 7).

Cierra un carrito en `Proximo_Cierre`: concilia entregado-vs-devuelto de los
materiales, revierte el inventario en uso, registra mermas (Kardex + tabla de
material roto) y deja el carrito en `Cerrado`. Todo en una transacción.

Fórmula por material (`merma = entregada − devuelta`):
    materiales.cantidad_en_uso -= entregada    # todo sale de "en uso"
    materiales.cantidad_total  -= merma         # lo perdido deja el patrimonio
Reactivos no se concilian (consumibles; su consumo quedó registrado en M6).
"""

from datetime import date

from ..database import get_db

ESTADO_CIERRE = "Proximo_Cierre"
ESTADO_CERRADO = "Cerrado"


class CierreEstadoInvalido(Exception):
    """El carrito no está en 'Proximo_Cierre'; no se puede cerrar."""


class DevolucionInvalida(Exception):
    """Una devolución no corresponde al carrito o excede lo entregado."""


def cerrar(carrito_id: int, datos) -> bool:
    """Concilia y cierra el carrito. False si no existe.

    Lanza CierreEstadoInvalido / DevolucionInvalida según corresponda.
    """
    with get_db() as conn:
        cab = conn.execute(
            "SELECT estado_carrito, docente_id FROM carritos_cabecera WHERE id = ?",
            (carrito_id,),
        ).fetchone()
        if cab is None:
            return False
        if cab["estado_carrito"] != ESTADO_CIERRE:
            raise CierreEstadoInvalido(
                f"Solo se cierran carritos en '{ESTADO_CIERRE}' "
                f"(actual: '{cab['estado_carrito']}')."
            )

        docente = conn.execute(
            "SELECT nombre FROM docentes WHERE id = ?", (cab["docente_id"],)
        ).fetchone()
        docente_nombre = docente["nombre"] if docente else "—"

        lineas = conn.execute(
            "SELECT id, material_id, nombre_material, cantidad_entregada "
            "FROM carrito_detalle_materiales WHERE carrito_id = ?",
            (carrito_id,),
        ).fetchall()
        ids_validos = {ln["id"] for ln in lineas}

        # Mapa de devoluciones provistas; valida que correspondan al carrito.
        provistas = {}
        for d in datos.devoluciones:
            if d.detalle_material_id not in ids_validos:
                raise DevolucionInvalida(
                    f"La línea {d.detalle_material_id} no pertenece al carrito."
                )
            provistas[d.detalle_material_id] = d

        hoy = date.today().isoformat()
        for ln in lineas:
            entregada = ln["cantidad_entregada"]
            dev = provistas.get(ln["id"])
            # Default: devolución completa (sin merma).
            devuelta = dev.cantidad_devuelta if dev else entregada
            observaciones = dev.observaciones if dev else None
            if devuelta > entregada:
                raise DevolucionInvalida(
                    f"Material '{ln['nombre_material']}': devuelta ({devuelta}) "
                    f"supera lo entregado ({entregada})."
                )
            merma = entregada - devuelta

            conn.execute(
                "UPDATE carrito_detalle_materiales SET cantidad_devuelta = ? "
                "WHERE id = ?",
                (devuelta, ln["id"]),
            )

            # Sin material de catálogo (ítem libre): no mueve inventario.
            if ln["material_id"] is None:
                continue

            conn.execute(
                "UPDATE materiales SET cantidad_en_uso = cantidad_en_uso - ?, "
                "cantidad_total = cantidad_total - ? WHERE id = ?",
                (entregada, merma, ln["material_id"]),
            )
            if devuelta > 0:
                conn.execute(
                    "INSERT INTO movimientos_inventario "
                    "(carrito_id, tipo_insumo, insumo_id, tipo_movimiento, cantidad) "
                    "VALUES (?, 'material', ?, 'retorno', ?)",
                    (carrito_id, ln["material_id"], devuelta),
                )
            if merma > 0:
                conn.execute(
                    "INSERT INTO movimientos_inventario "
                    "(carrito_id, tipo_insumo, insumo_id, tipo_movimiento, cantidad) "
                    "VALUES (?, 'material', ?, 'merma', ?)",
                    (carrito_id, ln["material_id"], merma),
                )
                codigo = conn.execute(
                    "SELECT codigo FROM materiales WHERE id = ?", (ln["material_id"],)
                ).fetchone()
                conn.execute(
                    "INSERT INTO registro_material_roto "
                    "(carrito_id, detalle_material_id, fecha_reporte, codigo_material, "
                    "tipo_material, docente_responsable, cantidad, observaciones_rotura) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        carrito_id,
                        ln["id"],
                        hoy,
                        codigo["codigo"] if codigo else None,
                        ln["nombre_material"],
                        docente_nombre,
                        merma,
                        observaciones,
                    ),
                )

        conn.execute(
            "UPDATE carritos_cabecera SET estado_carrito = ? WHERE id = ?",
            (ESTADO_CERRADO, carrito_id),
        )
        return True
