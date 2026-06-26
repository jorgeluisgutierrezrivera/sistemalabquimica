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
| 5 | Carrito (armado desde receta) | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 6 | Estados y dashboard | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 7 | Cierre y conciliación | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 8 | PWA / offline / QR | ✅ | ✅ | ✅ | ✅ | ✅ **Cerrado** |
| 9 | Empaquetado PyInstaller | ▶ | ☐ | ☐ | ☐ | ▶ En curso (Paso 1) |

> Nota: el orden 2/3 puede intercambiarse; ambos son catálogos base sin
> dependencias entre sí. Detalle de cada módulo en `docs/modulos/`.

---

## Tareas activas (Módulo 9 — Empaquetado PyInstaller)

- [ ] **Paso 1:** redactar propuesta en `docs/modulos/09-empaquetado.md`
- [ ] **Paso 1:** recibir `[APROBADO]` del usuario  ← *aquí estamos*
- [ ] **Paso 2:** build del `.exe` autocontenido (incluir frontend/, BD, segno) + arranque
- [ ] **Paso 3:** verificación del ejecutable
- [ ] **Paso 4:** *(verificar)* commit + push

> **Módulo 8 CERRADO (2026-06-26).** Último módulo: M9 (empaquetado del `.exe`
> con PyInstaller) para entregar el sistema autocontenido.

> **Módulo 7 CERRADO (2026-06-26).** Con M1–M7 el **ciclo funcional está
> completo**. Siguiente: Módulo 8 (PWA/offline/QR) en Paso 1; luego M9
> (empaquetado PyInstaller).

> **Módulo 6 CERRADO (2026-06-26).** Siguiente: Módulo 7 (Cierre y conciliación)
> en Paso 1. Aquí se cierra el carrito: conciliación entregado-vs-devuelto de
> materiales (retorno de `cantidad_en_uso` + Kardex `retorno`/`merma`), registro
> de mermas (`registro_material_roto`) y transición final a `Cerrado`.

> **Módulo 5 CERRADO (2026-06-26).** Siguiente: Módulo 6 (Estados y dashboard)
> en Paso 1. Aquí entra el movimiento de inventario diferido (materiales a
> 'en uso' + Kardex) al pasar a 'Activo', la máquina de estados
> (Preparacion → Activo → Custodia → Proximo_Cierre) y el tablero por estado.

---

## Historial — Módulo 8 (PWA / Offline / QR) ✅ CERRADO 2026-06-26

- [x] Service Worker con caché de app-shell (cache-first estáticos, network-only API)
- [x] Iconos PWA `icon-192/512.png` en Python puro (`scripts/gen_icons.py`)
- [x] Router público `/api/red` (info + QR `segno`) + tarjeta «Acceso móvil»
- [x] `requirements.txt` + `segno==1.6.1`
- [x] Suite `test_red.py` — 3/3 OK (total 79/79)
- [x] Verificación funcional (IP LAN detectada, QR SVG, iconos sin 404)
- [x] Commit `49c74c0` (feat) + cierre docs, push a `origin/main`

---

## Historial — Módulo 7 (Cierre y Conciliación) ✅ CERRADO 2026-06-26

- [x] `cierre_service` (conciliación + reversión de inventario + mermas) + `models/cierre`
- [x] `POST /api/carritos/{id}/cierre` + `DetalleMaterialOut.cantidad_devuelta`
- [x] Frontend: panel de cierre (devueltas + observaciones) en carritos
- [x] Suite `test_cierre.py` — 8/8 OK (total 76/76)
- [x] Verificación funcional con datos ficticios (cierre con merma + registro_material_roto)
- [x] Commit `2048b65` (feat) + cierre docs, push a `origin/main`

---

## Historial — Módulo 6 (Estados y Dashboard) ✅ CERRADO 2026-06-26

- [x] `estados_service` (transiciones forward-only + inventario en_uso/Kardex) + `dashboard_service`
- [x] `PATCH /api/carritos/{id}/estado` + `GET /api/dashboard`
- [x] Frontend `dashboard.html` + `js/dashboard.js` + botón avanzar estado en carritos
- [x] Suite `test_estados.py` — 12/12 OK (total 68/68)
- [x] Verificación funcional con datos ficticios (transición Activo movió inventario + Kardex)
- [x] Commit `e504d33` (feat) + cierre docs, push a `origin/main`

---

## Historial — Módulo 5 (Carrito de Insumos) ✅ CERRADO 2026-06-26

- [x] Modelos + servicio (armar desde receta + CRUD + reemplazo de líneas) + router
- [x] Frontend `carritos.html` + `js/carritos.js` (lista + editor desde receta)
- [x] Suite `test_carrito.py` — 11/11 OK (total 56/56)
- [x] Verificación funcional con datos ficticios (servidor + carrito demo)
- [x] Commit `44744b6` (feat) + cierre docs, push a `origin/main`

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
