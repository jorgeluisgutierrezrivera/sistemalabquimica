# Módulo 7 — Cierre y Conciliación

> Plan de trabajo (metodología SDD). Este documento es el **Paso 1 (Propuesta)**.
> No se escribe código hasta recibir `[APROBADO]`.

- **Estado:** ✅ Cerrado
- **Fecha inicio:** 2026-06-26
- **Fecha cierre:** 2026-06-26
- **Depende de:** Módulos 1–6. Tablas `carritos_cabecera` (estado),
  `carrito_detalle_materiales` (cantidad_devuelta), `registro_material_roto`,
  `movimientos_inventario`, `materiales` ya existen.

---

## 1. Objetivo
Cerrar el ciclo del carrito: **conciliar** lo entregado vs lo devuelto de los
materiales (retornables), registrar **mermas** (rotura/pérdida), **revertir** el
inventario en uso y dar la transición final a **`Cerrado`**. Es la contraparte
del movimiento de inventario que M6 hizo al entregar. Ver
[[proyecto-sistema-insumos]] y [[decisiones-esquema-bd]].

## 2. Alcance
**Incluye:**
- **Cierre con conciliación** (un solo endpoint, en transacción): desde
  `Proximo_Cierre`, captura `cantidad_devuelta` por línea de material, calcula la
  merma, mueve el inventario y pasa el carrito a `Cerrado`.
- **Reversión de inventario por material** (ver §7 para la fórmula):
  - `cantidad_en_uso -= cantidad_entregada` (sale del estado "en uso").
  - `cantidad_total -= merma` (lo perdido/roto deja el patrimonio).
  - Kardex `retorno` (= devuelta) y `merma` (= entregada − devuelta).
- **Registro de mermas:** todo faltante genera Kardex `merma` **y** una fila en
  `registro_material_roto` (docente del carrito como responsable + observación).
- **Reactivos:** no se concilian (consumibles; su `salida_consumo` ya quedó en M6).
- **Inmutabilidad:** una vez `Cerrado`, el carrito no admite más transiciones ni
  edición/borrado (coherente con M5/M6).
- Pantalla PWA de **cierre**: tabla de materiales con devuelta (precargada = lo
  entregado) y observación, y botón «Cerrar carrito».

**NO incluye (se difiere / fuera de alcance):**
- Reapertura de un carrito cerrado (no contemplado).
- Reportes/exportación de mermas (posible backlog).

## 3. Tablas del esquema usadas (sin cambios de esquema)
- `carritos_cabecera.estado_carrito` → `Cerrado`.
- `carrito_detalle_materiales.cantidad_devuelta` — se llena al cerrar.
- `registro_material_roto (carrito_id, detalle_material_id, fecha_reporte,
  codigo_material, tipo_material, docente_responsable, cantidad,
  observaciones_rotura)` — una fila por línea con merma.
- `movimientos_inventario` — Kardex `retorno` y `merma` (material).
- `materiales.cantidad_en_uso` / `cantidad_total` — se ajustan al cerrar.

## 4. Archivos a crear / modificar
| Archivo | Rol |
|---|---|
| `backend/app/models/cierre.py` | `DevolucionIn`, `CierreIn` |
| `backend/app/models/carritos.py` *(mod)* | `DetalleMaterialOut` + `cantidad_devuelta` |
| `backend/app/services/cierre_service.py` | Conciliación + reversión de inventario + mermas en transacción |
| `backend/app/routers/carritos.py` *(mod)* | `POST /api/carritos/{id}/cierre` |
| `frontend/carritos.html` + `frontend/js/carritos.js` *(mod)* | Panel de cierre (devueltas + observaciones) |
| `backend/tests/test_cierre.py` | Suite pytest del módulo (Paso 3) |

## 5. Endpoints / API
Token requerido. Prefijo `/api`.

| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| POST | `/api/carritos/{id}/cierre` | Conciliar y cerrar el carrito | 401, 404, 409 (no está en `Proximo_Cierre` / devuelta > entregada), 422 |

Cuerpo:
```json
{
  "devoluciones": [
    {"detalle_material_id": 5, "cantidad_devuelta": 3, "observaciones": "1 rota"}
  ]
}
```
- Cada `detalle_material_id` debe pertenecer al carrito (si no → 409).
- Líneas de material **omitidas** se cierran con `cantidad_devuelta =
  cantidad_entregada` (devolución completa, sin merma) — coincide con el default
  de la UI.
- `0 ≤ cantidad_devuelta ≤ cantidad_entregada`; fuera de rango → 409.
- Respuesta: el carrito (`CarritoOut`) ya `Cerrado`, con `cantidad_devuelta` por
  línea de material.

## 6. Interfaz (PWA)
- En `carritos.html`, cuando el carrito está en `Proximo_Cierre`, el bloque de
  estado ofrece **«Cerrar carrito»**, que despliega una tabla de materiales:
  nombre · entregada · **devuelta** (input, precargado = entregada) · observación.
- Al confirmar, POST al endpoint de cierre; mensajes claros para 409/422. Tras
  cerrar, el carrito queda de solo lectura (sin avanzar/editar).

