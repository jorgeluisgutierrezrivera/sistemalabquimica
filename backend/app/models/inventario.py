"""Esquemas Pydantic del Módulo 2 — Inventario (materiales y reactivos)."""

from pydantic import BaseModel, Field


# ============================================================
# REACTIVOS (catálogo puro, SIN stock — Regla 2.B)
# ============================================================
class ReactivoIn(BaseModel):
    """Datos de entrada para crear/editar un reactivo (catálogo)."""

    codigo: str | None = Field(default=None, max_length=60)
    nombre: str = Field(..., min_length=1, max_length=120)
    unidad_base: str | None = Field(default=None, max_length=30)


class ReactivoOut(BaseModel):
    """Representación de salida de un reactivo."""

    id: int
    codigo: str | None = None
    nombre: str
    unidad_base: str | None = None


# ============================================================
# MATERIALES (catálogo + inventario)
# ============================================================
class MaterialIn(BaseModel):
    """Datos de entrada para crear/editar un material.

    `cantidad_en_uso` NO se acepta aquí: solo la mueve la lógica de carritos
    (Módulo 5). Al crear inicia en 0; al editar nunca cambia desde este módulo.
    """

    codigo: str | None = Field(default=None, max_length=60)
    nombre: str = Field(..., min_length=1, max_length=120)
    capacidad: str | None = Field(default=None, max_length=60)
    cantidad_total: int = Field(default=0, ge=0)


class MaterialOut(BaseModel):
    """Representación de salida de un material, con disponible calculado."""

    id: int
    codigo: str | None = None
    nombre: str
    capacidad: str | None = None
    cantidad_total: int
    cantidad_en_uso: int
    cantidad_disponible: int  # = cantidad_total - cantidad_en_uso (no se almacena)
