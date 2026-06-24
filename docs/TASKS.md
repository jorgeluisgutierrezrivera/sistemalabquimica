# Tablero de Tareas — Sistema de Control de Insumos (UAJMS)

> Seguimiento global del avance por módulo bajo metodología **SDD** (4 pasos:
> Propuesta → Código → Pruebas → Git). Se actualiza al cerrar cada paso.
> Convenciones: ☐ pendiente · ▶ en curso · ✅ hecho · ⏸ en pausa.

_Última actualización: 2026-06-24_

---

## Estado general de módulos

| # | Módulo | Paso 1 (Spec) | Paso 2 (Code) | Paso 3 (Test) | Paso 4 (Git) | Estado |
|---|--------|:---:|:---:|:---:|:---:|--------|
| 0 | Entorno + BD (bootstrap) | — | ✅ | ✅ | ✅ | ✅ Versionado |
| 1 | **Autenticación** | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 2 | Inventario Materiales + catálogo Reactivos | ☐ | ☐ | ☐ | ☐ | Pendiente |
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

## Tareas activas (Módulo 1 — Autenticación)

- [x] Definir esquema `usuarios` y aplicarlo a `schema.sql`
- [x] `security.py` (pbkdf2 + JWT)
- [x] Servicio, modelos, router y dependencia de auth
- [x] Frontend: login + guarda de sesión
- [x] Script seed `crear_admin.py`
- [x] Prueba de humo interna
- [x] **Paso 3:** suite `test_auth.py` con pytest — 8/8 OK
- [x] **Paso 4:** repo en GitHub (`origin/main`), commits `ab3cabf` + `195a23e`

> **Módulo 1 CERRADO (2026-06-24).** Siguiente: Módulo 2 — empezar por su
> `docs/modulos/02-*.md` (Paso 1).

---

## Backlog / decisiones a revisar más adelante

- [ ] Gestión de usuarios y roles adicionales (hoy solo `administrador`).
- [ ] Estrategia de caché del Service Worker (offline real en LAN).
- [ ] Generación de QR físicos que apunten a la IP local.
