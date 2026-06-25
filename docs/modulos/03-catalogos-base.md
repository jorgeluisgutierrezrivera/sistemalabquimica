# Módulo 3 — Catálogos Base (Docentes / Materias / Ambientes)

> Plan de trabajo (metodología SDD). Este documento es el **Paso 1 (Propuesta)**.
> No se escribe código hasta recibir `[APROBADO]`.

- **Estado:** ▶ En curso (Pasos 1–3 hechos; pendiente Paso 4 — Git)
- **Fecha inicio:** 2026-06-25
- **Fecha cierre:** —
- **Depende de:** Módulo 1 (Autenticación — protección de endpoints). Tablas
  `docentes`, `materias`, `ambientes` ya existen en `schema.sql`.

---

## 1. Objetivo
Gestionar los **catálogos académicos base** que dan estructura a las recetas y
carritos: **docentes**, **materias** y **ambientes**. Son listas simples y
normalizadas; existen para evitar texto libre inconsistente que rompa los
bloqueos de unicidad del carrito (Regla 2.C). Ver [[decisiones-esquema-bd]].

## 2. Alcance
**Incluye:**
- CRUD de **Docentes** (nombre único).
- CRUD de **Materias** (sigla, nombre, carrera; único por sigla+nombre).
- CRUD de **Ambientes** (nombre único).
- Búsqueda por texto en cada catálogo (`?q=`).
- Validaciones de duplicado (409) y borrado protegido por integridad
  referencial (no borrar si está usado por horarios/recetas/carritos).
- Endpoints protegidos con sesión y pantalla PWA con pestañas (patrón del M2).

**NO incluye (se difiere):**
- **`horarios_semestre`** (distribución académica referencial): depende de las
  tres entidades de este módulo y es de naturaleza distinta (relación, no
  catálogo simple). **Recomendación: diferirlo** a un módulo propio o anexarlo
  al de Recetas/Carrito. *(A confirmar — ver §7 y Notas.)*
- Importación masiva (CSV) → backlog.

## 3. Tablas del esquema usadas
- `docentes (id, nombre UNIQUE)` — sin cambios de esquema.
- `materias (id, sigla, nombre, carrera, UNIQUE(sigla,nombre))` — sin cambios.
- `ambientes (id, nombre UNIQUE)` — sin cambios.

> No se requiere modificar `schema.sql`. Las tablas ya tienen restricciones
> UNIQUE a nivel de BD; aun así validamos en el servicio para devolver 409 con
> mensaje claro (en vez de un IntegrityError genérico).

## 4. Archivos a crear / modificar
| Archivo | Rol |
|---|---|
| `backend/app/models/catalogos.py` | Modelos Pydantic: `DocenteIn/Out`, `MateriaIn/Out`, `AmbienteIn/Out` |
| `backend/app/services/docentes_service.py` | CRUD docentes |
| `backend/app/services/materias_service.py` | CRUD materias |
| `backend/app/services/ambientes_service.py` | CRUD ambientes |
| `backend/app/routers/catalogos.py` | Endpoints `/api/docentes`, `/api/materias`, `/api/ambientes` |
| `backend/app/main.py` *(mod)* | Registrar el nuevo router |
| `frontend/catalogos.html` | Pantalla con 3 pestañas (Docentes / Materias / Ambientes) |
| `frontend/js/catalogos.js` | Lógica de la pantalla (reusa patrón de inventario.js) |
| `frontend/index.html` *(mod)* | Enlace de navegación a Catálogos |
| `backend/tests/test_catalogos.py` | Suite pytest del módulo (Paso 3) |

> Igual que en M2: **un router** y **una pantalla** con pestañas para las tres
> entidades; **un servicio por entidad** para mantener la lógica clara.

## 5. Endpoints / API
Todos exigen token válido (router con `dependencies=[Depends(get_current_user)]`).

### Docentes
| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| GET | `/api/docentes` | Listar; `?q=` por nombre | 401 |
| POST | `/api/docentes` | Crear | 401, 422, 409 (duplicado) |
| GET | `/api/docentes/{id}` | Obtener | 401, 404 |
| PUT | `/api/docentes/{id}` | Editar | 401, 404, 409 |
| DELETE | `/api/docentes/{id}` | Eliminar | 401, 404, 409 (en uso) |

### Materias
| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| GET | `/api/materias` | Listar; `?q=` por sigla/nombre/carrera | 401 |
| POST | `/api/materias` | Crear | 401, 422, 409 |
| GET | `/api/materias/{id}` | Obtener | 401, 404 |
| PUT | `/api/materias/{id}` | Editar | 401, 404, 409 |
| DELETE | `/api/materias/{id}` | Eliminar | 401, 404, 409 (en uso) |

