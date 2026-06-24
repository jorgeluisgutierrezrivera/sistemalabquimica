/*
 * login.js - lógica de la pantalla de acceso.
 */

// Si ya hay sesión, no mostramos el login.
if (Auth.isAuthenticated()) {
  window.location.replace("index.html");
}

const form = document.getElementById("login-form");
const errorEl = document.getElementById("login-error");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.textContent = "";

  const nombre_usuario = document.getElementById("usuario").value.trim();
  const password = document.getElementById("password").value;

  try {
    const resp = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre_usuario, password }),
    });

    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      errorEl.textContent = data.detail || "No se pudo iniciar sesión.";
      return;
    }

    const data = await resp.json();
    Auth.setToken(data.access_token);
    window.location.replace("index.html");
  } catch (err) {
    errorEl.textContent = "Sin conexión con el servidor.";
  }
});
