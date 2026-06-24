"""Configuración de pruebas (pytest).

Aísla las pruebas en una base de datos temporal vía la variable de entorno
INSUMOS_DB_PATH, que se fija ANTES de importar la aplicación. Así los tests
nunca tocan `data/laboratorio.db`.
"""

import os
import sys
import tempfile
from pathlib import Path

# 1) Raíz del proyecto al path (para importar el paquete `backend`).
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))

# 2) BD temporal ANTES de importar config/app.
_TMP_DIR = tempfile.mkdtemp(prefix="insumos_test_")
os.environ["INSUMOS_DB_PATH"] = str(Path(_TMP_DIR) / "test.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.app.db.init_db import init_db  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.services import usuarios_service  # noqa: E402

# Credenciales del usuario de prueba.
USUARIO_TEST = "admin_test"
PASSWORD_TEST = "Clave123"


@pytest.fixture(scope="session", autouse=True)
def _preparar_bd():
    """Crea el esquema y un usuario admin en la BD temporal."""
    init_db()
    if usuarios_service.obtener_por_usuario(USUARIO_TEST) is None:
        usuarios_service.crear_usuario(USUARIO_TEST, PASSWORD_TEST, "Admin Test")
    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def token(client: TestClient) -> str:
    """Devuelve un token válido para el usuario de prueba."""
    resp = client.post(
        "/api/auth/login",
        json={"nombre_usuario": USUARIO_TEST, "password": PASSWORD_TEST},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]
