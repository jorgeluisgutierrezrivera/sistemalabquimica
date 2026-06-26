/*
 * Service Worker (PWA) - Módulo 8.
 * Estrategia: caché del app-shell (estáticos) cache-first; las llamadas a la API
 * (/api/*) y los métodos no-GET van siempre a la red (network-only). Así la app
 * abre al instante aunque el server tarde, sin cachear datos ni sesión.
 */

const CACHE_NAME = "insumos-qmc-v1";

const APP_SHELL = [
  "./",
  "index.html",
  "login.html",
  "inventario.html",
  "catalogos.html",
  "recetas.html",
  "carritos.html",
  "dashboard.html",
  "manifest.json",
  "css/styles.css",
  "js/app.js",
  "js/auth.js",
  "js/login.js",
  "js/inventario.js",
  "js/catalogos.js",
  "js/recetas.js",
  "js/carritos.js",
  "js/dashboard.js",
  "assets/icons/icon-192.png",
  "assets/icons/icon-512.png",
];

// Precarga del app-shell.
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

// Limpieza de versiones de caché antiguas.
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((claves) =>
        Promise.all(
          claves.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

// Cache-first para estáticos; network-only para la API y no-GET.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // API o métodos que cambian estado: directo a la red (sin caché).
  if (event.request.method !== "GET" || url.pathname.startsWith("/api/")) {
    return; // passthrough: la red maneja la petición
  }

  event.respondWith(
    caches.match(event.request).then((cacheada) => {
      if (cacheada) return cacheada;
      return fetch(event.request)
        .then((resp) => {
          // Cachea copias de estáticos del mismo origen.
          if (resp.ok && url.origin === self.location.origin) {
            const copia = resp.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copia));
          }
          return resp;
        })
        .catch(() => {
          // Sin red: para navegaciones, devolver el shell.
          if (event.request.mode === "navigate") return caches.match("index.html");
        });
    })
  );
});
