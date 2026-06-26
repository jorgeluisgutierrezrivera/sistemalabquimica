/*
 * recetas.js - Módulo 4. Lista y editor de Recetas Maestras (agregado anidado).
 * La receta se guarda completa (cabecera + líneas) en un POST/PUT.
 */

Auth.requireAuth();

const $ = (id) => document.getElementById(id);
const vistaLista = $("vista-lista");
const vistaEditor = $("vista-editor");
const lista = $("lista");
const mensaje = $("mensaje");
const buscador = $("buscador");
const form = $("form");
const formError = $("form-error");

// Catálogos cacheados para los selectores del editor.
let cacheMaterias = [];
let cacheReactivos = [];
let cacheMateriales = [];
let buscarTimer = null;

// ============================================================
// Utilidades
// ============================================================
function mostrarMensaje(texto, esError = false) {
  mensaje.textContent = texto;
  mensaje.classList.toggle("mensaje-error", esError);
}

async function leerError(resp, porDefecto) {
  try {
    return (await resp.json()).detail || porDefecto;
  } catch {
    return porDefecto;
  }
}

function escapar(t) {
  const d = document.createElement("div");
  d.textContent = t ?? "";
  return d.innerHTML;
}

function opcion(valor, texto, seleccionado) {
  const o = document.createElement("option");
  o.value = valor;
  o.textContent = texto;
  if (seleccionado) o.selected = true;
  return o;
}

// ============================================================
// LISTA
// ============================================================
async function cargarLista() {
  const q = buscador.value.trim();
  const url = q ? `/api/recetas?q=${encodeURIComponent(q)}` : "/api/recetas";
  mostrarMensaje("Cargando…");
  try {
    const resp = await Auth.authFetch(url);
    if (!resp.ok) {
      mostrarMensaje(await leerError(resp, "No se pudo cargar."), true);
      return;
    }
    const recetas = await resp.json();
    renderLista(recetas);
    mostrarMensaje(recetas.length ? "" : "Sin recetas. Crea una con «+ Nueva».");
  } catch {
    mostrarMensaje("Sin conexión con el servidor.", true);
  }
}

function renderLista(recetas) {
  lista.innerHTML = "";
  for (const r of recetas) {
    const li = document.createElement("li");
    li.className = "item-insumo";

    const datos = document.createElement("div");
    datos.className = "item-datos";
    const estado = r.activa ? "" : ' · <span class="inactiva">inactiva</span>';
    datos.innerHTML = `
      <strong>${escapar(r.nombre_practica)}</strong>
      <span class="stock">${escapar(r.materia)}${estado}</span>`;

    const acc = document.createElement("div");
    acc.className = "item-acciones";
    const editar = document.createElement("button");
    editar.className = "btn-secundario btn-icono";
    editar.textContent = "Editar";
    editar.addEventListener("click", () => abrirEditor(r.id));
    const borrar = document.createElement("button");
    borrar.className = "btn-secundario btn-icono btn-peligro";
    borrar.textContent = "Borrar";
    borrar.addEventListener("click", () => eliminar(r));
    acc.append(editar, borrar);

    li.append(datos, acc);
    lista.appendChild(li);
  }
}

async function eliminar(r) {
  if (!confirm(`¿Eliminar la receta "${r.nombre_practica}"?`)) return;
  try {
    const resp = await Auth.authFetch(`/api/recetas/${r.id}`, { method: "DELETE" });
    if (resp.status === 204) {
      mostrarMensaje("Receta eliminada.");
      cargarLista();
    } else {
      mostrarMensaje(await leerError(resp, "No se pudo eliminar."), true);
    }
  } catch {
    mostrarMensaje("Sin conexión con el servidor.", true);
  }
}

// ============================================================
// CARGA DE CATÁLOGOS (para el editor)
// ============================================================
async function asegurarCatalogos() {
  if (cacheMaterias.length || cacheReactivos.length || cacheMateriales.length) return;
  const [m, r, mat] = await Promise.all([
    Auth.authFetch("/api/materias").then((x) => x.json()),
    Auth.authFetch("/api/reactivos").then((x) => x.json()),
    Auth.authFetch("/api/materiales").then((x) => x.json()),
  ]);
  cacheMaterias = m;
  cacheReactivos = r;
  cacheMateriales = mat;
}

