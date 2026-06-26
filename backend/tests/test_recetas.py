"""Pruebas del Módulo 4 — Recetas Maestras (Paso 3 del ciclo SDD).

Cubre el agregado receta (cabecera + líneas): CRUD anidado, filtros, reemplazo
de líneas al editar, duplicada (409), FK inexistente (400), validación (422),
borrado (con/sin carrito que la referencia) y auth.
La BD temporal aislada y el fixture `token` viven en conftest.py.
"""

import uuid

import pytest

from backend.app.database import get_db


@pytest.fixture()
def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def datos_base(client, auth):
    """Crea materia + reactivo + material de apoyo (nombres únicos) y devuelve ids.

    La BD de pruebas es de sesión (persiste entre tests), por eso cada llamada
    usa un sufijo único para no chocar con entidades de pruebas anteriores.
    """
    sufijo = uuid.uuid4().hex[:8]
    materia_id = client.post(
        "/api/materias",
        json={"sigla": f"RCT{sufijo}", "nombre": "Lab Recetas", "carrera": "ING."},
        headers=auth,
    ).json()["id"]
    reactivo_id = client.post(
        "/api/reactivos", json={"nombre": f"EDTA {sufijo}"}, headers=auth
    ).json()["id"]
    material_id = client.post(
        "/api/materiales",
        json={"nombre": f"Bureta {sufijo}", "capacidad": "25 mL", "cantidad_total": 5},
        headers=auth,
    ).json()["id"]
    return {"materia": materia_id, "reactivo": reactivo_id, "material": material_id}


def _payload(base, nombre="Práctica X", activa=True):
    return {
        "materia_id": base["materia"],
        "nombre_practica": nombre,
        "descripcion": "desc",
        "activa": activa,
        "reactivos": [
            {
                "reactivo_id": base["reactivo"],
                "concentracion_unidad": "0,01M / mL",
                "cantidad_por_grupo": 50,
            }
        ],
        "materiales": [
            {"material_id": base["material"], "cantidad_por_grupo": 2, "observaciones": "ok"}
        ],
    }


# ============================================================
# AUTH
# ============================================================
def test_recetas_sin_token_401(client):
    assert client.get("/api/recetas").status_code == 401


# ============================================================
# CRUD anidado
# ============================================================
def test_crear_y_obtener_con_detalles(client, auth, datos_base):
    resp = client.post("/api/recetas", json=_payload(datos_base), headers=auth)
    assert resp.status_code == 201
    rid = resp.json()["id"]

    r = client.get(f"/api/recetas/{rid}", headers=auth).json()
    assert r["nombre_practica"] == "Práctica X"
    assert r["materia"].startswith("RCT") and " - Lab Recetas" in r["materia"]
    assert len(r["reactivos"]) == 1 and r["reactivos"][0]["nombre"].startswith("EDTA")
    assert r["reactivos"][0]["cantidad_por_grupo"] == 50
    assert len(r["materiales"]) == 1 and r["materiales"][0]["capacidad"] == "25 mL"


def test_listar_y_filtros(client, auth, datos_base):
    client.post("/api/recetas", json=_payload(datos_base, "Filtrable A"), headers=auth)
    client.post(
        "/api/recetas",
        json=_payload(datos_base, "Inactiva B", activa=False),
        headers=auth,
    )

    # Filtro por texto.
    assert len(client.get("/api/recetas?q=filtrable", headers=auth).json()) == 1
    # Filtro por materia.
    porm = client.get(
        f"/api/recetas?materia_id={datos_base['materia']}", headers=auth
    ).json()
    assert len(porm) >= 2
    # Filtro por activa.
    activas = client.get("/api/recetas?activa=true", headers=auth).json()
    assert all(r["activa"] for r in activas)
    inactivas = client.get("/api/recetas?activa=false", headers=auth).json()
    assert all(not r["activa"] for r in inactivas)


def test_editar_reemplaza_lineas(client, auth, datos_base):
    rid = client.post(
        "/api/recetas", json=_payload(datos_base, "Editable"), headers=auth
    ).json()["id"]

    # Nuevo reactivo para sustituir la línea.
    otro_react = client.post(
        "/api/reactivos", json={"nombre": "Otro reactivo"}, headers=auth
    ).json()["id"]

    nuevo = _payload(datos_base, "Editable")
    nuevo["reactivos"] = [
        {"reactivo_id": otro_react, "concentracion_unidad": "1M", "cantidad_por_grupo": 10}
    ]
    nuevo["materiales"] = []  # se eliminan todos los materiales

    resp = client.put(f"/api/recetas/{rid}", json=nuevo, headers=auth)
    assert resp.status_code == 200

    r = client.get(f"/api/recetas/{rid}", headers=auth).json()
    assert len(r["reactivos"]) == 1 and r["reactivos"][0]["reactivo_id"] == otro_react
    assert len(r["materiales"]) == 0


def test_duplicada_misma_materia_practica_409(client, auth, datos_base):
    client.post("/api/recetas", json=_payload(datos_base, "Repetida"), headers=auth)
    resp = client.post(
        "/api/recetas", json=_payload(datos_base, "repetida"), headers=auth
    )
    assert resp.status_code == 409


def test_fk_inexistente_400(client, auth, datos_base):
    mal = _payload(datos_base)
    mal["reactivos"] = [{"reactivo_id": 999999, "cantidad_por_grupo": 1}]
    assert client.post("/api/recetas", json=mal, headers=auth).status_code == 400

    mal2 = _payload(datos_base)
    mal2["materia_id"] = 999999
    assert client.post("/api/recetas", json=mal2, headers=auth).status_code == 400


def test_validacion_cantidad_y_nombre_422(client, auth, datos_base):
    # cantidad_por_grupo <= 0
    mal = _payload(datos_base)
    mal["reactivos"][0]["cantidad_por_grupo"] = 0
    assert client.post("/api/recetas", json=mal, headers=auth).status_code == 422

    # nombre_practica vacío
    mal2 = _payload(datos_base, "")
    assert client.post("/api/recetas", json=mal2, headers=auth).status_code == 422


def test_inexistente_404(client, auth):
    assert client.get("/api/recetas/999999", headers=auth).status_code == 404
    assert client.delete("/api/recetas/999999", headers=auth).status_code == 404


# ============================================================
# Borrado
# ============================================================
def test_borrar_ok_y_cascada(client, auth, datos_base):
    rid = client.post(
        "/api/recetas", json=_payload(datos_base, "Borrable"), headers=auth
    ).json()["id"]
    assert client.delete(f"/api/recetas/{rid}", headers=auth).status_code == 204

    # Verifica cascada de líneas.
    with get_db() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM receta_detalle_reactivos WHERE receta_id = ?",
            (rid,),
        ).fetchone()[0]
    assert n == 0


def test_borrar_protegido_por_carrito_409(client, auth, datos_base):
    rid = client.post(
        "/api/recetas", json=_payload(datos_base, "Usada"), headers=auth
    ).json()["id"]

    # Simula un carrito que referencia la receta (lo hará el Módulo 5).
    docente_id = client.post(
        "/api/docentes", json={"nombre": "Docente carrito"}, headers=auth
    ).json()["id"]
    with get_db() as conn:
        conn.execute(
            "INSERT INTO carritos_cabecera "
            "(docente_id, materia_id, receta_id, nombre_numero_practica, fecha_realizacion) "
            "VALUES (?, ?, ?, 'Usada', '2026-06-25')",
            (docente_id, datos_base["materia"], rid),
        )

    assert client.delete(f"/api/recetas/{rid}", headers=auth).status_code == 409
