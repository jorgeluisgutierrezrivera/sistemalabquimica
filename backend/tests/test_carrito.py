"""Pruebas del Módulo 5 — Carrito de Insumos (Paso 3 del ciclo SDD).

Cubre el agregado carrito: armado desde receta (copia de líneas + snapshot +
cálculo de totales), filtros, edición con reemplazo de líneas y extras,
unicidad (409), FK inexistente / receta inactiva (400), validación (422),
borrado (solo en 'Preparacion', con cascada) y auth.
La BD temporal aislada y el fixture `token` viven en conftest.py.
"""

import uuid

import pytest

from backend.app.database import get_db


@pytest.fixture()
def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def base(client, auth):
    """Crea docente + materia + ambiente + reactivo + material + una receta con
    líneas (nombres únicos por L-005). Devuelve los ids necesarios."""
    s = uuid.uuid4().hex[:8]
    docente_id = client.post(
        "/api/docentes", json={"nombre": f"Docente {s}"}, headers=auth
    ).json()["id"]
    materia_id = client.post(
        "/api/materias",
        json={"sigla": f"CAR{s}", "nombre": "Lab Carrito", "carrera": "ING."},
        headers=auth,
    ).json()["id"]
    ambiente_id = client.post(
        "/api/ambientes", json={"nombre": f"Lab {s}"}, headers=auth
    ).json()["id"]
    # Nombre sin la subcadena "edt" para no chocar con la búsqueda q=edt de
    # test_inventario, que corre después en la misma BD de sesión (L-005).
    reactivo_id = client.post(
        "/api/reactivos", json={"nombre": f"Quelante {s}"}, headers=auth
    ).json()["id"]
    material_id = client.post(
        "/api/materiales",
        json={"nombre": f"Bureta {s}", "capacidad": "25 mL", "cantidad_total": 10},
        headers=auth,
    ).json()["id"]

    def crear_receta(nombre, activa=True):
        return client.post(
            "/api/recetas",
            json={
                "materia_id": materia_id,
                "nombre_practica": nombre,
                "activa": activa,
                "reactivos": [
                    {
                        "reactivo_id": reactivo_id,
                        "concentracion_unidad": "0,01M / mL",
                        "cantidad_por_grupo": 50,
                    }
                ],
                "materiales": [
                    {"material_id": material_id, "cantidad_por_grupo": 2,
                     "observaciones": "calibrada"}
                ],
            },
            headers=auth,
        ).json()["id"]

    receta_id = crear_receta(f"Práctica {s}")
    return {
        "docente": docente_id,
        "materia": materia_id,
        "ambiente": ambiente_id,
        "reactivo": reactivo_id,
        "material": material_id,
        "receta": receta_id,
        "crear_receta": crear_receta,
        "sufijo": s,
    }


def _armar(base, **over):
    cuerpo = {
        "receta_id": base["receta"],
        "docente_id": base["docente"],
        "materia_id": base["materia"],
        "nombre_numero_practica": "Complexometría #6",
        "fecha_realizacion": "2026-07-01",
        "ambiente_id": base["ambiente"],
        "hora_inicio": "08:00",
        "hora_fin": "10:00",
        "numero_pedido": 12,
        "numero_grupos": "1 y 3",
        "cantidad_grupos": 3,
        "codigo_lab_qmc": "QMC-LAB-1",
    }
    cuerpo.update(over)
    return cuerpo


# ============================================================
# AUTH
# ============================================================
def test_carritos_sin_token_401(client):
    assert client.get("/api/carritos").status_code == 401


# ============================================================
# Armado desde receta
# ============================================================
def test_armar_desde_receta_copia_lineas_y_totales(client, auth, base):
    resp = client.post("/api/carritos", json=_armar(base), headers=auth)
    assert resp.status_code == 201
    cid = resp.json()["id"]

    c = client.get(f"/api/carritos/{cid}", headers=auth).json()
    assert c["estado_carrito"] == "Preparacion"
    assert c["materia"].startswith("CAR") and " - Lab Carrito" in c["materia"]
    assert c["cantidad_grupos"] == 3
    # Reactivo: snapshot de nombre + total = por_grupo (50) × grupos (3) = 150.
    assert len(c["reactivos"]) == 1
    assert c["reactivos"][0]["nombre"].startswith("Quelante")
    assert c["reactivos"][0]["cantidad_por_grupo"] == 50
    assert c["reactivos"][0]["cantidad_total"] == 150
    assert c["reactivos"][0]["es_extra"] is False
    # Material: entregada = por_grupo (2) × grupos (3) = 6.
    assert len(c["materiales"]) == 1
    assert c["materiales"][0]["nombre"].startswith("Bureta")
    assert c["materiales"][0]["capacidad"] == "25 mL"
    assert c["materiales"][0]["cantidad_entregada"] == 6


