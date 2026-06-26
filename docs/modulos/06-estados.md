# Módulo 6 — Estados del Carrito y Dashboard

> Plan de trabajo (metodología SDD). Este documento es el **Paso 1 (Propuesta)**.
> No se escribe código hasta recibir `[APROBADO]`.

- **Estado:** ▶ En curso (Pasos 1–3 hechos; pendiente Paso 4 — Git)
- **Fecha inicio:** 2026-06-26
- **Fecha cierre:** —
- **Depende de:** Módulos 1–5. Tablas `carritos_cabecera` (estado),
  `carrito_detalle_*`, `materiales` (cantidad_en_uso), `movimientos_inventario`
  (Kardex) ya existen.

---

## 1. Objetivo
Dar vida al **ciclo de estados** del carrito y al **tablero de control**. Aquí se
ejecuta el **movimiento de inventario diferido** desde M5: al entregar un carrito
(pasar a `Activo`) los materiales pasan a "en uso" y se registra el Kardex. El
dashboard resume la operación por estado. Ver [[proyecto-sistema-insumos]] y
[[decisiones-esquema-bd]].

## 2. Alcance
**Incluye:**
- **Máquina de estados (solo hacia adelante):**
  `Preparacion → Activo → (Custodia) → Proximo_Cierre`. La transición final a
  `Cerrado` queda para **M7** (conciliación).
- **Endpoint de transición** que valida el cambio permitido y aplica los efectos.
- **Movimiento de inventario al pasar a `Activo`** (una sola vez):
  - Materiales: `cantidad_en_uso += cantidad_entregada` (M2 dejó este campo para
    "la lógica de carritos") + Kardex `entrada_uso`.
  - Reactivos: Kardex `salida_consumo` (informativo; sin stock que descontar).
  - Validación de disponibilidad: `cantidad_disponible (= total − en_uso) ≥
    cantidad_entregada` por material, o **409** (stock insuficiente).
- **Dashboard:** conteo de carritos por estado + listas de apoyo (activos,
  próximos a cierre, del día).
- Pantalla PWA de **tablero** + control para avanzar el estado desde el carrito.

**NO incluye (se difiere):**
- Transición a `Cerrado`, conciliación entregado-vs-devuelto, retorno de
  materiales y mermas (`registro_material_roto`) → **Módulo 7**.
- Retroceso de estados / deshacer inventario (se acordó **forward-only**).

## 3. Tablas del esquema usadas (sin cambios de esquema)
- `carritos_cabecera.estado_carrito` (CHECK con los 5 estados); el trigger
  `trg_carritos_touch` ya actualiza `timestamp_actualizacion`.
- `materiales.cantidad_en_uso` — se incrementa al pasar a `Activo`.
- `movimientos_inventario` — Kardex: `entrada_uso` (material), `salida_consumo`
  (reactivo). Trazabilidad inmutable.
- Índices `idx_carritos_estado/fecha/docente` ya existen (dashboard).

## 4. Archivos a crear / modificar
| Archivo | Rol |
|---|---|
| `backend/app/models/estados.py` | `CambioEstadoIn` (estado destino), `DashboardOut`, `ConteoEstado` |
| `backend/app/services/estados_service.py` | Transiciones válidas + efectos de inventario/Kardex en transacción |
| `backend/app/services/dashboard_service.py` | Agregaciones por estado y listas de apoyo |
| `backend/app/routers/carritos.py` *(mod)* | `PATCH /api/carritos/{id}/estado` |
| `backend/app/routers/dashboard.py` | `GET /api/dashboard` |
| `backend/app/main.py` *(mod)* | Registrar el router de dashboard |
| `frontend/dashboard.html` + `frontend/js/dashboard.js` | Tablero por estado |
| `frontend/carritos.html` + `frontend/js/carritos.js` *(mod)* | Botón «avanzar estado» + badge |
| `frontend/index.html` *(mod)* | Enlace a Tablero |
| `backend/tests/test_estados.py` | Suite pytest del módulo (Paso 3) |

## 5. Endpoints / API
Todos exigen token válido. Prefijo `/api`.

| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| PATCH | `/api/carritos/{id}/estado` | Avanzar el estado (con efectos de inventario al entrar a `Activo`) | 401, 404, 409 (transición inválida / stock insuficiente / ya cerrado), 422 |
| GET | `/api/dashboard` | Conteos por estado + listas (activos, próximos a cierre, del día) | 401 |

Cuerpo de la transición:
```json
{ "estado": "Activo" }
```

**Transiciones permitidas (forward-only):**
```
Preparacion → Activo
Activo      → Custodia | Proximo_Cierre
Custodia    → Proximo_Cierre
Proximo_Cierre → (Cerrado: Módulo 7)
```
Cualquier otra (saltos, retrocesos, desde/hacia `Cerrado`) → **409**.

Forma de `GET /api/dashboard`:
```json
{
  "por_estado": {"Preparacion": 2, "Activo": 3, "Custodia": 0,
                 "Proximo_Cierre": 1, "Cerrado": 5},
  "total": 11,
  "activos": [ {…carrito resumen…} ],
  "proximos_cierre": [ {…} ],
  "del_dia": [ {…} ]
}
```

