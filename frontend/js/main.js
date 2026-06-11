/* ---------------------------------------------------- */
/* SISTEMA ERP PILADORA DON GUILLO - ARCHIVO PRINCIPAL  */
/* ---------------------------------------------------- */

/* ---------------------------------------------------- */
/* VARIABLES GLOBALES DE SESIÓN                         */
/* ---------------------------------------------------- */

const usuarioGuardado = localStorage.getItem("usuarioERP");
const perfilGuardado = localStorage.getItem("perfilERP");
const idUsuarioGuardado = localStorage.getItem("idUsuarioERP");
const idAccesoGuardado = localStorage.getItem("idAccesoERP");

/* ---------------------------------------------------- */
/* FUNCIONES GENERALES                                  */
/* ---------------------------------------------------- */

function obtenerFechaActualISO() {
  const hoy = new Date();
  const anio = hoy.getFullYear();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");
  return `${anio}-${mes}-${dia}`;
}

function obtenerHoraActual() {
  const ahora = new Date();
  const horas = String(ahora.getHours()).padStart(2, "0");
  const minutos = String(ahora.getMinutes()).padStart(2, "0");
  const segundos = String(ahora.getSeconds()).padStart(2, "0");
  return `${horas}:${minutos}:${segundos}`;
}

async function apiPutLocal(ruta, datos) {
  const respuesta = await fetch(`https://erp-piladora-don-guillo.onrender.com${ruta}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(datos),
  });

  const resultado = await respuesta.json();

  if (!respuesta.ok) {
    throw new Error(resultado.detail || "Error en la petición.");
  }

  return resultado;
}

/* ---------------------------------------------------- */
/* VALIDACIÓN DE CÉDULA Y RUC ECUADOR                   */
/* ---------------------------------------------------- */

function validarCedulaEcuador(cedula) {
  if (!/^\d{10}$/.test(cedula)) {
    return false;
  }

  const provincia = parseInt(cedula.substring(0, 2), 10);

  if (provincia < 1 || provincia > 24) {
    return false;
  }

  const tercerDigito = parseInt(cedula[2], 10);

  if (tercerDigito >= 6) {
    return false;
  }

  const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
  let suma = 0;

  for (let i = 0; i < 9; i++) {
    let valor = parseInt(cedula[i], 10) * coeficientes[i];

    if (valor >= 10) {
      valor -= 9;
    }

    suma += valor;
  }

  const digitoVerificador = parseInt(cedula[9], 10);
  const decenaSuperior = Math.ceil(suma / 10) * 10;
  let digitoCalculado = decenaSuperior - suma;

  if (digitoCalculado === 10) {
    digitoCalculado = 0;
  }

  return digitoCalculado === digitoVerificador;
}

function validarRucPersonaNatural(ruc) {
  if (!/^\d{13}$/.test(ruc)) {
    return false;
  }

  const cedula = ruc.substring(0, 10);
  const establecimiento = ruc.substring(10, 13);

  return validarCedulaEcuador(cedula) && establecimiento === "001";
}

function validarIdentificacionEcuador(valor) {
  const identificacion = valor.trim();

  if (/^\d{10}$/.test(identificacion)) {
    return validarCedulaEcuador(identificacion);
  }

  if (/^\d{13}$/.test(identificacion)) {
    return validarRucPersonaNatural(identificacion);
  }

  return false;
}

/* ---------------------------------------------------- */
/* REGISTRAR ACCESO EN AUDITORÍA                        */
/* ---------------------------------------------------- */

async function registrarAccesoAuditoria(idUsuario) {
  try {
    /*
      IMPORTANTE:
      La IP real del cliente NO se debe enviar desde JavaScript.
      El navegador no puede conocer de forma confiable la IP pública real.
      Ahora la IP se captura correctamente desde el backend FastAPI usando Request
      y headers de proxy como x-forwarded-for, x-real-ip o cf-connecting-ip.
    */
    const respuesta = await window.apiPost("/api/auditoria/accesos", {
      id_usuario: Number(idUsuario),
      fecha_ingreso: obtenerFechaActualISO(),
      hora_ingreso: obtenerHoraActual(),
      estado_sesion: "Activa",
    });

    const idAcceso =
      respuesta.id_acceso ||
      respuesta.acceso?.id_acceso ||
      null;

    if (idAcceso) {
      localStorage.setItem("idAccesoERP", idAcceso);
    }

    return idAcceso;
  } catch (error) {
    console.error("Error al registrar acceso en auditoría:", error);
    return null;
  }
}

/* ---------------------------------------------------- */
/* REGISTRAR ACCIÓN AUTOMÁTICA EN AUDITORÍA             */
/* ---------------------------------------------------- */

async function registrarAccionSistema(modulo, accion, descripcion, tablaAfectada = null, idRegistroAfectado = null) {
  const idUsuario = localStorage.getItem("idUsuarioERP");

  if (!idUsuario) {
    return;
  }

  try {
    await window.apiPost("/api/auditoria/registrar-accion", {
      id_usuario: Number(idUsuario),
      modulo: modulo,
      accion: accion,
      descripcion: descripcion,
      tabla_afectada: tablaAfectada,
      id_registro_afectado: idRegistroAfectado,
    });
  } catch (error) {
    console.error("Error al registrar acción en auditoría:", error);
  }
}

window.registrarAccionSistema = registrarAccionSistema;

/* ---------------------------------------------------- */
/* LOGIN DEL SISTEMA                                    */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("loginForm");

  if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      const usuario = document.getElementById("usuario").value.trim();
      const contrasena = document.getElementById("contrasena").value.trim();
      const mensajeLogin = document.getElementById("mensajeLogin");

      if (usuario === "" || contrasena === "") {
        mensajeLogin.classList.remove("d-none");
        mensajeLogin.textContent = "Debe ingresar usuario y contraseña.";
        return;
      }

      try {
        const respuesta = await window.apiPost("/api/seguridad/login", {
          usuario: usuario,
          contrasena: contrasena,
        });

        localStorage.setItem("idUsuarioERP", respuesta.usuario.id_usuario);
        localStorage.setItem("usuarioERP", respuesta.usuario.usuario);
        localStorage.setItem("nombresERP", respuesta.usuario.nombres || "");
        localStorage.setItem("apellidosERP", respuesta.usuario.apellidos || "");
        localStorage.setItem("idPerfilERP", respuesta.usuario.id_perfil);
        localStorage.setItem("perfilERP", respuesta.usuario.nombre_perfil);

        const idAcceso =
          respuesta.id_acceso ||
          respuesta.usuario.id_acceso ||
          null;

        if (idAcceso) {
          localStorage.setItem("idAccesoERP", idAcceso);
          console.log("Sesión activa registrada con ID:", idAcceso);
        }

        window.location.href = "dashboard.html";
      } catch (error) {
        mensajeLogin.classList.remove("d-none");
        mensajeLogin.textContent = error.message;
      }
    });
  }
});

/* ---------------------------------------------------- */
/* MOSTRAR USUARIO Y PERFIL EN PANTALLAS INTERNAS       */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", function () {
  const usuarioActual = document.getElementById("usuarioActual");
  const perfilActual = document.getElementById("perfilActual");

  const usuario = localStorage.getItem("usuarioERP");
  const perfil = localStorage.getItem("perfilERP");

  if (usuarioActual) {
    usuarioActual.textContent = usuario || "Usuario no identificado";
  }

  if (perfilActual) {
    perfilActual.textContent = perfil || "Perfil no seleccionado";
  }
});

/* ---------------------------------------------------- */
/* REGISTRAR INGRESO AUTOMÁTICO A MÓDULOS               */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", function () {
  const paginaActual = window.location.pathname.split("/").pop();

  const modulosPorPagina = {
    "dashboard.html": "Panel principal",
    "compras.html": "Compras y báscula",
    "inventario.html": "Inventario",
    "produccion.html": "Producción",
    "ventas.html": "Ventas",
    "talento_humano.html": "Talento Humano",
    "activos.html": "Activos",
    "auditoria.html": "Auditoría",
    "reportes.html": "Reportes e IA",
    "seguridad.html": "Seguridad y Usuarios",
  };

  const modulo = modulosPorPagina[paginaActual];

  if (modulo && localStorage.getItem("idUsuarioERP")) {
    registrarAccionSistema(
      modulo,
      "INGRESO_MODULO",
      `El usuario ingresó al módulo ${modulo}.`,
      null,
      null
    );
  }
});

/* ---------------------------------------------------- */
/* CERRAR SESIÓN                                        */
/* ---------------------------------------------------- */

async function cerrarSesion() {
  const idUsuario = localStorage.getItem("idUsuarioERP");
  const idAcceso = localStorage.getItem("idAccesoERP");

  try {
    if (idUsuario) {
      await window.apiPost("/api/seguridad/logout", {
        id_usuario: Number(idUsuario),
        id_acceso: idAcceso ? Number(idAcceso) : null,
      });
    }
  } catch (error) {
    console.error("Error al cerrar sesión correctamente:", error);
  }

  localStorage.removeItem("idUsuarioERP");
  localStorage.removeItem("usuarioERP");
  localStorage.removeItem("nombresERP");
  localStorage.removeItem("apellidosERP");
  localStorage.removeItem("idPerfilERP");
  localStorage.removeItem("perfilERP");
  localStorage.removeItem("idAccesoERP");

  window.location.href = "login.html";
}

window.cerrarSesion = cerrarSesion;

/* ---------------------------------------------------- */
/* TARJETAS RESUMEN DASHBOARD                           */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  const totalCompras = document.getElementById("totalCompras");
  const montoVentas = document.getElementById("montoVentas");
  const inventarioTotal = document.getElementById("inventarioTotal");
  const rendimientoPromedio = document.getElementById("rendimientoPromedio");

  if (totalCompras && montoVentas && inventarioTotal && rendimientoPromedio) {
    try {
      const resumen = await window.apiGet("/api/reportes/resumen");

      totalCompras.textContent = resumen.total_compras ?? 0;
      montoVentas.textContent = `$ ${Number(resumen.monto_total_ventas ?? 0).toFixed(2)}`;
      inventarioTotal.textContent = `${Number(resumen.cantidad_total_inventario ?? 0).toFixed(2)} qq`;
      rendimientoPromedio.textContent = `${Number(resumen.rendimiento_promedio ?? 0).toFixed(2)}%`;
    } catch (error) {
      console.error("Error al cargar resumen gerencial:", error);
    }
  }
});

/* ---------------------------------------------------- */
/* PARA VER CONTRASEÑA EN EL LOGIN                      */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", function () {
  const checkMostrar = document.getElementById("mostrarContrasenaLogin");
  const inputContrasena = document.getElementById("contrasena");

  if (checkMostrar && inputContrasena) {
    checkMostrar.addEventListener("change", function () {
      inputContrasena.type = checkMostrar.checked ? "text" : "password";
    });
  }
});

// ============================================================
// SISTEMA DE SEGURIDAD GLOBAL (Capa Visual Avanzada)
// ============================================================

async function aplicarSeguridadVisual() {
  const path = window.location.pathname;
  let paginaActual = path.substring(path.lastIndexOf("/") + 1);

  if (paginaActual === "" || paginaActual === "login.html" || paginaActual === "index.html") return;

  const idUsuario = localStorage.getItem("idUsuarioERP");
  if (!idUsuario) {
    window.location.href = "login.html";
    return;
  }

  try {
    const url = `/api/seguridad/validar-modulo?id_usuario=${idUsuario}&ruta_html=${paginaActual}`;
    const respuesta = await window.apiGet(url);

    if (!respuesta.permitido) {
      alert("Acceso denegado: No tienes permiso para ver este módulo.");
      window.location.href = "dashboard.html";
      return;
    }

    const p = respuesta.permiso;

    // --- BLOQUEO SELECTIVO DE ACCIONES ---

    if (!p.puede_crear) {
      document.querySelectorAll('.btn-success, [id*="Guardar"], [id*="Registrar"], [onclick*="crear"]').forEach(el => el.style.display = "none");
    }

    if (!p.puede_editar) {
      document.querySelectorAll('.btn-warning, [onclick*="editar"], [id*="Editar"]').forEach(el => el.style.display = "none");
    }

    if (!p.puede_eliminar) {
      document.querySelectorAll('.btn-danger, [onclick*="anular"], [onclick*="eliminar"], [onclick*="desactivar"]').forEach(el => el.style.display = "none");
    }

    if (!p.puede_editar && !p.puede_eliminar) {
      setTimeout(() => {
        const table = document.querySelector("table");
        if (table) {
          const headerAcciones = Array.from(table.querySelectorAll("th")).find(th =>
            th.textContent.toLowerCase().includes("acciones")
          );

          if (headerAcciones) {
            const index = headerAcciones.cellIndex;
            headerAcciones.style.display = "none";

            table.querySelectorAll("tr").forEach(tr => {
              if (tr.cells[index]) tr.cells[index].style.display = "none";
            });
          }
        }
      }, 500);
    }

    // MODO SOLO LECTURA (Desactivar inputs, pero EXCLUYENDO el chat de IA)
    if (!p.puede_crear && !p.puede_editar) {
      // El selector :not(.ia-chat-input) protege el cuadro de texto del asistente
      document.querySelectorAll("input:not(.ia-chat-input), select, textarea").forEach(el => {
        if (!el.readOnly && !el.disabled) el.disabled = true;
      });
    }

  } catch (error) {
    console.error("Error validando seguridad:", error);
  }
}

document.addEventListener("DOMContentLoaded", aplicarSeguridadVisual);


// ============================================================
// ASISTENTE FLOTANTE DE IA AISLADO POR MÓDULOS
// ============================================================

document.addEventListener("DOMContentLoaded", function () {
  const path = window.location.pathname;
  let paginaActual = path.substring(path.lastIndexOf("/") + 1);

  if (paginaActual === "" || paginaActual === "login.html" || paginaActual === "index.html" || !localStorage.getItem("idUsuarioERP")) {
    return;
  }

  let moduloActual = "general";

  if (paginaActual.includes("compras")) moduloActual = "compras";
  else if (paginaActual.includes("ventas")) moduloActual = "ventas";
  else if (paginaActual.includes("inventario")) moduloActual = "inventario";
  else if (paginaActual.includes("produccion")) moduloActual = "produccion";
  else if (paginaActual.includes("talento")) moduloActual = "talento_humano";
  else if (paginaActual.includes("activos")) moduloActual = "activos";
  else if (paginaActual.includes("auditoria")) moduloActual = "auditoria";

  const chatHTML = `
    <div class="ia-floating-btn" id="btnAbrirChatIA" title="Asistente de IA de ${moduloActual.toUpperCase()}">
      🤖
    </div>
    <div class="ia-chat-window" id="ventanaChatIA">
      <div class="ia-chat-header">
        <span>Asistente Don Guillo (${moduloActual.toUpperCase()})</span>
        <button class="ia-close-btn" id="btnCerrarChatIA">&times;</button>
      </div>
      <div class="ia-chat-body" id="cuerpoChatIA">
        <div class="ia-message bot">
          Hola ${localStorage.getItem("nombresERP") || ""}, soy la IA operativa del módulo de <strong>${moduloActual.toUpperCase()}</strong>. ¿En qué te puedo ayudar hoy?
        </div>
      </div>
      <div class="ia-loading" id="iaCargando">La IA está analizando los datos...</div>
      <div class="ia-chat-footer">
        <input type="text" class="ia-chat-input" id="inputMensajeIA" placeholder="Escribe tu consulta...">
        <button class="ia-send-btn" id="btnEnviarMensajeIA">➤</button>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", chatHTML);

  const btnAbrirChatIA = document.getElementById("btnAbrirChatIA");
  const btnCerrarChatIA = document.getElementById("btnCerrarChatIA");
  const ventanaChatIA = document.getElementById("ventanaChatIA");
  const cuerpoChatIA = document.getElementById("cuerpoChatIA");
  const inputMensajeIA = document.getElementById("inputMensajeIA");
  const btnEnviarMensajeIA = document.getElementById("btnEnviarMensajeIA");
  const iaCargando = document.getElementById("iaCargando");

  // Seguro por si otro script intenta deshabilitarlo de nuevo
  inputMensajeIA.disabled = false;

  btnAbrirChatIA.addEventListener("click", () => {
    ventanaChatIA.classList.add("show");
    inputMensajeIA.focus();
  });

  btnCerrarChatIA.addEventListener("click", () => ventanaChatIA.classList.remove("show"));

  function agregarMensaje(texto, tipo) {
    let textoFormateado = texto
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>");

    const divMensaje = document.createElement("div");
    divMensaje.className = `ia-message ${tipo}`;
    divMensaje.innerHTML = textoFormateado;
    cuerpoChatIA.appendChild(divMensaje);
    cuerpoChatIA.scrollTop = cuerpoChatIA.scrollHeight;
  }

  async function enviarConsultaIA() {
    const pregunta = inputMensajeIA.value.trim();
    if (!pregunta) return;

    agregarMensaje(pregunta, "user");
    inputMensajeIA.value = "";
    iaCargando.style.display = "block";

    try {
      const respuesta = await window.apiPost("/api/ia/consultar", {
        pregunta: pregunta,
        usuario: localStorage.getItem("usuarioERP"),
        perfil: localStorage.getItem("perfilERP"),
        contexto_modulo: moduloActual,
      });

      iaCargando.style.display = "none";

      if (respuesta.estado === "bloqueado") {
        agregarMensaje("🔒 " + respuesta.respuesta, "bot");
      } else if (respuesta.estado === "exito") {
        agregarMensaje(respuesta.respuesta, "bot");
      } else {
        agregarMensaje("❌ " + (respuesta.respuesta || "Error desconocido en el servidor."), "bot");
      }

    } catch (error) {
      iaCargando.style.display = "none";
      agregarMensaje("❌ Error de conexión con el Asistente.", "bot");
      console.error(error);
    }
  }

  btnEnviarMensajeIA.addEventListener("click", enviarConsultaIA);

  inputMensajeIA.addEventListener("keypress", function (e) {
    if (e.key === "Enter") enviarConsultaIA();
  });
});