def test_listar_y_filtros(client, auth, base):
    client.post("/api/carritos", json=_armar(base), headers=auth)

    # Filtro por texto (práctica).
    assert len(client.get("/api/carritos?q=complexo", headers=auth).json()) >= 1
    # Filtro por materia.
    porm = client.get(
        f"/api/carritos?materia_id={base['materia']}", headers=auth
    ).json()
    assert len(porm) >= 1
    # Filtro por fecha.
    porf = client.get("/api/carritos?fecha=2026-07-01", headers=auth).json()
    assert all(c["fecha_realizacion"] == "2026-07-01" for c in porf)
    # Filtro por estado.
    prep = client.get("/api/carritos?estado=Preparacion", headers=auth).json()
    assert all(c["estado_carrito"] == "Preparacion" for c in prep)


def test_editar_reemplaza_lineas_y_extra(client, auth, base):
    cid = client.post("/api/carritos", json=_armar(base), headers=auth).json()["id"]

    # Otro reactivo para sustituir + marcar un material extra.
    otro_react = client.post(
        "/api/reactivos", json={"nombre": f"HCl {base['sufijo']}"}, headers=auth
    ).json()["id"]

    cuerpo = _armar(base)
    del cuerpo["receta_id"]  # el PUT no re-arma
    cuerpo["cantidad_grupos"] = 4
    cuerpo["reactivos"] = [
        {"reactivo_id": otro_react, "concentracion_unidad": "1M", "cantidad_por_grupo": 10,
         "es_extra": False}
    ]
    cuerpo["materiales"] = [
        {"material_id": base["material"], "cantidad_entregada": 8, "es_extra": True,
         "observaciones": "añadido a mano"}
    ]

    resp = client.put(f"/api/carritos/{cid}", json=cuerpo, headers=auth)
    assert resp.status_code == 200

    c = client.get(f"/api/carritos/{cid}", headers=auth).json()
    assert len(c["reactivos"]) == 1
    assert c["reactivos"][0]["reactivo_id"] == otro_react
    # total recalculado = 10 × 4 = 40.
    assert c["reactivos"][0]["cantidad_total"] == 40
    assert len(c["materiales"]) == 1
    assert c["materiales"][0]["es_extra"] is True
    assert c["materiales"][0]["cantidad_entregada"] == 8


# ============================================================
# Reglas
# ============================================================
def test_unicidad_misma_practica_fecha_hora_409(client, auth, base):
    assert client.post("/api/carritos", json=_armar(base), headers=auth).status_code == 201
    # Mismo materia + práctica + fecha + hora, no cerrado → 409.
    resp = client.post(
        "/api/carritos",
        json=_armar(base, nombre_numero_practica="complexometría #6"),
        headers=auth,
    )
    assert resp.status_code == 409


def test_fk_inexistente_400(client, auth, base):
    assert client.post(
        "/api/carritos", json=_armar(base, docente_id=999999), headers=auth
    ).status_code == 400
    assert client.post(
        "/api/carritos", json=_armar(base, receta_id=999999), headers=auth
    ).status_code == 400


def test_receta_inactiva_400(client, auth, base):
    inactiva = base["crear_receta"](f"Inactiva {base['sufijo']}", activa=False)
    resp = client.post(
        "/api/carritos", json=_armar(base, receta_id=inactiva), headers=auth
    )
    assert resp.status_code == 400


def test_validacion_422(client, auth, base):
    # cantidad_grupos <= 0
    assert client.post(
        "/api/carritos", json=_armar(base, cantidad_grupos=0), headers=auth
    ).status_code == 422
    # práctica vacía
    assert client.post(
        "/api/carritos", json=_armar(base, nombre_numero_practica=""), headers=auth
    ).status_code == 422


def test_inexistente_404(client, auth):
    assert client.get("/api/carritos/999999", headers=auth).status_code == 404
    assert client.delete("/api/carritos/999999", headers=auth).status_code == 404


# ============================================================
# Borrado
# ============================================================
def test_borrar_ok_en_preparacion_y_cascada(client, auth, base):
    cid = client.post("/api/carritos", json=_armar(base), headers=auth).json()["id"]
    assert client.delete(f"/api/carritos/{cid}", headers=auth).status_code == 204
    with get_db() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM carrito_detalle_reactivos WHERE carrito_id = ?",
            (cid,),
        ).fetchone()[0]
    assert n == 0


def test_borrar_bloqueado_si_no_preparacion_409(client, auth, base):
    cid = client.post("/api/carritos", json=_armar(base), headers=auth).json()["id"]
    # Simula que el carrito ya avanzó de estado (lo hará M6).
    with get_db() as conn:
        conn.execute(
            "UPDATE carritos_cabecera SET estado_carrito = 'Activo' WHERE id = ?",
            (cid,),
        )
    assert client.delete(f"/api/carritos/{cid}", headers=auth).status_code == 409
