# Módulo 5 — Carrito de Insumos (armado desde una Receta Maestra)

> Plan de trabajo (metodología SDD). Este documento es el **Paso 1 (Propuesta)**.
> No se escribe código hasta recibir `[APROBADO]`.

- **Estado:** ▶ En curso (Pasos 1–3 hechos; pendiente Paso 4 — Git)
- **Fecha inicio:** 2026-06-26
- **Fecha cierre:** —
- **Depende de:** Módulo 1 (Auth), Módulo 2 (materiales/reactivos), Módulo 3
  (docentes/materias/ambientes), Módulo 4 (recetas). Tablas `carritos_cabecera`,
  `carrito_detalle_materiales`, `carrito_detalle_reactivos` ya existen.

---

## 1. Objetivo
Digitalizar el concepto central del sistema: el **Carrito de Insumos**. Un
carrito se **arma desde una Receta Maestra** (M4) copiando sus líneas a un
**detalle editable**, con snapshot de nombres para histórico, permitiendo añadir
líneas extra (`es_extra`) y calculando la `cantidad_total` de reactivos por nº de
grupos. Ver [[proyecto-sistema-insumos]] y [[decisiones-esquema-bd]].

## 2. Alcance
**Incluye:**
- **Armar carrito desde una receta activa:** copiar líneas de reactivos y
  materiales al detalle del carrito, con **snapshot** (`nombre_reactivo`,
  `concentracion_unidad`, `nombre_material`, `capacidad`) tomado del catálogo.
- **Cabecera del carrito:** docente, materia, receta origen, nombre/nº de
  práctica, fecha de realización, ambiente, horario real (inicio/fin), nº de
  pedido, `numero_grupos` (texto descriptivo), `cantidad_grupos` (entero
  multiplicador), código lab. Se crea en estado **`Preparacion`**.
- **Detalle editable:** modificar cantidades, **añadir líneas extra**
  (`es_extra = 1`) y quitar líneas. `cantidad_total` de reactivos =
  `cantidad_por_grupo × cantidad_grupos` (calculado en el servidor).
- **Lectura anidada** del carrito (cabecera + 2 listas de detalle).
- Validaciones: FKs válidas (→400), unicidad de práctica (→409), borrado solo en
  `Preparacion` (→409 si no), `activa` de la receta. Todo protegido con sesión.
- Pantalla PWA: lista de carritos + editor (cabecera + 2 tablas de líneas).

**NO incluye (se difiere):**
- **Movimiento de inventario / Kardex** (materiales a "en uso",
  `movimientos_inventario`): ocurre al transicionar a **`Activo`** → **Módulo 6**.
- **Máquina de estados** completa (Activo → Custodia → Proximo_Cierre) y
  **dashboard** → **Módulo 6**. M5 deja el carrito en `Preparacion`.
- **Cierre, conciliación entregado-vs-devuelto y mermas**
  (`registro_material_roto`) → **Módulo 7**.

## 3. Tablas del esquema usadas (sin cambios de esquema)
- `carritos_cabecera` — cabecera; `receta_id` FK a la receta origen; unicidad por
  índice parcial `idx_carrito_unico_practica` (materia + práctica + fecha +
  hora_inicio) WHERE `estado_carrito <> 'Cerrado'`.
- `carrito_detalle_reactivos (… reactivo_id FK, nombre_reactivo, concentracion_
  unidad, cantidad_por_grupo, cantidad_total, es_extra)` — `ON DELETE CASCADE`.
- `carrito_detalle_materiales (… material_id FK, nombre_material, capacidad,
  cantidad_entregada, cantidad_devuelta NULL, es_extra, observaciones)` —
  `ON DELETE CASCADE`. (`cantidad_devuelta` se llenará en el cierre, M7.)

> **`cantidad_grupos` (multiplicador) NO se persiste como columna** para evitar
> regenerar la BD (L-003): viaja en la petición y se guarda solo el resultado
> `cantidad_total`. Al editar, el multiplicador es re-derivable
> (`cantidad_total / cantidad_por_grupo`). `numero_grupos` (texto) queda como
> etiqueta descriptiva.

