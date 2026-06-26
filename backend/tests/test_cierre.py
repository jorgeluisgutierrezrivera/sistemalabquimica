"""Pruebas del Módulo 7 — Cierre y Conciliación (Paso 3 del SDD).

Cubre el cierre con conciliación entregado-vs-devuelto: reversión de inventario,
mermas (Kardex + registro_material_roto), default de devolución completa, estado
inválido (409), devuelta > entregada (409 + rollback), inmutabilidad tras
Cerrado y auth. La BD temporal aislada y el fixture `token` viven en conftest.py.
"""

import uuid

import pytest

from backend.app.database import get_db


@pytest.fixture()
def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def proximo_cierre(client, auth):
    """Arma un carrito, lo lleva a 'Proximo_Cierre' (pasando por Activo, que mueve
    inventario) y devuelve ids. Material entregada = 2 × 3 = 6; total=20."""
    s = uuid.uuid4().hex[:8]
    docente_id = client.post(
        "/api/docentes", json={"nombre": f"Doc {s}"}, headers=auth
    ).json()["id"]
    materia_id = client.post(
        "/api/materias",
        json={"sigla": f"CIE{s}", "nombre": "Lab Cierre", "carrera": "ING."},
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
                {"reactivo_id": reactivo_id, "cantidad_por_grupo": 10}
            ],
            "materiales": [
                {"material_id": material_id, "cantidad_por_grupo": 2}
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
            "fecha_realizacion": "2026-07-05",
            "hora_inicio": "08:00",
            "cantidad_grupos": 3,
        },
        headers=auth,
    ).json()["id"]
    for e in ("Activo", "Custodia", "Proximo_Cierre"):
        client.patch(f"/api/carritos/{cid}/estado", json={"estado": e}, headers=auth)

    # id de la línea de material del carrito.
    detalle = client.get(f"/api/carritos/{cid}", headers=auth).json()["materiales"][0]
    return {
        "carrito": cid,
        "material": material_id,
        "detalle_material": detalle["id"],
        "entregada": detalle["cantidad_entregada"],  # 6
    }


def _en_uso(client, auth, mid):
    return client.get(f"/api/materiales/{mid}", headers=auth).json()["cantidad_en_uso"]


def _total(client, auth, mid):
    return client.get(f"/api/materiales/{mid}", headers=auth).json()["cantidad_total"]


def _estado(client, auth, cid):
    return client.get(f"/api/carritos/{cid}", headers=auth).json()["estado_carrito"]


# ============================================================
# AUTH
# ============================================================
def test_cierre_sin_token_401(client, proximo_cierre):
    assert client.post(
        f"/api/carritos/{proximo_cierre['carrito']}/cierre", json={"devoluciones": []}
    ).status_code == 401


# ============================================================
# Cierre completo (sin merma)
# ============================================================
def test_cierre_completo_sin_merma(client, auth, proximo_cierre):
    cid, mid = proximo_cierre["carrito"], proximo_cierre["material"]
    total_antes = _total(client, auth, mid)
    assert _en_uso(client, auth, mid) == 6  # entregada

    resp = client.post(
        f"/api/carritos/{cid}/cierre", json={"devoluciones": []}, headers=auth
    )
    assert resp.status_code == 200 and resp.json()["estado_carrito"] == "Cerrado"

    # Todo devuelto: en_uso vuelve a 0, total intacto.
    assert _en_uso(client, auth, mid) == 0
    assert _total(client, auth, mid) == total_antes
    # cantidad_devuelta guardada = entregada.
    mat = resp.json()["materiales"][0]
    assert mat["cantidad_devuelta"] == proximo_cierre["entregada"]

    # Kardex retorno presente, sin merma ni registro de roto.
    with get_db() as conn:
        ret = conn.execute(
            "SELECT cantidad FROM movimientos_inventario WHERE carrito_id = ? "
            "AND tipo_movimiento = 'retorno'",
            (cid,),
        ).fetchone()
        merma = conn.execute(
            "SELECT COUNT(*) FROM movimientos_inventario WHERE carrito_id = ? "
            "AND tipo_movimiento = 'merma'",
            (cid,),
        ).fetchone()[0]
        rotos = conn.execute(
            "SELECT COUNT(*) FROM registro_material_roto WHERE carrito_id = ?", (cid,)
        ).fetchone()[0]
    assert ret is not None and ret["cantidad"] == 6
    assert merma == 0 and rotos == 0


