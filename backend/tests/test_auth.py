"""Pruebas del Módulo 1 — Autenticación (Paso 3 del ciclo SDD)."""

from .conftest import PASSWORD_TEST, USUARIO_TEST


# ============================================================
# /api/auth/login
# ============================================================
def test_login_correcto_devuelve_token(client):
    resp = client.post(
        "/api/auth/login",
        json={"nombre_usuario": USUARIO_TEST, "password": PASSWORD_TEST},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_login_password_incorrecta_devuelve_401(client):
    resp = client.post(
        "/api/auth/login",
        json={"nombre_usuario": USUARIO_TEST, "password": "incorrecta"},
    )
    assert resp.status_code == 401


def test_login_usuario_inexistente_devuelve_401(client):
    resp = client.post(
        "/api/auth/login",
        json={"nombre_usuario": "no_existe", "password": "x"},
    )
    assert resp.status_code == 401


def test_login_payload_invalido_devuelve_422(client):
    # Falta el campo password → error de validación de Pydantic.
    resp = client.post("/api/auth/login", json={"nombre_usuario": "x"})
    assert resp.status_code == 422


# ============================================================
# /api/auth/me
# ============================================================
def test_me_con_token_valido(client, token):
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre_usuario"] == USUARIO_TEST
    assert data["rol"] == "administrador"
    assert "password_hash" not in data  # no se filtran datos sensibles


def test_me_sin_token_devuelve_401(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_con_token_invalido_devuelve_401(client):
    resp = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer token.falso.123"}
    )
    assert resp.status_code == 401


# ============================================================
# /api/auth/logout
# ============================================================
def test_logout_responde_ok(client):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
