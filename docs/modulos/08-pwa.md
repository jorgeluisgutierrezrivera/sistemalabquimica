# Módulo 8 — PWA / Offline / QR

> Plan de trabajo (metodología SDD). Este documento es el **Paso 1 (Propuesta)**.
> No se escribe código hasta recibir `[APROBADO]`.

- **Estado:** ▶ En curso (Pasos 1–3 hechos; pendiente Paso 4 — Git)
- **Fecha inicio:** 2026-06-26
- **Fecha cierre:** —
- **Depende de:** Módulos 1–7 (ciclo funcional completo). Toca infraestructura
  PWA, no reglas de negocio. Sin cambios de esquema.

---

## 1. Objetivo
Convertir el front en una **PWA instalable y robusta en la LAN**: caché del
*app-shell* para que la interfaz cargue al instante (y aunque el server tarde),
**iconos** válidos (hoy faltan → 404) y un **QR** que apunta a la IP local del
servidor para abrir la app desde el móvil sin teclear la dirección. Ver
[[proyecto-sistema-insumos]].

## 2. Alcance
**Incluye:**
- **Service Worker con caché de app-shell** (estrategia definitiva, hoy es un
  esqueleto sin caché): precarga estáticos y los sirve *cache-first*; las
  llamadas `/api/*` van **siempre a la red** (sin cachear datos ni auth).
- **Iconos PWA** `icon-192.png` y `icon-512.png` generados en **Python puro**
  (placeholder con el color del tema + glifo simple), reemplazables luego.
- **QR + datos de red** (backend con `segno`, pura Python): el server detecta su
  **IP LAN** y expone la URL + un **QR (SVG)**; se muestran en el inicio
  («Acceso móvil») para escanear desde el teléfono.
- Versionado de caché con limpieza de versiones viejas al activar.

**NO incluye (se difiere):**
- Caché de respuestas de la API / lectura offline de datos (se descartó: el
  server LAN está siempre encendido; evita datos rancios y problemas de token).
- Sincronización en segundo plano, notificaciones push.
- Empaquetado `.exe` → **Módulo 9**.

## 3. Decisiones de diseño (confirmadas con el usuario 2026-06-26)
- **Offline = solo app-shell:** el SW precachea HTML/CSS/JS/manifest/iconos
  (*cache-first*); `/api/*` es *network-only* (passthrough). La app abre sin
  esperar, pero los datos requieren el servidor.
- **QR con `segno`** (pura Python, MIT, empaqueta limpio con PyInstaller; sin
  PIL): endpoint que devuelve el QR en **SVG** (texto, ideal para empaquetar).
- **Iconos placeholder** generados en Python puro (sin PIL): quitan los 404 y se
  podrán sustituir por arte definitivo.
- **Endpoints de red públicos (sin token):** `/api/red/*` no exige sesión —solo
  revela la IP de la LAN (ya conocida por cualquiera en la red) y un QR— para que
  el `<img>` del QR cargue sin cabecera de auth. No expone datos sensibles.
- **Detección de IP/puerto:** IP LAN por *socket UDP* (sin enviar paquetes, válido
  offline); el puerto se toma del `Host`/URL de la petición. URL =
  `http://<ip-lan>:<puerto>/`.

## 4. Archivos a crear / modificar
| Archivo | Rol |
|---|---|
| `requirements.txt` *(mod)* | Añadir `segno` (QR, pura Python) |
| `backend/app/routers/red.py` | `GET /api/red/info` (ip/puerto/url) + `GET /api/red/qr.svg` (público) |
| `backend/app/main.py` *(mod)* | Registrar el router de red |
| `frontend/service-worker.js` *(reescritura)* | Caché de app-shell + limpieza de versiones |
| `frontend/assets/icons/icon-192.png`, `icon-512.png` | Iconos generados |
| `scripts/gen_icons.py` | Generador de iconos (Python puro, sin PIL) |
| `frontend/index.html` *(mod)* | Tarjeta «Acceso móvil» (QR + URL) |
| `frontend/js/app.js` *(mod)* | Cargar QR/URL desde `/api/red/*` |
| `backend/tests/test_red.py` | Pruebas de los endpoints de red |

