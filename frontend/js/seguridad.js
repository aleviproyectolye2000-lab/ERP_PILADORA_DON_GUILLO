/* ---------------------------------------------------- */
/* SEGURIDAD Y USUARIOS - ERP PILADORA DON GUILLO       */
/* Gestión de usuarios, perfiles, módulos y permisos    */
/* Validaciones reforzadas y reglas por perfil          */
/* ---------------------------------------------------- */

let usuariosSeguridad = [];
let perfilesSeguridad = [];
let modulosSeguridad = [];
let permisosUsuarioSeleccionado = [];

const API_SEGURIDAD_RENDER = "https://erp-piladora-don-guillo.onrender.com";

/* ---------------------------------------------------- */
/* CONSUMO DE API                                       */
/* ---------------------------------------------------- */

async function seguridadApiGet(ruta) {
  if (window.apiGet) {
    return await window.apiGet(ruta);
  }

  const respuesta = await fetch(`${API_SEGURIDAD_RENDER}${ruta}`);
  const datos = await respuesta.json();

  if (!respuesta.ok) {
    throw new Error(datos.detail || "Error al consultar datos.");
  }

  return datos;
}

async function seguridadApiPost(ruta, datos) {
  if (window.apiPost) {
    return await window.apiPost(ruta, datos);
  }

  const respuesta = await fetch(`${API_SEGURIDAD_RENDER}${ruta}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(datos),
  });

  const resultado = await respuesta.json();

  if (!respuesta.ok) {
    throw new Error(resultado.detail || "Error al guardar datos.");
  }

  return resultado;
}

async function seguridadApiPut(ruta, datos) {
  if (window.apiPut) {
    return await window.apiPut(ruta, datos);
  }

  const respuesta = await fetch(`${API_SEGURIDAD_RENDER}${ruta}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(datos),
  });

  const resultado = await respuesta.json();

  if (!respuesta.ok) {
    throw new Error(resultado.detail || "Error al actualizar datos.");
  }

  return resultado;
}

