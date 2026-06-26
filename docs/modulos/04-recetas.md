# Módulo 4 — Recetas Maestras (Plantillas Reutilizables)

> Plan de trabajo (metodología SDD). Este documento es el **Paso 1 (Propuesta)**.
> No se escribe código hasta recibir `[APROBADO]`.

- **Estado:** ✅ Cerrado
- **Fecha inicio:** 2026-06-25
- **Fecha cierre:** 2026-06-26
- **Depende de:** Módulo 1 (Auth), Módulo 2 (catálogos reactivos/materiales),
  Módulo 3 (catálogo materias). Tablas `recetas`,
  `receta_detalle_reactivos`, `receta_detalle_materiales` ya existen.

---

## 1. Objetivo
Gestionar **plantillas reutilizables** de prácticas de laboratorio. Una receta
define, para una **materia + práctica**, qué reactivos y materiales se necesitan
**por grupo**. Es la base desde la que el Módulo 5 armará un carrito copiando sus
líneas a un detalle editable (Regla: el carrito se arma desde una Receta
Maestra). Ver [[proyecto-sistema-insumos]] y [[decisiones-esquema-bd]].

## 2. Alcance
**Incluye:**
- CRUD de **recetas** (cabecera): materia, nombre de práctica, descripción,
  activa/inactiva. Único por (materia + nombre_practica).
- Gestión de las **líneas de detalle** de cada receta:
  - Reactivos: reactivo del catálogo + `concentracion_unidad` + `cantidad_por_grupo`.
  - Materiales: material del catálogo + `cantidad_por_grupo` + `observaciones`.
- Lectura de una receta **con sus detalles anidados** (para mostrarla/editarla).
- Validaciones: FKs válidas (materia/reactivo/material existen), duplicados (409),
  borrado y `activa` (ver §7). Todo protegido con sesión.
- Pantalla PWA: lista de recetas + editor de receta con sus dos tablas de líneas.

**NO incluye (se difiere):**
- Armado del carrito desde la receta (copia de líneas) → **Módulo 5**.
- Cálculo de `cantidad_total` por nº de grupos (eso ocurre en el carrito).
- `horarios_semestre` (sigue diferido).

## 3. Tablas del esquema usadas
- `recetas (id, materia_id FK, nombre_practica, descripcion, activa,
  UNIQUE(materia_id, nombre_practica))` — sin cambios de esquema.
- `receta_detalle_reactivos (id, receta_id FK ON DELETE CASCADE, reactivo_id FK,
  concentracion_unidad, cantidad_por_grupo REAL)` — sin cambios.
- `receta_detalle_materiales (id, receta_id FK ON DELETE CASCADE, material_id FK,
  cantidad_por_grupo INTEGER, observaciones)` — sin cambios.

> El `ON DELETE CASCADE` de los detalles permite borrar la receta y sus líneas
> en una sola operación. No se requiere modificar `schema.sql`.

## 4. Archivos a crear / modificar
| Archivo | Rol |
|---|---|
| `backend/app/models/recetas.py` | Modelos: `RecetaIn/Out`, `DetalleReactivoIn/Out`, `DetalleMaterialIn/Out` (anidados) |
| `backend/app/services/recetas_service.py` | CRUD de receta + reemplazo de detalles en transacción |
| `backend/app/routers/recetas.py` | Endpoints `/api/recetas` |
| `backend/app/main.py` *(mod)* | Registrar el router |
| `frontend/recetas.html` | Lista de recetas + editor (cabecera + 2 tablas de líneas) |
| `frontend/js/recetas.js` | Lógica del editor (selección de materia/insumos, alta de líneas) |
| `frontend/index.html` *(mod)* | Enlace de navegación a Recetas |
| `backend/tests/test_recetas.py` | Suite pytest del módulo (Paso 3) |

## 5. Endpoints / API
Todos exigen token válido (router con dependencia global). Prefijo `/api`.

**Enfoque recomendado: receta como agregado anidado.** La receta se crea/edita
en **una sola** operación que incluye sus líneas (la UI la maneja como un todo);
el servidor **reemplaza** el conjunto de detalles en una transacción. Ver §7.

| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| GET | `/api/recetas` | Listar recetas (cabecera); `?q=` por práctica, `?materia_id=`, `?activa=` | 401 |
| POST | `/api/recetas` | Crear receta **con** sus líneas | 401, 422, 409 (duplicada), 400 (FK inexistente) |
| GET | `/api/recetas/{id}` | Obtener receta **con detalles anidados** | 401, 404 |
| PUT | `/api/recetas/{id}` | Editar cabecera y **reemplazar** líneas | 401, 404, 409, 400 |
| DELETE | `/api/recetas/{id}` | Eliminar receta (+ líneas en cascada) | 401, 404, 409 (usada por carrito) |

