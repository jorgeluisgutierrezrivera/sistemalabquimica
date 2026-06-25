/*
 * inventario.js - Módulo 2. Administra los catálogos de Materiales y Reactivos.
 * Una sola pantalla con dos pestañas; reusa Auth.authFetch (token + 401).
 */

Auth.requireAuth();

// Estado de la vista.
let tab = "materiales"; // "materiales" | "reactivos"
let buscarTimer = null;

// --- Referencias del DOM ---
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
function esMaterial() {
  return tab === "materiales";
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

// ============================================================
// Carga y render de la lista
// ============================================================
async function cargar() {
  const q = buscador.value.trim();
  const base = esMaterial() ? "/api/materiales" : "/api/reactivos";
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
    li.appendChild(esMaterial() ? filaMaterial(it) : filaReactivo(it));
    li.appendChild(acciones(it));
    lista.appendChild(li);
  }
}

function filaMaterial(m) {
  const div = document.createElement("div");
  div.className = "item-datos";
  const cap = m.capacidad ? ` · ${m.capacidad}` : "";
  const cod = m.codigo ? `<span class="cod">${m.codigo}</span> ` : "";
  const agotado = m.cantidad_disponible <= 0 ? " agotado" : "";
  div.innerHTML = `
    <strong>${cod}${escapar(m.nombre)}${cap}</strong>
    <span class="stock">
      Total ${m.cantidad_total} ·
      En uso ${m.cantidad_en_uso} ·
      <b class="disp${agotado}">Disp. ${m.cantidad_disponible}</b>
    </span>`;
  return div;
}

function filaReactivo(r) {
  const div = document.createElement("div");
  div.className = "item-datos";
  const cod = r.codigo ? `<span class="cod">${r.codigo}</span> ` : "";
  const uni = r.unidad_base ? ` · ${escapar(r.unidad_base)}` : "";
  div.innerHTML = `<strong>${cod}${escapar(r.nombre)}</strong><span class="stock">${uni}</span>`;
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

function escapar(t) {
  const d = document.createElement("div");
  d.textContent = t ?? "";
  return d.innerHTML;
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
    : esMaterial()
    ? "Nuevo material"
    : "Nuevo reactivo";

  // Mostrar campos según pestaña.
  modal.classList.toggle("modo-material", esMaterial());
  modal.classList.toggle("modo-reactivo", !esMaterial());

  if (item) {
    $("f-nombre").value = item.nombre || "";
    $("f-codigo").value = item.codigo || "";
    if (esMaterial()) {
      $("f-capacidad").value = item.capacidad || "";
      $("f-total").value = item.cantidad_total;
      $("f-en-uso-info").textContent =
        `En uso actualmente: ${item.cantidad_en_uso} (no editable aquí).`;
    } else {
      $("f-unidad").value = item.unidad_base || "";
    }
  } else {
    $("f-en-uso-info").textContent = "";
  }

  modal.classList.remove("oculto");
  $("f-nombre").focus();
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
  if (esMaterial()) {
    cuerpo = {
      nombre,
      codigo: $("f-codigo").value.trim() || null,
      capacidad: $("f-capacidad").value.trim() || null,
      cantidad_total: parseInt($("f-total").value, 10) || 0,
    };
  } else {
    cuerpo = {
      nombre,
      codigo: $("f-codigo").value.trim() || null,
      unidad_base: $("f-unidad").value.trim() || null,
    };
  }

  const base = esMaterial() ? "/api/materiales" : "/api/reactivos";
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
  if (!confirm(`¿Eliminar "${item.nombre}"? Esta acción no se puede deshacer.`)) {
    return;
  }
  const base = esMaterial() ? "/api/materiales" : "/api/reactivos";
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
      $("sesion-info").textContent = `Inventario · ${u.nombre_completo || u.nombre_usuario}`;
    }
  } catch {
    /* sin bloqueo */
  }
})();

cargar();