### Ambientes
| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| GET | `/api/ambientes` | Listar; `?q=` por nombre | 401 |
| POST | `/api/ambientes` | Crear | 401, 422, 409 |
| GET | `/api/ambientes/{id}` | Obtener | 401, 404 |
| PUT | `/api/ambientes/{id}` | Editar | 401, 404, 409 |
| DELETE | `/api/ambientes/{id}` | Eliminar | 401, 404, 409 (en uso) |

## 6. Interfaz (PWA)
- `catalogos.html` protegida con `Auth.requireAuth()`; barra superior común.
- **Tres pestañas**: «Docentes», «Materias», «Ambientes» (mobile-first).
- Cada pestaña: buscador + botón «+ Nuevo» + lista con editar/borrar (modal),
  reutilizando el patrón visual de `inventario.html`.
- Materias muestra los tres campos (sigla, nombre, carrera); docentes y
  ambientes, solo el nombre.
- Mensajes claros de 409 (duplicado / en uso).

## 7. Decisiones de diseño
- **Borrado protegido (integridad referencial):** antes de borrar, contar
  referencias en `horarios_semestre`, `recetas`, `carritos_cabecera` (según
  corresponda a cada entidad) → 409 si hay alguna. Evita huérfanos pese a que
  los FK no sean `RESTRICT`.
  - Docente: referenciado por `horarios_semestre`, `carritos_cabecera`.
  - Materia: referenciado por `horarios_semestre`, `recetas`, `carritos_cabecera`.
  - Ambiente: referenciado por `horarios_semestre`, `carritos_cabecera`.
- **Duplicados:** validación en servicio (case-insensitive) → 409, además del
  UNIQUE de BD como red de seguridad.
- **`horarios_semestre` diferido:** no es un catálogo simple sino una relación
  materia×docente×ambiente×horario; encaja mejor junto a Recetas/Carrito.
  *(Confirmar: ¿lo dejamos fuera de M3 como propongo?)*
- **Reutiliza el patrón del M2:** `get_db()`, servicios con `sqlite3.Row`,
  modelos Pydantic, router con prefijo y dependencia global. Sin dependencias nuevas.

## 8. Plan de pruebas (Paso 3)
Suite pytest sobre BD temporal aislada (reusa `conftest.py`), todas con token
(y un par sin token → 401):
1. **Por entidad (docentes/materias/ambientes):** crear → listar → buscar `?q=`
   → obtener → editar → duplicado (409) → 404 inexistente → borrar OK.
2. **Materia:** unicidad por sigla+nombre (misma sigla con otro nombre = OK).
3. **Borrado protegido:** simular referencia (insertar en `horarios_semestre`)
   y verificar 409 al borrar.
4. **Validación:** nombre/sigla vacíos → 422.

Comando: `.\.venv\Scripts\python.exe -m pytest backend/tests -v`

---

## Estado SDD
- [x] **Paso 1 — Propuesta (Spec):** aprobada el 2026-06-25 (`APROBADO`; `horarios_semestre` diferido)
- [x] **Paso 2 — Código:** entregado el 2026-06-25 (backend + frontend)
- [x] **Paso 3 — Pruebas:** `test_catalogos.py` — **14/14 OK** (suite total 35/35) el 2026-06-25
- [ ] **Paso 4 — Git:** commit `<hash/mensaje>` el AAAA-MM-DD

### Resultado de pruebas (Paso 3)
14 casos sobre BD temporal aislada (reusa `conftest.py`): auth (401 sin token en
los tres catálogos), CRUD + búsqueda + duplicado (409) + 422 + 404 de docentes,
materias (unicidad sigla+nombre, misma sigla con otro nombre OK, campos
faltantes 422) y ambientes, y **borrado protegido** simulando un registro en
`horarios_semestre` (409 para las tres entidades). **Suite completa: 35 passed.**
Limitación documentada: la búsqueda es case-insensitive pero sensible a acentos
(ver `docs/LESSONS.md` L-004).

## Notas / lecciones
- **Punto a confirmar antes del Paso 2:** ¿se mantiene `horarios_semestre`
  fuera de M3 (recomendado) o lo incluimos aquí?
- Recordatorios de entorno (ver `docs/LESSONS.md`): usar `.\.venv\Scripts\python.exe`
  (L-001), heredoc/archivo para Python multilínea en PowerShell (L-002),
  regenerar BD ante cambios de esquema (L-003).
