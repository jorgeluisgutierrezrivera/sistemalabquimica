"""Pruebas del Módulo 3 — Catálogos Base (Paso 3 del ciclo SDD).

Cubre docentes, materias y ambientes: CRUD, búsqueda, duplicados (409),
validación (422), 404, borrado protegido por integridad referencial y auth.
La BD temporal aislada y el fixture `token` viven en conftest.py.
"""

import pytest

from backend.app.database import get_db


@pytest.fixture()
def auth(token):
    """Cabecera Authorization lista para usar."""
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# AUTENTICACIÓN
# ============================================================
def test_docentes_sin_token_401(client):
    assert client.get("/api/docentes").status_code == 401


def test_materias_sin_token_401(client):
    assert client.get("/api/materias").status_code == 401


def test_ambientes_sin_token_401(client):
    assert client.get("/api/ambientes").status_code == 401


# ============================================================
# DOCENTES
# ============================================================
def test_docente_crud_completo(client, auth):
    resp = client.post("/api/docentes", json={"nombre": "Condori"}, headers=auth)
    assert resp.status_code == 201
    did = resp.json()["id"]

    assert any(d["id"] == did for d in client.get("/api/docentes", headers=auth).json())
    buscados = client.get("/api/docentes?q=cond", headers=auth).json()
    assert len(buscados) == 1 and buscados[0]["nombre"] == "Condori"

    assert client.get(f"/api/docentes/{did}", headers=auth).json()["nombre"] == "Condori"

    resp = client.put(f"/api/docentes/{did}", json={"nombre": "Condori M."}, headers=auth)
    assert resp.status_code == 200 and resp.json()["nombre"] == "Condori M."

    assert client.delete(f"/api/docentes/{did}", headers=auth).status_code == 204
    assert client.get(f"/api/docentes/{did}", headers=auth).status_code == 404


def test_docente_duplicado_409(client, auth):
    client.post("/api/docentes", json={"nombre": "Irusta"}, headers=auth)
    resp = client.post("/api/docentes", json={"nombre": "irusta"}, headers=auth)
    assert resp.status_code == 409


def test_docente_nombre_vacio_422(client, auth):
    assert client.post("/api/docentes", json={"nombre": ""}, headers=auth).status_code == 422


def test_docente_inexistente_404(client, auth):
    assert client.get("/api/docentes/999999", headers=auth).status_code == 404
    assert (
        client.put("/api/docentes/999999", json={"nombre": "X"}, headers=auth).status_code
        == 404
    )
    assert client.delete("/api/docentes/999999", headers=auth).status_code == 404


# ============================================================
# MATERIAS
# ============================================================
def test_materia_crud_completo(client, auth):
    resp = client.post(
        "/api/materias",
        json={"sigla": "QMC021", "nombre": "Química Orgánica I", "carrera": "ING. QUÍMICA"},
        headers=auth,
    )
    assert resp.status_code == 201
    mid = resp.json()["id"]

    # Búsqueda por sigla (la búsqueda LIKE es case-insensitive pero NO ignora
    # acentos en SQLite; por eso filtramos por la sigla, sin tildes).
    buscados = client.get("/api/materias?q=qmc021", headers=auth).json()
    assert any(m["id"] == mid for m in buscados)

    resp = client.put(
        f"/api/materias/{mid}",
        json={"sigla": "QMC021", "nombre": "Química Orgánica I", "carrera": "FARMACIA"},
        headers=auth,
    )
    assert resp.status_code == 200 and resp.json()["carrera"] == "FARMACIA"

    assert client.delete(f"/api/materias/{mid}", headers=auth).status_code == 204


def test_materia_duplicada_por_sigla_y_nombre_409(client, auth):
    base = {"sigla": "BAS100", "nombre": "Química General", "carrera": "ING."}
    client.post("/api/materias", json=base, headers=auth)
    dup = {"sigla": "bas100", "nombre": "química general", "carrera": "OTRA"}
    assert client.post("/api/materias", json=dup, headers=auth).status_code == 409


def test_materia_misma_sigla_distinto_nombre_ok(client, auth):
    a = client.post(
        "/api/materias",
        json={"sigla": "QMC100", "nombre": "Lab A", "carrera": "ING."},
        headers=auth,
    )
    b = client.post(
        "/api/materias",
        json={"sigla": "QMC100", "nombre": "Lab B", "carrera": "ING."},
        headers=auth,
    )
    assert a.status_code == 201 and b.status_code == 201


def test_materia_campos_faltantes_422(client, auth):
    # Falta carrera.
    resp = client.post(
        "/api/materias", json={"sigla": "X", "nombre": "Y"}, headers=auth
    )
    assert resp.status_code == 422


# ============================================================
# AMBIENTES
# ============================================================
def test_ambiente_crud_completo(client, auth):
    resp = client.post("/api/ambientes", json={"nombre": "INA014"}, headers=auth)
    assert resp.status_code == 201
    aid = resp.json()["id"]

    assert client.get(f"/api/ambientes/{aid}", headers=auth).json()["nombre"] == "INA014"

    resp = client.put(f"/api/ambientes/{aid}", json={"nombre": "LAB QMC"}, headers=auth)
    assert resp.status_code == 200 and resp.json()["nombre"] == "LAB QMC"

    assert client.delete(f"/api/ambientes/{aid}", headers=auth).status_code == 204


def test_ambiente_duplicado_409(client, auth):
    client.post("/api/ambientes", json={"nombre": "INA015"}, headers=auth)
    assert client.post("/api/ambientes", json={"nombre": "ina015"}, headers=auth).status_code == 409


# ============================================================
# BORRADO PROTEGIDO (integridad referencial)
# ============================================================
def test_borrado_protegido_por_horario(client, auth):
    """Docente/materia/ambiente usados por un horario no se pueden borrar (409)."""
    did = client.post("/api/docentes", json={"nombre": "Ref Docente"}, headers=auth).json()["id"]
    mid = client.post(
        "/api/materias",
        json={"sigla": "REF1", "nombre": "Ref Materia", "carrera": "ING."},
        headers=auth,
    ).json()["id"]
    aid = client.post("/api/ambientes", json={"nombre": "REF-AMB"}, headers=auth).json()["id"]

    # Simula un horario que referencia las tres entidades (lo hará otro módulo).
    with get_db() as conn:
        conn.execute(
            "INSERT INTO horarios_semestre "
            "(materia_id, docente_id, ambiente_id, grupo_designado) "
            "VALUES (?, ?, ?, 'G1')",
            (mid, did, aid),
        )

    assert client.delete(f"/api/docentes/{did}", headers=auth).status_code == 409
    assert client.delete(f"/api/materias/{mid}", headers=auth).status_code == 409
    assert client.delete(f"/api/ambientes/{aid}", headers=auth).status_code == 409
