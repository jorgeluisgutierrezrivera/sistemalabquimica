r"""Genera los iconos PWA (placeholder) en Python puro, sin PIL.

Dibuja un matraz Erlenmeyer blanco sobre el color del tema (#0d6efd) y escribe
`icon-192.png` y `icon-512.png` en `frontend/assets/icons/`. Reemplazables por
arte definitivo más adelante.

Uso:  .\.venv\Scripts\python.exe scripts/gen_icons.py
"""

import struct
import zlib
from pathlib import Path

BG = (13, 110, 253)       # #0d6efd (color del tema)
FG = (255, 255, 255)      # blanco (matraz)
ICONS_DIR = Path(__file__).resolve().parents[1] / "frontend" / "assets" / "icons"


def _es_matraz(nx: float, ny: float) -> bool:
    """¿El punto normalizado (0..1) cae dentro del glifo del matraz?"""
    # Cuello (rectángulo estrecho arriba).
    if 0.43 <= nx <= 0.57 and 0.16 <= ny <= 0.40:
        return True
    # Cuerpo (triángulo que se ensancha hacia abajo).
    if 0.40 <= ny <= 0.80:
        hw = 0.07 + (ny - 0.40) / (0.80 - 0.40) * (0.33 - 0.07)
        if abs(nx - 0.5) <= hw:
            return True
    # Base (línea inferior).
    if 0.28 <= nx <= 0.72 and 0.80 <= ny <= 0.85:
        return True
    return False


def _png(size: int) -> bytes:
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filtro 0 (None) por scanline
        ny = (y + 0.5) / size
        for x in range(size):
            nx = (x + 0.5) / size
            raw += bytes(FG if _es_matraz(nx, ny) else BG)

    def chunk(typ: bytes, data: bytes) -> bytes:
        body = typ + data
        return (
            struct.pack(">I", len(data))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # RGB, 8 bits
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def main() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        destino = ICONS_DIR / f"icon-{size}.png"
        destino.write_bytes(_png(size))
        print(f"[OK] {destino} ({size}x{size})")


if __name__ == "__main__":
    main()
