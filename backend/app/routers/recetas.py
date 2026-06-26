"""Endpoints del Módulo 4 — Recetas Maestras.

La receta se maneja como un agregado anidado (cabecera + líneas). Todos los
endpoints exigen sesión válida (dependencia a nivel de router).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_user
from ..models.recetas import (
    DetalleMaterialOut,
    DetalleReactivoOut,
    RecetaIn,
    RecetaOut,
    RecetaResumen,
)
from ..services import recetas_service

router = APIRouter(
    prefix="/api/recetas",
    tags=["recetas"],
    dependencies=[Depends(get_current_user)],
)


# ============================================================
# Mapeo fila -> modelo
# ============================================================
def _resumen(f) -> RecetaResumen:
    return RecetaResumen(
        id=f["id"],
        materia_id=f["materia_id"],
        materia=f"{f['materia_sigla']} - {f['materia_nombre']}",
        nombre_practica=f["nombre_practica"],
        descripcion=f["descripcion"],
        activa=bool(f["activa"]),
    )


def _completa(data: dict) -> RecetaOut:
    cab = data["cabecera"]
    return RecetaOut(
        id=cab["id"],
        materia_id=cab["materia_id"],
        materia=f"{cab['materia_sigla']} - {cab['materia_nombre']}",
        nombre_practica=cab["nombre_practica"],
        descripcion=cab["descripcion"],
        activa=bool(cab["activa"]),
        reactivos=[
            DetalleReactivoOut(
                id=d["id"],
                reactivo_id=d["reactivo_id"],
                nombre=d["insumo_nombre"],
                concentracion_unidad=d["concentracion_unidad"],
                cantidad_por_grupo=d["cantidad_por_grupo"],
            )
            for d in data["reactivos"]
        ],
        materiales=[
            DetalleMaterialOut(
                id=d["id"],
                material_id=d["material_id"],
                nombre=d["insumo_nombre"],
                capacidad=d["insumo_capacidad"],
                cantidad_por_grupo=d["cantidad_por_grupo"],
                observaciones=d["observaciones"],
            )
            for d in data["materiales"]
        ],
    )


# ============================================================
# Endpoints
# ============================================================
@router.get("", response_model=list[RecetaResumen])
def listar_recetas(
    q: str | None = None,
    materia_id: int | None = None,
    activa: bool | None = None,
) -> list[RecetaResumen]:
    return [_resumen(f) for f in recetas_service.listar(q, materia_id, activa)]


@router.post("", response_model=RecetaOut, status_code=status.HTTP_201_CREATED)
def crear_receta(datos: RecetaIn) -> RecetaOut:
    try:
        nuevo_id = recetas_service.crear(datos)
    except recetas_service.FKInexistente as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except recetas_service.RecetaDuplicada as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    return _completa(recetas_service.obtener(nuevo_id))


@router.get("/{receta_id}", response_model=RecetaOut)
def obtener_receta(receta_id: int) -> RecetaOut:
    data = recetas_service.obtener(receta_id)
    if data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receta no encontrada.")
    return _completa(data)


@router.put("/{receta_id}", response_model=RecetaOut)
def actualizar_receta(receta_id: int, datos: RecetaIn) -> RecetaOut:
    try:
        ok = recetas_service.actualizar(receta_id, datos)
    except recetas_service.FKInexistente as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except recetas_service.RecetaDuplicada as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receta no encontrada.")
    return _completa(recetas_service.obtener(receta_id))


@router.delete("/{receta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_receta(receta_id: int) -> None:
    try:
        ok = recetas_service.eliminar(receta_id)
    except recetas_service.RecetaEnUso as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receta no encontrada.")
