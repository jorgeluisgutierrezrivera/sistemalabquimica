"""Esquemas Pydantic del Módulo 7 — Cierre y Conciliación."""

from pydantic import BaseModel, Field


class DevolucionIn(BaseModel):
    """Devolución de una línea de material al cerrar el carrito."""

    detalle_material_id: int
    cantidad_devuelta: int = Field(..., ge=0)
    observaciones: str | None = Field(default=None, max_length=200)


class CierreIn(BaseModel):
    """Cierre del carrito. Las líneas omitidas se devuelven completas."""

    devoluciones: list[DevolucionIn] = Field(default_factory=list)
