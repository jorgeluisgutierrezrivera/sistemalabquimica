# Sistema de Control de Insumos — Laboratorio de Química (UAJMS)

Sistema local (LAN) para digitalizar la logística de reactivos y materiales del
Laboratorio de Química mediante el concepto del **"Carrito de Insumos"**.

- **Backend:** Python + FastAPI
- **Base de datos:** SQLite (`schema.sql` es la **fuente de verdad**, no se rediseña)
- **Frontend:** PWA Mobile-First (HTML/CSS/JS)
- **Empaquetado:** PyInstaller (.exe autocontenido)

> Metodología: **Spec-Driven Development (SDD)**. Se desarrolla módulo por
> módulo siguiendo el ciclo de 4 pasos del `PROMPT MAESTRO.md`. No se avanza de
> paso sin la aprobación explícita (`[APROBADO]`).

## Estructura del proyecto

```
SISTEMA LABORATORIO DE QUÍMICA/
├── backend/
│   ├── app/
│   │   ├── main.py            # Arranque FastAPI (bootstrap; sin lógica de negocio aún)
│   │   ├── config.py          # Rutas y configuración central
│   │   ├── database.py        # Helper de conexión SQLite (FK ON, row_factory)
│   │   ├── db/init_db.py      # Crea la BD desde schema.sql
│   │   ├── routers/           # Endpoints por módulo (se llena en el SDD)
│   │   ├── services/          # Lógica de negocio (se llena en el SDD)
│   │   └── models/            # Esquemas Pydantic (se llena en el SDD)
│   └── tests/                 # Pruebas (Paso 3 del SDD)
├── frontend/                  # PWA estática (index.html, manifest, SW, css, js)
├── data/                      # laboratorio.db (generada, NO versionada)
├── scripts/                   # Utilidades (seeds, backups, QR, build)
├── schema.sql                 # Esquema SQLite (fuente de verdad)
├── requirements.txt
└── README.md
```

## Puesta en marcha (entorno de desarrollo)

```powershell
# 1. Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear / actualizar la base de datos desde el esquema
python -m backend.app.db.init_db

# 4. Levantar el servidor de desarrollo
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API de salud: `http://localhost:8000/api/health`
- Documentación automática (FastAPI): `http://localhost:8000/docs`

## Documentos de referencia

- `ESPECIFICACION TECNICA DEL SISTEMA.md` — reglas de negocio (fuente de verdad).
- `PROMPT MAESTRO.md` — rol, stack y metodología SDD.
- `schema.sql` — modelo relacional SQLite.