## 5. Endpoints / API
| Método | Ruta | Propósito | Auth |
|---|---|---|---|
| GET | `/api/red/info` | `{ "ip": "192.168.x.x", "puerto": 8000, "url": "http://192.168.x.x:8000/" }` | público |
| GET | `/api/red/qr.svg` | QR (SVG) de la URL de acceso | público |

## 6. Service Worker (estrategia)
- **install:** `cache.addAll(APP_SHELL)` con la lista de estáticos (todas las
  páginas HTML, `css/styles.css`, todos los `js/*.js`, `manifest.json`, iconos).
  `skipWaiting()`.
- **activate:** borrar cachés cuyo nombre no sea la versión actual; `clients.claim()`.
- **fetch:**
  - Peticiones a `/api/*` o no-GET → `fetch(event.request)` directo (network-only).
  - Resto (estáticos/navegación, GET) → *cache-first*: responde de caché y si no
    está, va a la red (y cachea la copia). Navegaciones fallidas → `index.html`.
- `CACHE_NAME = "insumos-qmc-v1"` (versionado para invalidar al actualizar).

## 7. Interfaz (PWA)
- En `index.html`, tarjeta **«Acceso móvil»**: muestra la **URL** de la LAN y el
  **QR** (`<img src="/api/red/qr.svg">`) para escanear desde el teléfono y abrir
  la app. Texto de ayuda: «Conéctate a la misma red Wi-Fi y escanea».
- Iconos del manifest válidos → instalación «Añadir a pantalla de inicio» sin 404.

## 8. Plan de pruebas (Paso 3)
La parte cacheable/SW e iconos es de front (verificación manual en navegador).
Las pruebas automáticas (pytest) cubren los endpoints de red:
1. **`GET /api/red/info`** → 200 **sin token**; trae `ip`, `puerto`, `url` y la
   `url` empieza por `http://` y termina en `/`.
2. **`GET /api/red/qr.svg`** → 200, `Content-Type` SVG y el cuerpo contiene `<svg`.
3. **Forma de la URL** coherente con ip+puerto.

**Verificación funcional (antes de Git):** servidor levantado; comprobar en el
navegador que (a) los iconos cargan (sin 404), (b) el SW queda *activated* y la
app carga la segunda vez sin red del shell, (c) la tarjeta «Acceso móvil» muestra
la URL y el QR escaneable.

Comando: `.\.venv\Scripts\python.exe -m pytest backend/tests -v`

---

## Estado SDD
- [x] **Paso 1 — Propuesta (Spec):** aprobada el 2026-06-26 (`APROBADO`; 3 decisiones recomendadas)
- [x] **Paso 2 — Código:** entregado el 2026-06-26 (SW app-shell + iconos + router red + UI; `segno` instalado)
- [x] **Paso 3 — Pruebas:** `test_red.py` — **3/3 OK** (suite total 79/79) el 2026-06-26
- [ ] **Paso 4 — Git:** *(verificado con servidor)* commit + push

### Resultado de pruebas (Paso 3)
3 casos pytest sobre los endpoints públicos: `/api/red/info` (200 sin token, trae
ip/puerto/url coherente), `/api/red/qr.svg` (200, `image/svg+xml`, contiene
`<svg`) y coherencia QR↔info. **Suite completa: 79 passed.**

### Verificación funcional (antes de Git)
Servidor en `0.0.0.0:8001`: `/api/red/info` detectó la IP LAN real
(`10.130.9.39:8001`), el QR salió en SVG con el color del tema, iconos
`icon-192/512.png` sirvieron 200 (matraz blanco sobre azul, reconocible),
`service-worker.js` v1 servido y la tarjeta «Acceso móvil» presente en
`index.html`. (Servir con `--host 0.0.0.0` para que el QR sea alcanzable desde
otros equipos de la LAN.)

## Notas / lecciones
- Nueva dependencia `segno`; actualizar `requirements.txt` e instalar en el venv.
  Es relevante para **M9 (PyInstaller)**: al ser pura Python empaqueta sin
  binarios extra.
- Recordatorios de entorno (`docs/LESSONS.md`): `.\.venv\Scripts\python.exe`
  (L-001), here-string/archivo para multilínea (L-002). El socket del puerto 8000
  quedó huérfano en sesiones previas; usar 8001 si 8000 no responde.
- **Verificación antes de Git** (ver [[verificar-antes-de-git]]).
