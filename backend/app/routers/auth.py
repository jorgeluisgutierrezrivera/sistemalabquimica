"""Endpoints de Autenticación: login, perfil y logout."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_user
from ..models.auth import LoginRequest, TokenResponse, UsuarioOut
from ..security import create_access_token
from ..services import usuarios_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest) -> TokenResponse:
    """Valida credenciales y devuelve un token JWT."""
    usuario = usuarios_service.autenticar(datos.nombre_usuario, datos.password)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
        )
    token = create_access_token(
        {
            "sub": str(usuario["id"]),
            "usuario": usuario["nombre_usuario"],
            "rol": usuario["rol"],
        }
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: UsuarioOut = Depends(get_current_user)) -> UsuarioOut:
    """Devuelve los datos del usuario autenticado (valida el token)."""
    return usuario


@router.post("/logout")
def logout() -> dict:
    """Logout sin estado: el cliente descarta el token.

    Con JWT no hay sesión en servidor que invalidar; el frontend elimina el
    token de su almacenamiento. Endpoint provisto por simetría/claridad.
    """
    return {"detail": "Sesión cerrada. Descarta el token en el cliente."}
