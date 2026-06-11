/* ---------------------------------------------------- */
/* AUDITORÍA DEL SISTEMA - ERP PILADORA DON GUILLO      */
/* Archivo: auditoria.js                                */
/* Consulta, filtros, colores, comprobante, paginación  */
/* y mantenimiento histórico.                           */
/* ---------------------------------------------------- */

let accesosAuditoria = [];
let accionesAuditoria = [];

let accesosFiltradosActuales = [];
let accionesFiltradasActuales = [];

let paginaAccesos = 0;
let paginaAcciones = 0;

let auditoriaInicializada = false;

const API_AUDITORIA_BASE = "";

/*
  IMPORTANTE:
  El ingreso al módulo ya lo registra main.js con registrarAccionSistema().
  Si también se registra aquí, se duplica INGRESO_MODULO.
*/
const REGISTRAR_INGRESO_AUDITORIA_DESDE_ESTE_ARCHIVO = false;

/* ---------------------------------------------------- */
/* SESIÓN ACTUAL                                        */
/* ---------------------------------------------------- */

function obtenerUsuarioSesionAuditoria() {
  const idUsuarioERP = localStorage.getItem("idUsuarioERP");
  const usuarioERP = localStorage.getItem("usuarioERP");
  const perfilERP = localStorage.getItem("perfilERP");
  const idPerfilERP = localStorage.getItem("idPerfilERP");

  if (idUsuarioERP && usuarioERP) {
    return {
      id_usuario: Number(idUsuarioERP),
      usuario: usuarioERP,
      perfil: perfilERP || "",
      nombre_perfil: perfilERP || "",
      id_perfil: idPerfilERP ? Number(idPerfilERP) : null,
    };
  }

  let usuarioActual = null;

  try {
    usuarioActual =
      JSON.parse(localStorage.getItem("usuarioActual")) ||
      JSON.parse(localStorage.getItem("usuario")) ||
      JSON.parse(localStorage.getItem("user"));
  } catch (error) {
    usuarioActual = null;
  }

  if (!usuarioActual && typeof usuarioGuardado !== "undefined") {
    usuarioActual = {
      usuario: usuarioGuardado,
      perfil: typeof perfilGuardado !== "undefined" ? perfilGuardado : "",
      nombre_perfil: typeof perfilGuardado !== "undefined" ? perfilGuardado : "",
    };
  }

  return usuarioActual;
}

/* ---------------------------------------------------- */
/* VALIDAR ACCESO A AUDITORÍA                           */
/* ---------------------------------------------------- */

function validarAccesoAuditoria() {
  const usuarioActual = obtenerUsuarioSesionAuditoria();

  if (!usuarioActual) {
    alert("Debe iniciar sesión para acceder al sistema.");
    window.location.href = "login.html";
    return false;
  }

  const perfil =
    usuarioActual.perfil ||
    usuarioActual.nombre_perfil ||
    usuarioActual.nombrePerfil ||
    "";

  const perfilNormalizado = perfil.toString().trim().toLowerCase();

  if (
    perfilNormalizado !== "administrador" &&
    perfilNormalizado !== "gerente"
  ) {
    alert("No tiene permisos para acceder al módulo de auditoría.");
    window.location.href = "dashboard.html";
    return false;
  }

  const usuarioTexto =
    usuarioActual.usuario ||
    usuarioActual.nombre_usuario ||
    usuarioActual.nombre_completo ||
    usuarioActual.nombres ||
    "Usuario";

  const usuarioActualElemento = document.getElementById("usuarioActual");
  const perfilActualElemento = document.getElementById("perfilActual");

  if (usuarioActualElemento) {
    usuarioActualElemento.textContent = usuarioTexto;
  }

  if (perfilActualElemento) {
    perfilActualElemento.textContent = perfil || "Perfil";
  }

  return true;
}

/* ---------------------------------------------------- */
/* API                                                  */
/* ---------------------------------------------------- */

async function consumirApiAuditoria(ruta) {
  if (window.apiGet) {
    return await window.apiGet(ruta);
  }

  const respuesta = await fetch(`${API_AUDITORIA_BASE}${ruta}`);

  if (!respuesta.ok) {
    const texto = await respuesta.text();
    throw new Error(texto || `Error HTTP ${respuesta.status}`);
  }

  return await respuesta.json();
}