## 4. Archivos a crear / modificar
| Archivo | Rol |
|---|---|
| `backend/app/models/carritos.py` | Modelos: `CarritoIn/Out`, líneas `DetalleMaterial*`, `DetalleReactivo*` (anidados) |
| `backend/app/services/carritos_service.py` | Armado desde receta + CRUD + reemplazo de detalles en transacción + cálculo de totales |
| `backend/app/routers/carritos.py` | Endpoints `/api/carritos` |
| `backend/app/main.py` *(mod)* | Registrar el router |
| `frontend/carritos.html` | Lista de carritos + editor (cabecera + 2 tablas de líneas) |
| `frontend/js/carritos.js` | Lógica: elegir receta → precargar líneas, editar, añadir extras, calcular totales |
| `frontend/index.html` *(mod)* | Enlace de navegación a Carritos |
| `backend/tests/test_carrito.py` | Suite pytest del módulo (Paso 3) |

## 5. Endpoints / API
Todos exigen token válido. Prefijo `/api`. Patrón **agregado anidado** (como M4):
una operación maneja cabecera + líneas; el PUT **reemplaza** el detalle en una
transacción.

| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| GET | `/api/carritos` | Listar cabeceras; `?estado=`, `?materia_id=`, `?fecha=`, `?q=` | 401 |
| POST | `/api/carritos` | **Armar** carrito desde `receta_id`: copia líneas + calcula totales | 401, 422, 409 (unicidad), 400 (FK / receta inactiva) |
| GET | `/api/carritos/{id}` | Carrito con detalle anidado | 401, 404 |
| PUT | `/api/carritos/{id}` | Editar cabecera + **reemplazar** líneas (incl. extras), recalcular totales | 401, 404, 409, 400, 422 |
| DELETE | `/api/carritos/{id}` | Eliminar carrito (+ líneas en cascada) — **solo en `Preparacion`** | 401, 404, 409 (si no está en Preparacion) |

Forma del cuerpo (POST):
```json
{
  "receta_id": 1,
  "docente_id": 1,
  "materia_id": 1,
  "nombre_numero_practica": "Complexometría #6",
  "fecha_realizacion": "2026-07-01",
  "ambiente_id": 1,
  "hora_inicio": "08:00",
  "hora_fin": "10:00",
  "numero_pedido": 12,
  "numero_grupos": "1 y 3",
  "cantidad_grupos": 2,
  "codigo_lab_qmc": "QMC-LAB-1"
}
```
El servidor copia las líneas de la receta al detalle (snapshot de nombres),
calcula `cantidad_total = cantidad_por_grupo × cantidad_grupos` y devuelve el
carrito anidado. El PUT acepta además las listas `reactivos[]`/`materiales[]`
editadas (con `es_extra` por línea) para reemplazar el detalle.

## 6. Interfaz (PWA)
- `carritos.html` protegida; lista de carritos (materia · práctica · fecha ·
  estado) con buscador/filtros y botón «+ Nuevo (desde receta)».
- **Editor:** cabecera (selección de docente/materia/ambiente desde catálogos,
  selección de **receta** que precarga las líneas, fecha, horario, nº grupos +
  `cantidad_grupos`) + dos tablas de líneas (Reactivos con total calculado en
  vivo; Materiales con cantidad entregada y observaciones). Añadir/quitar filas;
  marcar extras. Mobile-first; mensajes claros para 409/400.

## 7. Decisiones de diseño (confirmadas con el usuario 2026-06-26)
- **Inventario diferido a M6:** M5 NO mueve `cantidad_en_uso` ni escribe Kardex;
  solo construye el carrito en `Preparacion`. El consumo/entrada de uso ocurre al
  pasar a `Activo` (M6).
- **`cantidad_grupos` como campo numérico aparte** (no se parsea el texto, no se
  cambia el esquema): multiplica para `cantidad_total`; se persiste solo el
  total. `numero_grupos` (texto) es etiqueta.
- **Armado desde receta + extras:** POST copia la receta al detalle editable;
  luego se pueden añadir líneas manuales `es_extra = 1`. (Carrito 100% manual sin
  receta queda fuera de M5.)