// ============================================================
// EDITOR
// ============================================================
async function abrirEditor(recetaId = null) {
  formError.textContent = "";
  form.reset();
  $("lineas-reactivos").innerHTML = "";
  $("lineas-materiales").innerHTML = "";

  try {
    await asegurarCatalogos();
  } catch {
    mostrarMensaje("No se pudieron cargar los catálogos.", true);
    return;
  }

  // Poblar selector de materias.
  const selMateria = $("f-materia");
  selMateria.innerHTML = "";
  selMateria.appendChild(opcion("", "— Selecciona materia —", false));
  for (const m of cacheMaterias) {
    selMateria.appendChild(opcion(m.id, `${m.sigla} - ${m.nombre}`, false));
  }

  $("f-id").value = "";
  $("editor-titulo").textContent = "Nueva receta";

  if (recetaId) {
    // Cargar receta existente.
    const resp = await Auth.authFetch(`/api/recetas/${recetaId}`);
    if (!resp.ok) {
      mostrarMensaje("No se pudo cargar la receta.", true);
      return;
    }
    const r = await resp.json();
    $("f-id").value = r.id;
    $("editor-titulo").textContent = "Editar receta";
    selMateria.value = r.materia_id;
    $("f-practica").value = r.nombre_practica;
    $("f-descripcion").value = r.descripcion || "";
    $("f-activa").checked = r.activa;
    r.reactivos.forEach((d) => agregarLineaReactivo(d));
    r.materiales.forEach((d) => agregarLineaMaterial(d));
  }

  vistaLista.classList.add("oculto");
  vistaEditor.classList.remove("oculto");
}

function cerrarEditor() {
  vistaEditor.classList.add("oculto");
  vistaLista.classList.remove("oculto");
  cargarLista();
}

function quitarLinea(boton) {
  boton.closest(".linea").remove();
}

function agregarLineaReactivo(d = null) {
  const div = document.createElement("div");
  div.className = "linea linea-reactivo";

  const sel = document.createElement("select");
  sel.className = "sel-insumo";
  sel.appendChild(opcion("", "— Reactivo —", false));
  for (const r of cacheReactivos) {
    sel.appendChild(opcion(r.id, r.nombre, d && d.reactivo_id === r.id));
  }

  const conc = document.createElement("input");
  conc.type = "text";
  conc.className = "inp-conc";
  conc.placeholder = "Conc./unidad (ej: 0,01M / mL)";
  conc.maxLength = 60;
  if (d) conc.value = d.concentracion_unidad || "";

  const cant = document.createElement("input");
  cant.type = "number";
  cant.className = "inp-cant";
  cant.min = "0";
  cant.step = "any";
  cant.placeholder = "Cant.";
  if (d) cant.value = d.cantidad_por_grupo;

  const quitar = document.createElement("button");
  quitar.type = "button";
  quitar.className = "btn-secundario btn-icono btn-peligro";
  quitar.textContent = "✕";
  quitar.addEventListener("click", () => quitarLinea(quitar));

  div.append(sel, conc, cant, quitar);
  $("lineas-reactivos").appendChild(div);
}

function agregarLineaMaterial(d = null) {
  const div = document.createElement("div");
  div.className = "linea linea-material";

  const sel = document.createElement("select");
  sel.className = "sel-insumo";
  sel.appendChild(opcion("", "— Material —", false));
  for (const m of cacheMateriales) {
    const etiqueta = m.capacidad ? `${m.nombre} (${m.capacidad})` : m.nombre;
    sel.appendChild(opcion(m.id, etiqueta, d && d.material_id === m.id));
  }

  const cant = document.createElement("input");
  cant.type = "number";
  cant.className = "inp-cant";
  cant.min = "0";
  cant.step = "1";
  cant.placeholder = "Cant.";
  if (d) cant.value = d.cantidad_por_grupo;

  const obs = document.createElement("input");
  obs.type = "text";
  obs.className = "inp-obs";
  obs.placeholder = "Observaciones";
  obs.maxLength = 120;
  if (d) obs.value = d.observaciones || "";

  const quitar = document.createElement("button");
  quitar.type = "button";
  quitar.className = "btn-secundario btn-icono btn-peligro";
  quitar.textContent = "✕";
  quitar.addEventListener("click", () => quitarLinea(quitar));

  div.append(sel, cant, obs, quitar);
  $("lineas-materiales").appendChild(div);
}

