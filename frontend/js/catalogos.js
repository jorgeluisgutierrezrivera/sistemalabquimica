/*
 * catalogos.js - Módulo 3. Administra Docentes, Materias y Ambientes.
 * Una pantalla con tres pestañas; reusa Auth.authFetch (token + 401).
 * Mismo patrón que inventario.js.
 */

Auth.requireAuth();

// Configuración por pestaña: endpoint base y etiqueta singular.
const CONFIG = {
  docentes: { base: "/api/docentes", singular: "docente" },
  materias: { base: "/api/materias", singular: "materia" },
  ambientes: { base: "/api/ambientes", singular: "ambiente" },
};

let tab = "docentes";
let buscarTimer = null;

const $ = (id) => document.getElementById(id);
const lista = $("lista");
const mensaje = $("mensaje");
const buscador = $("buscador");
const modal = $("modal");
const form = $("form");
const formError = $("form-error");

// ============================================================
// Utilidades
// ============================================================
function esMateria() {
  return tab === "materias";
}

function mostrarMensaje(texto, esError = false) {
  mensaje.textContent = texto;
  mensaje.classList.toggle("mensaje-error", esError);
}

async function leerError(resp, porDefecto) {
  try {
    const data = await resp.json();
    return data.detail || porDefecto;
  } catch {
    return porDefecto;
  }
}

function escapar(t) {
  const d = document.createElement("div");
  d.textContent = t ?? "";
  return d.innerHTML;
}

// ============================================================
// Carga y render
// ============================================================
async function cargar() {
  const q = buscador.value.trim();
  const base = CONFIG[tab].base;
  const url = q ? `${base}?q=${encodeURIComponent(q)}` : base;
  mostrarMensaje("Cargando…");
  try {
    const resp = await Auth.authFetch(url);
    if (!resp.ok) {
      mostrarMensaje(await leerError(resp, "No se pudo cargar la lista."), true);
      return;
    }
    const items = await resp.json();
    render(items);
    mostrarMensaje(items.length ? "" : "Sin resultados.");
  } catch {
    mostrarMensaje("Sin conexión con el servidor.", true);
  }
}

function render(items) {
  lista.innerHTML = "";
  for (const it of items) {
    const li = document.createElement("li");
    li.className = "item-insumo";
    li.appendChild(fila(it));
    li.appendChild(acciones(it));
    lista.appendChild(li);
  }
}

function fila(it) {
  const div = document.createElement("div");
  div.className = "item-datos";
  if (esMateria()) {
    div.innerHTML = `
      <strong><span class="cod">${escapar(it.sigla)}</span> ${escapar(it.nombre)}</strong>
      <span class="stock">${escapar(it.carrera)}</span>`;
  } else {
    div.innerHTML = `<strong>${escapar(it.nombre)}</strong>`;
  }
  return div;
}

function acciones(it) {
  const cont = document.createElement("div");
  cont.className = "item-acciones";

  const editar = document.createElement("button");
  editar.className = "btn-secundario btn-icono";
  editar.textContent = "Editar";
  editar.addEventListener("click", () => abrirModal(it));

  const borrar = document.createElement("button");
  borrar.className = "btn-secundario btn-icono btn-peligro";
  borrar.textContent = "Borrar";
  borrar.addEventListener("click", () => eliminar(it));

  cont.append(editar, borrar);
  return cont;
}

// ============================================================
// Modal alta / edición
// ============================================================
function abrirModal(item = null) {
  formError.textContent = "";
  form.reset();
  $("f-id").value = item ? item.id : "";
  $("modal-titulo").textContent = item
    ? "Editar"
    : `Nuevo ${CONFIG[tab].singular}`;

  // Mostrar campos de materia solo en esa pestaña.
  modal.classList.toggle("modo-materia", esMateria());

  if (item) {
    $("f-nombre").value = item.nombre || "";
    if (esMateria()) {
      $("f-sigla").value = item.sigla || "";
      $("f-carrera").value = item.carrera || "";
    }
  }

  modal.classList.remove("oculto");
  ($("f-nombre")).focus();
  if (esMateria()) $("f-sigla").focus();
}

function cerrarModal() {
  modal.classList.add("oculto");
}

async function guardar(evento) {
  evento.preventDefault();
  formError.textContent = "";
  const id = $("f-id").value;
  const nombre = $("f-nombre").value.trim();
  if (!nombre) {
    formError.textContent = "El nombre es obligatorio.";
    return;
  }

  let cuerpo;
  if (esMateria()) {
    const sigla = $("f-sigla").value.trim();
    const carrera = $("f-carrera").value.trim();
    if (!sigla || !carrera) {
      formError.textContent = "Sigla, nombre y carrera son obligatorios.";
      return;
    }
    cuerpo = { sigla, nombre, carrera };
  } else {
    cuerpo = { nombre };
  }

  const base = CONFIG[tab].base;
  const url = id ? `${base}/${id}` : base;
  const metodo = id ? "PUT" : "POST";

  try {
    const resp = await Auth.authFetch(url, {
      method: metodo,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo),
    });
    if (!resp.ok) {
      formError.textContent = await leerError(resp, "No se pudo guardar.");
      return;
    }
    cerrarModal();
    mostrarMensaje(id ? "Cambios guardados." : "Creado correctamente.");
    cargar();
  } catch {
    formError.textContent = "Sin conexión con el servidor.";
  }
}

async function eliminar(item) {
  const etiqueta = esMateria() ? `${item.sigla} - ${item.nombre}` : item.nombre;
  if (!confirm(`¿Eliminar "${etiqueta}"? Esta acción no se puede deshacer.`)) {
    return;
  }
  const base = CONFIG[tab].base;
  try {
    const resp = await Auth.authFetch(`${base}/${item.id}`, { method: "DELETE" });
    if (resp.status === 204) {
      mostrarMensaje("Eliminado.");
      cargar();
    } else {
      mostrarMensaje(await leerError(resp, "No se pudo eliminar."), true);
    }
  } catch {
    mostrarMensaje("Sin conexión con el servidor.", true);
  }
}

// ============================================================
// Eventos
// ============================================================
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("activa"));
    btn.classList.add("activa");
    tab = btn.dataset.tab;
    buscador.value = "";
    cargar();
  });
});

buscador.addEventListener("input", () => {
  clearTimeout(buscarTimer);
  buscarTimer = setTimeout(cargar, 250);
});

$("btn-nuevo").addEventListener("click", () => abrirModal());
$("btn-cancelar").addEventListener("click", cerrarModal);
form.addEventListener("submit", guardar);
modal.addEventListener("click", (e) => {
  if (e.target === modal) cerrarModal();
});
$("logout").addEventListener("click", () => Auth.logout());

// Mostrar usuario en la barra.
(async () => {
  try {
    const resp = await Auth.authFetch("/api/auth/me");
    if (resp.ok) {
      const u = await resp.json();
      $("sesion-info").textContent = `Catálogos · ${u.nombre_completo || u.nombre_usuario}`;
    }
  } catch {
    /* sin bloqueo */
  }
})();

cargar();