async function enviarApiAuditoria(ruta, datos) {
  if (window.apiPost) {
    return await window.apiPost(ruta, datos);
  }

  const respuesta = await fetch(`${API_AUDITORIA_BASE}${ruta}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(datos),
  });

  if (!respuesta.ok) {
    const texto = await respuesta.text();
    throw new Error(texto || `Error HTTP ${respuesta.status}`);
  }

  return await respuesta.json();
}

/* ---------------------------------------------------- */
/* TEXTO SEGURO                                         */
/* ---------------------------------------------------- */

function valorSeguro(valor) {
  if (valor === null || valor === undefined || valor === "") {
    return "-";
  }

  return valor;
}

function textoSeguro(valor) {
  if (valor === null || valor === undefined) {
    return "";
  }

  return valor.toString().trim();
}

function escaparHtml(valor) {
  const texto = valorSeguro(valor).toString();

  return texto
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizarTexto(valor) {
  return textoSeguro(valor)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function normalizarFiltroSelect(valor) {
  const texto = normalizarTexto(valor);

  if (texto === "todos" || texto === "todas" || texto === "todo" || texto === "toda") {
    return "";
  }

  return texto;
}

/* ---------------------------------------------------- */
/* FECHAS Y HORAS                                       */
/* ---------------------------------------------------- */

function formatearHora(valor) {
  if (!valor) {
    return "-";
  }

  const texto = valor.toString();

  if (texto.includes(".")) {
    return texto.split(".")[0];
  }

  return texto;
}

function formatearTiempoConectado(valor) {
  if (!valor || valor === "-") {
    return "-";
  }

  const texto = valor.toString();

  if (texto.includes("day")) {
    return texto;
  }

  if (texto.includes(":")) {
    const partes = texto.split(":");

    const horas = parseInt(partes[0] || "0", 10);
    const minutos = parseInt(partes[1] || "0", 10);
    const segundos = parseInt((partes[2] || "0").split(".")[0], 10);

    if (horas > 0) {
      return `${horas}h ${minutos}m ${segundos}s`;
    }

    if (minutos > 0) {
      return `${minutos}m ${segundos}s`;
    }

    return `${segundos}s`;
  }

  return texto;
}

function fechaActualTexto() {
  const fecha = new Date();

  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");
  const hora = String(fecha.getHours()).padStart(2, "0");
  const minuto = String(fecha.getMinutes()).padStart(2, "0");
  const segundo = String(fecha.getSeconds()).padStart(2, "0");

  return `${anio}-${mes}-${dia} ${hora}:${minuto}:${segundo}`;
}

/* ---------------------------------------------------- */
/* NAVEGADOR / IP                                       */
/* ---------------------------------------------------- */

function obtenerIpAuditoria(registro) {
  return registro.ip_equipo || registro.ip_cliente || registro.ip || "-";
}

function obtenerNavegadorAuditoria(registro) {
  return registro.navegador || registro.user_agent || registro.agente_usuario || "-";
}

function resumirNavegador(navegador) {
  const texto = textoSeguro(navegador);

  if (!texto || texto === "-") {
    return "-";
  }

  if (texto.includes("Edg/")) return "Microsoft Edge";
  if (texto.includes("Chrome/")) return "Google Chrome";
  if (texto.includes("Firefox/")) return "Mozilla Firefox";
  if (texto.includes("Safari/") && !texto.includes("Chrome/")) return "Safari";
  if (texto.length > 45) return `${texto.substring(0, 45)}...`;

  return texto;
}

/* ---------------------------------------------------- */
/* CABECERAS DINÁMICAS                                  */
/* ---------------------------------------------------- */

function asegurarColumnaCabecera(tablaBodyId, claveNormalizada, titulo) {
  const tbody = document.getElementById(tablaBodyId);

  if (!tbody) return;

  const tabla = tbody.closest("table");

  if (!tabla) return;

  const filaCabecera = tabla.querySelector("thead tr");

  if (!filaCabecera) return;

  const existe = Array.from(filaCabecera.children).some((th) =>
    normalizarTexto(th.textContent).includes(claveNormalizada)
  );

  if (!existe) {
    const th = document.createElement("th");
    th.textContent = titulo;
    filaCabecera.appendChild(th);
  }
}

function prepararCabecerasAuditoria() {
  asegurarColumnaCabecera("tablaAuditoriaAccesos", "navegador", "Navegador");
  asegurarColumnaCabecera("tablaAuditoriaAcciones", "ip", "IP");
  asegurarColumnaCabecera("tablaAuditoriaAcciones", "navegador", "Navegador");
}

function obtenerTotalColumnasTabla(tablaBodyId, defecto) {
  const tbody = document.getElementById(tablaBodyId);

  if (!tbody) return defecto;

  const tabla = tbody.closest("table");

  if (!tabla) return defecto;

  const filaCabecera = tabla.querySelector("thead tr");

  if (!filaCabecera) return defecto;

  return filaCabecera.children.length || defecto;
}

/* ---------------------------------------------------- */
/* COLORES                                              */
/* ---------------------------------------------------- */

function obtenerClaseEstadoSesion(estado) {
  const estadoTexto = normalizarTexto(estado);

  if (estadoTexto.includes("activa")) {
    return "badge bg-success";
  }

  if (estadoTexto.includes("cerrada")) {
    return "badge bg-secondary";
  }

  return "badge bg-info text-dark";
}

function obtenerClasePerfil(perfil) {
  const texto = normalizarTexto(perfil);

  if (texto.includes("administrador")) return "badge-perfil perfil-administrador";
  if (texto.includes("gerente")) return "badge-perfil perfil-gerente";
  if (texto.includes("compras") || texto.includes("bascula")) return "badge-perfil perfil-compras";
  if (texto.includes("ventas")) return "badge-perfil perfil-ventas";
  if (texto.includes("inventario")) return "badge-perfil perfil-inventario";

  return "badge-perfil perfil-default";
}

function obtenerClaseModulo(modulo) {
  const texto = normalizarTexto(modulo);

  if (texto.includes("login")) return "badge-modulo modulo-login";
  if (texto.includes("panel") || texto.includes("dashboard")) return "badge-modulo modulo-panel";
  if (texto.includes("compra") || texto.includes("bascula")) return "badge-modulo modulo-compras";
  if (texto.includes("inventario")) return "badge-modulo modulo-inventario";
  if (texto.includes("produccion")) return "badge-modulo modulo-produccion";
  if (texto.includes("ventas")) return "badge-modulo modulo-ventas";
  if (texto.includes("talento") || texto.includes("humano")) return "badge-modulo modulo-talento";
  if (texto.includes("seguridad") || texto.includes("usuarios")) return "badge-modulo modulo-seguridad";
  if (texto.includes("auditoria")) return "badge-modulo modulo-auditoria";
  if (texto.includes("reporte") || texto.includes("ia")) return "badge-modulo modulo-reportes";
  if (texto.includes("activos")) return "badge-modulo modulo-activos";

  return "badge-modulo modulo-default";
}

function obtenerClaseAccion(accion) {
  const texto = normalizarTexto(accion).toUpperCase();

  if (texto.includes("ACCESO_DENEGADO")) return "badge-accion accion-denegado";
  if (texto.includes("LOGIN")) return "badge-accion accion-login";
  if (texto.includes("LOGOUT")) return "badge-accion accion-logout";
  if (texto.includes("INGRESO_MODULO")) return "badge-accion accion-modulo";
  if (texto.includes("CONSULTAR")) return "badge-accion accion-consultar";
  if (texto.includes("CREAR") || texto.includes("REGISTRAR") || texto.includes("GUARDAR")) return "badge-accion accion-crear";
  if (texto.includes("EDITAR") || texto.includes("MODIFICAR") || texto.includes("ACTUALIZAR")) return "badge-accion accion-editar";
  if (texto.includes("ELIMINAR")) return "badge-accion accion-eliminar";
  if (texto.includes("ANULAR")) return "badge-accion accion-anular";
  if (texto.includes("SUSPENDER") || texto.includes("INACTIVAR")) return "badge-accion accion-anular";
  if (texto.includes("CAMBIO_SUELDO")) return "badge-accion accion-editar";
  if (texto.includes("GENERAR_ROL")) return "badge-accion accion-reporte";
  if (texto.includes("REPORTE") || texto.includes("COMPROBANTE") || texto.includes("ARCHIVAR")) return "badge-accion accion-reporte";
  if (texto.includes("ERROR")) return "badge-accion accion-error";

  return "badge-accion accion-default";
}

function obtenerClaseFilaAccion(accion) {
  const texto = normalizarTexto(accion).toUpperCase();

  if (texto.includes("ACCESO_DENEGADO")) return "fila-denegada";

  if (
    texto.includes("ELIMINAR") ||
    texto.includes("ANULAR") ||
    texto.includes("EDITAR") ||
    texto.includes("MODIFICAR") ||
    texto.includes("ACTUALIZAR") ||
    texto.includes("SUSPENDER") ||
    texto.includes("INACTIVAR") ||
    texto.includes("CAMBIO_SUELDO") ||
    texto.includes("GENERAR_ROL")
  ) {
    return "fila-critica";
  }

  return "";
}

function obtenerClaseFilaAcceso(estado) {
  const texto = normalizarTexto(estado);

  if (texto.includes("activa")) return "fila-activa";

  return "";
}

/* ---------------------------------------------------- */
/* DATOS NORMALIZADOS                                   */
/* ---------------------------------------------------- */

function obtenerUsuarioAcceso(acceso) {
  return (
    acceso.usuario ||
    acceso.nombre_usuario ||
    acceso.nombre_completo ||
    acceso.nombres ||
    "-"
  );
}

function obtenerPerfilAcceso(acceso) {
  return acceso.nombre_perfil || acceso.perfil || "-";
}

function obtenerEstadoAcceso(acceso) {
  return acceso.estado_sesion || acceso.estado || "-";
}

function obtenerUsuarioAccion(accion) {
  return (
    accion.usuario ||
    accion.nombre_usuario ||
    accion.nombre_completo ||
    accion.nombres ||
    "-"
  );
}

function obtenerPerfilAccion(accion) {
  return accion.nombre_perfil || accion.perfil || "-";
}

function obtenerIdAccion(accion) {
  return accion.id_accion || accion.id_auditoria || accion.id || "-";
}

function obtenerLimiteRegistros() {
  const valor = document.getElementById("limiteRegistrosAuditoria")?.value || "50";
  const numero = Number(valor);

  if (Number.isNaN(numero) || numero <= 0) {
    return 50;
  }

  return numero;
}

/* ---------------------------------------------------- */
/* CARGAR ACCESOS Y ACCIONES                            */
/* ---------------------------------------------------- */

async function cargarAccesosAuditoria() {
  const tabla = document.getElementById("tablaAuditoriaAccesos");
  const estadoCarga = document.getElementById("estadoCargaAuditoria");

  if (!tabla) return;

  try {
    const limite = obtenerLimiteRegistros();
    const offset = paginaAccesos * limite;
    const totalColumnas = obtenerTotalColumnasTabla("tablaAuditoriaAccesos", 11);

    if (estadoCarga) estadoCarga.textContent = "Cargando accesos...";

    tabla.innerHTML = `
      <tr>
        <td colspan="${totalColumnas}" class="text-center text-muted">
          Cargando accesos...
        </td>
      </tr>
    `;

    const datos = await consumirApiAuditoria(`/api/auditoria/accesos?limite=${limite}&offset=${offset}`);

    accesosAuditoria = Array.isArray(datos) ? datos : datos.accesos || datos.data || [];
    accesosFiltradosActuales = [...accesosAuditoria];

    renderizarAccesosAuditoria(accesosFiltradosActuales);
    actualizarTextoPaginacion();

    if (estadoCarga) estadoCarga.textContent = "Accesos cargados";
  } catch (error) {
    const totalColumnas = obtenerTotalColumnasTabla("tablaAuditoriaAccesos", 11);

    tabla.innerHTML = `
      <tr>
        <td colspan="${totalColumnas}" class="text-center text-danger">
          Error al cargar accesos: ${escaparHtml(error.message)}
        </td>
      </tr>
    `;

    if (estadoCarga) estadoCarga.textContent = "Error al cargar accesos";
  }
}

async function cargarAccionesAuditoria() {
  const tabla = document.getElementById("tablaAuditoriaAcciones");
  const estadoCarga = document.getElementById("estadoCargaAuditoria");

  if (!tabla) return;

  try {
    const limite = obtenerLimiteRegistros();
    const offset = paginaAcciones * limite;
    const totalColumnas = obtenerTotalColumnasTabla("tablaAuditoriaAcciones", 12);

    if (estadoCarga) estadoCarga.textContent = "Cargando acciones...";

    tabla.innerHTML = `
      <tr>
        <td colspan="${totalColumnas}" class="text-center text-muted">
          Cargando acciones...
        </td>
      </tr>
    `;

    const datos = await consumirApiAuditoria(`/api/auditoria/acciones?limite=${limite}&offset=${offset}`);

    accionesAuditoria = Array.isArray(datos) ? datos : datos.acciones || datos.data || [];
    accionesFiltradasActuales = [...accionesAuditoria];

    renderizarAccionesAuditoria(accionesFiltradasActuales);
    actualizarTextoPaginacion();

    if (estadoCarga) estadoCarga.textContent = "Auditoría cargada correctamente";
  } catch (error) {
    const totalColumnas = obtenerTotalColumnasTabla("tablaAuditoriaAcciones", 12);

    tabla.innerHTML = `
      <tr>
        <td colspan="${totalColumnas}" class="text-center text-danger">
          Error al cargar acciones: ${escaparHtml(error.message)}
        </td>
      </tr>
    `;

    if (estadoCarga) estadoCarga.textContent = "Error al cargar acciones";
  }
}

async function cargarResumenGeneralAuditoria() {
  try {
    const resumen = await consumirApiAuditoria("/api/auditoria/resumen");

    const usuariosConectados = document.getElementById("usuariosConectados");
    const ingresosRegistrados = document.getElementById("ingresosRegistrados");
    const accionesRegistradas = document.getElementById("accionesRegistradas");
    const accesosDenegados = document.getElementById("accesosDenegados");
    const accionesCriticas = document.getElementById("accionesCriticas");
    const ultimoAcceso = document.getElementById("ultimoAcceso");

    if (usuariosConectados) usuariosConectados.textContent = resumen.usuarios_conectados ?? 0;
    if (ingresosRegistrados) ingresosRegistrados.textContent = resumen.ingresos_registrados ?? 0;
    if (accionesRegistradas) accionesRegistradas.textContent = resumen.acciones_registradas ?? 0;
    if (accesosDenegados) accesosDenegados.textContent = resumen.accesos_denegados ?? 0;
    if (accionesCriticas) accionesCriticas.textContent = resumen.acciones_criticas ?? 0;
    if (ultimoAcceso) ultimoAcceso.textContent = resumen.ultimo_acceso || "Sin datos";
  } catch (error) {
    console.warn("No se pudo cargar resumen general desde backend:", error);
    actualizarResumenAuditoria();
  }
}

async function recargarAuditoriaCompleta() {
  const estadoCarga = document.getElementById("estadoCargaAuditoria");

  if (estadoCarga) estadoCarga.textContent = "Recargando auditoría...";

  prepararCabecerasAuditoria();

  await cargarAccesosAuditoria();
  await cargarAccionesAuditoria();
  await cargarResumenMantenimientoAuditoria();
  await cargarResumenGeneralAuditoria();

  if (estadoCarga) estadoCarga.textContent = "Auditoría recargada correctamente";
}

/* ---------------------------------------------------- */
/* RENDERIZAR TABLAS                                    */
/* ---------------------------------------------------- */

function renderizarAccesosAuditoria(listaAccesos) {
  const tabla = document.getElementById("tablaAuditoriaAccesos");
  const contador = document.getElementById("contadorAccesos");

  if (!tabla) return;

  const totalColumnas = obtenerTotalColumnasTabla("tablaAuditoriaAccesos", 11);

  if (contador) contador.textContent = `${listaAccesos.length} registros`;

  if (!listaAccesos || listaAccesos.length === 0) {
    tabla.innerHTML = `
      <tr>
        <td colspan="${totalColumnas}" class="text-center text-muted">
          No existen accesos registrados con los filtros aplicados.
        </td>
      </tr>
    `;

    actualizarResumenAuditoria();
    return;
  }

  tabla.innerHTML = "";

  listaAccesos.forEach((acceso) => {
    const usuario = obtenerUsuarioAcceso(acceso);
    const perfil = obtenerPerfilAcceso(acceso);
    const estadoSesion = obtenerEstadoAcceso(acceso);
    const navegador = obtenerNavegadorAuditoria(acceso);

    const fila = document.createElement("tr");
    fila.className = obtenerClaseFilaAcceso(estadoSesion);
    fila.title = `Navegador: ${navegador}`;

    fila.innerHTML = `
      <td>${escaparHtml(acceso.id_acceso)}</td>
      <td><strong>${escaparHtml(usuario)}</strong></td>
      <td>
        <span class="${obtenerClasePerfil(perfil)}">${escaparHtml(perfil)}</span>
      </td>
      <td>${escaparHtml(acceso.fecha_ingreso)}</td>
      <td>${escaparHtml(formatearHora(acceso.hora_ingreso))}</td>
      <td>${escaparHtml(acceso.fecha_salida)}</td>
      <td>${escaparHtml(formatearHora(acceso.hora_salida))}</td>
      <td>${escaparHtml(formatearTiempoConectado(acceso.tiempo_conectado))}</td>
      <td>${escaparHtml(obtenerIpAuditoria(acceso))}</td>
      <td>
        <span class="${obtenerClaseEstadoSesion(estadoSesion)}">${escaparHtml(estadoSesion)}</span>
      </td>
      <td title="${escaparHtml(navegador)}">${escaparHtml(resumirNavegador(navegador))}</td>
    `;

    tabla.appendChild(fila);
  });

  actualizarResumenAuditoria();
}

function renderizarAccionesAuditoria(listaAcciones) {
  const tabla = document.getElementById("tablaAuditoriaAcciones");
  const contador = document.getElementById("contadorAcciones");

  if (!tabla) return;

  const totalColumnas = obtenerTotalColumnasTabla("tablaAuditoriaAcciones", 12);

  if (contador) contador.textContent = `${listaAcciones.length} registros`;

  if (!listaAcciones || listaAcciones.length === 0) {
    tabla.innerHTML = `
      <tr>
        <td colspan="${totalColumnas}" class="text-center text-muted">
          No existen acciones registradas con los filtros aplicados.
        </td>
      </tr>
    `;

    actualizarResumenAuditoria();
    return;
  }

  tabla.innerHTML = "";

  listaAcciones.forEach((accion) => {
    const usuario = obtenerUsuarioAccion(accion);
    const perfil = obtenerPerfilAccion(accion);
    const modulo = accion.modulo || "-";
    const accionTexto = accion.accion || "-";
    const ipEquipo = obtenerIpAuditoria(accion);
    const navegador = obtenerNavegadorAuditoria(accion);

    const fila = document.createElement("tr");
    fila.className = obtenerClaseFilaAccion(accionTexto);
    fila.title = `IP: ${ipEquipo} | Navegador: ${navegador}`;

    fila.innerHTML = `
      <td>${escaparHtml(obtenerIdAccion(accion))}</td>
      <td><strong>${escaparHtml(usuario)}</strong></td>
      <td>
        <span class="${obtenerClasePerfil(perfil)}">${escaparHtml(perfil)}</span>
      </td>
      <td>
        <span class="${obtenerClaseModulo(modulo)}">${escaparHtml(modulo)}</span>
      </td>
      <td>
        <span class="${obtenerClaseAccion(accionTexto)}">${escaparHtml(accionTexto)}</span>
      </td>
      <td>${escaparHtml(accion.descripcion)}</td>
      <td>${escaparHtml(accion.tabla_afectada)}</td>
      <td>${escaparHtml(accion.id_registro_afectado)}</td>
      <td>${escaparHtml(accion.fecha_accion)}</td>
      <td>${escaparHtml(formatearHora(accion.hora_accion))}</td>
      <td>${escaparHtml(ipEquipo)}</td>
      <td title="${escaparHtml(navegador)}">${escaparHtml(resumirNavegador(navegador))}</td>
    `;

    tabla.appendChild(fila);
  });

  actualizarResumenAuditoria();
}

/* ---------------------------------------------------- */
/* RESUMEN PRINCIPAL                                    */
/* ---------------------------------------------------- */

function esAccionCriticaAuditoria(accion) {
  const accionTexto = normalizarTexto(accion).toUpperCase();

  return (
    accionTexto.includes("ELIMINAR") ||
    accionTexto.includes("ANULAR") ||
    accionTexto.includes("EDITAR") ||
    accionTexto.includes("MODIFICAR") ||
    accionTexto.includes("ACTUALIZAR") ||
    accionTexto.includes("SUSPENDER") ||
    accionTexto.includes("INACTIVAR") ||
    accionTexto.includes("CAMBIO_SUELDO") ||
    accionTexto.includes("GENERAR_ROL") ||
    accionTexto.includes("ACCESO_DENEGADO")
  );
}

function actualizarResumenAuditoria() {
  const usuariosConectados = document.getElementById("usuariosConectados");
  const ingresosRegistrados = document.getElementById("ingresosRegistrados");
  const accionesRegistradas = document.getElementById("accionesRegistradas");
  const accesosDenegados = document.getElementById("accesosDenegados");
  const accionesCriticas = document.getElementById("accionesCriticas");
  const ultimoAcceso = document.getElementById("ultimoAcceso");

  const accesosParaResumen = accesosFiltradosActuales || [];
  const accionesParaResumen = accionesFiltradasActuales || [];

  const sesionesActivas = accesosParaResumen.filter((acceso) => {
    const estado = normalizarTexto(obtenerEstadoAcceso(acceso));
    return estado.includes("activa");
  });

  const denegados = accionesParaResumen.filter((accion) => {
    const accionTexto = normalizarTexto(accion.accion).toUpperCase();
    return accionTexto.includes("ACCESO_DENEGADO") || accionTexto.includes("DENEGADO");
  });

  const criticas = accionesParaResumen.filter((accion) => {
    return esAccionCriticaAuditoria(accion.accion);
  });

  if (usuariosConectados) usuariosConectados.textContent = sesionesActivas.length;
  if (ingresosRegistrados) ingresosRegistrados.textContent = accesosParaResumen.length;
  if (accionesRegistradas) accionesRegistradas.textContent = accionesParaResumen.length;
  if (accesosDenegados) accesosDenegados.textContent = denegados.length;
  if (accionesCriticas) accionesCriticas.textContent = criticas.length;

  if (ultimoAcceso) {
    if (accesosParaResumen.length > 0) {
      ultimoAcceso.textContent = accesosParaResumen[0].fecha_ingreso || "Sin datos";
    } else {
      ultimoAcceso.textContent = "Sin datos";
    }
  }
}

/* ---------------------------------------------------- */
/* FILTROS                                              */
/* ---------------------------------------------------- */

function aplicarFiltrosAuditoria() {
  const filtroUsuario = normalizarTexto(document.getElementById("filtroUsuario")?.value || "");
  const filtroPerfil = normalizarFiltroSelect(document.getElementById("filtroPerfil")?.value || "");
  const filtroModulo = normalizarFiltroSelect(document.getElementById("filtroModulo")?.value || "");
  const filtroAccion = normalizarFiltroSelect(document.getElementById("filtroAccion")?.value || "").toUpperCase();
  const filtroFechaDesde = document.getElementById("filtroFechaDesde")?.value || "";
  const filtroFechaHasta = document.getElementById("filtroFechaHasta")?.value || "";
  const filtroEstadoSesion = normalizarFiltroSelect(document.getElementById("filtroEstadoSesion")?.value || "");

  accesosFiltradosActuales = accesosAuditoria.filter((acceso) => {
    const usuario = normalizarTexto(obtenerUsuarioAcceso(acceso));
    const perfil = normalizarTexto(obtenerPerfilAcceso(acceso));
    const estado = normalizarTexto(obtenerEstadoAcceso(acceso));
    const fecha = acceso.fecha_ingreso || "";

    return (
      (filtroUsuario === "" || usuario.includes(filtroUsuario)) &&
      (filtroPerfil === "" || perfil === filtroPerfil) &&
      (filtroEstadoSesion === "" || estado === filtroEstadoSesion) &&
      (filtroFechaDesde === "" || fecha >= filtroFechaDesde) &&
      (filtroFechaHasta === "" || fecha <= filtroFechaHasta)
    );
  });

  accionesFiltradasActuales = accionesAuditoria.filter((accion) => {
    const usuario = normalizarTexto(obtenerUsuarioAccion(accion));
    const perfil = normalizarTexto(obtenerPerfilAccion(accion));
    const modulo = normalizarTexto(accion.modulo || "");
    const accionTexto = normalizarTexto(accion.accion || "").toUpperCase();
    const fecha = accion.fecha_accion || "";

    return (
      (filtroUsuario === "" || usuario.includes(filtroUsuario)) &&
      (filtroPerfil === "" || perfil === filtroPerfil) &&
      (filtroModulo === "" || modulo === filtroModulo) &&
      (filtroAccion === "" || accionTexto === filtroAccion) &&
      (filtroFechaDesde === "" || fecha >= filtroFechaDesde) &&
      (filtroFechaHasta === "" || fecha <= filtroFechaHasta)
    );
  });

  renderizarAccesosAuditoria(accesosFiltradosActuales);
  renderizarAccionesAuditoria(accionesFiltradasActuales);

  const estadoCarga = document.getElementById("estadoCargaAuditoria");
  if (estadoCarga) estadoCarga.textContent = "Filtros aplicados";
}

function limpiarFiltrosAuditoria() {
  const campos = [
    "filtroUsuario",
    "filtroPerfil",
    "filtroModulo",
    "filtroAccion",
    "filtroFechaDesde",
    "filtroFechaHasta",
    "filtroEstadoSesion",
  ];

  campos.forEach((id) => {
    const campo = document.getElementById(id);
    if (campo) campo.value = "";
  });

  accesosFiltradosActuales = [...accesosAuditoria];
  accionesFiltradasActuales = [...accionesAuditoria];

  renderizarAccesosAuditoria(accesosFiltradosActuales);
  renderizarAccionesAuditoria(accionesFiltradasActuales);

  cargarResumenGeneralAuditoria();

  const estadoCarga = document.getElementById("estadoCargaAuditoria");
  if (estadoCarga) estadoCarga.textContent = "Filtros limpiados";
}

/* ---------------------------------------------------- */
/* PAGINACIÓN                                           */
/* ---------------------------------------------------- */

function actualizarTextoPaginacion() {
  const paginaAccesosTexto = document.getElementById("paginaAccesosTexto");
  const paginaAccionesTexto = document.getElementById("paginaAccionesTexto");

  if (paginaAccesosTexto) {
    paginaAccesosTexto.textContent = `Página de accesos: ${paginaAccesos + 1}`;
  }

  if (paginaAccionesTexto) {
    paginaAccionesTexto.textContent = `Página de acciones: ${paginaAcciones + 1}`;
  }
}

async function paginaAnteriorAccesos() {
  if (paginaAccesos > 0) {
    paginaAccesos--;
    await cargarAccesosAuditoria();
    await cargarResumenGeneralAuditoria();
  }
}

async function paginaSiguienteAccesos() {
  paginaAccesos++;
  await cargarAccesosAuditoria();

  if (accesosAuditoria.length === 0 && paginaAccesos > 0) {
    paginaAccesos--;
    await cargarAccesosAuditoria();
  }

  await cargarResumenGeneralAuditoria();
}

async function paginaAnteriorAcciones() {
  if (paginaAcciones > 0) {
    paginaAcciones--;
    await cargarAccionesAuditoria();
    await cargarResumenGeneralAuditoria();
  }
}

async function paginaSiguienteAcciones() {
  paginaAcciones++;
  await cargarAccionesAuditoria();

  if (accionesAuditoria.length === 0 && paginaAcciones > 0) {
    paginaAcciones--;
    await cargarAccionesAuditoria();
  }

  await cargarResumenGeneralAuditoria();
}

async function reiniciarPaginacionYCargar() {
  paginaAccesos = 0;
  paginaAcciones = 0;
  actualizarTextoPaginacion();
  await recargarAuditoriaCompleta();
}

/* ---------------------------------------------------- */
/* COMPROBANTE                                          */
/* ---------------------------------------------------- */

function obtenerDescripcionFiltros() {
  return {
    usuario: document.getElementById("filtroUsuario")?.value || "Todos",
    perfil: document.getElementById("filtroPerfil")?.value || "Todos",
    modulo: document.getElementById("filtroModulo")?.value || "Todos",
    accion: document.getElementById("filtroAccion")?.value || "Todas",
    fechaDesde: document.getElementById("filtroFechaDesde")?.value || "Sin fecha inicial",
    fechaHasta: document.getElementById("filtroFechaHasta")?.value || "Sin fecha final",
    estadoSesion: document.getElementById("filtroEstadoSesion")?.value || "Todos",
  };
}

function generarFilasComprobanteAccesos() {
  if (!accesosFiltradosActuales || accesosFiltradosActuales.length === 0) {
    return `<tr><td colspan="10" style="text-align:center;">No existen accesos registrados.</td></tr>`;
  }

  return accesosFiltradosActuales.map((acceso) => `
    <tr>
      <td>${escaparHtml(acceso.id_acceso)}</td>
      <td>${escaparHtml(obtenerUsuarioAcceso(acceso))}</td>
      <td>${escaparHtml(obtenerPerfilAcceso(acceso))}</td>
      <td>${escaparHtml(acceso.fecha_ingreso)}</td>
      <td>${escaparHtml(formatearHora(acceso.hora_ingreso))}</td>
      <td>${escaparHtml(acceso.fecha_salida)}</td>
      <td>${escaparHtml(formatearHora(acceso.hora_salida))}</td>
      <td>${escaparHtml(formatearTiempoConectado(acceso.tiempo_conectado))}</td>
      <td>${escaparHtml(obtenerIpAuditoria(acceso))}</td>
      <td>${escaparHtml(obtenerEstadoAcceso(acceso))}</td>
    </tr>
  `).join("");
}

function generarFilasComprobanteAcciones() {
  if (!accionesFiltradasActuales || accionesFiltradasActuales.length === 0) {
    return `<tr><td colspan="10" style="text-align:center;">No existen acciones registradas.</td></tr>`;
  }

  return accionesFiltradasActuales.map((accion) => `
    <tr>
      <td>${escaparHtml(obtenerIdAccion(accion))}</td>
      <td>${escaparHtml(obtenerUsuarioAccion(accion))}</td>
      <td>${escaparHtml(obtenerPerfilAccion(accion))}</td>
      <td>${escaparHtml(accion.modulo)}</td>
      <td>${escaparHtml(accion.accion)}</td>
      <td>${escaparHtml(accion.descripcion)}</td>
      <td>${escaparHtml(accion.tabla_afectada)}</td>
      <td>${escaparHtml(accion.id_registro_afectado)}</td>
      <td>${escaparHtml(obtenerIpAuditoria(accion))}</td>
      <td>${escaparHtml(accion.fecha_accion)} ${escaparHtml(formatearHora(accion.hora_accion))}</td>
    </tr>
  `).join("");
}

async function generarComprobanteAuditoria() {
  aplicarFiltrosAuditoria();

  const filtros = obtenerDescripcionFiltros();
  const usuarioActual = obtenerUsuarioSesionAuditoria();

  const usuarioGenerador =
    usuarioActual?.usuario ||
    usuarioActual?.nombre_usuario ||
    usuarioActual?.nombre_completo ||
    "Usuario";

  const perfilGenerador =
    usuarioActual?.perfil ||
    usuarioActual?.nombre_perfil ||
    "Perfil";

  const totalDenegados = accionesFiltradasActuales.filter((accion) =>
    normalizarTexto(accion.accion).toUpperCase().includes("ACCESO_DENEGADO")
  ).length;

  const totalCriticas = accionesFiltradasActuales.filter((accion) => {
    return esAccionCriticaAuditoria(accion.accion);
  }).length;

  const contenido = `
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="UTF-8">
        <title>Comprobante de Auditoría</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 30px; color: #222; }
          .encabezado { border-bottom: 3px solid #198754; padding-bottom: 12px; margin-bottom: 20px; }
          .encabezado h1 { color: #198754; margin: 0; font-size: 24px; }
          .encabezado p { margin: 4px 0; font-size: 13px; }
          .bloque { border: 1px solid #ccc; border-radius: 8px; padding: 12px; margin-bottom: 18px; }
          .bloque h2 { font-size: 18px; color: #198754; margin-top: 0; }
          .resumen { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 18px; }
          .resumen div { border: 1px solid #ccc; border-left: 5px solid #198754; padding: 10px; border-radius: 6px; }
          .resumen strong { display: block; font-size: 22px; color: #198754; }
          table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10px; }
          th { background: #198754; color: white; padding: 6px; border: 1px solid #0f5132; }
          td { padding: 5px; border: 1px solid #ccc; vertical-align: top; }
          .nota { font-size: 12px; color: #555; margin-top: 20px; }
          .firma { margin-top: 45px; display: flex; justify-content: space-between; }
          .firma div { width: 40%; text-align: center; border-top: 1px solid #333; padding-top: 6px; font-size: 12px; }
          @media print { button { display: none; } body { margin: 18px; } }
        </style>
      </head>
      <body>
        <div class="encabezado">
          <h1>ERP Piladora Don Guillo</h1>
          <p><strong>Comprobante de Auditoría del Sistema</strong></p>
          <p>Generado por: ${escaparHtml(usuarioGenerador)} - ${escaparHtml(perfilGenerador)}</p>
          <p>Fecha y hora de generación: ${escaparHtml(fechaActualTexto())}</p>
        </div>

        <div class="bloque">
          <h2>Filtros aplicados</h2>
          <p><strong>Usuario:</strong> ${escaparHtml(filtros.usuario)}</p>
          <p><strong>Perfil:</strong> ${escaparHtml(filtros.perfil)}</p>
          <p><strong>Módulo:</strong> ${escaparHtml(filtros.modulo)}</p>
          <p><strong>Acción:</strong> ${escaparHtml(filtros.accion)}</p>
          <p><strong>Estado de sesión:</strong> ${escaparHtml(filtros.estadoSesion)}</p>
          <p><strong>Fecha desde:</strong> ${escaparHtml(filtros.fechaDesde)}</p>
          <p><strong>Fecha hasta:</strong> ${escaparHtml(filtros.fechaHasta)}</p>
        </div>

        <div class="resumen">
          <div><span>Accesos</span><strong>${accesosFiltradosActuales.length}</strong></div>
          <div><span>Acciones</span><strong>${accionesFiltradasActuales.length}</strong></div>
          <div><span>Accesos denegados</span><strong>${totalDenegados}</strong></div>
          <div><span>Acciones críticas</span><strong>${totalCriticas}</strong></div>
        </div>

        <div class="bloque">
          <h2>Historial de accesos</h2>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Usuario</th>
                <th>Perfil</th>
                <th>Fecha ingreso</th>
                <th>Hora ingreso</th>
                <th>Fecha salida</th>
                <th>Hora salida</th>
                <th>Tiempo</th>
                <th>IP</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>${generarFilasComprobanteAccesos()}</tbody>
          </table>
        </div>

        <div class="bloque">
          <h2>Acciones registradas</h2>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Usuario</th>
                <th>Perfil</th>
                <th>Módulo</th>
                <th>Acción</th>
                <th>Descripción</th>
                <th>Tabla afectada</th>
                <th>ID registro</th>
                <th>IP</th>
                <th>Fecha y hora</th>
              </tr>
            </thead>
            <tbody>${generarFilasComprobanteAcciones()}</tbody>
          </table>
        </div>

        <p class="nota">
          Nota: este comprobante se genera a partir de la información registrada en el módulo de auditoría.
          Sirve como evidencia de accesos, acciones, intentos denegados y operaciones realizadas dentro del ERP.
        </p>

        <div class="firma">
          <div>Responsable del sistema</div>
          <div>Revisión administrativa</div>
        </div>

        <br>
        <button onclick="window.print()">Imprimir o guardar como PDF</button>
      </body>
    </html>
  `;

  const ventana = window.open("", "_blank", "width=1200,height=800");

  if (!ventana) {
    alert("El navegador bloqueó la ventana emergente. Permita ventanas emergentes para generar el comprobante.");
    return;
  }

  ventana.document.open();
  ventana.document.write(contenido);
  ventana.document.close();

  await registrarAuditoriaAutomatica(
    "Auditoría",
    "GENERAR_COMPROBANTE",
    "El usuario generó un comprobante de auditoría con los filtros aplicados.",
    "auditoria_acciones",
    null
  );
}

/* ---------------------------------------------------- */
/* MANTENIMIENTO DE AUDITORÍA                           */
/* ---------------------------------------------------- */

async function cargarResumenMantenimientoAuditoria() {
  const mensaje = document.getElementById("mensajeMantenimientoAuditoria");

  try {
    const datos = await consumirApiAuditoria("/api/auditoria/mantenimiento/resumen");
    const resumen = datos.resumen || datos;

    const mantAccesosActuales = document.getElementById("mantAccesosActuales");
    const mantAccionesActuales = document.getElementById("mantAccionesActuales");
    const mantAccesosHistoricos = document.getElementById("mantAccesosHistoricos");
    const mantAccionesHistoricas = document.getElementById("mantAccionesHistoricas");
    const mantSesionesActivas = document.getElementById("mantSesionesActivas");
    const mantSesionesAntiguas = document.getElementById("mantSesionesAntiguas");

    if (mantAccesosActuales) mantAccesosActuales.textContent = resumen.accesos_actuales || 0;
    if (mantAccionesActuales) mantAccionesActuales.textContent = resumen.acciones_actuales || 0;
    if (mantAccesosHistoricos) mantAccesosHistoricos.textContent = resumen.accesos_historicos || 0;
    if (mantAccionesHistoricas) mantAccionesHistoricas.textContent = resumen.acciones_historicas || 0;
    if (mantSesionesActivas) mantSesionesActivas.textContent = resumen.sesiones_activas || 0;
    if (mantSesionesAntiguas) mantSesionesAntiguas.textContent = resumen.sesiones_activas_antiguas || 0;

    if (mensaje) mensaje.textContent = "Resumen de mantenimiento actualizado.";
  } catch (error) {
    if (mensaje) mensaje.textContent = `Error al cargar mantenimiento: ${error.message}`;
    console.error("Error al cargar resumen de mantenimiento:", error);
  }
}

async function cerrarSesionesAntiguasAuditoria() {
  const horas = Number(document.getElementById("horasCerrarSesionesAntiguas")?.value || 12);
  const mensaje = document.getElementById("mensajeMantenimientoAuditoria");

  if (horas < 1) {
    alert("Las horas deben ser mayores o iguales a 1.");
    return;
  }

  const confirmar = confirm(
    `Se cerrarán las sesiones activas con más de ${horas} hora(s) de antigüedad. ¿Desea continuar?`
  );

  if (!confirmar) return;

  try {
    if (mensaje) mensaje.textContent = "Cerrando sesiones antiguas...";

    const respuesta = await enviarApiAuditoria("/api/auditoria/mantenimiento/cerrar-sesiones-antiguas", {
      horas_antiguedad: horas,
    });

    alert(`Proceso terminado. Sesiones cerradas: ${respuesta.sesiones_cerradas || 0}`);

    await recargarAuditoriaCompleta();
  } catch (error) {
    alert(`Error al cerrar sesiones antiguas: ${error.message}`);
    if (mensaje) mensaje.textContent = "Error al cerrar sesiones antiguas.";
  }
}

async function archivarAuditoriaAntigua() {
  const dias = Number(document.getElementById("diasArchivarAuditoria")?.value || 30);
  const mensaje = document.getElementById("mensajeMantenimientoAuditoria");
  const usuarioActual = obtenerUsuarioSesionAuditoria();

  if (dias < 1) {
    alert("Los días deben ser mayores o iguales a 1.");
    return;
  }

  const confirmar = confirm(
    `Se moverán al histórico los accesos cerrados y acciones con más de ${dias} día(s). No se borrará evidencia, solo se archivará. ¿Desea continuar?`
  );

  if (!confirmar) return;

  try {
    if (mensaje) mensaje.textContent = "Archivando auditoría antigua...";

    const respuesta = await enviarApiAuditoria("/api/auditoria/mantenimiento/archivar", {
      dias_antiguedad: dias,
      id_usuario_admin:
        usuarioActual?.id_usuario ||
        usuarioActual?.id ||
        usuarioActual?.usuario_id ||
        null,
    });

    alert(
      `Auditoría archivada correctamente.\n` +
      `Accesos archivados: ${respuesta.accesos_archivados || 0}\n` +
      `Acciones archivadas: ${respuesta.acciones_archivadas || 0}`
    );

    await recargarAuditoriaCompleta();
  } catch (error) {
    alert(`Error al archivar auditoría: ${error.message}`);
    if (mensaje) mensaje.textContent = "Error al archivar auditoría.";
  }
}

/* ---------------------------------------------------- */
/* REGISTRAR AUDITORÍA AUTOMÁTICA                       */
/* ---------------------------------------------------- */

async function registrarAuditoriaAutomatica(
  modulo,
  accion,
  descripcion,
  tablaAfectada = null,
  idRegistroAfectado = null
) {
  const usuarioActual = obtenerUsuarioSesionAuditoria();

  if (!usuarioActual) return;

  const idUsuario =
    usuarioActual.id_usuario ||
    usuarioActual.id ||
    usuarioActual.usuario_id;

  if (!idUsuario) {
    console.warn("No se pudo registrar auditoría: usuario sin id.");
    return;
  }

  const datosAuditoria = {
    id_usuario: Number(idUsuario),
    modulo: modulo,
    accion: accion,
    descripcion: descripcion,
    tabla_afectada: tablaAfectada,
    id_registro_afectado: idRegistroAfectado,
  };

  try {
    await enviarApiAuditoria("/api/auditoria/registrar-accion", datosAuditoria);
  } catch (error) {
    console.error("Error al registrar auditoría automática:", error);
  }
}

window.registrarAuditoriaAutomatica = registrarAuditoriaAutomatica;

if (!window.registrarAccionSistema) {
  window.registrarAccionSistema = registrarAuditoriaAutomatica;
}

/* ---------------------------------------------------- */
/* INICIALIZAR MÓDULO                                   */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  if (auditoriaInicializada) return;
  auditoriaInicializada = true;

  const accesoPermitido = validarAccesoAuditoria();

  if (!accesoPermitido) return;

  prepararCabecerasAuditoria();

  const btnAplicarFiltros = document.getElementById("btnAplicarFiltros");
  const btnLimpiarFiltros = document.getElementById("btnLimpiarFiltros");
  const btnGenerarComprobante = document.getElementById("btnGenerarComprobante");
  const btnRecargarAuditoria = document.getElementById("btnRecargarAuditoria");

  const btnAnteriorAccesos = document.getElementById("btnAnteriorAccesos");
  const btnSiguienteAccesos = document.getElementById("btnSiguienteAccesos");
  const btnAnteriorAcciones = document.getElementById("btnAnteriorAcciones");
  const btnSiguienteAcciones = document.getElementById("btnSiguienteAcciones");

  const limiteRegistrosAuditoria = document.getElementById("limiteRegistrosAuditoria");

  const btnCerrarSesionesAntiguas = document.getElementById("btnCerrarSesionesAntiguas");
  const btnArchivarAuditoria = document.getElementById("btnArchivarAuditoria");
  const btnActualizarResumenMantenimiento = document.getElementById("btnActualizarResumenMantenimiento");

  if (btnAplicarFiltros) btnAplicarFiltros.addEventListener("click", aplicarFiltrosAuditoria);
  if (btnLimpiarFiltros) btnLimpiarFiltros.addEventListener("click", limpiarFiltrosAuditoria);
  if (btnGenerarComprobante) btnGenerarComprobante.addEventListener("click", generarComprobanteAuditoria);
  if (btnRecargarAuditoria) btnRecargarAuditoria.addEventListener("click", reiniciarPaginacionYCargar);

  if (btnAnteriorAccesos) btnAnteriorAccesos.addEventListener("click", paginaAnteriorAccesos);
  if (btnSiguienteAccesos) btnSiguienteAccesos.addEventListener("click", paginaSiguienteAccesos);
  if (btnAnteriorAcciones) btnAnteriorAcciones.addEventListener("click", paginaAnteriorAcciones);
  if (btnSiguienteAcciones) btnSiguienteAcciones.addEventListener("click", paginaSiguienteAcciones);

  if (limiteRegistrosAuditoria) {
    limiteRegistrosAuditoria.addEventListener("change", reiniciarPaginacionYCargar);
  }

  if (btnCerrarSesionesAntiguas) {
    btnCerrarSesionesAntiguas.addEventListener("click", cerrarSesionesAntiguasAuditoria);
  }

  if (btnArchivarAuditoria) {
    btnArchivarAuditoria.addEventListener("click", archivarAuditoriaAntigua);
  }

  if (btnActualizarResumenMantenimiento) {
    btnActualizarResumenMantenimiento.addEventListener("click", cargarResumenMantenimientoAuditoria);
  }

  await recargarAuditoriaCompleta();

  if (REGISTRAR_INGRESO_AUDITORIA_DESDE_ESTE_ARCHIVO) {
    await registrarAuditoriaAutomatica(
      "Auditoría",
      "INGRESO_MODULO",
      "El usuario ingresó al módulo Auditoría.",
      "auditoria_acciones",
      null
    );
  }
});