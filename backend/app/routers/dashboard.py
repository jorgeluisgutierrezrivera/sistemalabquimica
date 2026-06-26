"""Endpoint del tablero de control (Módulo 6)."""

from fastapi import APIRouter, Depends

from ..dependencies import get_current_user
from ..models.estados import DashboardOut
from ..services import dashboard_service
from .carritos import _resumen

router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=DashboardOut)
def obtener_dashboard() -> DashboardOut:
    data = dashboard_service.resumen()
    return DashboardOut(
        por_estado=data["por_estado"],
        total=data["total"],
        activos=[_resumen(f) for f in data["activos"]],
        proximos_cierre=[_resumen(f) for f in data["proximos_cierre"]],
        del_dia=[_resumen(f) for f in data["del_dia"]],
    )
