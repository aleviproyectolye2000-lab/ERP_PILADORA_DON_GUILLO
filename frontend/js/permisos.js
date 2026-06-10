/* ----------------------------------------------------
   PERMISOS DEL SISTEMA - ERP PILADORA DON GUILLO
   Control de sesión, perfiles, módulos, permisos y CRUD
---------------------------------------------------- */

let permisosUsuarioActual = [];
let permisoModuloActual = null;
let temporizadorInactividadERP = null;
let observadorPermisosERP = null;

/* ----------------------------------------------------
   CONFIGURACIÓN GENERAL
---------------------------------------------------- */

const PAGINA_LOGIN_ERP = "index.html";
const PAGINA_DASHBOARD_ERP = "dashboard.html";
const TIEMPO_INACTIVIDAD_ERP = 5 * 60 * 1000; // 5 minutos

const PAGINAS_LIBRES_ERP = [
  "",
  "index.html",
  "login.html"
];

const PAGINAS_SIN_BLOQUEO_CRUD = [
  "dashboard.html"
];

/* ----------------------------------------------------
   DATOS DE SESIÓN
---------------------------------------------------- */

function obtenerIdUsuarioActual() {
  return localStorage.getItem("idUsuarioERP");
}

function obtenerIdAccesoActual() {
  return localStorage.getItem("idAccesoERP");
}

function obtenerUsuarioActualPermisos() {
  return localStorage.getItem("usuarioERP") || "Usuario no identificado";
}

function obtenerPerfilActualPermisos() {
  return localStorage.getItem("perfilERP") || "Perfil no identificado";
}

function obtenerPaginaActual() {
  return window.location.pathname.split("/").pop() || PAGINA_LOGIN_ERP;
}