async function seguridadApiPatch(ruta, datos) {
  if (window.apiPatch) {
    return await window.apiPatch(ruta, datos);
  }

  const respuesta = await fetch(`${API_SEGURIDAD_RENDER}${ruta}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(datos),
  });

  const resultado = await respuesta.json();

  if (!respuesta.ok) {
    throw new Error(resultado.detail || "Error al actualizar datos.");
  }

  return resultado;
}

async function seguridadApiDelete(ruta) {
  if (window.apiDelete) {
    return await window.apiDelete(ruta);
  }

  const respuesta = await fetch(`${API_SEGURIDAD_RENDER}${ruta}`, {
    method: "DELETE",
  });

  const resultado = await respuesta.json();

  if (!respuesta.ok) {
    throw new Error(resultado.detail || "Error al eliminar datos.");
  }

  return resultado;
}

/* ---------------------------------------------------- */
/* UTILIDADES GENERALES                                 */
/* ---------------------------------------------------- */

function obtenerIdAdminActual() {
  return Number(localStorage.getItem("idUsuarioERP")) || null;
}

function limpiarTextoSeguridad(texto) {
  return String(texto || "").trim().replace(/\s+/g, " ");
}

function normalizarTextoSeguridad(texto) {
  return String(texto || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function escaparHTMLSeguridad(valor) {
  return String(valor ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function mostrarErrorSeguridad(error, mensajeDefecto) {
  if (error && error.message) {
    alert(error.message);
    return;
  }

  alert(mensajeDefecto || "Ocurrió un error en el módulo de seguridad.");
}

function usuarioActualEsAdministradorSeguridad() {
  if (window.esAdministradorERP) {
    return window.esAdministradorERP();
  }

  const perfil = normalizarTextoSeguridad(localStorage.getItem("perfilERP"));

  return perfil.includes("administrador") || perfil === "admin";
}

function esPerfilAdministradorNombre(nombrePerfil) {
  const perfil = normalizarTextoSeguridad(nombrePerfil);
  return perfil.includes("administrador") || perfil === "admin";
}

function esPerfilGerenteNombre(nombrePerfil) {
  const perfil = normalizarTextoSeguridad(nombrePerfil);
  return perfil.includes("gerente") || perfil.includes("directivo") || perfil.includes("direccion");
}

function esPerfilOperativoNombre(nombrePerfil) {
  const perfil = normalizarTextoSeguridad(nombrePerfil);

  return (
    !esPerfilAdministradorNombre(nombrePerfil) &&
    !esPerfilGerenteNombre(nombrePerfil) &&
    (
      perfil.includes("operador") ||
      perfil.includes("compras") ||
      perfil.includes("bascula") ||
      perfil.includes("ventas") ||
      perfil.includes("inventario") ||
      perfil.includes("talento") ||
      perfil.includes("produccion") ||
      perfil.includes("activos") ||
      perfil !== ""
    )
  );
}

function esModuloReportesIA(modulo) {
  const nombre = normalizarTextoSeguridad(modulo?.nombre_modulo || "");
  const ruta = normalizarTextoSeguridad(modulo?.ruta_html || "");

  return (
    nombre.includes("reporte") ||
    nombre.includes("ia") ||
    nombre.includes("inteligencia") ||
    ruta.includes("reporte") ||
    ruta.includes("ia")
  );
}

function esModuloSeguridadSistema(modulo) {
  const nombre = normalizarTextoSeguridad(modulo?.nombre_modulo || "");
  const ruta = normalizarTextoSeguridad(modulo?.ruta_html || "");

  return (
    nombre.includes("seguridad") ||
    nombre.includes("usuario") ||
    ruta.includes("seguridad")
  );
}

function obtenerPerfilPorId(idPerfil) {
  return perfilesSeguridad.find((perfil) => {
    return Number(perfil.id_perfil) === Number(idPerfil);
  });
}

function obtenerNombrePerfilPorId(idPerfil) {
  const perfil = obtenerPerfilPorId(idPerfil);
  return perfil ? perfil.nombre_perfil : "";
}

function obtenerPerfilUsuario(usuario) {
  if (!usuario) return "";
  return usuario.nombre_perfil || usuario.perfil || obtenerNombrePerfilPorId(usuario.id_perfil) || "";
}

function esUsuarioAdminPrincipal(usuario) {
  if (!usuario) return false;

  const nombreUsuario = normalizarTextoSeguridad(usuario.usuario);
  const nombrePerfil = normalizarTextoSeguridad(obtenerPerfilUsuario(usuario));

  return (
    Number(usuario.id_usuario) === 1 ||
    nombreUsuario === "admin" ||
    nombreUsuario === "administrador" ||
    (nombrePerfil.includes("administrador") && nombreUsuario === "admin")
  );
}

function usuarioEditadoEsAdminPrincipal() {
  const idUsuarioEditar = document.getElementById("idUsuarioEditar")?.value;

  if (!idUsuarioEditar) {
    return false;
  }

  const usuario = usuariosSeguridad.find((item) => {
    return Number(item.id_usuario) === Number(idUsuarioEditar);
  });

  return esUsuarioAdminPrincipal(usuario);
}

function validarSoloLetrasSeguridad(texto) {
  return /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(texto);
}

function validarUsuarioSistemaSeguridad(usuario) {
  return /^[A-Za-z0-9._-]{4,30}$/.test(usuario);
}

function validarCorreoSeguridad(correo) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(correo);
}

function validarContrasenaSeguridad(contrasena) {
  return /^(?=.*[A-Za-z])(?=.*\d).{8,40}$/.test(contrasena);
}

function existeUsuarioDuplicado(nombreUsuario, idUsuarioEditar) {
  const usuarioNormalizado = normalizarTextoSeguridad(nombreUsuario);

  return usuariosSeguridad.some((usuario) => {
    const idActual = String(usuario.id_usuario);
    const idEditar = String(idUsuarioEditar || "");
    const usuarioActual = normalizarTextoSeguridad(usuario.usuario);

    return usuarioActual === usuarioNormalizado && idActual !== idEditar;
  });
}

function existeCorreoDuplicado(correo, idUsuarioEditar) {
  if (!correo) return false;

  const correoNormalizado = normalizarTextoSeguridad(correo);

  return usuariosSeguridad.some((usuario) => {
    const idActual = String(usuario.id_usuario);
    const idEditar = String(idUsuarioEditar || "");
    const correoActual = normalizarTextoSeguridad(usuario.correo);

    return correoActual === correoNormalizado && idActual !== idEditar;
  });
}

function activarMostrarContrasenasSeguridad() {
  const checkContrasenaUsuario = document.getElementById("mostrarContrasenaUsuario");
  const inputContrasenaUsuario = document.getElementById("contrasenaUsuario");

  if (checkContrasenaUsuario && inputContrasenaUsuario) {
    checkContrasenaUsuario.addEventListener("change", function () {
      inputContrasenaUsuario.type = checkContrasenaUsuario.checked ? "text" : "password";
    });
  }

  const checkNuevaContrasena = document.getElementById("mostrarNuevaContrasena");
  const inputNuevaContrasena = document.getElementById("nuevaContrasena");

  if (checkNuevaContrasena && inputNuevaContrasena) {
    checkNuevaContrasena.addEventListener("change", function () {
      inputNuevaContrasena.type = checkNuevaContrasena.checked ? "text" : "password";
    });
  }
}

function aplicarFiltrosEscrituraSeguridad() {
  const nombresUsuario = document.getElementById("nombresUsuario");
  const apellidosUsuario = document.getElementById("apellidosUsuario");
  const usuarioSistema = document.getElementById("usuarioSistema");
  const correoUsuario = document.getElementById("correoUsuario");

  if (nombresUsuario) {
    nombresUsuario.addEventListener("input", function () {
      this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g, "");
      this.value = this.value.replace(/\s{2,}/g, " ");
    });
  }

  if (apellidosUsuario) {
    apellidosUsuario.addEventListener("input", function () {
      this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g, "");
      this.value = this.value.replace(/\s{2,}/g, " ");
    });
  }

  if (usuarioSistema) {
    usuarioSistema.addEventListener("input", function () {
      this.value = this.value.replace(/\s/g, "");
      this.value = this.value.replace(/[^A-Za-z0-9._-]/g, "");
      this.value = this.value.slice(0, 30).toLowerCase();
    });
  }

  if (correoUsuario) {
    correoUsuario.addEventListener("input", function () {
      this.value = this.value.replace(/\s/g, "").slice(0, 100).toLowerCase();
    });
  }
}

function bloquearCamposAdminPrincipal(bloquear) {
  const usuarioSistema = document.getElementById("usuarioSistema");
  const perfilUsuario = document.getElementById("perfilUsuario");
  const estadoUsuario = document.getElementById("estadoUsuario");

  if (usuarioSistema) {
    usuarioSistema.readOnly = bloquear;
  }

  if (perfilUsuario) {
    perfilUsuario.disabled = bloquear;
  }

  if (estadoUsuario) {
    estadoUsuario.disabled = bloquear;
  }
}

function limpiarFormularioUsuario() {
  const idUsuarioEditar = document.getElementById("idUsuarioEditar");
  const nombresUsuario = document.getElementById("nombresUsuario");
  const apellidosUsuario = document.getElementById("apellidosUsuario");
  const usuarioSistema = document.getElementById("usuarioSistema");
  const correoUsuario = document.getElementById("correoUsuario");
  const contrasenaUsuario = document.getElementById("contrasenaUsuario");
  const perfilUsuario = document.getElementById("perfilUsuario");
  const estadoUsuario = document.getElementById("estadoUsuario");

  if (idUsuarioEditar) idUsuarioEditar.value = "";
  if (nombresUsuario) nombresUsuario.value = "";
  if (apellidosUsuario) apellidosUsuario.value = "";
  if (usuarioSistema) usuarioSistema.value = "";
  if (correoUsuario) correoUsuario.value = "";

  if (contrasenaUsuario) {
    contrasenaUsuario.value = "";
    contrasenaUsuario.type = "password";
    contrasenaUsuario.required = true;
  }

  if (perfilUsuario) {
    perfilUsuario.value = "";
    perfilUsuario.disabled = false;
  }

  if (estadoUsuario) {
    estadoUsuario.value = "true";
    estadoUsuario.disabled = false;
  }

  const mostrarContrasenaUsuario = document.getElementById("mostrarContrasenaUsuario");
  if (mostrarContrasenaUsuario) {
    mostrarContrasenaUsuario.checked = false;
  }

  const btnGuardar = document.getElementById("btnGuardarUsuario");
  if (btnGuardar) {
    btnGuardar.textContent = "Guardar";
  }

  bloquearCamposAdminPrincipal(false);
}

function limpiarSeleccionPermisos() {
  const idUsuarioPermisos = document.getElementById("idUsuarioPermisos");
  const usuarioPermisosSeleccionado = document.getElementById("usuarioPermisosSeleccionado");
  const tablaPermisos = document.getElementById("tablaPermisos");

  if (idUsuarioPermisos) idUsuarioPermisos.value = "";

  if (usuarioPermisosSeleccionado) {
    usuarioPermisosSeleccionado.textContent = "Ningún usuario seleccionado";
  }

  if (tablaPermisos) {
    tablaPermisos.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted">
          Seleccione un usuario para cargar sus permisos.
        </td>
      </tr>
    `;
  }

  permisosUsuarioSeleccionado = [];
}

function limpiarCambioContrasena() {
  const idUsuarioContrasena = document.getElementById("idUsuarioContrasena");
  const usuarioContrasenaTexto = document.getElementById("usuarioContrasenaTexto");
  const nuevaContrasena = document.getElementById("nuevaContrasena");

  if (idUsuarioContrasena) idUsuarioContrasena.value = "";
  if (usuarioContrasenaTexto) usuarioContrasenaTexto.value = "";

  if (nuevaContrasena) {
    nuevaContrasena.value = "";
    nuevaContrasena.type = "password";
  }

  const mostrarNuevaContrasena = document.getElementById("mostrarNuevaContrasena");
  if (mostrarNuevaContrasena) {
    mostrarNuevaContrasena.checked = false;
  }
}

