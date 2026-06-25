"""Pruebas del Módulo 2 — Inventario (Paso 3 del ciclo SDD).

Cubre los catálogos de reactivos y materiales: CRUD, búsqueda, reglas de
negocio (duplicados, total < en_uso, borrado protegido) y autenticación.
La BD temporal aislada y el fixture `token` viven en conftest.py.
"""

import pytest

from backend.app.database import get_db


@pytest.fixture()
def auth(token):
    """Cabecera Authorization lista para usar."""
    return {"Authorization": f"Bearer {token}"}


def _poner_en_uso(material_id: int, cantidad: int) -> None:
    """Simula que un carrito tomó unidades (lo hará el Módulo 5)."""
    with get_db() as conn:
        conn.execute(
            "UPDATE materiales SET cantidad_en_uso = ? WHERE id = ?",
            (cantidad, material_id),
        )


# ============================================================
# AUTENTICACIÓN
# ============================================================
def test_reactivos_sin_token_401(client):
    assert client.get("/api/reactivos").status_code == 401


def test_materiales_sin_token_401(client):
    assert client.get("/api/materiales").status_code == 401


# ============================================================
# REACTIVOS
# ============================================================
def test_reactivo_crud_completo(client, auth):
    # Crear
    resp = client.post(
        "/api/reactivos",
        json={"nombre": "EDTA", "codigo": "M.F", "unidad_base": "mL"},
        headers=auth,
    )
    assert resp.status_code == 201
    rid = resp.json()["id"]

    # Listar y buscar
    assert any(r["id"] == rid for r in client.get("/api/reactivos", headers=auth).json())
    buscados = client.get("/api/reactivos?q=edt", headers=auth).json()
    assert len(buscados) == 1 and buscados[0]["nombre"] == "EDTA"

    # Obtener
    assert client.get(f"/api/reactivos/{rid}", headers=auth).json()["codigo"] == "M.F"

    # Editar
    resp = client.put(
        f"/api/reactivos/{rid}",
        json={"nombre": "EDTA 0.01M", "codigo": "M.F", "unidad_base": "g"},
        headers=auth,
    )
    assert resp.status_code == 200 and resp.json()["unidad_base"] == "g"

    # Borrar
    assert client.delete(f"/api/reactivos/{rid}", headers=auth).status_code == 204
    assert client.get(f"/api/reactivos/{rid}", headers=auth).status_code == 404


def test_reactivo_duplicado_409(client, auth):
    client.post("/api/reactivos", json={"nombre": "Acido Sulfurico"}, headers=auth)
    resp = client.post(
        "/api/reactivos", json={"nombre": "acido sulfurico"}, headers=auth
    )
    assert resp.status_code == 409


def test_reactivo_nombre_vacio_422(client, auth):
    resp = client.post("/api/reactivos", json={"nombre": ""}, headers=auth)
    assert resp.status_code == 422


def test_reactivo_inexistente_404(client, auth):
    assert client.get("/api/reactivos/999999", headers=auth).status_code == 404
    assert (
        client.put(
            "/api/reactivos/999999", json={"nombre": "X"}, headers=auth
        ).status_code
        == 404
    )
    assert client.delete("/api/reactivos/999999", headers=auth).status_code == 404


# ============================================================
# MATERIALES
# ============================================================
def test_material_crud_y_disponible(client, auth):
    resp = client.post(
        "/api/materiales",
        json={"nombre": "Bureta", "capacidad": "25 mL", "cantidad_total": 10},
        headers=auth,
    )
    assert resp.status_code == 201
    data = resp.json()
    mid = data["id"]
    assert data["cantidad_en_uso"] == 0
    assert data["cantidad_disponible"] == 10  # 10 - 0

    # Editar total
    resp = client.put(
        f"/api/materiales/{mid}",
        json={"nombre": "Bureta", "capacidad": "25 mL", "cantidad_total": 15},
        headers=auth,
    )
    assert resp.status_code == 200 and resp.json()["cantidad_disponible"] == 15

    # Borrar
    assert client.delete(f"/api/materiales/{mid}", headers=auth).status_code == 204


def test_material_disponible_con_en_uso(client, auth):
    mid = client.post(
        "/api/materiales",
        json={"nombre": "Pipeta", "capacidad": "10 mL", "cantidad_total": 20},
        headers=auth,
    ).json()["id"]
    _poner_en_uso(mid, 8)
    data = client.get(f"/api/materiales/{mid}", headers=auth).json()
    assert data["cantidad_en_uso"] == 8
    assert data["cantidad_disponible"] == 12  # 20 - 8


def test_material_total_menor_a_en_uso_409(client, auth):
    mid = client.post(
        "/api/materiales",
        json={"nombre": "Matraz", "capacidad": "250 mL", "cantidad_total": 12},
        headers=auth,
    ).json()["id"]
    _poner_en_uso(mid, 5)
    resp = client.put(
        f"/api/materiales/{mid}",
        json={"nombre": "Matraz", "capacidad": "250 mL", "cantidad_total": 3},
        headers=auth,
    )
    assert resp.status_code == 409


def test_material_borrar_con_en_uso_409(client, auth):
    mid = client.post(
        "/api/materiales",
        json={"nombre": "Vaso precipitado", "cantidad_total": 6},
        headers=auth,
    ).json()["id"]
    _poner_en_uso(mid, 2)
    assert client.delete(f"/api/materiales/{mid}", headers=auth).status_code == 409


def test_material_duplicado_409(client, auth):
    client.post(
        "/api/materiales",
        json={"nombre": "Probeta", "capacidad": "100 mL", "cantidad_total": 4},
        headers=auth,
    )
    resp = client.post(
        "/api/materiales",
        json={"nombre": "probeta", "capacidad": "100 mL", "cantidad_total": 1},
        headers=auth,
    )
    assert resp.status_code == 409


def test_material_mismo_nombre_distinta_capacidad_ok(client, auth):
    a = client.post(
        "/api/materiales",
        json={"nombre": "Vidrio reloj", "capacidad": "chico", "cantidad_total": 3},
        headers=auth,
    )
    b = client.post(
        "/api/materiales",
        json={"nombre": "Vidrio reloj", "capacidad": "grande", "cantidad_total": 3},
        headers=auth,
    )
    assert a.status_code == 201 and b.status_code == 201


def test_material_total_negativo_422(client, auth):
    resp = client.post(
        "/api/materiales",
        json={"nombre": "Soporte", "cantidad_total": -1},
        headers=auth,
    )
    assert resp.status_code == 422
