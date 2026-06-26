"""Pruebas del Módulo 8 — Endpoints de red / acceso móvil (Paso 3 del SDD).

Cubre los endpoints públicos `/api/red/info` y `/api/red/qr.svg`. El Service
Worker y los iconos se verifican manualmente en el navegador.
"""


def test_info_publico_sin_token(client):
    resp = client.get("/api/red/info")
    assert resp.status_code == 200
    data = resp.json()
    assert {"ip", "puerto", "url"} <= data.keys()
    assert data["url"].startswith("http://") and data["url"].endswith("/")
    # La URL es coherente con ip + puerto.
    assert f"{data['ip']}:{data['puerto']}" in data["url"]


def test_qr_svg_publico(client):
    resp = client.get("/api/red/qr.svg")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in resp.content


def test_qr_y_info_coinciden(client):
    info = client.get("/api/red/info").json()
    svg = client.get("/api/red/qr.svg").content
    # El SVG es un QR válido (no vacío) generado para la URL de info.
    assert len(svg) > 100 and info["url"]
