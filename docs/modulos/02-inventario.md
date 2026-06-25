# Módulo 2 — Inventario Maestro de Materiales + Catálogo de Reactivos

> Plan de trabajo (metodología SDD). Este documento es el **Paso 1 (Propuesta)**.
> No se escribe código hasta recibir `[APROBADO]`.

- **Estado:** ✅ Completo (4 pasos SDD cerrados)
- **Fecha inicio:** 2026-06-25
- **Fecha cierre:** 2026-06-25
- **Depende de:** Módulo 1 (Autenticación) — los endpoints se protegen con
  `get_current_user`. Tablas `materiales` y `reactivos` ya existen en `schema.sql`.

---

## 1. Objetivo
Gestionar los dos **catálogos maestros de insumos** del laboratorio, que son la
base sobre la que luego se arman recetas y carritos:

- **Materiales** (retornables / activos fijos): CRUD con **inventario** real
  (`cantidad_total`, `cantidad_en_uso`). Aquí vive el patrimonio del laboratorio.
- **Reactivos** (consumibles): CRUD de **catálogo puro**, *sin stock*
  (codigo, nombre, unidad_base). El reactivo es solo una etiqueta reutilizable
  para recetas/carritos (Regla 2.B). Ver [[decisiones-esquema-bd]].

## 2. Alcance
**Incluye:**
- CRUD de **Reactivos** (catálogo): crear, listar (con búsqueda), obtener,
  editar, eliminar.
- CRUD de **Materiales** (catálogo + inventario): crear, listar (con búsqueda),
  obtener, editar, eliminar.
- En materiales, gestión de `cantidad_total` (patrimonio). `cantidad_en_uso`
  es **solo lectura** desde este módulo (lo moverán los carritos en el Módulo 5).
- Campo derivado **`cantidad_disponible`** = `cantidad_total − cantidad_en_uso`
  expuesto en las respuestas (no se almacena).
- Validaciones de negocio (ver §7) y protección de todos los endpoints con sesión.
- Pantallas PWA mobile-first para administrar ambos catálogos.

**NO incluye (se difiere):**
- Movimientos de inventario / Kardex (`movimientos_inventario`) → Módulos 5–7
  (carrito y cierre). Aquí `cantidad_en_uso` no se toca salvo en validaciones.
- Recetas y carritos (Módulos 4–5).
- Importación masiva (CSV/Excel) del inventario inicial → backlog.

## 3. Tablas del esquema usadas
- `reactivos` (id, codigo, nombre, unidad_base) — **sin cambios de esquema.**
- `materiales` (id, codigo, nombre, capacidad, cantidad_total, cantidad_en_uso)
  — **sin cambios de esquema.**

> No se requiere modificar `schema.sql`. Si durante el desarrollo surge una
> necesidad de cambio, se aprueba antes (convención SDD).

## 4. Archivos a crear / modificar
| Archivo | Rol |
|---|---|
| `backend/app/models/inventario.py` | Modelos Pydantic: `ReactivoIn/Out`, `MaterialIn/Out` (con `cantidad_disponible`) |
| `backend/app/services/reactivos_service.py` | Acceso a datos de reactivos (CRUD) |
| `backend/app/services/materiales_service.py` | Acceso a datos de materiales (CRUD + cálculo disponible) |
| `backend/app/routers/inventario.py` | Endpoints `/api/reactivos` y `/api/materiales` |
| `backend/app/main.py` *(mod)* | Registrar el nuevo router |
| `frontend/inventario.html` | Pantalla de administración (pestañas Materiales / Reactivos) |
| `frontend/js/inventario.js` | Lógica de la pantalla (fetch con token, alta/edición/borrado) |
| `frontend/index.html`, `js/app.js` *(mod)* | Enlace de navegación al inventario |
| `backend/tests/test_inventario.py` | Suite pytest del módulo (Paso 3) |

> Decisión de empaquetado: reactivos y materiales comparten **un solo router**
> (`inventario.py`) y **una sola pantalla** con pestañas, por ser dominios
> gemelos y reducir archivos. Servicios separados para mantener la lógica clara.

## 5. Endpoints / API
Todos exigen token válido (`Depends(get_current_user)`). Prefijo `/api`.

### Reactivos (catálogo, sin stock)
| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| GET | `/api/reactivos` | Listar; `?q=` filtra por nombre/código | 401 |
| POST | `/api/reactivos` | Crear reactivo | 401, 422 (nombre vacío), 409 (duplicado) |
| GET | `/api/reactivos/{id}` | Obtener uno | 401, 404 |
| PUT | `/api/reactivos/{id}` | Editar | 401, 404, 409 |
| DELETE | `/api/reactivos/{id}` | Eliminar | 401, 404, 409 (en uso por receta/carrito) |

