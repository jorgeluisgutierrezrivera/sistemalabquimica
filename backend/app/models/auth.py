"""Esquemas Pydantic del módulo de Autenticación."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credenciales enviadas al endpoint de login."""

    nombre_usuario: str = Field(..., min_length=1, max_length=60)
    password: str = Field(..., min_length=1, max_length=200)


class TokenResponse(BaseModel):
    """Token devuelto tras un login exitoso."""

    access_token: str
    token_type: str = "bearer"


class UsuarioOut(BaseModel):
    """Representación pública de un usuario (sin datos sensibles)."""

    id: int
    nombre_usuario: str
    nombre_completo: str | None = None
    rol: str