## 6. Interfaz (PWA)
- `dashboard.html`: tarjetas con el conteo por estado y listas de carritos
  activos / próximos a cierre / del día (enlazan al carrito). Mobile-first.
- En `carritos.html`: badge de estado (ya existe) + botón **«Avanzar estado»**
  que ofrece el/los estados destino válidos; mensajes claros para 409.
- Enlace **Tablero** en `index.html`.

## 7. Decisiones de diseño (confirmadas con el usuario 2026-06-26)
- **Inventario al entrar a `Activo`:** materiales suben `cantidad_en_uso` (+Kardex
  `entrada_uso`) y reactivos registran Kardex `salida_consumo` (informativo, sin
  stock). Todo dentro de la transacción de la transición.
- **Forward-only:** no se permite retroceder; el inventario se mueve una sola vez
  (al entrar a `Activo`), evitando estados de inventario inconsistentes.
- **Frontera M6/M7:** M6 llega hasta `Proximo_Cierre`; el `Cerrado` (conciliación,
  devolución de materiales, mermas) es del Módulo 7.
- **"Próximo a Cerrarse" es MANUAL** (regla de negocio): es una transición que
  dispara la administradora, nunca el reloj.
- **Disponibilidad:** al entrar a `Activo` se valida `disponible ≥ entregada` por
  material; si no, 409 sin mover nada (rollback).
- **Consistencia con M2:** una vez `Activo`, los materiales en uso no se pueden
  borrar (M2 ya bloquea `en_uso > 0`) ni dejar `total < en_uso`.
- **Borrado (M5):** sigue permitido solo en `Preparacion`; tras `Activo` el
  carrito no se borra (409), preservando el inventario comprometido.

## 8. Plan de pruebas (Paso 3)
Suite pytest sobre BD temporal aislada (reusa `conftest.py`, nombres únicos
L-005); arma un carrito desde receta y luego:
1. **Auth:** transición/dashboard sin token → 401.
2. **Preparacion → Activo:** 200; `cantidad_en_uso` del material sube en
   `cantidad_entregada`; se crean filas de Kardex `entrada_uso` (material) y
   `salida_consumo` (reactivo).
3. **Idempotencia/forward:** repetir el mismo destino o retroceder → 409 (el
   inventario no se vuelve a mover).
4. **Cadena válida:** `Activo → Custodia → Proximo_Cierre` (200 cada paso).
5. **Transición inválida:** `Preparacion → Proximo_Cierre` (salto) → 409.
6. **Stock insuficiente:** material con `disponible < entregada` al entrar a
   `Activo` → 409 y sin cambios (rollback).
7. **Dashboard:** conteos por estado coherentes tras mover carritos.
8. **404:** transición sobre carrito inexistente.
9. **Borrado tras `Activo`:** DELETE → 409 (consistencia con M5).

Comando: `.\.venv\Scripts\python.exe -m pytest backend/tests -v`

---

## Estado SDD
- [x] **Paso 1 — Propuesta (Spec):** aprobada el 2026-06-26 (`APROBADO`; 3 decisiones recomendadas)
- [x] **Paso 2 — Código:** entregado el 2026-06-26 (estados + dashboard + frontend)
- [x] **Paso 3 — Pruebas:** `test_estados.py` — **12/12 OK** (suite total 68/68) el 2026-06-26
- [ ] **Paso 4 — Git:** *(verificado con datos ficticios + servidor)* commit + push

### Resultado de pruebas (Paso 3)
12 casos sobre BD temporal aislada (reusa `conftest.py`, nombres únicos L-005):
auth (401 estado + dashboard), `Preparacion→Activo` con verificación de
`cantidad_en_uso` y Kardex (`entrada_uso` material + `salida_consumo` reactivo),
cadena válida hasta `Proximo_Cierre`, salto inválido (409), retroceso (409),
`Cerrado` reservado a M7 (409), estado inexistente (422), 404, **stock
insuficiente (409 + rollback)**, dashboard por estado y borrado bloqueado tras
`Activo` (409). **Suite completa: 68 passed.**

### Verificación funcional (antes de Git)
Servidor + datos ficticios: transición `Activo` del carrito demo movió el
inventario (Matraz 0→6, Bureta 0→3 en uso), registró Kardex (entrada_uso 6/3,
salida_consumo 150/15), el dashboard reflejó `Activo=1`, el reintento dio 409
(forward-only) y el avance a `Custodia` 200.

## Notas / lecciones
- Recordatorios de entorno (ver `docs/LESSONS.md`): `.\.venv\Scripts\python.exe`
  (L-001), here-string/archivo para Python multilínea (L-002), regenerar BD ante
  cambios de esquema (L-003), búsqueda sensible a acentos (L-004), BD de pruebas
  de sesión → nombres únicos (L-005).
- **Verificación antes de Git:** sembrar datos ficticios y probar en navegador
  con el servidor levantado antes de commitear (ver [[verificar-antes-de-git]]).
