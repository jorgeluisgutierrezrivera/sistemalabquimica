"""Configuración central y rutas del proyecto.

Centraliza las rutas absolutas para que el código no dependa del
directorio desde donde se ejecute (importante al empaquetar con PyInstaller).
"""

import os
from pathlib import Path

# Raíz del proyecto: .../SISTEMA LABORATORIO DE QUÍMICA
# config.py está en backend/app/, por eso subimos 3 niveles.
BASE_DIR = Path(__file__).resolve().parents[2]

# Esquema SQL (fuente de verdad — NO se rediseña, ver PROMPT MAESTRO).
SCHEMA_PATH = BASE_DIR / "schema.sql"

# Carpeta y archivo de la base de datos SQLite.
# DB_PATH puede sobrescribirse con la variable de entorno INSUMOS_DB_PATH
# (útil para pruebas con BD aislada y para configurar la ubicación al empaquetar).
DATA_DIR = BASE_DIR / "data"
DB_PATH = (
    Path(os.environ["INSUMOS_DB_PATH"])
    if os.environ.get("INSUMOS_DB_PATH")
    else DATA_DIR / "laboratorio.db"
)

# Carpeta del frontend (PWA estática).
FRONTEND_DIR = BASE_DIR / "frontend"

# --- Servidor LAN ---
# Host 0.0.0.0 para ser accesible desde la red local (móvil vía QR).
HOST = "0.0.0.0"
PORT = 8000
