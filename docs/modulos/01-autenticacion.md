# Módulo 1 — Autenticación

- **Estado:** ▶ En curso (Paso 2 entregado; Paso 3 pendiente)
- **Fecha inicio:** 2026-06-24
- **Fecha cierre:** —
- **Depende de:** Entorno + BD (bootstrap). Es el módulo **fundacional**: el
  resto de módulos protegerá sus endpoints con su dependencia de sesión.

---

## 1. Objetivo
Controlar el **acceso** al sistema mediante login. Inicialmente un único
usuario **administrador**, con el modelo preparado para crear más usuarios y
roles a futuro. No añade firma digital a las acciones (se mantienen los
timestamps inmutables, Regla 2.G); solo regula quién entra.

## 2. Alcance
**Incluye:**
- Tabla `usuarios` (login + hash + rol).
- Login con JWT, endpoint de perfil (`/me`) y logout.
- Dependencia `get_current_user` reutilizable para blindar otros módulos.
- Pantalla de login y guarda de sesión en el frontend.
- Script de seed para crear el administrador inicial.

**NO incluye (se difiere):**
- Gestión CRUD de usuarios / alta de roles adicionales (futuro).
- Recuperación de contraseña, bloqueo por intentos, auditoría de accesos.

## 3. Tablas del esquema usadas
- `usuarios` — **cambio de esquema aprobado** el 2026-06-24 (tabla nueva).
  Campos: `id, nombre_usuario (UNIQUE), nombre_completo, password_hash, rol
  (CHECK 'administrador', extensible), activo, timestamp_creacion`.

## 4. Archivos creados / modificados
| Archivo | Rol |
|---|---|
| `backend/app/security.py` | Hash pbkdf2 (stdlib) + JWT (PyJWT) + secreto en `data/.jwt_secret` |
| `backend/app/models/auth.py` | `LoginRequest`, `TokenResponse`, `UsuarioOut` |
| `backend/app/services/usuarios_service.py` | Crear / obtener / autenticar / contar usuarios |
| `backend/app/dependencies.py` | `get_current_user` (dependencia de sesión) |
| `backend/app/routers/auth.py` | Endpoints de autenticación |
| `backend/app/main.py` *(mod)* | Registra router + monta la PWA estática |
| `scripts/crear_admin.py` | Seed interactivo del administrador inicial |
| `frontend/login.html`, `js/login.js`, `js/auth.js` | Login + helper de sesión |
| `frontend/index.html`, `js/app.js`, `css/styles.css` *(mod)* | Página protegida + estilos |

## 5. Endpoints / API
| Método | Ruta | Propósito | Errores |
|---|---|---|---|
| POST | `/api/auth/login` | Credenciales → token JWT | 401 credenciales inválidas |
| GET  | `/api/auth/me` | Datos del usuario autenticado | 401 token inválido/expirado |
| POST | `/api/auth/logout` | Logout sin estado (cliente descarta token) | — |

## 6. Interfaz (PWA)
- `login.html`: formulario usuario/contraseña; al validar guarda el token en
  `localStorage` y redirige a `index.html`.
- `index.html`: protegida con `Auth.requireAuth()`; barra superior con el
  usuario y botón «Salir».

## 7. Decisiones de diseño
- **Hash:** `hashlib.pbkdf2_hmac` (sha256, 200k iteraciones, salt por usuario) —
  sin dependencias nativas, empaqueta limpio con PyInstaller.
- **Token:** JWT HS256 con `PyJWT`; expira en **12 h** (una jornada).
- **Secreto JWT:** autogenerado y persistido en `data/.jwt_secret` (no
  versionado); nunca hardcodeado.
- **Admin inicial:** se crea por consola (`crear_admin.py`), sin credenciales
  en el código.

## 8. Plan de pruebas (Paso 3) — propuesto
1. **Unitario/servicio:** hash↔verify, JWT roundtrip, crear/autenticar/duplicado
   (ya cubierto por la prueba de humo; formalizar en `backend/tests/test_auth.py`).
2. **API (cURL/Swagger):**
   - `POST /api/auth/login` con credenciales correctas → 200 + token.
   - Con credenciales incorrectas → 401.
   - `GET /api/auth/me` con token válido → 200; sin token o token falso → 401.
3. **Manual (UI):** acceder sin sesión redirige a login; login correcto entra;
   «Salir» borra sesión y vuelve a login; token caducado redirige a login.

---

## Estado SDD
- [x] **Paso 1 — Propuesta (Spec):** aprobada el 2026-06-24
- [x] **Paso 2 — Código:** entregado el 2026-06-24 (prueba de humo OK)
- [x] **Paso 3 — Pruebas:** `backend/tests/test_auth.py` — **8/8 OK** (2026-06-24)
- [ ] **Paso 4 — Git:** pendiente (este módulo inicializa el repositorio)

### Resultado de pruebas (Paso 3)
Suite con pytest + TestClient sobre BD temporal aislada (`INSUMOS_DB_PATH`):
login correcto/incorrecto, usuario inexistente, payload inválido (422),
`/me` con token válido / sin token / token falso, y logout. **8 passed.**
Ejecutar: `.\.venv\Scripts\python.exe -m pytest backend/tests -v`

## Notas / lecciones
- Ver `docs/LESSONS.md`: L-001 (`py` roto), L-002 (Python multilínea en
  PowerShell), L-003 (regenerar BD ante cambios de esquema).
