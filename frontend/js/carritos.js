/*
 * carritos.js - Módulo 5. Lista y editor del Carrito de Insumos.
 * "Nuevo" arma el carrito desde una receta (POST copia las líneas).
 * "Editar" reemplaza cabecera + líneas (PUT), permitiendo extras.
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
let cacheDocentes = [];
let cacheMaterias = [];
let cacheAmbientes = [];
let cacheRecetas = [];
let cacheReactivos = [];
let cacheMateriales = [];
let buscarTimer = null;
let modo = "nuevo"; // "nuevo" | "editar"

// Transiciones válidas (forward-only; 'Cerrado' es del Módulo 7).
const TRANSICIONES = {
  Preparacion: ["Activo"],
  Activo: ["Custodia", "Proximo_Cierre"],
  Custodia: ["Proximo_Cierre"],
  Proximo_Cierre: [],
  Cerrado: [],
};

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

function gruposActuales() {
  const n = parseInt($("f-grupos-cant").value, 10);
  return n > 0 ? n : 1;
}

// ============================================================
// LISTA
// ============================================================
async function cargarLista() {
  const q = buscador.value.trim();
  const url = q ? `/api/carritos?q=${encodeURIComponent(q)}` : "/api/carritos";
  mostrarMensaje("Cargando…");
  try {
    const resp = await Auth.authFetch(url);
    if (!resp.ok) {
      mostrarMensaje(await leerError(resp, "No se pudo cargar."), true);
      return;
    }
    const carritos = await resp.json();
    renderLista(carritos);
    mostrarMensaje(carritos.length ? "" : "Sin carritos. Crea uno con «+ Nuevo».");
  } catch {
    mostrarMensaje("Sin conexión con el servidor.", true);
  }
}

function renderLista(carritos) {
  lista.innerHTML = "";
  for (const c of carritos) {
    const li = document.createElement("li");
    li.className = "item-insumo";

    const datos = document.createElement("div");
    datos.className = "item-datos";
    datos.innerHTML = `
      <strong>${escapar(c.nombre_numero_practica)}</strong>
      <span class="stock">${escapar(c.materia)} · ${escapar(c.fecha_realizacion)}
        · <span class="badge-estado">${escapar(c.estado_carrito)}</span></span>`;

    const acc = document.createElement("div");
    acc.className = "item-acciones";
    const editar = document.createElement("button");
    editar.className = "btn-secundario btn-icono";
    editar.textContent = "Abrir";
    editar.addEventListener("click", () => abrirEditor(c.id));
    const borrar = document.createElement("button");
    borrar.className = "btn-secundario btn-icono btn-peligro";
    borrar.textContent = "Borrar";
    borrar.addEventListener("click", () => eliminar(c));
    acc.append(editar, borrar);

    li.append(datos, acc);
    lista.appendChild(li);
  }
}

async function eliminar(c) {
  if (!confirm(`¿Eliminar el carrito "${c.nombre_numero_practica}"?`)) return;
  try {
    const resp = await Auth.authFetch(`/api/carritos/${c.id}`, { method: "DELETE" });
    if (resp.status === 204) {
      mostrarMensaje("Carrito eliminado.");
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
  if (cacheDocentes.length || cacheRecetas.length) return;
  const [d, m, a, rec, r, mat] = await Promise.all([
    Auth.authFetch("/api/docentes").then((x) => x.json()),
    Auth.authFetch("/api/materias").then((x) => x.json()),
    Auth.authFetch("/api/ambientes").then((x) => x.json()),
    Auth.authFetch("/api/recetas?activa=true").then((x) => x.json()),
    Auth.authFetch("/api/reactivos").then((x) => x.json()),
    Auth.authFetch("/api/materiales").then((x) => x.json()),
  ]);
  cacheDocentes = d;
  cacheMaterias = m;
  cacheAmbientes = a;
  cacheRecetas = rec;
  cacheReactivos = r;
  cacheMateriales = mat;
}

function poblarSelectores() {
  const selRec = $("f-receta");
  selRec.innerHTML = "";
  selRec.appendChild(opcion("", "— Selecciona receta —", false));
  for (const r of cacheRecetas) {
    selRec.appendChild(opcion(r.id, `${r.materia} · ${r.nombre_practica}`, false));
  }
  const selDoc = $("f-docente");
  selDoc.innerHTML = "";
  selDoc.appendChild(opcion("", "— Selecciona docente —", false));
  for (const d of cacheDocentes) selDoc.appendChild(opcion(d.id, d.nombre, false));

  const selMat = $("f-materia");
  selMat.innerHTML = "";
  selMat.appendChild(opcion("", "— Selecciona materia —", false));
  for (const m of cacheMaterias) {
    selMat.appendChild(opcion(m.id, `${m.sigla} - ${m.nombre}`, false));
  }
  const selAmb = $("f-ambiente");
  selAmb.innerHTML = "";
  selAmb.appendChild(opcion("", "— (sin ambiente) —", false));
  for (const a of cacheAmbientes) selAmb.appendChild(opcion(a.id, a.nombre, false));
}

// Al elegir receta en modo "nuevo", prefill materia + práctica.
function onRecetaChange() {
  if (modo !== "nuevo") return;
  const id = parseInt($("f-receta").value, 10);
  const rec = cacheRecetas.find((r) => r.id === id);
  if (!rec) return;
  $("f-materia").value = rec.materia_id;
  if (!$("f-practica").value.trim()) $("f-practica").value = rec.nombre_practica;
}

// ============================================================
// EDITOR
// ============================================================
async function abrirEditor(carritoId = null) {
  formError.textContent = "";
  form.reset();
  $("f-grupos-cant").value = "1";
  $("lineas-reactivos").innerHTML = "";
  $("lineas-materiales").innerHTML = "";

  try {
    await asegurarCatalogos();
  } catch {
    mostrarMensaje("No se pudieron cargar los catálogos.", true);
    return;
  }
  poblarSelectores();

  const selRec = $("f-receta");
  if (carritoId) {
    // -------- modo editar --------
    modo = "editar";
    const resp = await Auth.authFetch(`/api/carritos/${carritoId}`);
    if (!resp.ok) {
      mostrarMensaje("No se pudo cargar el carrito.", true);
      return;
    }
    const c = await resp.json();
    $("f-id").value = c.id;
    $("editor-titulo").textContent = "Editar carrito";
    $("btn-guardar").textContent = "Guardar cambios";
    $("bloque-detalle").classList.remove("oculto");
    $("aviso-nuevo").classList.add("oculto");

    // Receta origen fija (no se re-arma).
    if (c.receta_id) {
      if (!selRec.querySelector(`option[value="${c.receta_id}"]`)) {
        selRec.appendChild(opcion(c.receta_id, "(receta origen)", false));
      }
      selRec.value = c.receta_id;
    }
    selRec.disabled = true;
    $("hint-receta").textContent = "(origen, no editable)";

    $("f-docente").value = c.docente_id;
    $("f-materia").value = c.materia_id;
    $("f-practica").value = c.nombre_numero_practica;
    $("f-fecha").value = c.fecha_realizacion;
    $("f-grupos-cant").value = c.cantidad_grupos || 1;
    $("f-grupos-txt").value = c.numero_grupos || "";
    if (c.ambiente_id) $("f-ambiente").value = c.ambiente_id;
    $("f-hora-ini").value = c.hora_inicio || "";
    $("f-hora-fin").value = c.hora_fin || "";
    $("f-pedido").value = c.numero_pedido ?? "";
    $("f-codigo").value = c.codigo_lab_qmc || "";

    c.reactivos.forEach((d) => agregarLineaReactivo(d));
    c.materiales.forEach((d) => agregarLineaMaterial(d));
    recomputarTotales();
    mostrarBloqueEstado(c.estado_carrito);
  } else {
    // -------- modo nuevo (armar) --------
    modo = "nuevo";
    $("f-id").value = "";
    $("editor-titulo").textContent = "Nuevo carrito";
    $("btn-guardar").textContent = "Armar carrito";
    $("bloque-detalle").classList.add("oculto");
    $("aviso-nuevo").classList.remove("oculto");
    $("bloque-estado").classList.add("oculto");
    selRec.disabled = false;
    $("hint-receta").textContent = "(define las líneas iniciales)";
  }

  vistaLista.classList.add("oculto");
  vistaEditor.classList.remove("oculto");
}

function cerrarEditor() {
  vistaEditor.classList.add("oculto");
  vistaLista.classList.remove("oculto");
  cargarLista();
}

// Muestra el bloque de estado con las transiciones válidas (modo edición).
function mostrarBloqueEstado(estado) {
  const bloque = $("bloque-estado");
  const destinos = TRANSICIONES[estado] || [];
  $("estado-actual").textContent = estado;
  $("estado-msg").textContent = "";
  const sel = $("f-estado-destino");
  sel.innerHTML = "";
  for (const e of destinos) sel.appendChild(opcion(e, e.replace("_", " "), false));
  // Sin destinos válidos (Proximo_Cierre / Cerrado): deshabilitar avance.
  const sinAvance = destinos.length === 0;
  sel.disabled = sinAvance;
  $("btn-avanzar").disabled = sinAvance;
  if (sinAvance) {
    $("estado-msg").textContent =
      estado === "Proximo_Cierre"
        ? "El cierre se realizará en el Módulo 7."
        : "Sin transiciones disponibles.";
  }
  bloque.classList.remove("oculto");
}

async function avanzarEstado() {
  const cid = $("f-id").value;
  const destino = $("f-estado-destino").value;
  if (!cid || !destino) return;
  $("estado-msg").textContent = "Aplicando…";
  try {
    const resp = await Auth.authFetch(`/api/carritos/${cid}/estado`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ estado: destino }),
    });
    if (!resp.ok) {
      $("estado-msg").textContent = await leerError(resp, "No se pudo avanzar.");
      return;
    }
    const c = await resp.json();
    mostrarBloqueEstado(c.estado_carrito);
    $("estado-msg").textContent = `Estado actualizado a "${c.estado_carrito}".`;
  } catch {
    $("estado-msg").textContent = "Sin conexión con el servidor.";
  }
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
  conc.placeholder = "Conc./unidad";
  conc.maxLength = 60;
  if (d) conc.value = d.concentracion_unidad || "";

  const cant = document.createElement("input");
  cant.type = "number";
  cant.className = "inp-cant";
  cant.min = "0";
  cant.step = "any";
  cant.placeholder = "x grupo";
  if (d) cant.value = d.cantidad_por_grupo;
  cant.addEventListener("input", recomputarTotales);

  const total = document.createElement("span");
  total.className = "inp-total";
  total.textContent = d ? `= ${d.cantidad_total}` : "= 0";

  const extra = document.createElement("label");
  extra.className = "check-extra";
  const chk = document.createElement("input");
  chk.type = "checkbox";
  chk.className = "chk-extra";
  if (d) chk.checked = !!d.es_extra;
  extra.append(chk, document.createTextNode(" extra"));

  const quitar = document.createElement("button");
  quitar.type = "button";
  quitar.className = "btn-secundario btn-icono btn-peligro";
  quitar.textContent = "✕";
  quitar.addEventListener("click", () => quitarLinea(quitar));

  div.append(sel, conc, cant, total, extra, quitar);
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
  cant.placeholder = "entregada";
  if (d) cant.value = d.cantidad_entregada;

  const obs = document.createElement("input");
  obs.type = "text";
  obs.className = "inp-obs";
  obs.placeholder = "Observaciones";
  obs.maxLength = 200;
  if (d) obs.value = d.observaciones || "";

  const extra = document.createElement("label");
  extra.className = "check-extra";
  const chk = document.createElement("input");
  chk.type = "checkbox";
  chk.className = "chk-extra";
  if (d) chk.checked = !!d.es_extra;
  extra.append(chk, document.createTextNode(" extra"));

  const quitar = document.createElement("button");
  quitar.type = "button";
  quitar.className = "btn-secundario btn-icono btn-peligro";
  quitar.textContent = "✕";
  quitar.addEventListener("click", () => quitarLinea(quitar));

  div.append(sel, cant, obs, extra, quitar);
  $("lineas-materiales").appendChild(div);
}

// Recalcula el total visible de cada reactivo (= por_grupo × nº grupos).
function recomputarTotales() {
  const g = gruposActuales();
  for (const div of document.querySelectorAll(".linea-reactivo")) {
    const cant = parseFloat(div.querySelector(".inp-cant").value);
    const total = cant > 0 ? cant * g : 0;
    div.querySelector(".inp-total").textContent = `= ${total}`;
  }
}

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
      es_extra: div.querySelector(".chk-extra").checked,
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
    if (!(cant > 0)) throw new Error("Cada material necesita una cantidad entregada mayor que 0.");
    out.push({
      material_id: parseInt(id, 10),
      cantidad_entregada: cant,
      observaciones: div.querySelector(".inp-obs").value.trim() || null,
      es_extra: div.querySelector(".chk-extra").checked,
    });
  }
  return out;
}

function cabeceraComun() {
  return {
    docente_id: parseInt($("f-docente").value, 10),
    materia_id: parseInt($("f-materia").value, 10),
    nombre_numero_practica: $("f-practica").value.trim(),
    fecha_realizacion: $("f-fecha").value,
    ambiente_id: $("f-ambiente").value ? parseInt($("f-ambiente").value, 10) : null,
    hora_inicio: $("f-hora-ini").value || null,
    hora_fin: $("f-hora-fin").value || null,
    numero_pedido: $("f-pedido").value ? parseInt($("f-pedido").value, 10) : null,
    numero_grupos: $("f-grupos-txt").value.trim() || null,
    cantidad_grupos: gruposActuales(),
    codigo_lab_qmc: $("f-codigo").value.trim() || null,
  };
}

async function guardar(evento) {
  evento.preventDefault();
  formError.textContent = "";

  if (!$("f-docente").value || !$("f-materia").value) {
    formError.textContent = "Selecciona docente y materia.";
    return;
  }
  if (!$("f-practica").value.trim() || !$("f-fecha").value) {
    formError.textContent = "La práctica y la fecha son obligatorias.";
    return;
  }

  const cuerpo = cabeceraComun();
  let url, metodo;

  if (modo === "nuevo") {
    const recetaId = $("f-receta").value;
    if (!recetaId) {
      formError.textContent = "Selecciona la receta desde la que armar el carrito.";
      return;
    }
    cuerpo.receta_id = parseInt(recetaId, 10);
    url = "/api/carritos";
    metodo = "POST";
  } else {
    try {
      cuerpo.reactivos = recolectarReactivos();
      cuerpo.materiales = recolectarMateriales();
    } catch (e) {
      formError.textContent = e.message;
      return;
    }
    url = `/api/carritos/${$("f-id").value}`;
    metodo = "PUT";
  }

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
    if (modo === "nuevo") {
      // Re-abrir en modo edición para ajustar líneas / añadir extras.
      const creado = await resp.json();
      mostrarMensaje("Carrito armado desde la receta. Ya puedes editar sus líneas.");
      abrirEditor(creado.id);
    } else {
      mostrarMensaje("Carrito actualizado.");
      cerrarEditor();
    }
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
$("btn-nuevo").addEventListener("click", () => abrirEditor());
$("btn-cancelar").addEventListener("click", cerrarEditor);
$("btn-add-reactivo").addEventListener("click", () => agregarLineaReactivo());
$("btn-add-material").addEventListener("click", () => agregarLineaMaterial());
$("f-receta").addEventListener("change", onRecetaChange);
$("f-grupos-cant").addEventListener("input", recomputarTotales);
$("btn-avanzar").addEventListener("click", avanzarEstado);
form.addEventListener("submit", guardar);
$("logout").addEventListener("click", () => Auth.logout());

(async () => {
  try {
    const resp = await Auth.authFetch("/api/auth/me");
    if (resp.ok) {
      const u = await resp.json();
      $("sesion-info").textContent = `Carritos · ${u.nombre_completo || u.nombre_usuario}`;
    }
  } catch {
    /* sin bloqueo */
  }
})();

cargarLista();
