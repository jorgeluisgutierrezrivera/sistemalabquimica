"""Esquemas Pydantic del Módulo 5 — Carrito de Insumos (agregado anidado).

El carrito se **arma desde una Receta Maestra** (POST con `receta_id`): el
servidor copia las líneas de la receta al detalle editable, con snapshot de
nombres y `cantidad_total = cantidad_por_grupo × cantidad_grupos`. La edición
(PUT) reemplaza las líneas, permitiendo extras (`es_extra`).
"""

from pydantic import BaseModel, Field

# ============================================================
# LÍNEAS DE DETALLE — entrada (para el PUT de edición)
# ============================================================
class DetalleReactivoIn(BaseModel):
    """Línea de reactivo del carrito (consumible). `cantidad_total` se calcula."""

    reactivo_id: int
    concentracion_unidad: str | None = Field(default=None, max_length=60)
    cantidad_por_grupo: float = Field(..., gt=0)
    es_extra: bool = False


class DetalleMaterialIn(BaseModel):
    """Línea de material del carrito (retornable). Cantidad entregada absoluta."""

    material_id: int
    cantidad_entregada: int = Field(..., gt=0)
    observaciones: str | None = Field(default=None, max_length=200)
    es_extra: bool = False


# ============================================================
# LÍNEAS DE DETALLE — salida (con snapshot de nombre para la UI)
# ============================================================
class DetalleReactivoOut(BaseModel):
    id: int
    reactivo_id: int | None
    nombre: str  # snapshot nombre_reactivo
    concentracion_unidad: str | None = None
    cantidad_por_grupo: float
    cantidad_total: float
    es_extra: bool


class DetalleMaterialOut(BaseModel):
    id: int
    material_id: int | None
    nombre: str  # snapshot nombre_material
    capacidad: str | None = None
    cantidad_entregada: int
    es_extra: bool
    observaciones: str | None = None


# ============================================================
# CABECERA — campos comunes
# ============================================================
class _CabeceraBase(BaseModel):
    docente_id: int
    materia_id: int
    nombre_numero_practica: str = Field(..., min_length=1, max_length=120)
    fecha_realizacion: str = Field(..., min_length=1, max_length=10)  # YYYY-MM-DD
    ambiente_id: int | None = None
    hora_inicio: str | None = Field(default=None, max_length=20)
    hora_fin: str | None = Field(default=None, max_length=20)
    numero_pedido: int | None = None
    numero_grupos: str | None = Field(default=None, max_length=60)  # etiqueta "1 y 3"
    cantidad_grupos: int = Field(..., gt=0)  # multiplicador (no se persiste)
    codigo_lab_qmc: str | None = Field(default=None, max_length=40)


# ============================================================
# CARRITO — entrada
# ============================================================
class CarritoArmarIn(_CabeceraBase):
    """Armar carrito desde una receta (POST). Las líneas las copia el servidor."""

    receta_id: int


class CarritoEditarIn(_CabeceraBase):
    """Editar cabecera + reemplazar líneas (PUT)."""

    reactivos: list[DetalleReactivoIn] = Field(default_factory=list)
    materiales: list[DetalleMaterialIn] = Field(default_factory=list)


# ============================================================
# CARRITO — salida
# ============================================================
class CarritoResumen(BaseModel):
    """Cabecera para el listado (sin detalles)."""

    id: int
    docente_id: int
    docente: str
    materia_id: int
    materia: str  # "SIGLA - Nombre"
    receta_id: int | None
    nombre_numero_practica: str
    fecha_realizacion: str
    estado_carrito: str
    numero_grupos: str | None = None


class CarritoOut(CarritoResumen):
    """Carrito completo (cabecera + líneas anidadas)."""

    ambiente_id: int | None = None
    ambiente: str | None = None
    hora_inicio: str | None = None
    hora_fin: str | None = None
    numero_pedido: int | None = None
    codigo_lab_qmc: str | None = None
    cantidad_grupos: int | None = None  # re-derivado de las líneas de reactivo
    reactivos: list[DetalleReactivoOut] = Field(default_factory=list)
    materiales: list[DetalleMaterialOut] = Field(default_factory=list)