### Materiales (catálogo + inventario)
| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| GET | `/api/materiales` | Listar; `?q=` filtra por nombre/código | 401 |
| POST | `/api/materiales` | Crear material (`cantidad_total` ≥ 0; `en_uso` inicia en 0) | 401, 422, 409 |
| GET | `/api/materiales/{id}` | Obtener uno (incluye `cantidad_disponible`) | 401, 404 |
| PUT | `/api/materiales/{id}` | Editar datos y `cantidad_total` | 401, 404, 409, 422 |
| DELETE | `/api/materiales/{id}` | Eliminar | 401, 404, 409 (en uso) |

## 6. Interfaz (PWA)
- `inventario.html` protegida con `Auth.requireAuth()`; barra superior común.
- **Dos pestañas**: «Materiales» y «Reactivos» (mobile-first, una columna).
- **Materiales:** tabla/tarjetas con nombre, capacidad, total, en uso, disponible.
  Botón «+ Nuevo», editar y borrar en línea. El campo *en uso* se muestra como
  solo lectura. Disponible resaltado si llega a 0.
- **Reactivos:** lista simple (código, nombre, unidad). Alta/edición/borrado.
- Buscador por nombre/código en cada pestaña (usa `?q=`).
- Mensajes de error claros para 409 (duplicado / en uso).

## 7. Decisiones de diseño
- **`cantidad_en_uso` inmutable aquí:** solo lo moverá la lógica de carritos.
  Crear material lo fija en 0; editar nunca lo cambia desde este módulo.
- **No bajar `cantidad_total` por debajo de `cantidad_en_uso`:** al editar, si
  el nuevo total < en_uso → **409** (rompería la conciliación). Coherente con
  «materiales exigen conciliación entregado vs devuelto».
- **`cantidad_disponible` calculado, no almacenado:** evita un tercer campo que
  pueda desincronizarse; se computa en el servicio/modelo de salida.
- **Borrado protegido (integridad referencial):** no permitir DELETE si el
  insumo está referenciado por recetas o carritos (consulta previa → 409),
  evitando huérfanos pese a que el FK no tenga `ON DELETE` restrictivo aquí.
  Para materiales, además bloquear si `cantidad_en_uso > 0`.
- **Duplicados:** material y reactivo se consideran duplicados por
  (nombre + capacidad) y (nombre + unidad_base/código) respectivamente; el
  esquema no tiene UNIQUE en estas tablas, así que la validación es a nivel de
  servicio (case-insensitive) → 409. *(A confirmar: ¿quieres UNIQUE en BD?)*
- **Reutiliza el patrón del Módulo 1:** `get_db()` context manager, servicios
  con `sqlite3.Row`, modelos Pydantic, router con prefijo. Sin dependencias nuevas.

## 8. Plan de pruebas (Paso 3)
Suite pytest sobre BD temporal aislada (`INSUMOS_DB_PATH`), patrón de `test_auth.py`,
todas las llamadas con token válido (y un par sin token → 401):
1. **Reactivos:** crear → listar → buscar `?q=` → obtener → editar → duplicado (409)
   → borrar → 404 tras borrar.
2. **Materiales:** crear (en_uso=0) → `cantidad_disponible` correcto → editar total
   → bajar total < en_uso (409) → borrar con en_uso>0 (409) → borrar OK.
3. **Auth:** cualquier endpoint sin token → 401.
4. **Validación:** nombre vacío / total negativo → 422.

Comando: `.\.venv\Scripts\python.exe -m pytest backend/tests -v`

---

## Estado SDD
- [x] **Paso 1 — Propuesta (Spec):** aprobada el 2026-06-25 (`APROBADO`)
- [x] **Paso 2 — Código:** entregado el 2026-06-25 (backend + frontend)
- [x] **Paso 3 — Pruebas:** `test_inventario.py` — **13/13 OK** (suite total 21/21) el 2026-06-25
- [x] **Paso 4 — Git:** commit `ba5772e` (push a `origin/main`) el 2026-06-25

### Resultado de pruebas (Paso 3)
13 casos sobre BD temporal aislada (reusa `conftest.py`): auth (401 sin token),
CRUD de reactivos + búsqueda + duplicado (409) + 422 + 404, CRUD de materiales
con `cantidad_disponible`, `cantidad_en_uso` simulado, total<en_uso (409),
borrado con en_uso (409), duplicado por nombre+capacidad (409), mismo nombre con
distinta capacidad (OK) y total negativo (422). **Suite completa: 21 passed.**
Ejecutar: `.\.venv\Scripts\python.exe -m pytest backend/tests -v`

## Notas / lecciones
- Recordatorios de entorno (ver `docs/LESSONS.md`): usar `.\.venv\Scripts\python.exe`
  (L-001), heredoc/archivo para Python multilínea en PowerShell (L-002),
  regenerar BD ante cambios de esquema (L-003).
- **Puntos a confirmar antes del Paso 2:** (a) ¿añadir restricción UNIQUE en BD
  para materiales/reactivos o validar solo en servicio?; (b) ¿el orden de
  pestañas y campos visibles es el adecuado para la operación móvil?
