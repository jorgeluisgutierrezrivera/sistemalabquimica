"""Endpoints del Módulo 3 — Catálogos Base: docentes, materias y ambientes.

Todos los endpoints exigen sesión válida (dependencia a nivel de router).
Catálogos simples normalizados que dan estructura a recetas y carritos.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_user
from ..models.catalogos import (
    AmbienteIn,
    AmbienteOut,
    DocenteIn,
    DocenteOut,
    MateriaIn,
    MateriaOut,
)
from ..services import ambientes_service, docentes_service, materias_service

router = APIRouter(
    prefix="/api",
    tags=["catalogos"],
    dependencies=[Depends(get_current_user)],  # blinda todo el router
)


# ============================================================
# DOCENTES
# ============================================================
@router.get("/docentes", response_model=list[DocenteOut])
def listar_docentes(q: str | None = None) -> list[DocenteOut]:
    return [
        DocenteOut(id=f["id"], nombre=f["nombre"])
        for f in docentes_service.listar(q)
    ]


@router.post("/docentes", response_model=DocenteOut, status_code=status.HTTP_201_CREATED)
def crear_docente(datos: DocenteIn) -> DocenteOut:
    try:
        nuevo_id = docentes_service.crear(datos.nombre)
    except docentes_service.DocenteDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    f = docentes_service.obtener(nuevo_id)
    return DocenteOut(id=f["id"], nombre=f["nombre"])


@router.get("/docentes/{docente_id}", response_model=DocenteOut)
def obtener_docente(docente_id: int) -> DocenteOut:
    f = docentes_service.obtener(docente_id)
    if f is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Docente no encontrado.")
    return DocenteOut(id=f["id"], nombre=f["nombre"])


@router.put("/docentes/{docente_id}", response_model=DocenteOut)
def actualizar_docente(docente_id: int, datos: DocenteIn) -> DocenteOut:
    try:
        ok = docentes_service.actualizar(docente_id, datos.nombre)
    except docentes_service.DocenteDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Docente no encontrado.")
    f = docentes_service.obtener(docente_id)
    return DocenteOut(id=f["id"], nombre=f["nombre"])


@router.delete("/docentes/{docente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_docente(docente_id: int) -> None:
    try:
        ok = docentes_service.eliminar(docente_id)
    except docentes_service.DocenteEnUso as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Docente no encontrado.")


# ============================================================
# MATERIAS
# ============================================================
def _materia_out(f) -> MateriaOut:
    return MateriaOut(
        id=f["id"], sigla=f["sigla"], nombre=f["nombre"], carrera=f["carrera"]
    )


@router.get("/materias", response_model=list[MateriaOut])
def listar_materias(q: str | None = None) -> list[MateriaOut]:
    return [_materia_out(f) for f in materias_service.listar(q)]


@router.post("/materias", response_model=MateriaOut, status_code=status.HTTP_201_CREATED)
def crear_materia(datos: MateriaIn) -> MateriaOut:
    try:
        nuevo_id = materias_service.crear(datos.sigla, datos.nombre, datos.carrera)
    except materias_service.MateriaDuplicada as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    return _materia_out(materias_service.obtener(nuevo_id))


@router.get("/materias/{materia_id}", response_model=MateriaOut)
def obtener_materia(materia_id: int) -> MateriaOut:
    f = materias_service.obtener(materia_id)
    if f is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Materia no encontrada.")
    return _materia_out(f)


@router.put("/materias/{materia_id}", response_model=MateriaOut)
def actualizar_materia(materia_id: int, datos: MateriaIn) -> MateriaOut:
    try:
        ok = materias_service.actualizar(
            materia_id, datos.sigla, datos.nombre, datos.carrera
        )
    except materias_service.MateriaDuplicada as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Materia no encontrada.")
    return _materia_out(materias_service.obtener(materia_id))


@router.delete("/materias/{materia_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_materia(materia_id: int) -> None:
    try:
        ok = materias_service.eliminar(materia_id)
    except materias_service.MateriaEnUso as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Materia no encontrada.")


# ============================================================
# AMBIENTES
# ============================================================
@router.get("/ambientes", response_model=list[AmbienteOut])
def listar_ambientes(q: str | None = None) -> list[AmbienteOut]:
    return [
        AmbienteOut(id=f["id"], nombre=f["nombre"])
        for f in ambientes_service.listar(q)
    ]


@router.post("/ambientes", response_model=AmbienteOut, status_code=status.HTTP_201_CREATED)
def crear_ambiente(datos: AmbienteIn) -> AmbienteOut:
    try:
        nuevo_id = ambientes_service.crear(datos.nombre)
    except ambientes_service.AmbienteDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    f = ambientes_service.obtener(nuevo_id)
    return AmbienteOut(id=f["id"], nombre=f["nombre"])


@router.get("/ambientes/{ambiente_id}", response_model=AmbienteOut)
def obtener_ambiente(ambiente_id: int) -> AmbienteOut:
    f = ambientes_service.obtener(ambiente_id)
    if f is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ambiente no encontrado.")
    return AmbienteOut(id=f["id"], nombre=f["nombre"])


@router.put("/ambientes/{ambiente_id}", response_model=AmbienteOut)
def actualizar_ambiente(ambiente_id: int, datos: AmbienteIn) -> AmbienteOut:
    try:
        ok = ambientes_service.actualizar(ambiente_id, datos.nombre)
    except ambientes_service.AmbienteDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ambiente no encontrado.")
    f = ambientes_service.obtener(ambiente_id)
    return AmbienteOut(id=f["id"], nombre=f["nombre"])


@router.delete("/ambientes/{ambiente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ambiente(ambiente_id: int) -> None:
    try:
        ok = ambientes_service.eliminar(ambiente_id)
    except ambientes_service.AmbienteEnUso as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ambiente no encontrado.")
