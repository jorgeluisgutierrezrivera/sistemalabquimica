# Tablero de Tareas — Sistema de Control de Insumos (UAJMS)

> Seguimiento global del avance por módulo bajo metodología **SDD** (4 pasos:
> Propuesta → Código → Pruebas → Git). Se actualiza al cerrar cada paso.
> Convenciones: ☐ pendiente · ▶ en curso · ✅ hecho · ⏸ en pausa.

_Última actualización: 2026-06-26_

---

## Estado general de módulos

| # | Módulo | Paso 1 (Spec) | Paso 2 (Code) | Paso 3 (Test) | Paso 4 (Git) | Estado |
|---|--------|:---:|:---:|:---:|:---:|--------|
| 0 | Entorno + BD (bootstrap) | — | ✅ | ✅ | ✅ | ✅ Versionado |
| 1 | **Autenticación** | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 2 | Inventario Materiales + catálogo Reactivos | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 3 | Catálogos Base (docentes/materias/ambientes) | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 4 | Recetas Maestras | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 5 | Carrito (armado desde receta) | ▶ | ☐ | ☐ | ☐ | ▶ En curso (Paso 1) |
| 6 | Estados y dashboard | ☐ | ☐ | ☐ | ☐ | Pendiente |
| 7 | Cierre y conciliación | ☐ | ☐ | ☐ | ☐ | Pendiente |
| 8 | PWA / offline / QR | ☐ | ☐ | ☐ | ☐ | Pendiente |
| 9 | Empaquetado PyInstaller | ☐ | ☐ | ☐ | ☐ | Pendiente |

> Nota: el orden 2/3 puede intercambiarse; ambos son catálogos base sin
> dependencias entre sí. Detalle de cada módulo en `docs/modulos/`.

---

## Tareas activas (Módulo 5 — Carrito armado desde receta)

- [x] **Paso 1:** propuesta en `docs/modulos/05-carrito.md` + `[APROBADO]` (3 decisiones recomendadas)
- [x] **Paso 2:** backend (copia de líneas de receta a detalle editable, extras)
- [x] **Paso 2:** frontend `carritos.html` + `js/carritos.js` + navegación
- [x] **Paso 3:** suite `test_carrito.py` — 11/11 OK (total 56/56)
- [ ] **Paso 4:** *(verificado: servidor + datos ficticios)* commit + push  ← *aquí estamos*

> **Módulo 4 CERRADO (2026-06-26).** Módulo 5 (Carrito) con Pasos 1–3 cerrados y
> verificado funcionalmente; pendiente el commit/push (Paso 4).
> Decisiones: inventario diferido a M6, `cantidad_grupos` numérico sin cambio de
> esquema, armado desde receta + extras.

---

## Historial — Módulo 4 (Recetas Maestras) ✅ CERRADO 2026-06-26

- [x] Modelos + servicio (CRUD + reemplazo de detalles en transacción) + router
- [x] Frontend `recetas.html` + `js/recetas.js` (lista + editor con 2 tablas)
- [x] Suite `test_recetas.py` — 10/10 OK (total 45/45)
- [x] Commit `60decb3` (feat) + cierre docs, push a `origin/main`

---

## Historial — Módulo 3 (Catálogos Base) ✅ CERRADO 2026-06-25

- [x] Modelos + servicios (docentes/materias/ambientes) + router + `main.py`
- [x] Frontend `catalogos.html` + `js/catalogos.js` con 3 pestañas
- [x] Suite `test_catalogos.py` — 14/14 OK (total 35/35)
- [x] Commit `92486a9` + cierre docs `b488b51`, push a `origin/main`

---

## Historial — Módulo 2 (Inventario) ✅ CERRADO 2026-06-25

- [x] Modelos + servicios (reactivos sin stock / materiales con inventario) + router
- [x] Frontend `inventario.html` + `js/inventario.js` con pestañas y modal
- [x] Suite `test_inventario.py` — 13/13 OK (total 21/21)
- [x] Commit `ba5772e` + cierre docs `756e8e4`, push a `origin/main`

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
