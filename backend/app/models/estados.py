"""Esquemas Pydantic del Módulo 6 — Estados del Carrito y Dashboard."""

from typing import Literal

from pydantic import BaseModel, Field

from .carritos import CarritoResumen

# Estados válidos del carrito (CHECK en carritos_cabecera.estado_carrito).
EstadoCarrito = Literal[
    "Preparacion", "Activo", "Custodia", "Proximo_Cierre", "Cerrado"
]


class CambioEstadoIn(BaseModel):
    """Petición de transición de estado."""

    estado: EstadoCarrito


class DashboardOut(BaseModel):
    """Resumen del tablero de control."""

    por_estado: dict[str, int]
    total: int
    activos: list[CarritoResumen] = Field(default_factory=list)
    proximos_cierre: list[CarritoResumen] = Field(default_factory=list)
    del_dia: list[CarritoResumen] = Field(default_factory=list)