function mostrarEstadoUsuario(estado) {
  if (estado === true) {
    return `<span class="badge-estado-activo">Activo</span>`;
  }

  return `<span class="badge-estado-inactivo">Inactivo</span>`;
}

function validarCampoTexto(valor, nombreCampo) {
  if (!valor || valor.trim() === "") {
    alert(`Debe ingresar ${nombreCampo}.`);
    return false;
  }

  return true;
}

/* ---------------------------------------------------- */
/* AUDITORÍA FRONTEND OPCIONAL                          */
/* ---------------------------------------------------- */

async function registrarAccionSeguridadFrontend(accion, descripcion, tablaAfectada = null, idRegistroAfectado = null) {
  if (window.registrarAccionSistema) {
    try {
      await window.registrarAccionSistema(
        "Seguridad y Usuarios",
        accion,
        descripcion,
        tablaAfectada,
        idRegistroAfectado
      );
    } catch (error) {
      console.warn("No se pudo registrar auditoría desde seguridad.js:", error);
    }
  }
}

/* ---------------------------------------------------- */
/* CARGAR DATOS INICIALES                               */
/* ---------------------------------------------------- */

async function cargarPerfilesSeguridad() {
  perfilesSeguridad = await seguridadApiGet("/api/seguridad/perfiles");

  const perfilUsuario = document.getElementById("perfilUsuario");

  if (!perfilUsuario) {
    return;
  }

  perfilUsuario.innerHTML = `<option value="">Seleccione</option>`;

  perfilesSeguridad.forEach((perfil) => {
    const option = document.createElement("option");
    option.value = perfil.id_perfil;
    option.textContent = perfil.nombre_perfil;
    perfilUsuario.appendChild(option);
  });
}

async function cargarModulosSeguridad() {
  modulosSeguridad = await seguridadApiGet("/api/seguridad/modulos");

  const totalModulos = document.getElementById("totalModulos");

  if (totalModulos) {
    totalModulos.textContent = modulosSeguridad.length;
  }
}

async function cargarUsuariosSeguridad() {
  usuariosSeguridad = await seguridadApiGet("/api/seguridad/usuarios");

  if (!Array.isArray(usuariosSeguridad)) {
    usuariosSeguridad = [];
  }

  renderizarUsuariosSeguridad();
  actualizarTarjetasSeguridad();
}

async function cargarDatosSeguridad() {
  try {
    await cargarPerfilesSeguridad();
    await cargarModulosSeguridad();
    await cargarUsuariosSeguridad();
  } catch (error) {
    alert(`Error al cargar datos de seguridad: ${error.message}`);
  }
}

/* ---------------------------------------------------- */
/* TARJETAS RESUMEN                                     */
/* ---------------------------------------------------- */

function actualizarTarjetasSeguridad() {
  const totalUsuarios = document.getElementById("totalUsuarios");
  const usuariosActivos = document.getElementById("usuariosActivos");
  const usuariosInactivos = document.getElementById("usuariosInactivos");

  const total = usuariosSeguridad.length;
  const activos = usuariosSeguridad.filter((u) => u.estado === true).length;
  const inactivos = usuariosSeguridad.filter((u) => u.estado === false).length;

  if (totalUsuarios) totalUsuarios.textContent = total;
  if (usuariosActivos) usuariosActivos.textContent = activos;
  if (usuariosInactivos) usuariosInactivos.textContent = inactivos;
}

/* ---------------------------------------------------- */
/* RENDERIZAR USUARIOS                                  */
/* ---------------------------------------------------- */

