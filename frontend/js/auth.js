/*
 * auth.js - helper de sesión del cliente (compartido por todas las vistas).
 * Guarda el token JWT en localStorage y centraliza las llamadas autenticadas.
 */

const Auth = {
  TOKEN_KEY: "insumos_qmc_token",

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
  },

  clear() {
    localStorage.removeItem(this.TOKEN_KEY);
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  /** Redirige al login si no hay sesión. Usar al cargar páginas protegidas. */
  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.replace("login.html");
    }
  },

  /** fetch con cabecera Authorization. Si el token caduca (401), va al login. */
  async authFetch(url, options = {}) {
    const opts = {
      ...options,
      headers: {
        ...(options.headers || {}),
        Authorization: `Bearer ${this.getToken()}`,
      },
    };
    const resp = await fetch(url, opts);
    if (resp.status === 401) {
      this.clear();
      window.location.replace("login.html");
    }
    return resp;
  },

  logout() {
    this.clear();
    window.location.replace("login.html");
  },
};
