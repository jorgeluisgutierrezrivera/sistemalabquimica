# Tablero de Tareas — Sistema de Control de Insumos (UAJMS)

> Seguimiento global del avance por módulo bajo metodología **SDD** (4 pasos:
> Propuesta → Código → Pruebas → Git). Se actualiza al cerrar cada paso.
> Convenciones: ☐ pendiente · ▶ en curso · ✅ hecho · ⏸ en pausa.

_Última actualización: 2026-06-25_

---

## Estado general de módulos

| # | Módulo | Paso 1 (Spec) | Paso 2 (Code) | Paso 3 (Test) | Paso 4 (Git) | Estado |
|---|--------|:---:|:---:|:---:|:---:|--------|
| 0 | Entorno + BD (bootstrap) | — | ✅ | ✅ | ✅ | ✅ Versionado |
| 1 | **Autenticación** | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 2 | Inventario Materiales + catálogo Reactivos | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 3 | Catálogos Base (docentes/materias/ambientes) | ☐ | ☐ | ☐ | ☐ | Pendiente |
| 4 | Recetas Maestras | ☐ | ☐ | ☐ | ☐ | Pendiente |
| 5 | Carrito (armado desde receta) | ☐ | ☐ | ☐ | ☐ | Pendiente |
| 6 | Estados y dashboard | ☐ | ☐ | ☐ | ☐ | Pendiente |
| 7 | Cierre y conciliación | ☐ | ☐ | ☐ | ☐ | Pendiente |
| 8 | PWA / offline / QR | ☐ | ☐ | ☐ | ☐ | Pendiente |
| 9 | Empaquetado PyInstaller | ☐ | ☐ | ☐ | ☐ | Pendiente |

> Nota: el orden 2/3 puede intercambiarse; ambos son catálogos base sin
> dependencias entre sí. Detalle de cada módulo en `docs/modulos/`.

---

## Tareas activas (Módulo 2 — Inventario)

- [x] **Paso 1:** propuesta en `docs/modulos/02-inventario.md` + `[APROBADO]`
- [x] **Paso 2:** modelos + servicios (reactivos/materiales) + router + `main.py`
- [x] **Paso 2:** frontend `inventario.html` + `js/inventario.js` + estilos + navegación
- [x] **Paso 3:** suite `test_inventario.py` — 13/13 OK (total 21/21)
- [x] **Paso 4:** commit `ba5772e` + push a `origin/main`

> **Módulo 2 CERRADO (2026-06-25).** Siguiente: Módulo 3 — Catálogos Base
> (docentes/materias/ambientes); empezar por su `docs/modulos/03-*.md` (Paso 1).

---

## Historial — Módulo 1 (Autenticación) ✅ CERRADO 2026-06-24

- [x] Esquema `usuarios`, `security.py` (pbkdf2+JWT), servicios/modelos/router
- [x] Frontend login + seed `crear_admin.py` + suite `test_auth.py` (8/8 OK)
- [x] Repo en GitHub (`origin/main`), commits `ab3cabf` + `195a23e`

---

## Backlog / decisiones a revisar más adelante

- [ ] Gestión de usuarios y roles adicionales (hoy solo `administrador`).
- [ ] Estrategia de caché del Service Worker (offline real en LAN).
- [ ] Generación de QR físicos que apunten a la IP local.