function renderizarUsuariosSeguridad() {
  const tablaUsuarios = document.getElementById("tablaUsuarios");

  if (!tablaUsuarios) {
    return;
  }

  if (!usuariosSeguridad || usuariosSeguridad.length === 0) {
    tablaUsuarios.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-muted">
          No existen usuarios registrados.
        </td>
      </tr>
    `;
    return;
  }

  tablaUsuarios.innerHTML = "";

  usuariosSeguridad.forEach((usuario) => {
    const fila = document.createElement("tr");

    const adminPrincipal = esUsuarioAdminPrincipal(usuario);
    const nombrePerfil = obtenerPerfilUsuario(usuario);
    const textoBotonEstado = usuario.estado ? "Desactivar" : "Activar";
    const claseBotonEstado = usuario.estado ? "btn-danger" : "btn-success";

    let botonEstado = `
      <button
        type="button"
        class="btn btn-sm ${claseBotonEstado}"
        onclick="cambiarEstadoUsuarioSeguridad(${Number(usuario.id_usuario)}, ${!usuario.estado})"
      >
        ${textoBotonEstado}
      </button>
    `;

    if (adminPrincipal) {
      botonEstado = `
        <button
          type="button"
          class="btn btn-sm btn-outline-secondary"
          disabled
          title="El administrador principal no puede ser desactivado."
        >
          Protegido
        </button>
      `;
    }

    fila.innerHTML = `
      <td>${escaparHTMLSeguridad(usuario.id_usuario)}</td>
      <td>${escaparHTMLSeguridad(usuario.nombres || "-")}</td>
      <td>${escaparHTMLSeguridad(usuario.apellidos || "-")}</td>
      <td>
        ${escaparHTMLSeguridad(usuario.usuario || "-")}
        ${
          adminPrincipal
            ? `<span class="badge bg-dark ms-1">Admin principal</span>`
            : ""
        }
      </td>
      <td>${escaparHTMLSeguridad(usuario.correo || "-")}</td>
      <td>
        <span class="badge bg-primary">
          ${escaparHTMLSeguridad(nombrePerfil || "-")}
        </span>
      </td>
      <td>${mostrarEstadoUsuario(usuario.estado)}</td>
      <td>
        <div class="d-flex flex-wrap gap-1">
          <button
            type="button"
            class="btn btn-sm btn-warning"
            onclick="editarUsuarioSeguridad(${Number(usuario.id_usuario)})"
          >
            Editar
          </button>

          <button
            type="button"
            class="btn btn-sm btn-info text-white"
            onclick="seleccionarPermisosUsuario(${Number(usuario.id_usuario)})"
          >
            Permisos
          </button>

          <button
            type="button"
            class="btn btn-sm btn-secondary"
            onclick="seleccionarCambioContrasena(${Number(usuario.id_usuario)})"
          >
            Contraseña
          </button>

          ${botonEstado}
        </div>
      </td>
    `;

    tablaUsuarios.appendChild(fila);
  });
}

/* ---------------------------------------------------- */
/* VALIDAR USUARIO                                      */
/* ---------------------------------------------------- */

function obtenerDatosFormularioUsuario() {
  const idUsuarioEditar = document.getElementById("idUsuarioEditar")?.value || "";
  const nombres = limpiarTextoSeguridad(document.getElementById("nombresUsuario")?.value);
  const apellidos = limpiarTextoSeguridad(document.getElementById("apellidosUsuario")?.value);
  const usuario = limpiarTextoSeguridad(document.getElementById("usuarioSistema")?.value).toLowerCase();
  const correo = limpiarTextoSeguridad(document.getElementById("correoUsuario")?.value).toLowerCase();
  const contrasena = document.getElementById("contrasenaUsuario")?.value.trim() || "";
  const idPerfil = document.getElementById("perfilUsuario")?.value || "";
  const estado = document.getElementById("estadoUsuario")?.value === "true";

  return {
    idUsuarioEditar,
    nombres,
    apellidos,
    usuario,
    correo,
    contrasena,
    idPerfil,
    estado,
  };
}

function validarFormularioUsuarioSeguridad(datos) {
  const esEdicion = Boolean(datos.idUsuarioEditar);
  const adminPrincipal = usuarioEditadoEsAdminPrincipal();

  if (!validarCampoTexto(datos.nombres, "los nombres")) return false;
  if (!validarCampoTexto(datos.apellidos, "los apellidos")) return false;
  if (!validarCampoTexto(datos.usuario, "el nombre de usuario")) return false;

  if (!validarSoloLetrasSeguridad(datos.nombres)) {
    alert("Los nombres solo deben contener letras y espacios. No se permiten números.");
    return false;
  }

  if (datos.nombres.length < 2 || datos.nombres.length > 60) {
    alert("Los nombres deben tener entre 2 y 60 caracteres.");
    return false;
  }

  if (!validarSoloLetrasSeguridad(datos.apellidos)) {
    alert("Los apellidos solo deben contener letras y espacios. No se permiten números.");
    return false;
  }

  if (datos.apellidos.length < 2 || datos.apellidos.length > 60) {
    alert("Los apellidos deben tener entre 2 y 60 caracteres.");
    return false;
  }

  if (!validarUsuarioSistemaSeguridad(datos.usuario)) {
    alert(
      "El usuario debe tener entre 4 y 30 caracteres. Use solo letras, números, punto, guion o guion bajo. No use espacios."
    );
    return false;
  }

  if (existeUsuarioDuplicado(datos.usuario, datos.idUsuarioEditar)) {
    alert("Ya existe otro usuario registrado con ese nombre de usuario.");
    return false;
  }

  if (!datos.correo) {
    alert("Debe ingresar el correo del usuario.");
    return false;
  }

  if (!validarCorreoSeguridad(datos.correo)) {
    alert("Ingrese un correo electrónico válido. Ejemplo: usuario@donguillo.com");
    return false;
  }

  if (existeCorreoDuplicado(datos.correo, datos.idUsuarioEditar)) {
    alert("Ya existe otro usuario registrado con ese correo electrónico.");
    return false;
  }

  if (!datos.idPerfil) {
    alert("Debe seleccionar un perfil.");
    return false;
  }

  const nombrePerfilSeleccionado = obtenerNombrePerfilPorId(datos.idPerfil);

  if (adminPrincipal) {
    const usuarioOriginal = usuariosSeguridad.find((usuario) => {
      return Number(usuario.id_usuario) === Number(datos.idUsuarioEditar);
    });

    if (normalizarTextoSeguridad(datos.usuario) !== normalizarTextoSeguridad(usuarioOriginal.usuario)) {
      alert("No se permite cambiar el nombre de usuario del administrador principal.");
      return false;
    }

    if (!datos.estado) {
      alert("No se permite dejar inactivo al administrador principal.");
      return false;
    }

    if (!esPerfilAdministradorNombre(nombrePerfilSeleccionado)) {
      alert("No se permite cambiar el perfil del administrador principal.");
      return false;
    }
  }

  if (!esEdicion && !validarCampoTexto(datos.contrasena, "la contraseña")) {
    return false;
  }

  if (!esEdicion && !validarContrasenaSeguridad(datos.contrasena)) {
    alert("La contraseña debe tener entre 8 y 40 caracteres, al menos una letra y al menos un número.");
    return false;
  }

  if (esEdicion && datos.contrasena) {
    alert("Para cambiar una contraseña use la sección 'Cambio de contraseña'.");
    return false;
  }

  return true;
}

/* ---------------------------------------------------- */
/* CREAR / ACTUALIZAR USUARIO                           */
/* ---------------------------------------------------- */

async function guardarUsuarioSeguridad(event) {
  event.preventDefault();

  const datos = obtenerDatosFormularioUsuario();

  if (!validarFormularioUsuarioSeguridad(datos)) {
    return;
  }

  try {
    let idUsuarioGuardado = null;

    if (datos.idUsuarioEditar) {
      const datosActualizar = {
        id_perfil: Number(datos.idPerfil),
        nombres: datos.nombres,
        apellidos: datos.apellidos,
        usuario: datos.usuario,
        correo: datos.correo || null,
        estado: datos.estado,
        id_admin: obtenerIdAdminActual(),
      };

      await seguridadApiPut(
        `/api/seguridad/usuarios/${datos.idUsuarioEditar}`,
        datosActualizar
      );

      idUsuarioGuardado = Number(datos.idUsuarioEditar);
      alert("Usuario actualizado correctamente.");
    } else {
      const datosCrear = {
        id_perfil: Number(datos.idPerfil),
        nombres: datos.nombres,
        apellidos: datos.apellidos,
        usuario: datos.usuario,
        correo: datos.correo || null,
        contrasena: datos.contrasena,
        estado: datos.estado,
        id_admin: obtenerIdAdminActual(),
      };

      const respuesta = await seguridadApiPost("/api/seguridad/usuarios", datosCrear);
      idUsuarioGuardado = Number(respuesta?.usuario?.id_usuario || respuesta?.id_usuario || 0);

      alert("Usuario creado correctamente.");
    }

    await registrarAccionSeguridadFrontend(
      datos.idUsuarioEditar ? "EDITAR_USUARIO" : "CREAR_USUARIO",
      datos.idUsuarioEditar
        ? `Se actualizó el usuario ${datos.usuario}.`
        : `Se creó el usuario ${datos.usuario}.`,
      "usuarios",
      idUsuarioGuardado || null
    );

    limpiarFormularioUsuario();
    await cargarUsuariosSeguridad();
  } catch (error) {
    mostrarErrorSeguridad(error, "No se pudo guardar el usuario.");
  }
}

function editarUsuarioSeguridad(idUsuario) {
  const usuario = usuariosSeguridad.find((u) => Number(u.id_usuario) === Number(idUsuario));

  if (!usuario) {
    alert("Usuario no encontrado.");
    return;
  }

  const idUsuarioEditar = document.getElementById("idUsuarioEditar");
  const nombresUsuario = document.getElementById("nombresUsuario");
  const apellidosUsuario = document.getElementById("apellidosUsuario");
  const usuarioSistema = document.getElementById("usuarioSistema");
  const correoUsuario = document.getElementById("correoUsuario");
  const contrasenaUsuario = document.getElementById("contrasenaUsuario");
  const perfilUsuario = document.getElementById("perfilUsuario");
  const estadoUsuario = document.getElementById("estadoUsuario");

  if (idUsuarioEditar) idUsuarioEditar.value = usuario.id_usuario;
  if (nombresUsuario) nombresUsuario.value = usuario.nombres || "";
  if (apellidosUsuario) apellidosUsuario.value = usuario.apellidos || "";
  if (usuarioSistema) usuarioSistema.value = usuario.usuario || "";
  if (correoUsuario) correoUsuario.value = usuario.correo || "";

  if (contrasenaUsuario) {
    contrasenaUsuario.value = "";
    contrasenaUsuario.type = "password";
    contrasenaUsuario.required = false;
  }

  const mostrarContrasenaUsuario = document.getElementById("mostrarContrasenaUsuario");
  if (mostrarContrasenaUsuario) {
    mostrarContrasenaUsuario.checked = false;
  }

  if (perfilUsuario) {
    perfilUsuario.disabled = false;
    perfilUsuario.value = usuario.id_perfil;
  }

  if (estadoUsuario) {
    estadoUsuario.disabled = false;
    estadoUsuario.value = usuario.estado ? "true" : "false";
  }

  const btnGuardar = document.getElementById("btnGuardarUsuario");
  if (btnGuardar) {
    btnGuardar.textContent = "Actualizar";
  }

  if (esUsuarioAdminPrincipal(usuario)) {
    bloquearCamposAdminPrincipal(true);
    alert(
      "Está editando el administrador principal. Por seguridad no se puede cambiar su usuario, perfil ni estado."
    );
  } else {
    bloquearCamposAdminPrincipal(false);
  }

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

async function cambiarEstadoUsuarioSeguridad(idUsuario, nuevoEstado) {
  const usuario = usuariosSeguridad.find((u) => Number(u.id_usuario) === Number(idUsuario));

  if (!usuario) {
    alert("Usuario no encontrado.");
    return;
  }

  if (esUsuarioAdminPrincipal(usuario) && nuevoEstado === false) {
    alert("No se permite desactivar al administrador principal del sistema.");
    return;
  }

  const accionTexto = nuevoEstado ? "activar" : "desactivar";

  const confirmar = confirm(
    `¿Está seguro de ${accionTexto} el usuario ${usuario.usuario}?`
  );

  if (!confirmar) {
    return;
  }

  try {
    await seguridadApiPut(`/api/seguridad/usuarios/${idUsuario}/estado`, {
      estado: nuevoEstado,
      id_admin: obtenerIdAdminActual(),
    });

    await registrarAccionSeguridadFrontend(
      nuevoEstado ? "ACTIVAR_USUARIO" : "INACTIVAR_USUARIO",
      `${nuevoEstado ? "Activó" : "Inactivó"} el usuario ${usuario.usuario}.`,
      "usuarios",
      Number(idUsuario)
    );

    alert(`Usuario ${nuevoEstado ? "activado" : "desactivado"} correctamente.`);

    await cargarUsuariosSeguridad();
  } catch (error) {
    mostrarErrorSeguridad(error, "No se pudo cambiar el estado del usuario.");
  }
}

/* ---------------------------------------------------- */
/* CAMBIAR CONTRASEÑA                                   */
/* ---------------------------------------------------- */

function seleccionarCambioContrasena(idUsuario) {
  const usuario = usuariosSeguridad.find((u) => Number(u.id_usuario) === Number(idUsuario));

  if (!usuario) {
    alert("Usuario no encontrado.");
    return;
  }

  const idUsuarioContrasena = document.getElementById("idUsuarioContrasena");
  const usuarioContrasenaTexto = document.getElementById("usuarioContrasenaTexto");
  const nuevaContrasena = document.getElementById("nuevaContrasena");

  if (idUsuarioContrasena) idUsuarioContrasena.value = usuario.id_usuario;
  if (usuarioContrasenaTexto) usuarioContrasenaTexto.value = usuario.usuario;

  if (nuevaContrasena) {
    nuevaContrasena.value = "";
    nuevaContrasena.type = "password";
    nuevaContrasena.focus();
  }

  const mostrarNuevaContrasena = document.getElementById("mostrarNuevaContrasena");
  if (mostrarNuevaContrasena) {
    mostrarNuevaContrasena.checked = false;
  }
}

async function cambiarContrasenaUsuarioSeguridad(event) {
  event.preventDefault();

  const idUsuario = document.getElementById("idUsuarioContrasena")?.value;
  const nuevaContrasena = document.getElementById("nuevaContrasena")?.value.trim();

  if (!idUsuario) {
    alert("Debe seleccionar un usuario para cambiar la contraseña.");
    return;
  }

  if (!validarCampoTexto(nuevaContrasena, "la nueva contraseña")) {
    return;
  }

  if (!validarContrasenaSeguridad(nuevaContrasena)) {
    alert("La nueva contraseña debe tener entre 8 y 40 caracteres, al menos una letra y al menos un número.");
    return;
  }

  const usuario = usuariosSeguridad.find((u) => Number(u.id_usuario) === Number(idUsuario));
  const confirmar = confirm(`¿Desea cambiar la contraseña del usuario ${usuario?.usuario || idUsuario}?`);

  if (!confirmar) {
    return;
  }

  try {
    await seguridadApiPut(`/api/seguridad/usuarios/${idUsuario}/contrasena`, {
      nueva_contrasena: nuevaContrasena,
      id_admin: obtenerIdAdminActual(),
    });

    await registrarAccionSeguridadFrontend(
      "CAMBIAR_CONTRASENA",
      `Cambió la contraseña del usuario ${usuario?.usuario || idUsuario}.`,
      "usuarios",
      Number(idUsuario)
    );

    alert("Contraseña actualizada correctamente.");

    limpiarCambioContrasena();
  } catch (error) {
    mostrarErrorSeguridad(error, "No se pudo cambiar la contraseña.");
  }
}

/* ---------------------------------------------------- */
/* PERMISOS POR USUARIO                                 */
/* ---------------------------------------------------- */

async function seleccionarPermisosUsuario(idUsuario) {
  const usuario = usuariosSeguridad.find((u) => Number(u.id_usuario) === Number(idUsuario));

  if (!usuario) {
    alert("Usuario no encontrado.");
    return;
  }

  const idUsuarioPermisos = document.getElementById("idUsuarioPermisos");
  const usuarioPermisosSeleccionado = document.getElementById("usuarioPermisosSeleccionado");

  if (idUsuarioPermisos) {
    idUsuarioPermisos.value = usuario.id_usuario;
  }

  if (usuarioPermisosSeleccionado) {
    usuarioPermisosSeleccionado.textContent = `${usuario.usuario} - ${obtenerPerfilUsuario(usuario)}`;
  }

  try {
    permisosUsuarioSeleccionado = await seguridadApiGet(
      `/api/seguridad/permisos-usuario/${idUsuario}`
    );

    if (!Array.isArray(permisosUsuarioSeleccionado)) {
      permisosUsuarioSeleccionado = [];
    }

    renderizarPermisosUsuario(usuario);
  } catch (error) {
    mostrarErrorSeguridad(error, "No se pudieron cargar los permisos del usuario.");
  }
}

function obtenerUsuarioPermisosSeleccionado() {
  const idUsuario = document.getElementById("idUsuarioPermisos")?.value;

  if (!idUsuario) {
    return null;
  }

  return usuariosSeguridad.find((item) => Number(item.id_usuario) === Number(idUsuario)) || null;
}

function obtenerCheckboxPermiso(fila, clase) {
  return fila.querySelector(clase);
}

function marcarCheckbox(checkbox, valor, deshabilitar = false) {
  if (!checkbox) return;
  checkbox.checked = Boolean(valor);
  checkbox.disabled = Boolean(deshabilitar);
}

function aplicarValoresFilaPermiso(fila, valores, deshabilitar = false) {
  marcarCheckbox(obtenerCheckboxPermiso(fila, ".permiso-ver"), valores.ver, deshabilitar);
  marcarCheckbox(obtenerCheckboxPermiso(fila, ".permiso-crear-check"), valores.crear, deshabilitar);
  marcarCheckbox(obtenerCheckboxPermiso(fila, ".permiso-editar-check"), valores.editar, deshabilitar);
  marcarCheckbox(obtenerCheckboxPermiso(fila, ".permiso-eliminar-check"), valores.eliminar, deshabilitar);
  marcarCheckbox(obtenerCheckboxPermiso(fila, ".permiso-consultar-check"), valores.consultar, deshabilitar);
  marcarCheckbox(obtenerCheckboxPermiso(fila, ".permiso-reporte-check"), valores.reporte, deshabilitar);
}

function obtenerModuloPorFila(fila) {
  const idModulo = fila.querySelector(".permiso-id-modulo")?.value;

  return modulosSeguridad.find((modulo) => {
    return Number(modulo.id_modulo) === Number(idModulo);
  });
}

function obtenerReglaPermisoParaPerfil(usuario, modulo) {
  const perfil = obtenerPerfilUsuario(usuario);

  if (esPerfilAdministradorNombre(perfil)) {
    return {
      valores: {
        ver: true,
        crear: true,
        editar: true,
        eliminar: true,
        consultar: true,
        reporte: true,
      },
      bloquear: true,
      mensaje: "Perfil Administrador: control total obligatorio."
    };
  }

  if (esPerfilGerenteNombre(perfil)) {
    if (esModuloReportesIA(modulo)) {
      return {
        valores: {
          ver: true,
          crear: true,
          editar: true,
          eliminar: true,
          consultar: true,
          reporte: true,
        },
        bloquear: true,
        mensaje: "Gerente/Directivo: control total en Reportes e IA."
      };
    }

    return {
      valores: {
        ver: true,
        crear: false,
        editar: false,
        eliminar: false,
        consultar: true,
        reporte: false,
      },
      bloquear: true,
      mensaje: "Gerente/Directivo: solo consulta en módulos operativos."
    };
  }

  return {
    valores: null,
    bloquear: false,
    mensaje: "Operativo: permisos personalizados por administrador."
  };
}

function agregarEventosCheckboxesFilaPermiso(fila) {
  const checkVer = obtenerCheckboxPermiso(fila, ".permiso-ver");
  const checkCrear = obtenerCheckboxPermiso(fila, ".permiso-crear-check");
  const checkEditar = obtenerCheckboxPermiso(fila, ".permiso-editar-check");
  const checkEliminar = obtenerCheckboxPermiso(fila, ".permiso-eliminar-check");
  const checkConsultar = obtenerCheckboxPermiso(fila, ".permiso-consultar-check");
  const checkReporte = obtenerCheckboxPermiso(fila, ".permiso-reporte-check");

  [checkCrear, checkEditar, checkEliminar, checkReporte].forEach((check) => {
    if (!check) return;

    check.addEventListener("change", function () {
      if (this.checked) {
        if (checkVer) checkVer.checked = true;
        if (checkConsultar) checkConsultar.checked = true;
      }
    });
  });

  if (checkVer) {
    checkVer.addEventListener("change", function () {
      if (!this.checked) {
        if (checkCrear) checkCrear.checked = false;
        if (checkEditar) checkEditar.checked = false;
        if (checkEliminar) checkEliminar.checked = false;
        if (checkReporte) checkReporte.checked = false;
      }
    });
  }
}

function renderizarPermisosUsuario(usuario) {
  const tablaPermisos = document.getElementById("tablaPermisos");

  if (!tablaPermisos) {
    return;
  }

  tablaPermisos.innerHTML = "";

  if (!modulosSeguridad || modulosSeguridad.length === 0) {
    tablaPermisos.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted">
          No existen módulos registrados para asignar permisos.
        </td>
      </tr>
    `;
    return;
  }

  const adminPrincipal = esUsuarioAdminPrincipal(usuario);
  const perfil = obtenerPerfilUsuario(usuario);

  modulosSeguridad.forEach((modulo) => {
    const permisoExistente = permisosUsuarioSeleccionado.find(
      (permiso) => Number(permiso.id_modulo) === Number(modulo.id_modulo)
    );

    let valores = {
      ver: permisoExistente?.puede_ver === true,
      crear: permisoExistente?.puede_crear === true,
      editar: permisoExistente?.puede_editar === true,
      eliminar: permisoExistente?.puede_eliminar === true,
      consultar: permisoExistente?.puede_consultar === true,
      reporte: permisoExistente?.puede_generar_reporte === true,
    };

    let disabled = false;
    let etiquetaRegla = "";

    const reglaPerfil = obtenerReglaPermisoParaPerfil(usuario, modulo);

    if (reglaPerfil.valores) {
      valores = reglaPerfil.valores;
      disabled = reglaPerfil.bloquear;
      etiquetaRegla = reglaPerfil.mensaje;
    }

    if (adminPrincipal) {
      disabled = true;
      etiquetaRegla = "Administrador principal protegido: control total obligatorio.";
    }

    const fila = document.createElement("tr");
    fila.dataset.idModulo = String(modulo.id_modulo);

    fila.innerHTML = `
      <td>
        <strong>${escaparHTMLSeguridad(modulo.nombre_modulo)}</strong><br>
        <small class="text-muted">${escaparHTMLSeguridad(modulo.ruta_html || "")}</small>
        ${
          etiquetaRegla
            ? `<br><small class="text-success">${escaparHTMLSeguridad(etiquetaRegla)}</small>`
            : ""
        }
        <input type="hidden" class="permiso-id-modulo" value="${Number(modulo.id_modulo)}">
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-checkbox permiso-ver" ${valores.ver ? "checked" : ""} ${disabled ? "disabled" : ""}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-checkbox permiso-crear-check" ${valores.crear ? "checked" : ""} ${disabled ? "disabled" : ""}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-checkbox permiso-editar-check" ${valores.editar ? "checked" : ""} ${disabled ? "disabled" : ""}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-checkbox permiso-eliminar-check" ${valores.eliminar ? "checked" : ""} ${disabled ? "disabled" : ""}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-checkbox permiso-consultar-check" ${valores.consultar ? "checked" : ""} ${disabled ? "disabled" : ""}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-checkbox permiso-reporte-check" ${valores.reporte ? "checked" : ""} ${disabled ? "disabled" : ""}>
      </td>
    `;

    tablaPermisos.appendChild(fila);
    agregarEventosCheckboxesFilaPermiso(fila);
  });

  if (adminPrincipal) {
    const aviso = document.createElement("tr");
    aviso.innerHTML = `
      <td colspan="7" class="text-center text-success fw-bold">
        El administrador principal tiene control total del ERP. Sus permisos no pueden ser reducidos desde esta pantalla.
      </td>
    `;
    tablaPermisos.appendChild(aviso);
  } else if (esPerfilGerenteNombre(perfil)) {
    const aviso = document.createElement("tr");
    aviso.innerHTML = `
      <td colspan="7" class="text-center text-primary fw-bold">
        Regla aplicada: Gerente/Directivo consulta todos los módulos y tiene control total en Reportes e IA.
      </td>
    `;
    tablaPermisos.appendChild(aviso);
  } else if (esPerfilAdministradorNombre(perfil)) {
    const aviso = document.createElement("tr");
    aviso.innerHTML = `
      <td colspan="7" class="text-center text-success fw-bold">
        Regla aplicada: el perfil Administrador mantiene control total en todos los módulos.
      </td>
    `;
    tablaPermisos.appendChild(aviso);
  }
}

