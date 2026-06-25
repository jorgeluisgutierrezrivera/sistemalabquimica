"""Esquemas Pydantic del Módulo 3 — Catálogos Base (docentes, materias, ambientes)."""

from pydantic import BaseModel, Field


# ============================================================
# DOCENTES
# ============================================================
class DocenteIn(BaseModel):
    """Datos de entrada para crear/editar un docente."""

    nombre: str = Field(..., min_length=1, max_length=120)


class DocenteOut(BaseModel):
    """Representación de salida de un docente."""

    id: int
    nombre: str


# ============================================================
# MATERIAS
# ============================================================
class MateriaIn(BaseModel):
    """Datos de entrada para crear/editar una materia."""

    sigla: str = Field(..., min_length=1, max_length=30)
    nombre: str = Field(..., min_length=1, max_length=120)
    carrera: str = Field(..., min_length=1, max_length=120)


class MateriaOut(BaseModel):
    """Representación de salida de una materia."""

    id: int
    sigla: str
    nombre: str
    carrera: str


# ============================================================
# AMBIENTES
# ============================================================
class AmbienteIn(BaseModel):
    """Datos de entrada para crear/editar un ambiente."""

    nombre: str = Field(..., min_length=1, max_length=60)


class AmbienteOut(BaseModel):
    """Representación de salida de un ambiente."""

    id: int
    nombre: str
