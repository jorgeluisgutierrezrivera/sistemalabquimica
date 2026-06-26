"""Esquemas Pydantic del Módulo 4 — Recetas Maestras (agregado anidado).

Una receta se maneja como un agregado: la cabecera viaja junto con sus listas de
líneas (reactivos y materiales) en una sola operación de creación/edición.
"""

from pydantic import BaseModel, Field


# ============================================================
# LÍNEAS DE DETALLE — entrada
# ============================================================
class DetalleReactivoIn(BaseModel):
    """Línea de reactivo de una receta (plantilla, cantidad por grupo)."""

    reactivo_id: int
    concentracion_unidad: str | None = Field(default=None, max_length=60)
    cantidad_por_grupo: float = Field(..., gt=0)


class DetalleMaterialIn(BaseModel):
    """Línea de material de una receta (plantilla, cantidad por grupo)."""

    material_id: int
    cantidad_por_grupo: int = Field(..., gt=0)
    observaciones: str | None = Field(default=None, max_length=120)


# ============================================================
# LÍNEAS DE DETALLE — salida (con nombre del insumo para la UI)
# ============================================================
class DetalleReactivoOut(BaseModel):
    id: int
    reactivo_id: int
    nombre: str  # nombre del reactivo (catálogo), para mostrar
    concentracion_unidad: str | None = None
    cantidad_por_grupo: float


class DetalleMaterialOut(BaseModel):
    id: int
    material_id: int
    nombre: str  # nombre del material (catálogo), para mostrar
    capacidad: str | None = None
    cantidad_por_grupo: int
    observaciones: str | None = None


# ============================================================
# RECETA (cabecera + listas)
# ============================================================
class RecetaIn(BaseModel):
    """Receta completa de entrada (cabecera + líneas)."""

    materia_id: int
    nombre_practica: str = Field(..., min_length=1, max_length=120)
    descripcion: str | None = Field(default=None, max_length=500)
    activa: bool = True
    reactivos: list[DetalleReactivoIn] = Field(default_factory=list)
    materiales: list[DetalleMaterialIn] = Field(default_factory=list)


class RecetaResumen(BaseModel):
    """Cabecera de receta para el listado (sin detalles)."""

    id: int
    materia_id: int
    materia: str  # "SIGLA - Nombre" para mostrar
    nombre_practica: str
    descripcion: str | None = None
    activa: bool


class RecetaOut(RecetaResumen):
    """Receta completa de salida (cabecera + líneas anidadas)."""

    reactivos: list[DetalleReactivoOut] = Field(default_factory=list)
    materiales: list[DetalleMaterialOut] = Field(default_factory=list)
