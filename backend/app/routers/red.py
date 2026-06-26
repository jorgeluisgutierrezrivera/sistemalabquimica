"""Endpoints de red para acceso móvil (Módulo 8 — PWA).

Públicos (sin token): solo revelan la IP de la LAN —ya conocida por cualquiera en
la red— y un QR que apunta a la app, para que el `<img>` del QR cargue sin
cabecera de auth. La IP se detecta por un socket UDP que NO envía paquetes
(válido en una LAN sin internet); el puerto se toma de la petición.
"""

import io
import socket

import segno
from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/api/red", tags=["red"])


def _lan_ip() -> str:
    """IP de la interfaz hacia la LAN (sin enviar tráfico; funciona offline)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # solo selecciona la interfaz de salida
        return s.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        s.close()


def _info(request: Request) -> dict:
    ip = _lan_ip()
    puerto = request.url.port or (443 if request.url.scheme == "https" else 80)
    return {"ip": ip, "puerto": puerto, "url": f"http://{ip}:{puerto}/"}


@router.get("/info")
def info(request: Request) -> dict:
    """Datos de acceso: IP de la LAN, puerto y URL para abrir la app."""
    return _info(request)


@router.get("/qr.svg")
def qr_svg(request: Request) -> Response:
    """QR (SVG) que codifica la URL de acceso a la app en la LAN."""
    url = _info(request)["url"]
    qr = segno.make(url, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=6, border=2, dark="#0d6efd")
    return Response(content=buf.getvalue(), media_type="image/svg+xml")