# ============================================================
# Cierre con merma
# ============================================================
def test_cierre_con_merma_registra_roto(client, auth, proximo_cierre):
    cid, mid = proximo_cierre["carrito"], proximo_cierre["material"]
    did = proximo_cierre["detalle_material"]
    total_antes = _total(client, auth, mid)

    # Devuelve 4 de 6 → merma 2.
    resp = client.post(
        f"/api/carritos/{cid}/cierre",
        json={"devoluciones": [
            {"detalle_material_id": did, "cantidad_devuelta": 4,
             "observaciones": "2 rotas"}
        ]},
        headers=auth,
    )
    assert resp.status_code == 200

    assert _en_uso(client, auth, mid) == 0
    assert _total(client, auth, mid) == total_antes - 2  # merma deja el patrimonio

    with get_db() as conn:
        merma = conn.execute(
            "SELECT cantidad FROM movimientos_inventario WHERE carrito_id = ? "
            "AND tipo_movimiento = 'merma'",
            (cid,),
        ).fetchone()
        roto = conn.execute(
            "SELECT cantidad, docente_responsable, observaciones_rotura "
            "FROM registro_material_roto WHERE carrito_id = ?",
            (cid,),
        ).fetchone()
    assert merma is not None and merma["cantidad"] == 2
    assert roto is not None and roto["cantidad"] == 2
    assert roto["observaciones_rotura"] == "2 rotas"


# ============================================================
# Reglas
# ============================================================
def test_cierre_estado_invalido_409(client, auth):
    # Carrito recién armado (Preparacion) no se puede cerrar.
    s = uuid.uuid4().hex[:8]
    docente_id = client.post(
        "/api/docentes", json={"nombre": f"Doc {s}"}, headers=auth
    ).json()["id"]
    materia_id = client.post(
        "/api/materias",
        json={"sigla": f"INV{s}", "nombre": "Lab Inv", "carrera": "ING."},
        headers=auth,
    ).json()["id"]
    receta_id = client.post(
        "/api/recetas",
        json={"materia_id": materia_id, "nombre_practica": f"P {s}",
              "reactivos": [], "materiales": []},
        headers=auth,
    ).json()["id"]
    cid = client.post(
        "/api/carritos",
        json={"receta_id": receta_id, "docente_id": docente_id,
              "materia_id": materia_id, "nombre_numero_practica": f"P {s}",
              "fecha_realizacion": "2026-07-05", "cantidad_grupos": 1},
        headers=auth,
    ).json()["id"]
    assert client.post(
        f"/api/carritos/{cid}/cierre", json={"devoluciones": []}, headers=auth
    ).status_code == 409


def test_devuelta_mayor_que_entregada_409_rollback(client, auth, proximo_cierre):
    cid, mid = proximo_cierre["carrito"], proximo_cierre["material"]
    did = proximo_cierre["detalle_material"]

    resp = client.post(
        f"/api/carritos/{cid}/cierre",
        json={"devoluciones": [{"detalle_material_id": did, "cantidad_devuelta": 99}]},
        headers=auth,
    )
    assert resp.status_code == 409
    # Rollback: sigue en Proximo_Cierre y el inventario no cambió (en_uso=6).
    assert _estado(client, auth, cid) == "Proximo_Cierre"
    assert _en_uso(client, auth, mid) == 6


def test_cierre_404(client, auth):
    assert client.post(
        "/api/carritos/999999/cierre", json={"devoluciones": []}, headers=auth
    ).status_code == 404


def test_inmutable_tras_cerrado_409(client, auth, proximo_cierre):
    cid = proximo_cierre["carrito"]
    assert client.post(
        f"/api/carritos/{cid}/cierre", json={"devoluciones": []}, headers=auth
    ).status_code == 200
    # Segundo cierre, transición y borrado ya no se permiten.
    assert client.post(
        f"/api/carritos/{cid}/cierre", json={"devoluciones": []}, headers=auth
    ).status_code == 409
    assert client.patch(
        f"/api/carritos/{cid}/estado", json={"estado": "Activo"}, headers=auth
    ).status_code == 409
    assert client.delete(f"/api/carritos/{cid}", headers=auth).status_code == 409


def test_cierre_no_genera_movimientos_de_reactivo(client, auth, proximo_cierre):
    cid = proximo_cierre["carrito"]
    client.post(f"/api/carritos/{cid}/cierre", json={"devoluciones": []}, headers=auth)
    with get_db() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM movimientos_inventario WHERE carrito_id = ? "
            "AND tipo_insumo = 'reactivo' AND tipo_movimiento <> 'salida_consumo'",
            (cid,),
        ).fetchone()[0]
    assert n == 0
