/* ---------------------------------------------------- */
/* SEGURIDAD Y USUARIOS - ERP PILADORA DON GUILLO       */
/* Gestión de usuarios, perfiles, módulos y permisos    */
/* Validaciones reforzadas y protección de administrador */
/* ---------------------------------------------------- */

let usuariosSeguridad = [];
let perfilesSeguridad = [];
let modulosSeguridad = [];
let permisosUsuarioSeleccionado = [];

/* ---------------------------------------------------- */
/* CONSUMO DE API                                       */
/* ---------------------------------------------------- */

async function seguridadApiGet(ruta) {
  if (window.apiGet) {
    return await window.apiGet(ruta);
  }

  const respuesta = await fetch(`https://erp-piladora-don-guillo.onrender.com${ruta}`);
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

  const respuesta = await fetch(`https://erp-piladora-don-guillo.onrender.com${ruta}`, {
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

  const respuesta = await fetch(`https://erp-piladora-don-guillo.onrender.com${ruta}`, {
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

  const respuesta = await fetch(`https://erp-piladora-don-guillo.onrender.com${ruta}`, {
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

  const respuesta = await fetch(`https://erp-piladora-don-guillo.onrender.com${ruta}`, {
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
  return perfil.includes("gerente");
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

function esUsuarioAdminPrincipal(usuario) {
  if (!usuario) return false;

  const nombreUsuario = normalizarTextoSeguridad(usuario.usuario);
  const nombrePerfil = normalizarTextoSeguridad(usuario.nombre_perfil);

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
  }

  if (perfilUsuario) {
    perfilUsuario.value = "";
    
    // REGLA DE SEGURIDAD: Volver a ocultar el perfil Administrador al limpiar
    Array.from(perfilUsuario.options).forEach(opt => {
        const textNorm = normalizarTextoSeguridad(opt.textContent);
        if (textNorm.includes("administrador") || textNorm === "admin") {
            opt.disabled = true;
            opt.style.display = "none";
        }
    });
  }
  
  if (estadoUsuario) estadoUsuario.value = "true";

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
    return `<span class="badge bg-success">Activo</span>`;
  }

  return `<span class="badge bg-danger">Inactivo</span>`;
}

function validarCampoTexto(valor, nombreCampo) {
  if (!valor || valor.trim() === "") {
    alert(`Debe ingresar ${nombreCampo}.`);
    return false;
  }

  return true;
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

    // REGLA DE SEGURIDAD: Ocultar el perfil Administrador de la lista para crear nuevos usuarios
    const nombreNormalizado = normalizarTextoSeguridad(perfil.nombre_perfil);
    if (nombreNormalizado.includes("administrador") || nombreNormalizado === "admin") {
        option.disabled = true;
        option.style.display = "none";
    }

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
          ${escaparHTMLSeguridad(usuario.nombre_perfil || "-")}
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

      await seguridadApiPost("/api/seguridad/usuarios", datosCrear);

      alert("Usuario creado correctamente.");
    }

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
  }

  const mostrarContrasenaUsuario = document.getElementById("mostrarContrasenaUsuario");
  if (mostrarContrasenaUsuario) {
    mostrarContrasenaUsuario.checked = false;
  }

  if (perfilUsuario) {
    // REGLA DE SEGURIDAD: Si está editando al Admin Principal, mostramos su perfil temporalmente
    if (esUsuarioAdminPrincipal(usuario)) {
        Array.from(perfilUsuario.options).forEach(opt => {
            if (Number(opt.value) === Number(usuario.id_perfil)) {
                opt.disabled = false;
                opt.style.display = "block";
            }
        });
    }
    perfilUsuario.value = usuario.id_perfil;
  }
  
  if (estadoUsuario) estadoUsuario.value = usuario.estado ? "true" : "false";

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

  try {
    await seguridadApiPut(`/api/seguridad/usuarios/${idUsuario}/contrasena`, {
      nueva_contrasena: nuevaContrasena,
      id_admin: obtenerIdAdminActual(),
    });

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
    usuarioPermisosSeleccionado.textContent = `${usuario.usuario} - ${usuario.nombre_perfil}`;
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

function renderizarPermisosUsuario(usuario) {
  const tablaPermisos = document.getElementById("tablaPermisos");

  if (!tablaPermisos) {
    return;
  }

  tablaPermisos.innerHTML = "";

  const adminPrincipal = esUsuarioAdminPrincipal(usuario);

  modulosSeguridad.forEach((modulo) => {
    const permisoExistente = permisosUsuarioSeleccionado.find(
      (permiso) => Number(permiso.id_modulo) === Number(modulo.id_modulo)
    );

    let puedeVer = permisoExistente?.puede_ver === true;
    let puedeCrear = permisoExistente?.puede_crear === true;
    let puedeEditar = permisoExistente?.puede_editar === true;
    let puedeEliminar = permisoExistente?.puede_eliminar === true;
    let puedeConsultar = permisoExistente?.puede_consultar === true;
    let puedeReporte = permisoExistente?.puede_generar_reporte === true;

    if (adminPrincipal) {
      puedeVer = true;
      puedeCrear = true;
      puedeEditar = true;
      puedeEliminar = true;
      puedeConsultar = true;
      puedeReporte = true;
    }

    const disabledAdmin = adminPrincipal ? "disabled" : "";

    const fila = document.createElement("tr");

    fila.innerHTML = `
      <td>
        <strong>${escaparHTMLSeguridad(modulo.nombre_modulo)}</strong><br>
        <small class="text-muted">${escaparHTMLSeguridad(modulo.ruta_html || "")}</small>
        <input type="hidden" class="permiso-id-modulo" value="${Number(modulo.id_modulo)}">
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-ver" ${puedeVer ? "checked" : ""} ${disabledAdmin}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-crear-check" ${puedeCrear ? "checked" : ""} ${disabledAdmin}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-editar-check" ${puedeEditar ? "checked" : ""} ${disabledAdmin}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-eliminar-check" ${puedeEliminar ? "checked" : ""} ${disabledAdmin}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-consultar-check" ${puedeConsultar ? "checked" : ""} ${disabledAdmin}>
      </td>

      <td class="text-center">
        <input type="checkbox" class="form-check-input permiso-reporte-check" ${puedeReporte ? "checked" : ""} ${disabledAdmin}>
      </td>
    `;

    tablaPermisos.appendChild(fila);
  });

  if (adminPrincipal) {
    const aviso = document.createElement("tr");
    aviso.innerHTML = `
      <td colspan="7" class="text-center text-success fw-bold">
        El administrador principal tiene control total del ERP. Sus permisos no pueden ser modificados desde esta pantalla.
      </td>
    `;
    tablaPermisos.appendChild(aviso);
  }
}

function construirPermisosDesdeTabla(usuario) {
  const filas = document.querySelectorAll("#tablaPermisos tr");
  const permisos = [];
  const adminPrincipal = esUsuarioAdminPrincipal(usuario);

  filas.forEach((fila) => {
    const idModulo = fila.querySelector(".permiso-id-modulo")?.value;

    if (!idModulo) {
      return;
    }

    let puedeVer = fila.querySelector(".permiso-ver")?.checked || false;
    let puedeCrear = fila.querySelector(".permiso-crear-check")?.checked || false;
    let puedeEditar = fila.querySelector(".permiso-editar-check")?.checked || false;
    let puedeEliminar = fila.querySelector(".permiso-eliminar-check")?.checked || false;
    let puedeConsultar = fila.querySelector(".permiso-consultar-check")?.checked || false;
    let puedeReporte = fila.querySelector(".permiso-reporte-check")?.checked || false;

    if (adminPrincipal) {
      puedeVer = true;
      puedeCrear = true;
      puedeEditar = true;
      puedeEliminar = true;
      puedeConsultar = true;
      puedeReporte = true;
    }

    permisos.push({
      id_modulo: Number(idModulo),
      puede_ver: puedeVer,
      puede_crear: puedeCrear,
      puede_editar: puedeEditar,
      puede_eliminar: puedeEliminar,
      puede_consultar: puedeConsultar,
      puede_generar_reporte: puedeReporte,
    });
  });

  return permisos;
}

function validarPermisosUsuarioSeguridad(usuario, permisos) {
  if (!usuario) {
    alert("Debe seleccionar un usuario válido para asignar permisos.");
    return false;
  }

  if (esUsuarioAdminPrincipal(usuario)) {
    alert("No se permite modificar los permisos del administrador principal.");
    return false;
  }

  if (!Array.isArray(permisos) || permisos.length === 0) {
    alert("No existen permisos para guardar.");
    return false;
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

    alert("Permisos actualizados correctamente.");

    await seleccionarPermisosUsuario(Number(idUsuario));
  } catch (error) {
    mostrarErrorSeguridad(error, "No se pudieron actualizar los permisos.");
  }
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