// Recolecta las líneas; lanza Error con mensaje si alguna es inválida.
function recolectarReactivos() {
  const out = [];
  for (const div of document.querySelectorAll(".linea-reactivo")) {
    const id = div.querySelector(".sel-insumo").value;
    const cant = parseFloat(div.querySelector(".inp-cant").value);
    if (!id) throw new Error("Hay una línea de reactivo sin seleccionar.");
    if (!(cant > 0)) throw new Error("Cada reactivo necesita una cantidad mayor que 0.");
    out.push({
      reactivo_id: parseInt(id, 10),
      concentracion_unidad: div.querySelector(".inp-conc").value.trim() || null,
      cantidad_por_grupo: cant,
    });
  }
  return out;
}

function recolectarMateriales() {
  const out = [];
  for (const div of document.querySelectorAll(".linea-material")) {
    const id = div.querySelector(".sel-insumo").value;
    const cant = parseInt(div.querySelector(".inp-cant").value, 10);
    if (!id) throw new Error("Hay una línea de material sin seleccionar.");
    if (!(cant > 0)) throw new Error("Cada material necesita una cantidad mayor que 0.");
    out.push({
      material_id: parseInt(id, 10),
      cantidad_por_grupo: cant,
      observaciones: div.querySelector(".inp-obs").value.trim() || null,
    });
  }
  return out;
}

async function guardar(evento) {
  evento.preventDefault();
  formError.textContent = "";

  const materia_id = $("f-materia").value;
  const nombre_practica = $("f-practica").value.trim();
  if (!materia_id) {
    formError.textContent = "Selecciona una materia.";
    return;
  }
  if (!nombre_practica) {
    formError.textContent = "El nombre de la práctica es obligatorio.";
    return;
  }

  let reactivos, materiales;
  try {
    reactivos = recolectarReactivos();
    materiales = recolectarMateriales();
  } catch (e) {
    formError.textContent = e.message;
    return;
  }

  const cuerpo = {
    materia_id: parseInt(materia_id, 10),
    nombre_practica,
    descripcion: $("f-descripcion").value.trim() || null,
    activa: $("f-activa").checked,
    reactivos,
    materiales,
  };

  const id = $("f-id").value;
  const url = id ? `/api/recetas/${id}` : "/api/recetas";
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
    mostrarMensaje(id ? "Receta actualizada." : "Receta creada.");
    cerrarEditor();
  } catch {
    formError.textContent = "Sin conexión con el servidor.";
  }
}

// ============================================================
// Eventos
// ============================================================
buscador.addEventListener("input", () => {
  clearTimeout(buscarTimer);
  buscarTimer = setTimeout(cargarLista, 250);
});
$("btn-nueva").addEventListener("click", () => abrirEditor());
$("btn-cancelar").addEventListener("click", cerrarEditor);
$("btn-add-reactivo").addEventListener("click", () => agregarLineaReactivo());
$("btn-add-material").addEventListener("click", () => agregarLineaMaterial());
form.addEventListener("submit", guardar);
$("logout").addEventListener("click", () => Auth.logout());

(async () => {
  try {
    const resp = await Auth.authFetch("/api/auth/me");
    if (resp.ok) {
      const u = await resp.json();
      $("sesion-info").textContent = `Recetas · ${u.nombre_completo || u.nombre_usuario}`;
    }
  } catch {
    /* sin bloqueo */
  }
})();

cargarLista();