function normalizarPermisoPorPerfil(usuario, modulo, permiso) {
  const perfil = obtenerPerfilUsuario(usuario);

  if (esPerfilAdministradorNombre(perfil)) {
    return {
      ...permiso,
      puede_ver: true,
      puede_crear: true,
      puede_editar: true,
      puede_eliminar: true,
      puede_consultar: true,
      puede_generar_reporte: true,
    };
  }

  if (esPerfilGerenteNombre(perfil)) {
    if (esModuloReportesIA(modulo)) {
      return {
        ...permiso,
        puede_ver: true,
        puede_crear: true,
        puede_editar: true,
        puede_eliminar: true,
        puede_consultar: true,
        puede_generar_reporte: true,
      };
    }

    return {
      ...permiso,
      puede_ver: true,
      puede_crear: false,
      puede_editar: false,
      puede_eliminar: false,
      puede_consultar: true,
      puede_generar_reporte: false,
    };
  }

  const necesitaVerConsultar =
    permiso.puede_crear ||
    permiso.puede_editar ||
    permiso.puede_eliminar ||
    permiso.puede_generar_reporte;

  if (necesitaVerConsultar) {
    return {
      ...permiso,
      puede_ver: true,
      puede_consultar: true,
    };
  }

  return permiso;
}

function construirPermisosDesdeTabla(usuario) {
  const filas = document.querySelectorAll("#tablaPermisos tr");
  const permisos = [];

  filas.forEach((fila) => {
    const idModulo = fila.querySelector(".permiso-id-modulo")?.value;

    if (!idModulo) {
      return;
    }

    const modulo = obtenerModuloPorFila(fila);

    let permiso = {
      id_modulo: Number(idModulo),
      puede_ver: fila.querySelector(".permiso-ver")?.checked || false,
      puede_crear: fila.querySelector(".permiso-crear-check")?.checked || false,
      puede_editar: fila.querySelector(".permiso-editar-check")?.checked || false,
      puede_eliminar: fila.querySelector(".permiso-eliminar-check")?.checked || false,
      puede_consultar: fila.querySelector(".permiso-consultar-check")?.checked || false,
      puede_generar_reporte: fila.querySelector(".permiso-reporte-check")?.checked || false,
    };

    permiso = normalizarPermisoPorPerfil(usuario, modulo, permiso);
    permisos.push(permiso);
  });

  return permisos;
}