Forma del cuerpo (POST/PUT):
```json
{
  "materia_id": 1,
  "nombre_practica": "Complexometría #6",
  "descripcion": "…",
  "activa": true,
  "reactivos": [
    {"reactivo_id": 3, "concentracion_unidad": "0,01M / mL", "cantidad_por_grupo": 50}
  ],
  "materiales": [
    {"material_id": 7, "cantidad_por_grupo": 2, "observaciones": "grandes"}
  ]
}
```

## 6. Interfaz (PWA)
- `recetas.html` protegida; lista de recetas (materia · práctica · activa) con
  buscador y botón «+ Nueva».
- **Editor de receta:** cabecera (selección de materia desde catálogo, nombre de
  práctica, descripción, activa) + dos secciones de líneas (Reactivos y
  Materiales). Cada línea: selector de insumo del catálogo + campos numéricos;
  botón para añadir/quitar filas.
- Mobile-first; mensajes claros para 409/400.

## 7. Decisiones de diseño
- **Receta como agregado (recomendado):** un POST/PUT maneja cabecera + líneas;
  el servidor borra y reinserta los detalles dentro de una transacción
  (`get_db()` ya hace commit/rollback). Más simple para la UI y evita estados
  intermedios inconsistentes. *(Alternativa: endpoints separados por línea
  `/api/recetas/{id}/reactivos`… — más verboso; a confirmar contigo.)*
- **Validación de FKs:** antes de insertar, verificar que `materia_id`,
  `reactivo_id` y `material_id` existen → 400 con mensaje claro (en vez de
  IntegrityError). Reusa los services de M2/M3 para comprobar existencia.
- **Duplicados:** (materia + nombre_practica) ya es UNIQUE en BD; validar en
  servicio para devolver 409 legible.
- **Borrado protegido:** no permitir DELETE si la receta está referenciada por
  `carritos_cabecera.receta_id` (→ 409); las líneas sí caen en cascada.
- **`activa`:** baja lógica para no perder histórico; las recetas inactivas no
  se ofrecerán al armar carritos (lo usará M5). Filtro `?activa=`.
- **Copia histórica:** este módulo NO copia nombres al carrito; eso es del M5
  (que guardará `nombre_reactivo`/`nombre_material` como snapshot).

## 8. Plan de pruebas (Paso 3)
Suite pytest sobre BD temporal aislada (reusa `conftest.py`); crea materia +
reactivo + material de apoyo y luego:
1. **Crear** receta con líneas → 201; **GET** devuelve detalles anidados correctos.
2. **Listar** + filtros `?q=`, `?materia_id=`, `?activa=`.
3. **Editar** (PUT): cambiar cabecera y **reemplazar** líneas; verificar que las
   viejas se eliminaron y quedan solo las nuevas.
4. **Duplicada** (misma materia+práctica) → 409.
5. **FK inexistente** (reactivo/material/materia que no existe) → 400.
6. **Validación** (nombre vacío, cantidad ≤ 0) → 422.
7. **Borrado:** OK normal; **409** si un carrito la referencia (insertar carrito
   de apoyo); verificar cascada de líneas al borrar.
8. **Auth:** endpoints sin token → 401.

Comando: `.\.venv\Scripts\python.exe -m pytest backend/tests -v`

---

## Estado SDD
- [x] **Paso 1 — Propuesta (Spec):** aprobada el 2026-06-25 (`APROBADO`; opción A — agregado anidado)
- [x] **Paso 2 — Código:** entregado el 2026-06-25 (backend + frontend lista/editor)
- [x] **Paso 3 — Pruebas:** `test_recetas.py` — **10/10 OK** (suite total 45/45) el 2026-06-25
- [x] **Paso 4 — Git:** commit `60decb3` (feat) + cierre de docs, push a `origin/main` el 2026-06-26

### Resultado de pruebas (Paso 3)
10 casos sobre BD temporal aislada (reusa `conftest.py`): auth (401), crear +
GET con detalles anidados, listar + filtros (`q`/`materia_id`/`activa`), edición
que **reemplaza** las líneas, duplicada (409), FK inexistente (400), validación
(422), 404, borrado OK con cascada de líneas y **borrado protegido por carrito**
(409). **Suite completa: 45 passed.** Lección nueva: L-005 (BD de pruebas de
sesión → fixtures con nombres únicos).

## Notas / lecciones
- **Punto a confirmar antes del Paso 2:** ¿receta como **agregado anidado**
  (recomendado, un POST/PUT con sus líneas) o **endpoints separados** por línea?
- Recordatorios de entorno (ver `docs/LESSONS.md`): `.\.venv\Scripts\python.exe`
  (L-001), here-string/archivo para Python multilínea (L-002), regenerar BD ante
  cambios de esquema (L-003), búsqueda sensible a acentos en SQLite (L-004).
