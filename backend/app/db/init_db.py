"""Inicializa la base de datos SQLite a partir de `schema.sql`.

Lee el esquema (fuente de verdad en la raíz del proyecto) y lo ejecuta
sobre `data/laboratorio.db`. Es idempotente: el esquema usa
`CREATE TABLE IF NOT EXISTS`, por lo que se puede ejecutar varias veces
sin destruir datos.

Uso:
    python -m backend.app.db.init_db
"""

import sqlite3

from ..config import DATA_DIR, DB_PATH, SCHEMA_PATH


def init_db() -> None:
    """Crea la carpeta de datos y aplica el esquema sobre la BD SQLite."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"No se encontró el esquema: {SCHEMA_PATH}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)
        conn.commit()

        # Verificación: listar las tablas creadas.
        tablas = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name;"
        ).fetchall()
    finally:
        conn.close()

    print(f"[OK] Base de datos lista en: {DB_PATH}")
    print(f"[OK] {len(tablas)} tablas creadas:")
    for (nombre,) in tablas:
        print(f"     - {nombre}")


if __name__ == "__main__":
    init_db()