function validarPermisosUsuarioSeguridad(usuario, permisos) {
  if (!usuario) {
    alert("Debe seleccionar un usuario válido para asignar permisos.");
    return false;
  }

  if (esUsuarioAdminPrincipal(usuario)) {
    const confirmar = confirm(
      "El administrador principal tendrá control total obligatorio. ¿Desea guardar nuevamente esos permisos?"
    );

    return confirmar;
  }

  if (!Array.isArray(permisos) || permisos.length === 0) {
    alert("No existen permisos para guardar.");
    return false;
  }

  const perfil = obtenerPerfilUsuario(usuario);

  if (esPerfilAdministradorNombre(perfil)) {
    const confirmar = confirm(
      "El usuario tiene perfil Administrador. Se guardará control total en todos los módulos. ¿Desea continuar?"
    );

    return confirmar;
  }

  if (esPerfilGerenteNombre(perfil)) {
    const confirmar = confirm(
      "El usuario tiene perfil Gerente/Directivo. Se guardará consulta en módulos operativos y control total en Reportes e IA. ¿Desea continuar?"
    );

    return confirmar;
  }

  const tieneAlgunAcceso = permisos.some((permiso) => {
    return (
      permiso.puede_ver ||
      permiso.puede_crear ||
      permiso.puede_editar ||
      permiso.puede_eliminar ||
      permiso.puede_consultar ||
      permiso.puede_generar_reporte
    );
  });

  if (!tieneAlgunAcceso) {
    const confirmar = confirm(
      "Este usuario quedará sin permisos de acceso a módulos. ¿Está seguro de guardar así?"
    );

    if (!confirmar) {
      return false;
    }
  }

  return true;
}

