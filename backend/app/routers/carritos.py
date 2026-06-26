"""Endpoints del Módulo 5 — Carrito de Insumos.

El carrito se arma desde una receta (POST) y se edita como agregado anidado
(PUT reemplaza las líneas). Todos los endpoints exigen sesión válida.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_user
from ..models.carritos import (
    CarritoArmarIn,
    CarritoEditarIn,
    CarritoOut,
    CarritoResumen,
    DetalleMaterialOut,
    DetalleReactivoOut,
)
from ..models.cierre import CierreIn
from ..models.estados import CambioEstadoIn
from ..services import carritos_service, cierre_service, estados_service

router = APIRouter(
    prefix="/api/carritos",
    tags=["carritos"],
    dependencies=[Depends(get_current_user)],
)


# ============================================================
# Mapeo fila -> modelo
# ============================================================
def _resumen(f) -> CarritoResumen:
    return CarritoResumen(
        id=f["id"],
        docente_id=f["docente_id"],
        docente=f["docente_nombre"],
        materia_id=f["materia_id"],
        materia=f"{f['materia_sigla']} - {f['materia_nombre']}",
        receta_id=f["receta_id"],
        nombre_numero_practica=f["nombre_numero_practica"],
        fecha_realizacion=f["fecha_realizacion"],
        estado_carrito=f["estado_carrito"],
        numero_grupos=f["numero_grupos"],
    )


def _derivar_grupos(reactivos) -> int | None:
    """Re-deriva el multiplicador de grupos desde la primera línea de reactivo."""
    for d in reactivos:
        if d["cantidad_por_grupo"]:
            return int(round(d["cantidad_total"] / d["cantidad_por_grupo"]))
    return None


def _completa(data: dict) -> CarritoOut:
    cab = data["cabecera"]
    return CarritoOut(
        id=cab["id"],
        docente_id=cab["docente_id"],
        docente=cab["docente_nombre"],
        materia_id=cab["materia_id"],
        materia=f"{cab['materia_sigla']} - {cab['materia_nombre']}",
        receta_id=cab["receta_id"],
        nombre_numero_practica=cab["nombre_numero_practica"],
        fecha_realizacion=cab["fecha_realizacion"],
        estado_carrito=cab["estado_carrito"],
        numero_grupos=cab["numero_grupos"],
        ambiente_id=cab["ambiente_id"],
        ambiente=cab["ambiente_nombre"],
        hora_inicio=cab["hora_inicio"],
        hora_fin=cab["hora_fin"],
        numero_pedido=cab["numero_pedido"],
        codigo_lab_qmc=cab["codigo_lab_qmc"],
        cantidad_grupos=_derivar_grupos(data["reactivos"]),
        reactivos=[
            DetalleReactivoOut(
                id=d["id"],
                reactivo_id=d["reactivo_id"],
                nombre=d["nombre_reactivo"],
                concentracion_unidad=d["concentracion_unidad"],
                cantidad_por_grupo=d["cantidad_por_grupo"],
                cantidad_total=d["cantidad_total"],
                es_extra=bool(d["es_extra"]),
            )
            for d in data["reactivos"]
        ],
        materiales=[
            DetalleMaterialOut(
                id=d["id"],
                material_id=d["material_id"],
                nombre=d["nombre_material"],
                capacidad=d["capacidad"],
                cantidad_entregada=d["cantidad_entregada"],
                cantidad_devuelta=d["cantidad_devuelta"],
                es_extra=bool(d["es_extra"]),
                observaciones=d["observaciones"],
            )
            for d in data["materiales"]
        ],
    )


# ============================================================
# Endpoints
# ============================================================
@router.get("", response_model=list[CarritoResumen])
def listar_carritos(
    q: str | None = None,
    materia_id: int | None = None,
    fecha: str | None = None,
    estado: str | None = None,
) -> list[CarritoResumen]:
    return [_resumen(f) for f in carritos_service.listar(q, materia_id, fecha, estado)]


@router.post("", response_model=CarritoOut, status_code=status.HTTP_201_CREATED)
def armar_carrito(datos: CarritoArmarIn) -> CarritoOut:
    try:
        nuevo_id = carritos_service.armar(datos)
    except carritos_service.FKInexistente as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except carritos_service.RecetaInactiva as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except carritos_service.CarritoDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    return _completa(carritos_service.obtener(nuevo_id))


@router.get("/{carrito_id}", response_model=CarritoOut)
def obtener_carrito(carrito_id: int) -> CarritoOut:
    data = carritos_service.obtener(carrito_id)
    if data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carrito no encontrado.")
    return _completa(data)


@router.put("/{carrito_id}", response_model=CarritoOut)
def actualizar_carrito(carrito_id: int, datos: CarritoEditarIn) -> CarritoOut:
    try:
        ok = carritos_service.actualizar(carrito_id, datos)
    except carritos_service.FKInexistente as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except carritos_service.CarritoDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carrito no encontrado.")
    return _completa(carritos_service.obtener(carrito_id))


@router.patch("/{carrito_id}/estado", response_model=CarritoOut)
def cambiar_estado(carrito_id: int, datos: CambioEstadoIn) -> CarritoOut:
    """Avanza el estado del carrito (Módulo 6). Al entrar a 'Activo' mueve el
    inventario (materiales a 'en uso' + Kardex)."""
    try:
        ok = estados_service.transicionar(carrito_id, datos.estado)
    except estados_service.TransicionInvalida as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    except estados_service.StockInsuficiente as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carrito no encontrado.")
    return _completa(carritos_service.obtener(carrito_id))


@router.post("/{carrito_id}/cierre", response_model=CarritoOut)
def cerrar_carrito(carrito_id: int, datos: CierreIn) -> CarritoOut:
    """Concilia y cierra el carrito (Módulo 7): devolución de materiales,
    reversión de inventario, mermas y transición a 'Cerrado'."""
    try:
        ok = cierre_service.cerrar(carrito_id, datos)
    except cierre_service.CierreEstadoInvalido as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    except cierre_service.DevolucionInvalida as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carrito no encontrado.")
    return _completa(carritos_service.obtener(carrito_id))


@router.delete("/{carrito_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_carrito(carrito_id: int) -> None:
    try:
        ok = carritos_service.eliminar(carrito_id)
    except carritos_service.CarritoNoEliminable as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carrito no encontrado.")
