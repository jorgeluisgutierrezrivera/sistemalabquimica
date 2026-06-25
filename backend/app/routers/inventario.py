"""Endpoints del Módulo 2 — Inventario: catálogos de Reactivos y Materiales.

Todos los endpoints exigen sesión válida (Depends(get_current_user)).
Reactivos = catálogo puro (sin stock); Materiales = catálogo + inventario.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_user
from ..models.inventario import (
    MaterialIn,
    MaterialOut,
    ReactivoIn,
    ReactivoOut,
)
from ..services import materiales_service, reactivos_service

router = APIRouter(
    prefix="/api",
    tags=["inventario"],
    dependencies=[Depends(get_current_user)],  # blinda todo el router
)


# ============================================================
# Helpers de mapeo fila -> modelo de salida
# ============================================================
def _reactivo_out(fila) -> ReactivoOut:
    return ReactivoOut(
        id=fila["id"],
        codigo=fila["codigo"],
        nombre=fila["nombre"],
        unidad_base=fila["unidad_base"],
    )


def _material_out(fila) -> MaterialOut:
    total = fila["cantidad_total"]
    en_uso = fila["cantidad_en_uso"]
    return MaterialOut(
        id=fila["id"],
        codigo=fila["codigo"],
        nombre=fila["nombre"],
        capacidad=fila["capacidad"],
        cantidad_total=total,
        cantidad_en_uso=en_uso,
        cantidad_disponible=total - en_uso,
    )


# ============================================================
# REACTIVOS
# ============================================================
@router.get("/reactivos", response_model=list[ReactivoOut])
def listar_reactivos(q: str | None = None) -> list[ReactivoOut]:
    return [_reactivo_out(f) for f in reactivos_service.listar(q)]


@router.post("/reactivos", response_model=ReactivoOut, status_code=status.HTTP_201_CREATED)
def crear_reactivo(datos: ReactivoIn) -> ReactivoOut:
    try:
        nuevo_id = reactivos_service.crear(
            datos.nombre, datos.codigo, datos.unidad_base
        )
    except reactivos_service.ReactivoDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    return _reactivo_out(reactivos_service.obtener(nuevo_id))


@router.get("/reactivos/{reactivo_id}", response_model=ReactivoOut)
def obtener_reactivo(reactivo_id: int) -> ReactivoOut:
    fila = reactivos_service.obtener(reactivo_id)
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reactivo no encontrado.")
    return _reactivo_out(fila)


@router.put("/reactivos/{reactivo_id}", response_model=ReactivoOut)
def actualizar_reactivo(reactivo_id: int, datos: ReactivoIn) -> ReactivoOut:
    try:
        ok = reactivos_service.actualizar(
            reactivo_id, datos.nombre, datos.codigo, datos.unidad_base
        )
    except reactivos_service.ReactivoDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reactivo no encontrado.")
    return _reactivo_out(reactivos_service.obtener(reactivo_id))


@router.delete("/reactivos/{reactivo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_reactivo(reactivo_id: int) -> None:
    try:
        ok = reactivos_service.eliminar(reactivo_id)
    except reactivos_service.ReactivoEnUso as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reactivo no encontrado.")


# ============================================================
# MATERIALES
# ============================================================
@router.get("/materiales", response_model=list[MaterialOut])
def listar_materiales(q: str | None = None) -> list[MaterialOut]:
    return [_material_out(f) for f in materiales_service.listar(q)]


@router.post("/materiales", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
def crear_material(datos: MaterialIn) -> MaterialOut:
    try:
        nuevo_id = materiales_service.crear(
            datos.nombre, datos.codigo, datos.capacidad, datos.cantidad_total
        )
    except materiales_service.MaterialDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    return _material_out(materiales_service.obtener(nuevo_id))


@router.get("/materiales/{material_id}", response_model=MaterialOut)
def obtener_material(material_id: int) -> MaterialOut:
    fila = materiales_service.obtener(material_id)
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material no encontrado.")
    return _material_out(fila)


@router.put("/materiales/{material_id}", response_model=MaterialOut)
def actualizar_material(material_id: int, datos: MaterialIn) -> MaterialOut:
    try:
        ok = materiales_service.actualizar(
            material_id,
            datos.nombre,
            datos.codigo,
            datos.capacidad,
            datos.cantidad_total,
        )
    except materiales_service.MaterialDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    except materiales_service.TotalMenorAEnUso as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material no encontrado.")
    return _material_out(materiales_service.obtener(material_id))


@router.delete("/materiales/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_material(material_id: int) -> None:
    try:
        ok = materiales_service.eliminar(material_id)
    except materiales_service.MaterialEnUso as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material no encontrado.")
