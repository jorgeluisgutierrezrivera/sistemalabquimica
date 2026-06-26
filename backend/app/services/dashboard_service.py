"""Agregaciones del tablero de control (Módulo 6)."""

from datetime import date

from ..database import get_db
from . import carritos_service

ESTADOS = ["Preparacion", "Activo", "Custodia", "Proximo_Cierre", "Cerrado"]


def resumen() -> dict:
    """Conteo de carritos por estado + listas de apoyo para el tablero."""
    with get_db() as conn:
        filas = conn.execute(
            "SELECT estado_carrito, COUNT(*) AS n "
            "FROM carritos_cabecera GROUP BY estado_carrito"
        ).fetchall()
    por_estado = {e: 0 for e in ESTADOS}
    for f in filas:
        por_estado[f["estado_carrito"]] = f["n"]
    total = sum(por_estado.values())

    return {
        "por_estado": por_estado,
        "total": total,
        "activos": carritos_service.listar(estado="Activo"),
        "proximos_cierre": carritos_service.listar(estado="Proximo_Cierre"),
        "del_dia": carritos_service.listar(fecha=date.today().isoformat()),
    }
