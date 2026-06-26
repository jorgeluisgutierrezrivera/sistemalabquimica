"""Pruebas del Módulo 6 — Estados del Carrito y Dashboard (Paso 3 del SDD).

Cubre la máquina de estados forward-only, el movimiento de inventario al entrar
a 'Activo' (cantidad_en_uso + Kardex), transiciones inválidas (409), stock
insuficiente (409 con rollback), dashboard y auth.
La BD temporal aislada y el fixture `token` viven en conftest.py.
"""

import uuid

import pytest

from backend.app.database import get_db


@pytest.fixture()
def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def carrito(client, auth):
    """Crea catálogos + receta y arma un carrito (estado 'Preparacion').
    Devuelve ids relevantes. Material con stock holgado (cantidad_total=20)."""
    s = uuid.uuid4().hex[:8]
    docente_id = client.post(
        "/api/docentes", json={"nombre": f"Doc {s}"}, headers=auth
    ).json()["id"]
    materia_id = client.post(
        "/api/materias",
        json={"sigla": f"EST{s}", "nombre": "Lab Estados", "carrera": "ING."},
        headers=auth,
    ).json()["id"]
    reactivo_id = client.post(
        "/api/reactivos", json={"nombre": f"Quelante {s}"}, headers=auth
    ).json()["id"]
    material_id = client.post(
        "/api/materiales",
        json={"nombre": f"Bureta {s}", "capacidad": "25 mL", "cantidad_total": 20},
        headers=auth,
    ).json()["id"]
    receta_id = client.post(
        "/api/recetas",
        json={
            "materia_id": materia_id,
            "nombre_practica": f"Práctica {s}",
            "reactivos": [
                {"reactivo_id": reactivo_id, "concentracion_unidad": "1M",
                 "cantidad_por_grupo": 10}
            ],
            "materiales": [
                {"material_id": material_id, "cantidad_por_grupo": 2,
                 "observaciones": None}
            ],
        },
        headers=auth,
    ).json()["id"]
    cid = client.post(
        "/api/carritos",
        json={
            "receta_id": receta_id,
            "docente_id": docente_id,
            "materia_id": materia_id,
            "nombre_numero_practica": f"P {s}",
            "fecha_realizacion": "2026-07-02",
            "hora_inicio": "08:00",
            "cantidad_grupos": 3,  # material entregada = 2 × 3 = 6
        },
        headers=auth,
    ).json()["id"]
    return {"carrito": cid, "material": material_id, "reactivo": reactivo_id}


def _estado(client, auth, cid):
    return client.get(f"/api/carritos/{cid}", headers=auth).json()["estado_carrito"]


# ============================================================
# AUTH
# ============================================================
def test_estado_sin_token_401(client, carrito):
    assert client.patch(
        f"/api/carritos/{carrito['carrito']}/estado", json={"estado": "Activo"}
    ).status_code == 401


def test_dashboard_sin_token_401(client):
    assert client.get("/api/dashboard").status_code == 401


# ============================================================
# Transición a Activo: inventario + Kardex
# ============================================================
def test_activar_mueve_inventario_y_kardex(client, auth, carrito):
    cid, mid, rid = carrito["carrito"], carrito["material"], carrito["reactivo"]

    en_uso_antes = client.get(f"/api/materiales/{mid}", headers=auth).json()[
        "cantidad_en_uso"
    ]
    resp = client.patch(
        f"/api/carritos/{cid}/estado", json={"estado": "Activo"}, headers=auth
    )
    assert resp.status_code == 200 and resp.json()["estado_carrito"] == "Activo"

    # cantidad_en_uso sube en la cantidad entregada (6).
    en_uso_despues = client.get(f"/api/materiales/{mid}", headers=auth).json()[
        "cantidad_en_uso"
    ]
    assert en_uso_despues == en_uso_antes + 6

    # Kardex: entrada_uso (material) + salida_consumo (reactivo).
    with get_db() as conn:
        mat = conn.execute(
            "SELECT cantidad FROM movimientos_inventario WHERE carrito_id = ? "
            "AND tipo_insumo = 'material' AND tipo_movimiento = 'entrada_uso'",
            (cid,),
        ).fetchone()
        rea = conn.execute(
            "SELECT cantidad FROM movimientos_inventario WHERE carrito_id = ? "
            "AND tipo_insumo = 'reactivo' AND tipo_movimiento = 'salida_consumo'",
            (cid,),
        ).fetchone()
    assert mat is not None and mat["cantidad"] == 6
    assert rea is not None and rea["cantidad"] == 30  # 10 × 3 grupos


def test_cadena_valida_hasta_proximo_cierre(client, auth, carrito):
    cid = carrito["carrito"]
    assert client.patch(
        f"/api/carritos/{cid}/estado", json={"estado": "Activo"}, headers=auth
    ).status_code == 200
    assert client.patch(
        f"/api/carritos/{cid}/estado", json={"estado": "Custodia"}, headers=auth
    ).status_code == 200
    assert client.patch(
        f"/api/carritos/{cid}/estado", json={"estado": "Proximo_Cierre"}, headers=auth
    ).status_code == 200
    assert _estado(client, auth, cid) == "Proximo_Cierre"