async function guardarPermisosUsuarioSeguridad() {
  const idUsuario = document.getElementById("idUsuarioPermisos")?.value;

  if (!idUsuario) {
    alert("Debe seleccionar un usuario para asignar permisos.");
    return;
  }

  const usuario = usuariosSeguridad.find((item) => {
    return Number(item.id_usuario) === Number(idUsuario);
  });

  const permisos = construirPermisosDesdeTabla(usuario);

  if (!validarPermisosUsuarioSeguridad(usuario, permisos)) {
    return;
  }

  try {
    await seguridadApiPut(`/api/seguridad/permisos-usuario/${idUsuario}`, {
      id_usuario: Number(idUsuario),
      permisos,
      id_admin: obtenerIdAdminActual(),
    });

    await registrarAccionSeguridadFrontend(
      "EDITAR_PERMISOS",
      `Se actualizaron los permisos del usuario ${usuario?.usuario || idUsuario}.`,
      "permisos_usuario",
      Number(idUsuario)
    );

    alert("Permisos actualizados correctamente.");

    await seleccionarPermisosUsuario(Number(idUsuario));
  } catch (error) {
    mostrarErrorSeguridad(error, "No se pudieron actualizar los permisos.");
  }
}

/* ---------------------------------------------------- */
/* PLANTILLAS DE PERMISOS                               */
/* ---------------------------------------------------- */