## 7. Decisiones de diseño (confirmadas con el usuario 2026-06-26)
- **Fórmula de inventario por material** (`merma = entregada − devuelta`):
  ```
  materiales.cantidad_en_uso -= entregada      # todo sale de "en uso"
  materiales.cantidad_total  -= merma           # lo perdido deja el patrimonio
  carrito_detalle_materiales.cantidad_devuelta = devuelta
  Kardex: retorno (devuelta) si > 0 ; merma (merma) si > 0
  ```
  Resultado: lo devuelto vuelve a `disponible`; lo roto/perdido se descuenta del
  patrimonio. Reactivos no se tocan.
- **Mermas automáticas:** todo faltante (`merma > 0`) crea Kardex `merma` **y**
  `registro_material_roto` (responsable = docente del carrito; `tipo_material` =
  nombre snapshot; `codigo_material` = código del catálogo; `cantidad` = merma;
  `observaciones_rotura` = la de la línea).
- **Solo desde `Proximo_Cierre`:** cerrar desde otro estado → 409. Respeta el
  flujo y el carácter manual de "Próximo a Cerrarse".
- **Devuelta por defecto = entregada:** la UI precarga la devolución completa; la
  administradora solo corrige las líneas con faltante.
- **Inmutable tras `Cerrado`:** sin reapertura; el índice de unicidad ya solo
  aplica a no-cerrados, así que la práctica puede repetirse luego.
- **Transacción atómica:** si algo falla (estado o devolución inválida), no se
  mueve inventario ni se cambia el estado (rollback de `get_db`).

## 8. Plan de pruebas (Paso 3)
Suite pytest sobre BD temporal aislada (reusa `conftest.py`, nombres únicos
L-005); arma un carrito, lo lleva a `Proximo_Cierre` (pasando por `Activo`, que
mueve el inventario) y luego:
1. **Auth:** cierre sin token → 401.
2. **Cierre completo** (devuelta = entregada): estado → `Cerrado`;
   `cantidad_en_uso` vuelve a 0; `cantidad_total` intacto; Kardex `retorno`; sin
   `registro_material_roto`; `cantidad_devuelta` guardado.
3. **Cierre con merma** (devuelta < entregada): `cantidad_total` baja en la merma;
   `en_uso` vuelve a 0; Kardex `retorno` + `merma`; se crea `registro_material_roto`
   con `cantidad = merma` y docente responsable.
4. **Default:** líneas omitidas se cierran con devuelta = entregada (sin merma).
5. **Estado inválido** (cerrar desde `Activo`/`Preparacion`) → 409.
6. **Devuelta > entregada** → 409 sin cambios (rollback).
7. **404** en carrito inexistente.
8. **Inmutabilidad:** tras `Cerrado`, `PATCH …/estado` y segundo `…/cierre` → 409;
   `DELETE` → 409.
9. **Reactivos:** el cierre no genera movimientos de reactivo nuevos.

Comando: `.\.venv\Scripts\python.exe -m pytest backend/tests -v`

---

## Estado SDD
- [x] **Paso 1 — Propuesta (Spec):** aprobada el 2026-06-26 (`APROBADO`; 3 decisiones recomendadas)
- [x] **Paso 2 — Código:** entregado el 2026-06-26 (servicio + endpoint + frontend panel de cierre)
- [x] **Paso 3 — Pruebas:** `test_cierre.py` — **8/8 OK** (suite total 76/76) el 2026-06-26
- [x] **Paso 4 — Git:** commit `2048b65` (feat) + cierre de docs, push a `origin/main` el 2026-06-26

### Resultado de pruebas (Paso 3)
8 casos sobre BD temporal aislada (reusa `conftest.py`, nombres únicos L-005):
auth (401), cierre completo sin merma (en_uso→0, total intacto, Kardex `retorno`,
sin roto), cierre con merma (total baja, Kardex `retorno`+`merma`,
`registro_material_roto` creado), estado inválido (409), devuelta > entregada
(409 + rollback), 404, inmutabilidad tras `Cerrado` (2º cierre/transición/borrado
→ 409) y reactivos sin movimientos nuevos. **Suite completa: 76 passed.**

### Verificación funcional (antes de Git)
Servidor + datos ficticios: cierre del carrito demo con merma (Matraz 4/6 →
merma 2): estado `Cerrado`, `cantidad_devuelta` guardado, Matraz en_uso 6→0 y
total 30→28, Bureta en_uso 3→0 y total intacto, Kardex `retorno` 3/4 + `merma` 2,
`registro_material_roto` (resp. docente, cant. 2), 2º cierre → 409, dashboard
con `Cerrado=1`.

## Notas / lecciones
- Recordatorios de entorno (ver `docs/LESSONS.md`): `.\.venv\Scripts\python.exe`
  (L-001), here-string/archivo para Python multilínea (L-002), regenerar BD ante
  cambios de esquema (L-003), búsqueda sensible a acentos (L-004), BD de pruebas
  de sesión → nombres únicos (L-005).
- **Verificación antes de Git:** sembrar datos ficticios y probar en navegador
  con el servidor levantado antes de commitear (ver [[verificar-antes-de-git]]).
- Con M7 se completa el ciclo funcional del sistema (Módulos 1–7); quedan
  PWA/offline/QR (M8) y empaquetado (M9).