function normalizarTextoPermisos(texto) {
  return String(texto || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function esAdministradorERP() {
  const perfil = normalizarTextoPermisos(obtenerPerfilActualPermisos());
  const usuario = normalizarTextoPermisos(obtenerUsuarioActualPermisos());

  return (
    perfil.includes("administrador") ||
    perfil === "admin" ||
    usuario === "admin" ||
    usuario === "administrador"
  );
}

function esGerenteERP() {
  const perfil = normalizarTextoPermisos(obtenerPerfilActualPermisos());

  return (
    perfil.includes("gerente") ||
    perfil.includes("directivo") ||
    perfil.includes("consulta")
  );
}

function usuarioTieneSesionERP() {
  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_LIBRES_ERP.includes(paginaActual)) {
    return true;
  }

  const idUsuario = obtenerIdUsuarioActual();
  const usuario = obtenerUsuarioActualPermisos();
  const perfil = obtenerPerfilActualPermisos();

  return Boolean(
    idUsuario &&
      usuario &&
      usuario !== "Usuario no identificado" &&
      perfil &&
      perfil !== "Perfil no identificado"
  );
}

/* ----------------------------------------------------
   API
---------------------------------------------------- */

async function permisosApiGet(ruta) {
  if (window.apiGet) {
    return await window.apiGet(ruta);
  }

  const respuesta = await fetch(`http://127.0.0.1:8000${ruta}`);
  const datos = await respuesta.json();

  if (!respuesta.ok) {
    throw new Error(datos.detail || "Error al consultar permisos.");
  }

  return datos;
}

async function permisosApiPost(ruta, datosEnviar) {
  if (window.apiPost) {
    return await window.apiPost(ruta, datosEnviar);
  }

  const respuesta = await fetch(`http://127.0.0.1:8000${ruta}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(datosEnviar),
  });

  const datos = await respuesta.json();

  if (!respuesta.ok) {
    throw new Error(datos.detail || "Error al enviar datos.");
  }

  return datos;
}

/* ----------------------------------------------------
   AUDITORÍA
---------------------------------------------------- */

async function registrarAuditoriaPermisos(modulo, accion, descripcion) {
  const idUsuario = obtenerIdUsuarioActual();

  if (!idUsuario) return;

  try {
    if (window.registrarAccionSistema) {
      await window.registrarAccionSistema(
        modulo,
        accion,
        descripcion,
        null,
        null
      );
      return;
    }

    await permisosApiPost("/api/auditoria/registrar-accion", {
      id_usuario: Number(idUsuario),
      modulo: modulo,
      accion: accion,
      descripcion: descripcion,
      tabla_afectada: null,
      id_registro_afectado: null,
    });
  } catch (error) {
    console.warn("No se pudo registrar auditoría de permisos:", error);
  }
}

/* ----------------------------------------------------
   VALIDACIÓN DE SESIÓN
---------------------------------------------------- */

function validarSesionPermisos() {
  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_LIBRES_ERP.includes(paginaActual)) {
    return true;
  }

  if (!usuarioTieneSesionERP()) {
    alert("Debe iniciar sesión para acceder al ERP.");
    window.location.href = PAGINA_LOGIN_ERP;
    return false;
  }

  return true;
}

function mostrarDatosUsuarioActual() {
  const usuarioActual = document.getElementById("usuarioActual");
  const perfilActual = document.getElementById("perfilActual");

  if (usuarioActual) {
    usuarioActual.textContent = obtenerUsuarioActualPermisos();
  }

  if (perfilActual) {
    perfilActual.textContent = obtenerPerfilActualPermisos();
  }
}

/* ----------------------------------------------------
   CIERRE DE SESIÓN
---------------------------------------------------- */

async function registrarCierreSesionPermisos(motivo) {
  const idAcceso = obtenerIdAccesoActual();
  const idUsuario = obtenerIdUsuarioActual();

  if (!idUsuario) return;

  try {
    await registrarAuditoriaPermisos(
      "Seguridad",
      "CIERRE_SESION",
      motivo || "Cierre de sesión del usuario."
    );

    if (idAcceso) {
      try {
        await permisosApiPost("/api/auditoria/cerrar-acceso", {
          id_acceso: Number(idAcceso),
          id_usuario: Number(idUsuario),
          motivo: motivo || "Cierre de sesión",
        });
      } catch (error) {
        console.warn("No se pudo registrar cierre de acceso:", error);
      }
    }
  } catch (error) {
    console.warn("No se pudo registrar cierre de sesión:", error);
  }
}

async function cerrarSesionPermisos(motivo) {
  await registrarCierreSesionPermisos(motivo || "Sesión cerrada.");

  localStorage.removeItem("idUsuarioERP");
  localStorage.removeItem("idAccesoERP");
  localStorage.removeItem("usuarioERP");
  localStorage.removeItem("perfilERP");
  localStorage.removeItem("permisosERP");
  localStorage.removeItem("ultimoMovimientoERP");

  window.location.href = PAGINA_LOGIN_ERP;
}

if (!window.cerrarSesion) {
  window.cerrarSesion = function () {
    cerrarSesionPermisos("Sesión cerrada manualmente por el usuario.");
  };
}

/* ----------------------------------------------------
   INACTIVIDAD
---------------------------------------------------- */

function reiniciarTemporizadorInactividadERP() {
  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_LIBRES_ERP.includes(paginaActual)) {
    return;
  }

  if (!usuarioTieneSesionERP()) {
    return;
  }

  localStorage.setItem("ultimoMovimientoERP", String(Date.now()));

  if (temporizadorInactividadERP) {
    clearTimeout(temporizadorInactividadERP);
  }

  temporizadorInactividadERP = setTimeout(function () {
    alert("La sesión se cerró automáticamente por inactividad.");
    cerrarSesionPermisos("Sesión cerrada automáticamente por inactividad.");
  }, TIEMPO_INACTIVIDAD_ERP);
}

function activarControlInactividadERP() {
  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_LIBRES_ERP.includes(paginaActual)) {
    return;
  }

  const eventos = [
    "mousemove",
    "mousedown",
    "keypress",
    "keydown",
    "click",
    "scroll",
    "touchstart"
  ];

  eventos.forEach((evento) => {
    document.addEventListener(evento, reiniciarTemporizadorInactividadERP, true);
  });

  reiniciarTemporizadorInactividadERP();
}

/* ----------------------------------------------------
   MÓDULOS Y PERMISOS
---------------------------------------------------- */

function obtenerNombreModuloPorPagina(pagina) {
  const mapa = {
    "dashboard.html": "Panel principal",
    "compras.html": "Compras y báscula",
    "inventario.html": "Inventario",
    "produccion.html": "Producción",
    "ventas.html": "Ventas",
    "talento_humano.html": "Talento Humano",
    "auditoria.html": "Auditoría",
    "seguridad.html": "Seguridad y Usuarios",
    "activos.html": "Activos",
    "reportes.html": "Reportes e IA",
  };

  return mapa[pagina] || pagina;
}

function obtenerPermisoPorPagina(pagina) {
  if (!Array.isArray(permisosUsuarioActual)) {
    return null;
  }

  const paginaNormalizada = normalizarTextoPermisos(pagina);
  const moduloPagina = normalizarTextoPermisos(obtenerNombreModuloPorPagina(pagina));

  return permisosUsuarioActual.find((permiso) => {
    const ruta = normalizarTextoPermisos(
      permiso.ruta_html ||
      permiso.ruta ||
      permiso.url ||
      ""
    );

    const nombreModulo = normalizarTextoPermisos(
      permiso.nombre_modulo ||
      permiso.modulo ||
      permiso.nombre ||
      ""
    );

    return (
      ruta === paginaNormalizada ||
      ruta.includes(paginaNormalizada) ||
      nombreModulo === moduloPagina ||
      moduloPagina.includes(nombreModulo) ||
      nombreModulo.includes(moduloPagina)
    );
  });
}

function construirPermisoTotalAdministrador() {
  return {
    puede_ver: true,
    puede_crear: true,
    puede_editar: true,
    puede_eliminar: true,
    puede_consultar: true,
    puede_generar_reporte: true,
  };
}

function construirPermisoConsultaGerente(pagina) {
  const paginaNormalizada = normalizarTextoPermisos(pagina);
  const esReporte = paginaNormalizada.includes("reporte");

  return {
    puede_ver: true,
    puede_crear: false,
    puede_editar: false,
    puede_eliminar: false,
    puede_consultar: true,
    puede_generar_reporte: esReporte,
  };
}

async function cargarPermisosUsuarioActual() {
  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_LIBRES_ERP.includes(paginaActual)) {
    return;
  }

  if (esAdministradorERP()) {
    permisoModuloActual = construirPermisoTotalAdministrador();
    permisosUsuarioActual = [];
    window.permisoModuloActualERP = permisoModuloActual;
    return;
  }

  if (esGerenteERP()) {
    permisoModuloActual = construirPermisoConsultaGerente(paginaActual);
  }

  const idUsuario = obtenerIdUsuarioActual();

  if (!idUsuario) {
    permisosUsuarioActual = [];
    return;
  }

  try {
    const permisos = await permisosApiGet(`/api/seguridad/permisos-usuario/${idUsuario}`);

    permisosUsuarioActual = Array.isArray(permisos) ? permisos : [];

    const permisoPagina = obtenerPermisoPorPagina(paginaActual);

    if (permisoPagina) {
      permisoModuloActual = permisoPagina;
    } else if (esGerenteERP()) {
      permisoModuloActual = construirPermisoConsultaGerente(paginaActual);
    } else {
      permisoModuloActual = {
        puede_ver: false,
        puede_crear: false,
        puede_editar: false,
        puede_eliminar: false,
        puede_consultar: false,
        puede_generar_reporte: false,
      };
    }

    window.permisosUsuarioActualERP = permisosUsuarioActual;
    window.permisoModuloActualERP = permisoModuloActual;
  } catch (error) {
    console.warn("No se pudieron cargar permisos del usuario:", error);

    if (esGerenteERP()) {
      permisoModuloActual = construirPermisoConsultaGerente(paginaActual);
    } else {
      permisoModuloActual = {
        puede_ver: false,
        puede_crear: false,
        puede_editar: false,
        puede_eliminar: false,
        puede_consultar: false,
        puede_generar_reporte: false,
      };
    }
  }
}

/* ----------------------------------------------------
   CONSULTA DE PERMISOS
---------------------------------------------------- */

function tienePermisoERP(accion) {
  if (esAdministradorERP()) {
    return true;
  }

  const permiso = permisoModuloActual || {};

  if (accion === "ver") {
    return permiso.puede_ver === true || permiso.puede_consultar === true;
  }

  if (accion === "crear") {
    return permiso.puede_crear === true;
  }

  if (accion === "editar") {
    return permiso.puede_editar === true;
  }

  if (accion === "eliminar") {
    return permiso.puede_eliminar === true;
  }

  if (accion === "consultar") {
    return permiso.puede_consultar === true || permiso.puede_ver === true;
  }

  if (accion === "reporte") {
    return permiso.puede_generar_reporte === true;
  }

  return false;
}

function obtenerAccionBotonERP(elemento) {
  const texto = normalizarTextoPermisos(elemento.textContent || "");
  const id = normalizarTextoPermisos(elemento.id || "");
  const clases = normalizarTextoPermisos(elemento.className || "");
  const onclick = normalizarTextoPermisos(elemento.getAttribute("onclick") || "");

  const combinado = `${texto} ${id} ${clases} ${onclick}`;

  if (
    combinado.includes("eliminar") ||
    combinado.includes("desactivar") ||
    combinado.includes("inactivar") ||
    combinado.includes("anular") ||
    combinado.includes("borrar") ||
    combinado.includes("suspender")
  ) {
    return "eliminar";
  }

  if (
    combinado.includes("editar") ||
    combinado.includes("actualizar") ||
    combinado.includes("modificar") ||
    combinado.includes("activar") ||
    combinado.includes("marcar salida") ||
    combinado.includes("cambiar contrasena") ||
    combinado.includes("cambiar contraseña") ||
    combinado.includes("permisos")
  ) {
    return "editar";
  }

  if (
    combinado.includes("guardar") ||
    combinado.includes("registrar") ||
    combinado.includes("crear") ||
    combinado.includes("generar") ||
    combinado.includes("marcar entrada")
  ) {
    if (
      combinado.includes("reporte") ||
      combinado.includes("pdf") ||
      combinado.includes("comprobante") ||
      combinado.includes("imprimir")
    ) {
      return "reporte";
    }

    return "crear";
  }

  if (
    combinado.includes("reporte") ||
    combinado.includes("pdf") ||
    combinado.includes("comprobante") ||
    combinado.includes("imprimir") ||
    combinado.includes("exportar")
  ) {
    return "reporte";
  }

  return null;
}

function bloquearElementoPermisos(elemento, motivo) {
  if (!elemento) return;

  elemento.disabled = true;
  elemento.classList.add("disabled");
  elemento.setAttribute("title", motivo || "No tiene permiso para realizar esta acción.");
  elemento.setAttribute("data-permiso-bloqueado", "true");
}

function desbloquearElementoPermisos(elemento) {
  if (!elemento) return;

  if (elemento.getAttribute("data-permiso-bloqueado") === "true") {
    elemento.disabled = false;
    elemento.classList.remove("disabled");
    elemento.removeAttribute("data-permiso-bloqueado");
  }
}

function aplicarPermisoAElemento(elemento, accion) {
  if (!accion) return;

  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_SIN_BLOQUEO_CRUD.includes(paginaActual)) {
    return;
  }

  if (esAdministradorERP()) {
    desbloquearElementoPermisos(elemento);
    return;
  }

  if (!tienePermisoERP(accion)) {
    let mensaje = "No tiene permiso para realizar esta acción.";

    if (accion === "crear") {
      mensaje = "No tiene permiso para crear o registrar información en este módulo.";
    }

    if (accion === "editar") {
      mensaje = "No tiene permiso para editar, actualizar o modificar información en este módulo.";
    }

    if (accion === "eliminar") {
      mensaje = "No tiene permiso para eliminar, anular, suspender, activar o desactivar información en este módulo.";
    }

    if (accion === "reporte") {
      mensaje = "No tiene permiso para generar reportes o comprobantes en este módulo.";
    }

    bloquearElementoPermisos(elemento, mensaje);
  } else {
    desbloquearElementoPermisos(elemento);
  }
}

function aplicarPermisosBotones() {
  const elementos = document.querySelectorAll(
    "button, input[type='submit'], input[type='button'], a.btn"
  );

  elementos.forEach((elemento) => {
    const accion = obtenerAccionBotonERP(elemento);
    aplicarPermisoAElemento(elemento, accion);
  });

  const crear = document.querySelectorAll(".permiso-crear");
  crear.forEach((elemento) => aplicarPermisoAElemento(elemento, "crear"));

  const editar = document.querySelectorAll(".permiso-editar");
  editar.forEach((elemento) => aplicarPermisoAElemento(elemento, "editar"));

  const eliminar = document.querySelectorAll(".permiso-eliminar");
  eliminar.forEach((elemento) => aplicarPermisoAElemento(elemento, "eliminar"));

  const reporte = document.querySelectorAll(".permiso-reporte");
  reporte.forEach((elemento) => aplicarPermisoAElemento(elemento, "reporte"));
}

function bloquearFormulariosSinPermiso() {
  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_SIN_BLOQUEO_CRUD.includes(paginaActual)) {
    return;
  }

  if (esAdministradorERP()) {
    return;
  }

  const formularios = document.querySelectorAll("form");

  formularios.forEach((formulario) => {
    if (formulario.getAttribute("data-permisos-listener") === "true") {
      return;
    }

    formulario.setAttribute("data-permisos-listener", "true");

    formulario.addEventListener(
      "submit",
      function (event) {
        const idFormulario = normalizarTextoPermisos(formulario.id || "");
        const textoFormulario = normalizarTextoPermisos(formulario.textContent || "");

        let accion = "crear";

        if (
          idFormulario.includes("editar") ||
          idFormulario.includes("actualizar") ||
          textoFormulario.includes("actualizar")
        ) {
          accion = "editar";
        }

        if (
          idFormulario.includes("reporte") ||
          textoFormulario.includes("reporte") ||
          textoFormulario.includes("comprobante")
        ) {
          accion = "reporte";
        }

        if (!tienePermisoERP(accion)) {
          event.preventDefault();
          event.stopImmediatePropagation();

          if (accion === "crear") {
            alert("No tiene permiso para registrar información en este módulo.");
          } else if (accion === "editar") {
            alert("No tiene permiso para actualizar información en este módulo.");
          } else if (accion === "reporte") {
            alert("No tiene permiso para generar reportes o comprobantes.");
          } else {
            alert("No tiene permiso para realizar esta acción.");
          }

          return false;
        }

        return true;
      },
      true
    );
  });
}

function bloquearInputsModoConsulta() {
  if (esAdministradorERP()) {
    return;
  }

  const soloConsulta =
    tienePermisoERP("ver") &&
    tienePermisoERP("consultar") &&
    !tienePermisoERP("crear") &&
    !tienePermisoERP("editar") &&
    !tienePermisoERP("eliminar");

  if (!soloConsulta) {
    return;
  }

  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_SIN_BLOQUEO_CRUD.includes(paginaActual)) {
    return;
  }

  const campos = document.querySelectorAll(
    "form input:not([type='hidden']), form select, form textarea"
  );

  campos.forEach((campo) => {
    const tipo = normalizarTextoPermisos(campo.type || "");
    const id = normalizarTextoPermisos(campo.id || "");
    const placeholder = normalizarTextoPermisos(campo.placeholder || "");

    const pareceFiltro =
      id.includes("buscar") ||
      id.includes("filtro") ||
      placeholder.includes("buscar") ||
      placeholder.includes("filtrar");

    if (pareceFiltro) {
      return;
    }

    if (tipo === "button" || tipo === "submit" || tipo === "reset") {
      return;
    }

    campo.disabled = true;
    campo.setAttribute(
      "title",
      "Modo consulta: este usuario no puede modificar datos en este módulo."
    );
  });
}

function protegerAccionesGlobales() {
  const nombresFunciones = [
    ["eliminar", "eliminar"],
    ["desactivar", "eliminar"],
    ["inactivar", "eliminar"],
    ["anular", "eliminar"],
    ["suspender", "eliminar"],
    ["activar", "editar"],
    ["editar", "editar"],
    ["actualizar", "editar"],
    ["marcarSalida", "editar"],
    ["guardar", "crear"],
    ["registrar", "crear"],
    ["marcarEntrada", "crear"],
    ["generar", "crear"],
  ];

  Object.keys(window).forEach((nombreFuncion) => {
    const valor = window[nombreFuncion];

    if (typeof valor !== "function") {
      return;
    }

    const nombreNormalizado = normalizarTextoPermisos(nombreFuncion);

    const regla = nombresFunciones.find(([texto]) => {
      return nombreNormalizado.includes(texto);
    });

    if (!regla) {
      return;
    }

    const accion = regla[1];

    if (valor.__protegidaPorPermisosERP) {
      return;
    }

    const funcionOriginal = valor;

    const funcionProtegida = function (...args) {
      if (!tienePermisoERP(accion)) {
        if (accion === "crear") {
          alert("No tiene permiso para crear o registrar información en este módulo.");
        } else if (accion === "editar") {
          alert("No tiene permiso para editar o actualizar información en este módulo.");
        } else if (accion === "eliminar") {
          alert("No tiene permiso para eliminar, anular, activar, suspender o desactivar información en este módulo.");
        } else {
          alert("No tiene permiso para realizar esta acción.");
        }

        return null;
      }

      return funcionOriginal.apply(this, args);
    };

    funcionProtegida.__protegidaPorPermisosERP = true;
    window[nombreFuncion] = funcionProtegida;
  });
}

/* ----------------------------------------------------
   PROTECCIÓN DE MÓDULOS
---------------------------------------------------- */

function usuarioPuedeEntrarPaginaActual() {
  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_LIBRES_ERP.includes(paginaActual)) {
    return true;
  }

  if (paginaActual === PAGINA_DASHBOARD_ERP) {
    return true;
  }

  if (esAdministradorERP()) {
    return true;
  }

  if (paginaActual === "seguridad.html") {
    return false;
  }

  if (esGerenteERP()) {
    return true;
  }

  return (
    permisoModuloActual &&
    (
      permisoModuloActual.puede_ver === true ||
      permisoModuloActual.puede_consultar === true ||
      permisoModuloActual.puede_crear === true ||
      permisoModuloActual.puede_editar === true ||
      permisoModuloActual.puede_eliminar === true ||
      permisoModuloActual.puede_generar_reporte === true
    )
  );
}

function aplicarProteccionPaginaActual() {
  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_LIBRES_ERP.includes(paginaActual)) {
    return;
  }

  if (paginaActual === "seguridad.html" && !esAdministradorERP()) {
    alert("Solo el administrador puede acceder al módulo de Seguridad y Usuarios.");
    window.location.href = PAGINA_DASHBOARD_ERP;
    return;
  }

  if (!usuarioPuedeEntrarPaginaActual()) {
    alert("No tiene permisos para acceder a este módulo.");
    window.location.href = PAGINA_DASHBOARD_ERP;
    return;
  }

  aplicarPermisosBotones();
  bloquearFormulariosSinPermiso();
  bloquearInputsModoConsulta();

  setTimeout(function () {
    aplicarPermisosBotones();
    bloquearFormulariosSinPermiso();
    bloquearInputsModoConsulta();
    protegerAccionesGlobales();
  }, 800);

  setTimeout(function () {
    aplicarPermisosBotones();
    bloquearFormulariosSinPermiso();
    bloquearInputsModoConsulta();
    protegerAccionesGlobales();
  }, 1800);
}

/* ----------------------------------------------------
   OBSERVADOR PARA BOTONES DINÁMICOS
---------------------------------------------------- */

function activarObservadorPermisos() {
  if (observadorPermisosERP) {
    observadorPermisosERP.disconnect();
  }

  observadorPermisosERP = new MutationObserver(function () {
    aplicarPermisosBotones();
    bloquearFormulariosSinPermiso();
    bloquearInputsModoConsulta();
  });

  observadorPermisosERP.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

/* ----------------------------------------------------
   MENSAJES Y AYUDAS GLOBALES
---------------------------------------------------- */

function mostrarResumenPermisoActual() {
  const paginaActual = obtenerPaginaActual();

  if (PAGINAS_LIBRES_ERP.includes(paginaActual)) {
    return;
  }

  console.log("Usuario actual:", obtenerUsuarioActualPermisos());
  console.log("Perfil actual:", obtenerPerfilActualPermisos());
  console.log("Página actual:", paginaActual);
  console.log("Permiso módulo actual:", permisoModuloActual);
}

function obtenerPermisoActualERP() {
  return permisoModuloActual;
}

function obtenerPermisosUsuarioERP() {
  return permisosUsuarioActual;
}

/* ----------------------------------------------------
   INICIALIZACIÓN
---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  const paginaActual = obtenerPaginaActual();

  if (!validarSesionPermisos()) {
    return;
  }

  mostrarDatosUsuarioActual();

  if (PAGINAS_LIBRES_ERP.includes(paginaActual)) {
    return;
  }

  await cargarPermisosUsuarioActual();

  aplicarProteccionPaginaActual();
  activarObservadorPermisos();
  activarControlInactividadERP();
  mostrarResumenPermisoActual();

  await registrarAuditoriaPermisos(
    obtenerNombreModuloPorPagina(paginaActual),
    "ACCESO_MODULO",
    `El usuario ${obtenerUsuarioActualPermisos()} ingresó al módulo ${obtenerNombreModuloPorPagina(paginaActual)}.`
  );
});

/* ----------------------------------------------------
   EXPORTAR FUNCIONES GLOBALES
---------------------------------------------------- */

window.esAdministradorERP = esAdministradorERP;
window.esGerenteERP = esGerenteERP;
window.tienePermisoERP = tienePermisoERP;
window.obtenerPermisoActualERP = obtenerPermisoActualERP;
window.obtenerPermisosUsuarioERP = obtenerPermisosUsuarioERP;
window.cerrarSesionPermisos = cerrarSesionPermisos;