# ============================================================
# Transiciones inválidas
# ============================================================
def test_salto_invalido_409(client, auth, carrito):
    # Preparacion → Proximo_Cierre (salta Activo) no permitido.
    assert client.patch(
        f"/api/carritos/{carrito['carrito']}/estado",
        json={"estado": "Proximo_Cierre"},
        headers=auth,
    ).status_code == 409


def test_retroceso_invalido_409(client, auth, carrito):
    cid = carrito["carrito"]
    client.patch(f"/api/carritos/{cid}/estado", json={"estado": "Activo"}, headers=auth)
    # Activo → Preparacion (retroceso) no permitido.
    assert client.patch(
        f"/api/carritos/{cid}/estado", json={"estado": "Preparacion"}, headers=auth
    ).status_code == 409


def test_cerrado_es_m7_409(client, auth, carrito):
    cid = carrito["carrito"]
    for e in ("Activo", "Custodia", "Proximo_Cierre"):
        client.patch(f"/api/carritos/{cid}/estado", json={"estado": e}, headers=auth)
    # Proximo_Cierre → Cerrado pertenece a M7.
    assert client.patch(
        f"/api/carritos/{cid}/estado", json={"estado": "Cerrado"}, headers=auth
    ).status_code == 409


def test_estado_invalido_422(client, auth, carrito):
    assert client.patch(
        f"/api/carritos/{carrito['carrito']}/estado",
        json={"estado": "Inventado"},
        headers=auth,
    ).status_code == 422


def test_transicion_404(client, auth):
    assert client.patch(
        "/api/carritos/999999/estado", json={"estado": "Activo"}, headers=auth
    ).status_code == 404


# ============================================================
# Stock insuficiente (rollback)
# ============================================================
def test_stock_insuficiente_409_y_rollback(client, auth):
    s = uuid.uuid4().hex[:8]
    docente_id = client.post(
        "/api/docentes", json={"nombre": f"Doc {s}"}, headers=auth
    ).json()["id"]
    materia_id = client.post(
        "/api/materias",
        json={"sigla": f"STK{s}", "nombre": "Lab Stock", "carrera": "ING."},
        headers=auth,
    ).json()["id"]
    # Material con muy poco stock.
    material_id = client.post(
        "/api/materiales",
        json={"nombre": f"Escaso {s}", "capacidad": "1 L", "cantidad_total": 1},
        headers=auth,
    ).json()["id"]
    receta_id = client.post(
        "/api/recetas",
        json={
            "materia_id": materia_id,
            "nombre_practica": f"Práctica {s}",
            "reactivos": [],
            "materiales": [{"material_id": material_id, "cantidad_por_grupo": 5}],
        },
        headers=auth,
    ).json()["id"]
    cid = client.post(
        "/api/carritos",
        json={
            "receta_id": receta_id,
            "docente_id": docente_id,
            "materia_id": materia_id,
            "nombre_numero_practica": f"P {s}",
            "fecha_realizacion": "2026-07-02",
            "cantidad_grupos": 2,  # entregada = 5 × 2 = 10 > 1 disponible
        },
        headers=auth,
    ).json()["id"]

    resp = client.patch(
        f"/api/carritos/{cid}/estado", json={"estado": "Activo"}, headers=auth
    )
    assert resp.status_code == 409
    # Rollback: ni el estado ni el inventario cambiaron.
    assert _estado(client, auth, cid) == "Preparacion"
    assert client.get(f"/api/materiales/{material_id}", headers=auth).json()[
        "cantidad_en_uso"
    ] == 0


# ============================================================
# Dashboard
# ============================================================
def test_dashboard_cuenta_por_estado(client, auth, carrito):
    cid = carrito["carrito"]
    client.patch(f"/api/carritos/{cid}/estado", json={"estado": "Activo"}, headers=auth)

    d = client.get("/api/dashboard", headers=auth).json()
    assert set(d["por_estado"].keys()) == {
        "Preparacion", "Activo", "Custodia", "Proximo_Cierre", "Cerrado"
    }
    assert d["por_estado"]["Activo"] >= 1
    assert d["total"] == sum(d["por_estado"].values())
    assert any(c["id"] == cid for c in d["activos"])


# ============================================================
# Consistencia con M5: borrado tras Activo
# ============================================================
def test_borrado_bloqueado_tras_activar_409(client, auth, carrito):
    cid = carrito["carrito"]
    client.patch(f"/api/carritos/{cid}/estado", json={"estado": "Activo"}, headers=auth)
    assert client.delete(f"/api/carritos/{cid}", headers=auth).status_code == 409
