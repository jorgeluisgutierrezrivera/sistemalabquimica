"""Punto de entrada de la aplicación FastAPI (bootstrap del entorno).

NOTA (SDD): Este archivo es solo el arranque mínimo del servidor para
validar que el entorno funciona. La lógica de cada módulo de negocio
(inventario, recetas, carritos, dashboard...) se incorporará módulo por
módulo siguiendo el ciclo SDD del PROMPT MAESTRO. No agregar aquí
endpoints de negocio sin pasar por el Paso 1 (Propuesta) y "[APROBADO]".

Ejecutar en desarrollo:
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import FRONTEND_DIR
from .routers import auth, carritos, catalogos, inventario, recetas

app = FastAPI(
    title="Sistema de Control de Insumos - Laboratorio de Química (UAJMS)",
    description="API local (LAN) para la gestión de reactivos y materiales "
    "mediante el concepto de 'Carrito de Insumos'.",
    version=__version__,
)


@app.get("/api/health", tags=["sistema"])
def health() -> JSONResponse:
    """Verifica que la API está viva (usado para validar el entorno)."""
    return JSONResponse({"status": "ok", "version": __version__})


# --- Routers de la API (se irán sumando módulo por módulo en el SDD) ---
app.include_router(auth.router)
app.include_router(inventario.router)  # Módulo 2 — Inventario
app.include_router(catalogos.router)  # Módulo 3 — Catálogos Base
app.include_router(recetas.router)  # Módulo 4 — Recetas Maestras
app.include_router(carritos.router)  # Módulo 5 — Carrito de Insumos

# --- Frontend (PWA estática) ---
# Se monta al final, en la raíz: las rutas /api/* tienen prioridad y el resto
# resuelve archivos del frontend (html=True sirve index.html por defecto).
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
