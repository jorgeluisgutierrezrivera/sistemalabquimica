/*
 * Service Worker (PWA) - esqueleto bootstrap.
 * La estrategia de caché definitiva (app-shell, offline en LAN) se definirá
 * en el módulo de PWA durante el ciclo SDD. Por ahora no cachea nada.
 */

const CACHE_NAME = "insumos-qmc-v0";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Passthrough por ahora (sin caché). Se implementará por módulo.
});
