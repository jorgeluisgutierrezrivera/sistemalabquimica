/*
 * app.js - arranque de la página principal (protegida).
 * Exige sesión, muestra el usuario y comprueba la salud de la API.
 * La lógica de cada vista se construirá por módulo (ciclo SDD).
 */

// Puerta de entrada: sin token válido, al login.
Auth.requireAuth();

(async function () {
  const sesionInfo = document.getElementById("sesion-info");
  const estado = document.getElementById("estado-api");

  // Datos del usuario autenticado (valida el token en el servidor).
  try {
    const resp = await Auth.authFetch("/api/auth/me");
    if (resp.ok) {
      const u = await resp.json();
      sesionInfo.textContent = `${u.nombre_completo || u.nombre_usuario} · ${u.rol}`;
    }
  } catch (err) {
    sesionInfo.textContent = "Sesión activa";
  }

  // Comprobación de salud de la API.
  try {
    const resp = await fetch("/api/health");
    const data = await resp.json();
    estado.textContent = `Servidor conectado ✓ (v${data.version})`;
  } catch (err) {
    estado.textContent = "Sin conexión con el servidor.";
  }

  // Cerrar sesión.
  const logoutBtn = document.getElementById("logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => Auth.logout());
  }
})();

// Registro del Service Worker (PWA). La estrategia se afinará por módulo.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("service-worker.js").catch(() => {});
  });
}
