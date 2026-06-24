"""Crea (o reinicia) el usuario administrador inicial de forma interactiva.

No deja credenciales escritas en el código: pide usuario y contraseña por
consola. Ejecutar desde la raíz del proyecto, con el venv activo:

    python scripts/crear_admin.py
"""

import getpass
import sys
from pathlib import Path

# Permite ejecutar el script directamente añadiendo la raíz al path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.db.init_db import init_db  # noqa: E402
from backend.app.services import usuarios_service  # noqa: E402


def main() -> None:
    print("=== Crear usuario administrador ===")

    # Garantiza que la BD y la tabla existan.
    init_db()
    print()

    nombre_usuario = input("Usuario: ").strip()
    if not nombre_usuario:
        print("[ERROR] El usuario no puede estar vacío.")
        sys.exit(1)

    nombre_completo = input("Nombre completo (opcional): ").strip() or None

    password = getpass.getpass("Contraseña: ")
    if len(password) < 4:
        print("[ERROR] La contraseña debe tener al menos 4 caracteres.")
        sys.exit(1)
    if password != getpass.getpass("Repetir contraseña: "):
        print("[ERROR] Las contraseñas no coinciden.")
        sys.exit(1)

    try:
        nuevo_id = usuarios_service.crear_usuario(
            nombre_usuario=nombre_usuario,
            password=password,
            nombre_completo=nombre_completo,
            rol="administrador",
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    print(f"\n[OK] Administrador '{nombre_usuario}' creado (id={nuevo_id}).")


if __name__ == "__main__":
    main()
