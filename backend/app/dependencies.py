"""Dependencias reutilizables de FastAPI (autenticación / autorización).

Los módulos protegidos importarán `get_current_user` para exigir un token
válido, ej.:  `def listar(... , user = Depends(get_current_user))`.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models.auth import UsuarioOut
from .security import decode_access_token
from .services import usuarios_service

# auto_error=False para devolver 401 con mensaje propio en vez de 403 genérico.
_bearer = HTTPBearer(auto_error=False)

_CREDENCIALES_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado o token inválido.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UsuarioOut:
    """Valida el token Bearer y devuelve el usuario autenticado."""
    if credentials is None:
        raise _CREDENCIALES_INVALIDAS
    try:
        payload = decode_access_token(credentials.credentials)
        usuario_id = int(payload["sub"])
    except Exception:
        raise _CREDENCIALES_INVALIDAS

    usuario = usuarios_service.obtener_por_id(usuario_id)
    if usuario is None:
        raise _CREDENCIALES_INVALIDAS

    return UsuarioOut(
        id=usuario["id"],
        nombre_usuario=usuario["nombre_usuario"],
        nombre_completo=usuario["nombre_completo"],
        rol=usuario["rol"],
    )
