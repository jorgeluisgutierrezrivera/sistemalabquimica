/*
 * dashboard.js - Módulo 6. Tablero de control: conteo por estado y listas.
 */

Auth.requireAuth();

const $ = (id) => document.getElementById(id);
const mensaje = $("mensaje");

const ESTADOS = ["Preparacion", "Activo", "Custodia", "Proximo_Cierre", "Cerrado"];

function escapar(t) {
  const d = document.createElement("div");
  d.textContent = t ?? "";
  return d.innerHTML;
}

function renderTarjetas(porEstado) {
  const cont = $("tarjetas-estado");
  cont.innerHTML = "";
  for (const e of ESTADOS) {
    const card = document.createElement("a");
    card.className = "tarjeta-estado";
    card.href = "carritos.html";
    card.innerHTML = `
      <span class="tarjeta-num">${porEstado[e] ?? 0}</span>
      <span class="tarjeta-lbl">${escapar(e.replace("_", " "))}</span>`;
    cont.appendChild(card);
  }
}

function renderLista(ulId, carritos) {
  const ul = $(ulId);
  ul.innerHTML = "";
  if (!carritos.length) {
    const li = document.createElement("li");
    li.className = "item-insumo vacio";
    li.textContent = "— sin carritos —";
    ul.appendChild(li);
    return;
  }
  for (const c of carritos) {
    const li = document.createElement("li");
    li.className = "item-insumo";
    const a = document.createElement("a");
    a.className = "item-datos enlace-carrito";
    a.href = "carritos.html";
    a.innerHTML = `
      <strong>${escapar(c.nombre_numero_practica)}</strong>
      <span class="stock">${escapar(c.materia)} · ${escapar(c.fecha_realizacion)}
        · <span class="badge-estado">${escapar(c.estado_carrito)}</span></span>`;
    li.appendChild(a);
    ul.appendChild(li);
  }
}

async function cargar() {
  mensaje.textContent = "Cargando…";
  try {
    const resp = await Auth.authFetch("/api/dashboard");
    if (!resp.ok) {
      mensaje.textContent = "No se pudo cargar el tablero.";
      mensaje.classList.add("mensaje-error");
      return;
    }
    const d = await resp.json();
    renderTarjetas(d.por_estado);
    renderLista("lista-activos", d.activos);
    renderLista("lista-proximos", d.proximos_cierre);
    renderLista("lista-dia", d.del_dia);
    mensaje.textContent = `${d.total} carrito(s) en total.`;
    mensaje.classList.remove("mensaje-error");
  } catch {
    mensaje.textContent = "Sin conexión con el servidor.";
    mensaje.classList.add("mensaje-error");
  }
}

$("logout").addEventListener("click", () => Auth.logout());

(async () => {
  try {
    const resp = await Auth.authFetch("/api/auth/me");
    if (resp.ok) {
      const u = await resp.json();
      $("sesion-info").textContent = `Tablero · ${u.nombre_completo || u.nombre_usuario}`;
    }
  } catch {
    /* sin bloqueo */
  }
})();

cargar();