- **Snapshot histórico:** al armar se copian `nombre_reactivo`/`nombre_material`
  (+ `concentracion_unidad`/`capacidad`) del catálogo, para que el carrito
  conserve el dato aunque luego cambie el catálogo.
- **Unicidad (Regla 2.C):** índice parcial ya existente; el servicio valida y
  devuelve 409 legible (misma materia + práctica + fecha + hora, no cerrado).
- **Borrado protegido:** solo se permite DELETE en `Preparacion` (aún no hay
  inventario comprometido); → 409 en otros estados. Líneas en cascada.
- **Receta inactiva:** no se puede armar desde una receta `activa = 0` → 400.

## 8. Plan de pruebas (Paso 3)
Suite pytest sobre BD temporal aislada (reusa `conftest.py`, nombres únicos por
L-005); crea docente + materia + ambiente + receta con líneas, y luego:
1. **Armar** carrito desde receta → 201; **GET** anidado con snapshot de nombres
   y `cantidad_total = por_grupo × cantidad_grupos`.
2. **Listar** + filtros `?estado=`, `?materia_id=`, `?fecha=`, `?q=`.
3. **Editar** (PUT): modificar cantidades, **añadir extra** (`es_extra=1`),
   reemplazar líneas y **recalcular** totales; verificar que las viejas se borran.
4. **Unicidad** (mismo materia+práctica+fecha+hora, no cerrado) → 409.
5. **FK inexistente** (docente/receta/material/reactivo) → 400; **receta inactiva** → 400.
6. **Validación** (práctica vacía, `cantidad ≤ 0`, `cantidad_grupos ≤ 0`) → 422.
7. **404** en GET/PUT/DELETE inexistente.
8. **Borrado:** OK en `Preparacion` con cascada de líneas; (cuando exista M6)
   bloquear en otros estados → 409.
9. **Auth:** endpoints sin token → 401.

Comando: `.\.venv\Scripts\python.exe -m pytest backend/tests -v`

---

## Estado SDD
- [x] **Paso 1 — Propuesta (Spec):** aprobada el 2026-06-26 (`APROBADO`; 3 decisiones recomendadas)
- [x] **Paso 2 — Código:** entregado el 2026-06-26 (backend + frontend lista/editor)
- [x] **Paso 3 — Pruebas:** `test_carrito.py` — **11/11 OK** (suite total 56/56) el 2026-06-26
- [ ] **Paso 4 — Git:** *(verificado con datos ficticios + servidor)* commit + push

### Resultado de pruebas (Paso 3)
11 casos sobre BD temporal aislada (reusa `conftest.py`, nombres únicos L-005):
auth (401), armado desde receta + GET anidado (snapshot + `cantidad_total =
por_grupo × cantidad_grupos`), listar + filtros (`q`/`materia_id`/`fecha`/
`estado`), edición que **reemplaza** líneas y marca extra (`es_extra`), unicidad
(409), FK inexistente (400), receta inactiva (400), validación (422), 404,
borrado OK en `Preparacion` con cascada y **bloqueo si no está en Preparacion**
(409). **Suite completa: 56 passed.**

### Verificación funcional (antes de Git)
Servidor levantado + datos ficticios sembrados (docente, ambiente, carrito desde
la receta demo). HTTP verificado: lista y GET anidado devuelven docente/materia/
ambiente resueltos, `cantidad_grupos` re-derivado (3), reactivos con total
50→150 y 5→15, materiales entregada 2→6 y 1→3, snapshot de nombres y `es_extra`.

## Notas / lecciones
- Recordatorios de entorno (ver `docs/LESSONS.md`): `.\.venv\Scripts\python.exe`
  (L-001), here-string/archivo para Python multilínea (L-002), regenerar BD ante
  cambios de esquema (L-003), búsqueda sensible a acentos (L-004), BD de pruebas
  de sesión → fixtures con nombres únicos (L-005).
- **Verificación antes de Git:** sembrar datos ficticios y probar en navegador
  con el servidor levantado antes de commitear (preferencia del usuario).
