"""Capa de acceso a la base de datos SQLite.

Provee un helper de conexión con la configuración correcta:
- PRAGMA foreign_keys = ON (las FK no se aplican por defecto en SQLite).
- row_factory = sqlite3.Row para acceder a columnas por nombre.

La lógica de negocio de cada módulo se construirá sobre estos helpers
durante el ciclo SDD; aquí solo vive la infraestructura de conexión.
"""

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Abre una conexión a la BD con FK activadas y filas por nombre."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """Context manager: commit al salir bien, rollback ante excepción."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