function aplicarPlantillaAdministradorPermisos() {
  const usuario = obtenerUsuarioPermisosSeleccionado();

  if (!usuario) {
    alert("Seleccione primero un usuario para aplicar la plantilla.");
    return;
  }

  const filas = document.querySelectorAll("#tablaPermisos tr");

  filas.forEach((fila) => {
    if (!fila.querySelector(".permiso-id-modulo")) return;

    aplicarValoresFilaPermiso(
      fila,
      {
        ver: true,
        crear: true,
        editar: true,
        eliminar: true,
        consultar: true,
        reporte: true,
      },
      false
    );
  });

  alert("Plantilla de Administrador aplicada. Revise y guarde los permisos.");
}

function aplicarPlantillaGerentePermisos() {
  const usuario = obtenerUsuarioPermisosSeleccionado();

  if (!usuario) {
    alert("Seleccione primero un usuario para aplicar la plantilla.");
    return;
  }

  const filas = document.querySelectorAll("#tablaPermisos tr");

  filas.forEach((fila) => {
    if (!fila.querySelector(".permiso-id-modulo")) return;

    const modulo = obtenerModuloPorFila(fila);

    if (esModuloReportesIA(modulo)) {
      aplicarValoresFilaPermiso(
        fila,
        {
          ver: true,
          crear: true,
          editar: true,
          eliminar: true,
          consultar: true,
          reporte: true,
        },
        false
      );
    } else {
      aplicarValoresFilaPermiso(
        fila,
        {
          ver: true,
          crear: false,
          editar: false,
          eliminar: false,
          consultar: true,
          reporte: false,
        },
        false
      );
    }
  });

  alert("Plantilla de Gerente/Directivo aplicada. Revise y guarde los permisos.");
}

function aplicarPlantillaSoloConsultaPermisos() {
  const usuario = obtenerUsuarioPermisosSeleccionado();

  if (!usuario) {
    alert("Seleccione primero un usuario para aplicar la plantilla.");
    return;
  }

  const filas = document.querySelectorAll("#tablaPermisos tr");

  filas.forEach((fila) => {
    if (!fila.querySelector(".permiso-id-modulo")) return;

    aplicarValoresFilaPermiso(
      fila,
      {
        ver: true,
        crear: false,
        editar: false,
        eliminar: false,
        consultar: true,
        reporte: false,
      },
      false
    );
  });

  alert("Plantilla de solo consulta aplicada. Revise y guarde los permisos.");
}

function limpiarChecksPermisosUsuario() {
  const usuario = obtenerUsuarioPermisosSeleccionado();

  if (!usuario) {
    alert("Seleccione primero un usuario para limpiar permisos.");
    return;
  }

  const confirmar = confirm("Se quitarán las marcas visibles de permisos. ¿Desea continuar?");

  if (!confirmar) {
    return;
  }

  const filas = document.querySelectorAll("#tablaPermisos tr");

  filas.forEach((fila) => {
    if (!fila.querySelector(".permiso-id-modulo")) return;

    aplicarValoresFilaPermiso(
      fila,
      {
        ver: false,
        crear: false,
        editar: false,
        eliminar: false,
        consultar: false,
        reporte: false,
      },
      false
    );
  });
}

/* ---------------------------------------------------- */
/* INICIALIZACIÓN                                       */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  if (!usuarioActualEsAdministradorSeguridad()) {
    alert("Solo el administrador puede acceder al módulo de Seguridad y Usuarios.");
    window.location.href = "dashboard.html";
    return;
  }

  const formUsuario = document.getElementById("formUsuario");
  const btnLimpiarUsuario = document.getElementById("btnLimpiarUsuario");
  const btnGuardarPermisos = document.getElementById("btnGuardarPermisos");
  const btnLimpiarPermisos = document.getElementById("btnLimpiarPermisos");
  const formCambiarContrasena = document.getElementById("formCambiarContrasena");

  const btnPermisosAdministrador = document.getElementById("btnPermisosAdministrador");
  const btnPermisosGerente = document.getElementById("btnPermisosGerente");
  const btnPermisosSoloConsulta = document.getElementById("btnPermisosSoloConsulta");
  const btnPermisosLimpiarChecks = document.getElementById("btnPermisosLimpiarChecks");

  if (formUsuario) {
    formUsuario.addEventListener("submit", guardarUsuarioSeguridad);
  }

  if (btnLimpiarUsuario) {
    btnLimpiarUsuario.addEventListener("click", limpiarFormularioUsuario);
  }

  if (btnGuardarPermisos) {
    btnGuardarPermisos.addEventListener("click", guardarPermisosUsuarioSeguridad);
  }

  if (btnLimpiarPermisos) {
    btnLimpiarPermisos.addEventListener("click", limpiarSeleccionPermisos);
  }

  if (formCambiarContrasena) {
    formCambiarContrasena.addEventListener("submit", cambiarContrasenaUsuarioSeguridad);
  }

  if (btnPermisosAdministrador) {
    btnPermisosAdministrador.addEventListener("click", aplicarPlantillaAdministradorPermisos);
  }

  if (btnPermisosGerente) {
    btnPermisosGerente.addEventListener("click", aplicarPlantillaGerentePermisos);
  }

  if (btnPermisosSoloConsulta) {
    btnPermisosSoloConsulta.addEventListener("click", aplicarPlantillaSoloConsultaPermisos);
  }

  if (btnPermisosLimpiarChecks) {
    btnPermisosLimpiarChecks.addEventListener("click", limpiarChecksPermisosUsuario);
  }

  activarMostrarContrasenasSeguridad();
  aplicarFiltrosEscrituraSeguridad();

  await cargarDatosSeguridad();
});

/* ---------------------------------------------------- */
/* FUNCIONES GLOBALES PARA BOTONES HTML                 */
/* ---------------------------------------------------- */

window.editarUsuarioSeguridad = editarUsuarioSeguridad;
window.cambiarEstadoUsuarioSeguridad = cambiarEstadoUsuarioSeguridad;
window.seleccionarPermisosUsuario = seleccionarPermisosUsuario;
window.seleccionarCambioContrasena = seleccionarCambioContrasena;

window.aplicarPlantillaAdministradorPermisos = aplicarPlantillaAdministradorPermisos;
window.aplicarPlantillaGerentePermisos = aplicarPlantillaGerentePermisos;
window.aplicarPlantillaSoloConsultaPermisos = aplicarPlantillaSoloConsultaPermisos;
window.limpiarChecksPermisosUsuario = limpiarChecksPermisosUsuario;