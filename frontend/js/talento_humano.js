/* ============================================================
   MÓDULO TALENTO HUMANO - ERP PILADORA DON GUILLO
   Empleados + Asistencia manual + Roles de pago
   Validaciones reforzadas según talento_humano.html
============================================================ */

document.addEventListener("DOMContentLoaded", function () {
  const API_TALENTO = "/api/talento-humano";

  let empleadosCache = [];
  let asistenciaCache = [];

  // ============================================================
  // ELEMENTOS: EMPLEADOS
  // ============================================================

  const formTalentoHumano = document.getElementById("formTalentoHumano");
  const idEmpleadoEditar = document.getElementById("idEmpleadoEditar");

  const cedulaEmpleado = document.getElementById("cedulaEmpleado");
  const nombresEmpleado = document.getElementById("nombresEmpleado");
  const apellidosEmpleado = document.getElementById("apellidosEmpleado");
  const telefonoEmpleado = document.getElementById("telefonoEmpleado");
  const direccionEmpleado = document.getElementById("direccionEmpleado");
  const cargoEmpleado = document.getElementById("cargoEmpleado");
  const areaEmpleado = document.getElementById("areaEmpleado");
  const sueldoEmpleado = document.getElementById("sueldoEmpleado");
  const fechaIngresoEmpleado = document.getElementById("fechaIngresoEmpleado");
  const estadoEmpleado = document.getElementById("estadoEmpleado");

  const tituloFormularioEmpleado = document.getElementById("tituloFormularioEmpleado");
  const btnGuardarEmpleado = document.getElementById("btnGuardarEmpleado");
  const btnCancelarEdicionEmpleado = document.getElementById("btnCancelarEdicionEmpleado");

  const tablaEmpleados = document.getElementById("tablaEmpleados");

  // ============================================================
  // ELEMENTOS: TARJETAS RESUMEN
  // ============================================================

  const totalEmpleados = document.getElementById("totalEmpleados");
  const empleadosActivos = document.getElementById("empleadosActivos");
  const empleadosNoActivos = document.getElementById("empleadosNoActivos");
  const totalMensualSueldos = document.getElementById("totalMensualSueldos");

  // ============================================================
  // ELEMENTOS: ROLES DE PAGO
  // ============================================================

  const formRolPago = document.getElementById("formRolPago");
  const empleadoRolPago = document.getElementById("empleadoRolPago");
  const periodoRolPago = document.getElementById("periodoRolPago");
  const horasExtrasRolPago = document.getElementById("horasExtrasRolPago");
  const bonificacionesRolPago = document.getElementById("bonificacionesRolPago");
  const sancionesRolPago = document.getElementById("sancionesRolPago");
  const descuentosRolPago = document.getElementById("descuentosRolPago");
  const observacionRolPago = document.getElementById("observacionRolPago");
  const tablaRolesPago = document.getElementById("tablaRolesPago");

  // ============================================================
  // ELEMENTOS: ASISTENCIA MANUAL
  // ============================================================

  const formMarcarEntrada = document.getElementById("formMarcarEntrada");
  const empleadoAsistencia = document.getElementById("empleadoAsistencia");
  const fechaAsistencia = document.getElementById("fechaAsistencia");
  const horaProgramadaEntrada = document.getElementById("horaProgramadaEntrada");
  const horaEntradaAsistencia = document.getElementById("horaEntradaAsistencia");
  const sancionAsistencia = document.getElementById("sancionAsistencia");
  const observacionAsistencia = document.getElementById("observacionAsistencia");
  const tablaAsistencia = document.getElementById("tablaAsistencia");

  // ============================================================
  // FUNCIONES GENERALES
  // ============================================================

  function obtenerFechaActualISO() {
    const fecha = new Date();
    const anio = fecha.getFullYear();
    const mes = String(fecha.getMonth() + 1).padStart(2, "0");
    const dia = String(fecha.getDate()).padStart(2, "0");
    return `${anio}-${mes}-${dia}`;
  }

  function obtenerMesActualISO() {
    const fecha = new Date();
    const anio = fecha.getFullYear();
    const mes = String(fecha.getMonth() + 1).padStart(2, "0");
    return `${anio}-${mes}`;
  }

  function obtenerHoraActual() {
    const fecha = new Date();
    const hora = String(fecha.getHours()).padStart(2, "0");
    const minutos = String(fecha.getMinutes()).padStart(2, "0");
    return `${hora}:${minutos}`;
  }

  function formatearDinero(valor) {
    return "$ " + Number(valor || 0).toFixed(2);
  }

  function formatearNumero(valor) {
    return Number(valor || 0).toFixed(2);
  }

  function limpiarTexto(texto) {
    return String(texto || "").trim().replace(/\s+/g, " ");
  }

  function escaparHTML(valor) {
    return String(valor ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function mostrarMensajeError(error, mensajeDefecto) {
    let mensaje = mensajeDefecto;

    if (error && error.message) {
      mensaje = error.message;
    }

    alert(mensaje);
  }

  function obtenerClaseEstado(estado) {
    if (estado === "Activo") return "bg-success";
    if (estado === "Suspendido") return "bg-warning text-dark";
    if (estado === "Inactivo") return "bg-danger";
    return "bg-secondary";
  }

  function obtenerClaseAsistencia(estado) {
    if (estado === "Presente") return "bg-success";
    if (estado === "Atraso") return "bg-warning text-dark";
    if (estado === "Falta") return "bg-danger";
    if (estado === "Justificado") return "bg-info text-dark";
    return "bg-secondary";
  }

  function validarCedulaEcuador(cedula) {
    if (!/^\d{10}$/.test(cedula)) {
      return false;
    }

    const provincia = Number(cedula.substring(0, 2));

    if (provincia < 1 || provincia > 24) {
      return false;
    }

    const tercerDigito = Number(cedula[2]);

    if (tercerDigito >= 6) {
      return false;
    }

    const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
    let suma = 0;

    for (let i = 0; i < 9; i++) {
      let valor = Number(cedula[i]) * coeficientes[i];

      if (valor >= 10) {
        valor -= 9;
      }

      suma += valor;
    }

    const digitoVerificador = Number(cedula[9]);
    const decenaSuperior = Math.ceil(suma / 10) * 10;
    let digitoCalculado = decenaSuperior - suma;

    if (digitoCalculado === 10) {
      digitoCalculado = 0;
    }

    return digitoCalculado === digitoVerificador;
  }

  function validarSoloLetras(texto) {
    return /^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(texto);
  }

  function validarTelefonoEcuador(telefono) {
    return /^09\d{8}$/.test(telefono);
  }

  function validarHora(hora) {
    return /^([01]\d|2[0-3]):([0-5]\d)$/.test(hora);
  }

  function horaAMinutos(hora) {
    if (!validarHora(hora)) return null;

    const partes = hora.split(":");
    const horas = Number(partes[0]);
    const minutos = Number(partes[1]);

    return horas * 60 + minutos;
  }

  function esNumeroValidoNoNegativo(valor) {
    const numero = Number(valor);
    return Number.isFinite(numero) && numero >= 0;
  }

  function esNumeroValidoMayorCero(valor) {
    const numero = Number(valor);
    return Number.isFinite(numero) && numero > 0;
  }

  function configurarLimitesFechas() {
    const fechaActual = obtenerFechaActualISO();
    const mesActual = obtenerMesActualISO();

    if (fechaIngresoEmpleado) {
      fechaIngresoEmpleado.max = fechaActual;
    }

    if (fechaAsistencia) {
      fechaAsistencia.max = fechaActual;
    }

    if (periodoRolPago) {
      periodoRolPago.max = mesActual;
    }
  }

  function limpiarFormularioEmpleado() {
    if (!formTalentoHumano) return;

    formTalentoHumano.reset();

    if (idEmpleadoEditar) {
      idEmpleadoEditar.value = "";
    }

    if (estadoEmpleado) {
      estadoEmpleado.value = "Activo";
    }

    if (tituloFormularioEmpleado) {
      tituloFormularioEmpleado.textContent = "Registrar empleado";
    }

    if (btnGuardarEmpleado) {
      btnGuardarEmpleado.textContent = "Registrar empleado";
    }

    if (btnCancelarEdicionEmpleado) {
      btnCancelarEdicionEmpleado.style.display = "none";
    }

    configurarLimitesFechas();
  }

  function limpiarFormularioAsistencia() {
    if (!formMarcarEntrada) return;

    formMarcarEntrada.reset();

    if (fechaAsistencia) {
      fechaAsistencia.value = obtenerFechaActualISO();
      fechaAsistencia.max = obtenerFechaActualISO();
    }

    if (horaProgramadaEntrada) {
      horaProgramadaEntrada.value = "08:00";
    }

    if (horaEntradaAsistencia) {
      horaEntradaAsistencia.value = obtenerHoraActual();
    }

    if (sancionAsistencia) {
      sancionAsistencia.value = 0;
    }
  }

  function limpiarFormularioRolPago() {
    if (!formRolPago) return;

    formRolPago.reset();

    if (periodoRolPago) {
      periodoRolPago.max = obtenerMesActualISO();
    }

    if (horasExtrasRolPago) {
      horasExtrasRolPago.value = 0;
    }

    if (sancionesRolPago) {
      sancionesRolPago.value = 0;
    }

    if (bonificacionesRolPago) {
      bonificacionesRolPago.value = 0;
    }

    if (descuentosRolPago) {
      descuentosRolPago.value = 0;
    }
  }

  function construirEmpleadoDesdeFormulario() {
    return {
      identificacion: limpiarTexto(cedulaEmpleado?.value),
      nombres: limpiarTexto(nombresEmpleado?.value),
      apellidos: limpiarTexto(apellidosEmpleado?.value),
      telefono: limpiarTexto(telefonoEmpleado?.value),
      direccion: limpiarTexto(direccionEmpleado?.value),
      cargo: cargoEmpleado?.value || "",
      area: areaEmpleado?.value || "",
      sueldo: Number(sueldoEmpleado?.value || 0),
      fecha_ingreso: fechaIngresoEmpleado?.value || "",
      estado_empleado: estadoEmpleado?.value || ""
    };
  }

  function existeCedulaDuplicada(cedula, idEditar) {
    return empleadosCache.some((empleado) => {
      const idActual = String(empleado.id_empleado);
      const idFormulario = String(idEditar || "");
      const identificacion = String(empleado.identificacion || "");

      return identificacion === cedula && idActual !== idFormulario;
    });
  }

  function validarFormularioEmpleado(empleado) {
    const idEditar = idEmpleadoEditar?.value || "";

    if (
      empleado.identificacion === "" ||
      empleado.nombres === "" ||
      empleado.apellidos === "" ||
      empleado.telefono === "" ||
      empleado.direccion === "" ||
      empleado.cargo === "" ||
      empleado.area === "" ||
      empleado.fecha_ingreso === "" ||
      empleado.estado_empleado === ""
    ) {
      alert("Complete todos los campos obligatorios del empleado.");
      return false;
    }

    if (!/^\d{10}$/.test(empleado.identificacion)) {
      alert("La cédula debe contener exactamente 10 dígitos numéricos.");
      return false;
    }

    if (!validarCedulaEcuador(empleado.identificacion)) {
      alert("La cédula ingresada no es válida según el algoritmo ecuatoriano.");
      return false;
    }

    if (existeCedulaDuplicada(empleado.identificacion, idEditar)) {
      alert("Ya existe otro empleado registrado con esta cédula.");
      return false;
    }

    if (!validarSoloLetras(empleado.nombres)) {
      alert("Los nombres solo deben contener letras y espacios.");
      return false;
    }

    if (empleado.nombres.length < 2) {
      alert("Los nombres deben tener al menos 2 caracteres.");
      return false;
    }

    if (!validarSoloLetras(empleado.apellidos)) {
      alert("Los apellidos solo deben contener letras y espacios.");
      return false;
    }

    if (empleado.apellidos.length < 2) {
      alert("Los apellidos deben tener al menos 2 caracteres.");
      return false;
    }

    if (!validarTelefonoEcuador(empleado.telefono)) {
      alert("El teléfono debe tener 10 dígitos y empezar con 09. Ejemplo: 0987654321.");
      return false;
    }

    if (empleado.direccion.length < 5) {
      alert("La dirección debe ser más específica. Ingrese al menos 5 caracteres.");
      return false;
    }

    if (!esNumeroValidoMayorCero(empleado.sueldo)) {
      alert("El sueldo base debe ser mayor a cero.");
      return false;
    }

    if (empleado.sueldo > 10000) {
      alert("Revise el sueldo ingresado. El valor parece demasiado alto para este módulo.");
      return false;
    }

    if (empleado.fecha_ingreso > obtenerFechaActualISO()) {
      alert("No se permite registrar una fecha de ingreso futura.");
      return false;
    }

    if (!["Activo", "Inactivo", "Suspendido"].includes(empleado.estado_empleado)) {
      alert("Seleccione un estado válido para el empleado.");
      return false;
    }

    return true;
  }

  // ============================================================
  // VALIDACIONES DE ESCRITURA EN TIEMPO REAL
  // ============================================================

  if (cedulaEmpleado) {
    cedulaEmpleado.addEventListener("input", function () {
      this.value = this.value.replace(/\D/g, "").slice(0, 10);
    });
  }

  if (telefonoEmpleado) {
    telefonoEmpleado.addEventListener("input", function () {
      this.value = this.value.replace(/\D/g, "").slice(0, 10);
    });
  }

  if (nombresEmpleado) {
    nombresEmpleado.addEventListener("input", function () {
      this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g, "");
      this.value = this.value.replace(/\s{2,}/g, " ");
    });
  }

  if (apellidosEmpleado) {
    apellidosEmpleado.addEventListener("input", function () {
      this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g, "");
      this.value = this.value.replace(/\s{2,}/g, " ");
    });
  }

  if (sueldoEmpleado) {
    sueldoEmpleado.addEventListener("input", function () {
      if (Number(this.value) < 0) {
        this.value = 0;
      }
    });
  }

  if (sancionAsistencia) {
    sancionAsistencia.addEventListener("input", function () {
      if (Number(this.value) < 0) {
        this.value = 0;
      }
    });
  }

  if (bonificacionesRolPago) {
    bonificacionesRolPago.addEventListener("input", function () {
      if (Number(this.value) < 0) {
        this.value = 0;
      }
    });
  }

  if (descuentosRolPago) {
    descuentosRolPago.addEventListener("input", function () {
      if (Number(this.value) < 0) {
        this.value = 0;
      }
    });
  }

  // ============================================================
  // RESUMEN
  // ============================================================

  async function cargarResumenEmpleados() {
    if (!totalEmpleados) return;

    try {
      const resumen = await window.apiGet(`${API_TALENTO}/empleados/resumen`);

      const inactivos = Number(resumen.empleados_inactivos || 0);
      const suspendidos = Number(resumen.empleados_suspendidos || 0);

      totalEmpleados.textContent = resumen.total_empleados || 0;
      empleadosActivos.textContent = resumen.empleados_activos || 0;
      empleadosNoActivos.textContent = inactivos + suspendidos;
      totalMensualSueldos.textContent = formatearDinero(resumen.total_mensual_sueldos);
    } catch (error) {
      console.error("Error al cargar resumen de empleados:", error);
    }
  }

  // ============================================================
  // EMPLEADOS
  // ============================================================

  async function cargarEmpleados() {
    if (!tablaEmpleados) return;

    try {
      const empleados = await window.apiGet(`${API_TALENTO}/empleados`);
      empleadosCache = Array.isArray(empleados) ? empleados : [];

      tablaEmpleados.innerHTML = "";

      if (!empleadosCache || empleadosCache.length === 0) {
        tablaEmpleados.innerHTML = `
          <tr>
            <td colspan="10" class="text-center text-muted">
              No existen empleados registrados.
            </td>
          </tr>
        `;

        cargarSelectEmpleadosActivos([]);
        return;
      }

      empleadosCache.forEach((empleado) => {
        const fila = document.createElement("tr");

        const estado = empleado.estado_empleado || "-";
        const claseEstado = obtenerClaseEstado(estado);

        fila.innerHTML = `
          <td>${escaparHTML(empleado.id_empleado)}</td>
          <td>${escaparHTML(empleado.identificacion)}</td>
          <td>${escaparHTML(`${empleado.nombres || ""} ${empleado.apellidos || ""}`)}</td>
          <td>${escaparHTML(empleado.telefono || "-")}</td>
          <td>${escaparHTML(empleado.cargo || "-")}</td>
          <td>${escaparHTML(empleado.area || "-")}</td>
          <td>${formatearDinero(empleado.sueldo)}</td>
          <td>${escaparHTML(empleado.fecha_ingreso || "-")}</td>
          <td><span class="badge ${claseEstado}">${escaparHTML(estado)}</span></td>
          <td>
            <div class="btn-group btn-group-sm" role="group">
              <button class="btn btn-primary" onclick="editarEmpleado(${Number(empleado.id_empleado)})">
                Editar
              </button>
              <button class="btn btn-warning" onclick="suspenderEmpleado(${Number(empleado.id_empleado)})">
                Suspender
              </button>
              <button class="btn btn-secondary" onclick="desactivarEmpleado(${Number(empleado.id_empleado)})">
                Inactivar
              </button>
              <button class="btn btn-success" onclick="activarEmpleado(${Number(empleado.id_empleado)})">
                Activar
              </button>
              <button class="btn btn-danger" onclick="eliminarEmpleado(${Number(empleado.id_empleado)})">
                Eliminar
              </button>
            </div>
          </td>
        `;

        tablaEmpleados.appendChild(fila);
      });

      cargarSelectEmpleadosActivos(empleadosCache);
    } catch (error) {
      tablaEmpleados.innerHTML = `
        <tr>
          <td colspan="10" class="text-center text-danger">
            Error al cargar empleados: ${escaparHTML(error.message)}
          </td>
        </tr>
      `;
    }
  }

  function cargarSelectEmpleadosActivos(empleados) {
    if (empleadoRolPago) {
      empleadoRolPago.innerHTML = `
        <option value="">Seleccione empleado activo</option>
      `;
    }

    if (empleadoAsistencia) {
      empleadoAsistencia.innerHTML = `
        <option value="">Seleccione empleado activo</option>
      `;
    }

    empleados
      .filter((empleado) => empleado.estado_empleado === "Activo")
      .forEach((empleado) => {
        const textoEmpleado = `${empleado.nombres || ""} ${empleado.apellidos || ""} - ${empleado.cargo || ""}`;

        if (empleadoRolPago) {
          const optionRol = document.createElement("option");
          optionRol.value = empleado.id_empleado;
          optionRol.textContent = textoEmpleado;
          empleadoRolPago.appendChild(optionRol);
        }

        if (empleadoAsistencia) {
          const optionAsistencia = document.createElement("option");
          optionAsistencia.value = empleado.id_empleado;
          optionAsistencia.textContent = textoEmpleado;
          empleadoAsistencia.appendChild(optionAsistencia);
        }
      });
  }

  if (formTalentoHumano) {
    formTalentoHumano.addEventListener("submit", async function (event) {
      event.preventDefault();

      const empleado = construirEmpleadoDesdeFormulario();

      if (!validarFormularioEmpleado(empleado)) {
        return;
      }

      const idEditar = idEmpleadoEditar?.value || "";

      try {
        if (idEditar) {
          await window.apiPut(`${API_TALENTO}/empleados/${idEditar}`, empleado);
          alert("Empleado actualizado correctamente.");
        } else {
          await window.apiPost(`${API_TALENTO}/empleados`, empleado);
          alert("Empleado registrado correctamente.");
        }

        limpiarFormularioEmpleado();
        await cargarEmpleados();
        await cargarResumenEmpleados();
      } catch (error) {
        mostrarMensajeError(error, "No se pudo guardar el empleado.");
      }
    });
  }

  if (btnCancelarEdicionEmpleado) {
    btnCancelarEdicionEmpleado.addEventListener("click", limpiarFormularioEmpleado);
  }

  window.editarEmpleado = async function (idEmpleado) {
    try {
      const empleado = await window.apiGet(`${API_TALENTO}/empleados/${idEmpleado}`);

      idEmpleadoEditar.value = empleado.id_empleado;
      cedulaEmpleado.value = empleado.identificacion || "";
      nombresEmpleado.value = empleado.nombres || "";
      apellidosEmpleado.value = empleado.apellidos || "";
      telefonoEmpleado.value = empleado.telefono || "";
      direccionEmpleado.value = empleado.direccion || "";
      cargoEmpleado.value = empleado.cargo || "";
      areaEmpleado.value = empleado.area || "";
      sueldoEmpleado.value = empleado.sueldo || "";
      fechaIngresoEmpleado.value = empleado.fecha_ingreso || "";
      estadoEmpleado.value = empleado.estado_empleado || "Activo";

      tituloFormularioEmpleado.textContent = "Editar empleado";
      btnGuardarEmpleado.textContent = "Actualizar empleado";
      btnCancelarEdicionEmpleado.style.display = "inline-block";

      configurarLimitesFechas();

      window.scrollTo({
        top: 0,
        behavior: "smooth"
      });
    } catch (error) {
      mostrarMensajeError(error, "No se pudo cargar el empleado.");
    }
  };

  window.desactivarEmpleado = async function (idEmpleado) {
    if (!confirm("¿Desea inactivar este empleado? El empleado no estará disponible para operaciones.")) return;

    try {
      await window.apiPatch(`${API_TALENTO}/empleados/${idEmpleado}/desactivar`);
      alert("Empleado inactivado correctamente.");
      await cargarEmpleados();
      await cargarResumenEmpleados();
    } catch (error) {
      mostrarMensajeError(error, "No se pudo inactivar el empleado.");
    }
  };

  window.suspenderEmpleado = async function (idEmpleado) {
    if (!confirm("¿Desea suspender este empleado temporalmente?")) return;

    try {
      await window.apiPatch(`${API_TALENTO}/empleados/${idEmpleado}/suspender`);
      alert("Empleado suspendido correctamente.");
      await cargarEmpleados();
      await cargarResumenEmpleados();
    } catch (error) {
      mostrarMensajeError(
        error,
        "No se pudo suspender el empleado. Revise que el backend esté encendido y que api.js tenga apiPatch."
      );
    }
  };

  window.activarEmpleado = async function (idEmpleado) {
    if (!confirm("¿Desea activar este empleado?")) return;

    try {
      await window.apiPatch(`${API_TALENTO}/empleados/${idEmpleado}/activar`);
      alert("Empleado activado correctamente.");
      await cargarEmpleados();
      await cargarResumenEmpleados();
    } catch (error) {
      mostrarMensajeError(error, "No se pudo activar el empleado.");
    }
  };

  window.eliminarEmpleado = async function (idEmpleado) {
    const confirmar = confirm(
      "¿Desea eliminar lógicamente este empleado? No se borrará físicamente de la base de datos."
    );

    if (!confirmar) return;

    try {
      await window.apiDelete(`${API_TALENTO}/empleados/${idEmpleado}`);
      alert("Empleado eliminado lógicamente correctamente.");
      await cargarEmpleados();
      await cargarResumenEmpleados();
    } catch (error) {
      mostrarMensajeError(error, "No se pudo eliminar el empleado.");
    }
  };

  // ============================================================
  // ASISTENCIA MANUAL
  // ============================================================

  function construirDatosEntrada() {
    return {
      id_empleado: Number(empleadoAsistencia?.value || 0),
      fecha: fechaAsistencia?.value || "",
      hora_entrada: horaEntradaAsistencia?.value || "",
      hora_programada_entrada: horaProgramadaEntrada?.value || "",
      sancion: Number(sancionAsistencia?.value || 0),
      observacion: limpiarTexto(observacionAsistencia?.value) || null
    };
  }

  function validarEntradaAsistencia(datosEntrada) {
    if (!datosEntrada.id_empleado) {
      alert("Seleccione el empleado para marcar asistencia.");
      return false;
    }

    if (!datosEntrada.fecha) {
      alert("Seleccione la fecha de asistencia.");
      return false;
    }

    if (datosEntrada.fecha > obtenerFechaActualISO()) {
      alert("No se permite registrar asistencia con fecha futura.");
      return false;
    }

    if (!validarHora(datosEntrada.hora_programada_entrada)) {
      alert("Ingrese una hora programada válida.");
      return false;
    }

    if (!validarHora(datosEntrada.hora_entrada)) {
      alert("Ingrese una hora de entrada válida.");
      return false;
    }

    if (!esNumeroValidoNoNegativo(datosEntrada.sancion)) {
      alert("La sanción debe ser un valor numérico positivo o cero.");
      return false;
    }

    const empleadoActivo = empleadosCache.find((empleado) => {
      return Number(empleado.id_empleado) === Number(datosEntrada.id_empleado);
    });

    if (!empleadoActivo || empleadoActivo.estado_empleado !== "Activo") {
      alert("Solo se puede registrar asistencia a empleados activos.");
      return false;
    }

    const yaTieneEntradaPendiente = asistenciaCache.some((registro) => {
      return (
        Number(registro.id_empleado) === Number(datosEntrada.id_empleado) &&
        registro.fecha === datosEntrada.fecha &&
        registro.hora_entrada &&
        !registro.hora_salida
      );
    });

    if (yaTieneEntradaPendiente) {
      alert("Este empleado ya tiene una entrada marcada en esta fecha y todavía no tiene salida registrada.");
      return false;
    }

    return true;
  }

  if (formMarcarEntrada) {
    formMarcarEntrada.addEventListener("submit", async function (event) {
      event.preventDefault();

      const datosEntrada = construirDatosEntrada();

      if (!validarEntradaAsistencia(datosEntrada)) {
        return;
      }

      try {
        await window.apiPost(`${API_TALENTO}/asistencia/marcar-entrada`, datosEntrada);
        alert("Entrada marcada correctamente.");

        limpiarFormularioAsistencia();
        await cargarAsistencia();
      } catch (error) {
        mostrarMensajeError(error, "No se pudo marcar la entrada.");
      }
    });
  }

  async function cargarAsistencia() {
    if (!tablaAsistencia) return;

    try {
      const asistencia = await window.apiGet(`${API_TALENTO}/asistencia`);
      asistenciaCache = Array.isArray(asistencia) ? asistencia : [];

      tablaAsistencia.innerHTML = "";

      if (!asistenciaCache || asistenciaCache.length === 0) {
        tablaAsistencia.innerHTML = `
          <tr>
            <td colspan="13" class="text-center text-muted">
              No existe asistencia registrada.
            </td>
          </tr>
        `;
        return;
      }

      asistenciaCache.forEach((registro) => {
        const fila = document.createElement("tr");

        const estado = registro.estado_asistencia || "-";
        const claseEstado = obtenerClaseAsistencia(estado);

        let botonSalida = `
          <button class="btn btn-success btn-sm" onclick="marcarSalida(${Number(registro.id_asistencia)})">
            Marcar salida
          </button>
        `;

        if (registro.hora_salida) {
          botonSalida = `<span class="badge bg-secondary">Salida marcada</span>`;
        }

        fila.innerHTML = `
          <td>${escaparHTML(registro.id_asistencia)}</td>
          <td>${escaparHTML(registro.empleado || "-")}</td>
          <td>${escaparHTML(registro.cargo || "-")}</td>
          <td>${escaparHTML(registro.area || "-")}</td>
          <td>${escaparHTML(registro.fecha || "-")}</td>
          <td>${escaparHTML(registro.hora_entrada || "-")}</td>
          <td>${escaparHTML(registro.hora_salida || "-")}</td>
          <td><span class="badge ${claseEstado}">${escaparHTML(estado)}</span></td>
          <td>${escaparHTML(registro.minutos_atraso || 0)} min</td>
          <td>${formatearDinero(registro.sancion)}</td>
          <td>${formatearNumero(registro.horas_trabajadas)} h</td>
          <td>${formatearNumero(registro.horas_extras)} h</td>
          <td>${botonSalida}</td>
        `;

        tablaAsistencia.appendChild(fila);
      });
    } catch (error) {
      tablaAsistencia.innerHTML = `
        <tr>
          <td colspan="13" class="text-center text-danger">
            Error al cargar asistencia: ${escaparHTML(error.message)}
          </td>
        </tr>
      `;
    }
  }

  window.marcarSalida = async function (idAsistencia) {
    const registro = asistenciaCache.find((item) => {
      return Number(item.id_asistencia) === Number(idAsistencia);
    });

    if (!registro) {
      alert("No se encontró el registro de asistencia seleccionado.");
      return;
    }

    if (registro.hora_salida) {
      alert("Este registro ya tiene salida marcada.");
      return;
    }

    const horaSalida = prompt(
      "Ingrese la hora de salida en formato HH:MM. Ejemplo: 17:30",
      obtenerHoraActual()
    );

    if (!horaSalida) {
      return;
    }

    if (!validarHora(horaSalida)) {
      alert("Ingrese una hora de salida válida en formato HH:MM.");
      return;
    }

    const minutosEntrada = horaAMinutos(registro.hora_entrada);
    const minutosSalida = horaAMinutos(horaSalida);

    if (minutosEntrada !== null && minutosSalida !== null && minutosSalida <= minutosEntrada) {
      alert("La hora de salida debe ser mayor que la hora de entrada.");
      return;
    }

    const jornadaNormal = prompt("Ingrese las horas de jornada normal. Ejemplo: 8", "8");

    if (!jornadaNormal) {
      return;
    }

    const horasJornada = Number(jornadaNormal);

    if (!Number.isFinite(horasJornada) || horasJornada <= 0) {
      alert("Las horas de jornada normal deben ser mayores a cero.");
      return;
    }

    if (horasJornada > 24) {
      alert("La jornada normal no puede ser mayor a 24 horas.");
      return;
    }

    const observacion = prompt(
      "Observación de salida:",
      "Salida registrada correctamente"
    );

    const datosSalida = {
      hora_salida: horaSalida,
      horas_jornada_normal: horasJornada,
      observacion: limpiarTexto(observacion) || "Salida registrada correctamente"
    };

    try {
      await window.apiPatch(`${API_TALENTO}/asistencia/${idAsistencia}/marcar-salida`, datosSalida);
      alert("Salida marcada correctamente.");

      await cargarAsistencia();
    } catch (error) {
      mostrarMensajeError(error, "No se pudo marcar la salida.");
    }
  };

  // ============================================================
  // ROLES DE PAGO
  // ============================================================

  async function cargarRolesPago() {
    if (!tablaRolesPago) return;

    try {
      const roles = await window.apiGet(`${API_TALENTO}/roles-pago`);

      tablaRolesPago.innerHTML = "";

      if (!roles || roles.length === 0) {
        tablaRolesPago.innerHTML = `
          <tr>
            <td colspan="11" class="text-center text-muted">
              No existen roles de pago archivados.
            </td>
          </tr>
        `;
        return;
      }

      roles.forEach((rol, index) => {
        const idRol = rol.id_rol_pago || rol.id || rol.id_rol || index + 1;
        const empleado = rol.empleado || rol.nombres || rol.nombre_empleado || "-";

        const fila = document.createElement("tr");
        const rolSeguro = encodeURIComponent(JSON.stringify(rol));

        fila.innerHTML = `
          <td>${escaparHTML(idRol)}</td>
          <td>${escaparHTML(empleado)}</td>
          <td>${escaparHTML(rol.periodo || "-")}</td>
          <td>${formatearDinero(rol.sueldo_base)}</td>
          <td>${formatearDinero(rol.horas_extras)}</td>
          <td>${formatearDinero(rol.bonificaciones)}</td>
          <td>${formatearDinero(rol.sanciones)}</td>
          <td>${formatearDinero(rol.descuentos)}</td>
          <td><strong>${formatearDinero(rol.total_pagar)}</strong></td>
          <td>${escaparHTML(rol.fecha_generacion || "-")}</td>
          <td>
            <button class="btn btn-outline-success btn-sm" onclick="generarComprobanteRolDesdeTexto('${rolSeguro}')">
              Generar comprobante
            </button>
          </td>
        `;

        tablaRolesPago.appendChild(fila);
      });
    } catch (error) {
      tablaRolesPago.innerHTML = `
        <tr>
          <td colspan="11" class="text-center text-danger">
            Error al cargar roles de pago: ${escaparHTML(error.message)}
          </td>
        </tr>
      `;
    }
  }

  function construirRolPagoDesdeFormulario() {
    return {
      id_empleado: Number(empleadoRolPago?.value || 0),
      periodo: periodoRolPago?.value || "",
      horas_extras: Number(horasExtrasRolPago?.value || 0),
      bonificaciones: Number(bonificacionesRolPago?.value || 0),
      sanciones: Number(sancionesRolPago?.value || 0),
      descuentos: Number(descuentosRolPago?.value || 0),
      observacion: limpiarTexto(observacionRolPago?.value) || "Rol generado automáticamente desde Talento Humano"
    };
  }

  function validarRolPago(rolPago) {
    if (!rolPago.id_empleado) {
      alert("Seleccione un empleado activo para generar el rol de pago.");
      return false;
    }

    if (!rolPago.periodo) {
      alert("Seleccione el periodo del rol de pago.");
      return false;
    }

    if (rolPago.periodo > obtenerMesActualISO()) {
      alert("No se permite generar roles de pago de meses futuros.");
      return false;
    }

    if (
      !esNumeroValidoNoNegativo(rolPago.horas_extras) ||
      !esNumeroValidoNoNegativo(rolPago.bonificaciones) ||
      !esNumeroValidoNoNegativo(rolPago.sanciones) ||
      !esNumeroValidoNoNegativo(rolPago.descuentos)
    ) {
      alert("No se permiten valores negativos en el rol de pago.");
      return false;
    }

    const empleadoActivo = empleadosCache.find((empleado) => {
      return Number(empleado.id_empleado) === Number(rolPago.id_empleado);
    });

    if (!empleadoActivo || empleadoActivo.estado_empleado !== "Activo") {
      alert("Solo se puede generar rol de pago a empleados activos.");
      return false;
    }

    return true;
  }

  if (formRolPago) {
    formRolPago.addEventListener("submit", async function (event) {
      event.preventDefault();

      const rolPago = construirRolPagoDesdeFormulario();

      if (!validarRolPago(rolPago)) {
        return;
      }

      try {
        await window.apiPost(`${API_TALENTO}/roles-pago`, rolPago);
        alert("Rol de pago generado correctamente.");

        limpiarFormularioRolPago();
        await cargarRolesPago();
      } catch (error) {
        mostrarMensajeError(error, "No se pudo generar el rol de pago.");
      }
    });
  }

  window.generarComprobanteRolDesdeTexto = function (rolCodificado) {
    try {
      const rol = JSON.parse(decodeURIComponent(rolCodificado));
      window.generarComprobanteRol(rol);
    } catch (error) {
      alert("No se pudo abrir el comprobante del rol de pago.");
    }
  };

  window.generarComprobanteRol = function (rol) {
    const empleado = escaparHTML(rol.empleado || rol.nombres || rol.nombre_empleado || "Empleado no especificado");
    const cedula = escaparHTML(rol.identificacion || rol.cedula || "-");
    const cargo = escaparHTML(rol.cargo || "-");
    const area = escaparHTML(rol.area || "-");
    const periodo = escaparHTML(rol.periodo || "-");
    const fechaGeneracion = escaparHTML(rol.fecha_generacion || "-");

    const sueldoBase = Number(rol.sueldo_base || 0);
    const horasExtras = Number(rol.horas_extras || 0);
    const bonificaciones = Number(rol.bonificaciones || 0);
    const sanciones = Number(rol.sanciones || 0);
    const descuentos = Number(rol.descuentos || 0);
    const totalPagar = Number(rol.total_pagar || 0);

    const totalIngresos = sueldoBase + horasExtras + bonificaciones;
    const totalEgresos = sanciones + descuentos;

    const contenido = `
      <!doctype html>
      <html lang="es">
        <head>
          <meta charset="UTF-8">
          <title>Comprobante de Rol de Pago</title>

          <style>
            * {
              box-sizing: border-box;
            }

            body {
              font-family: Arial, Helvetica, sans-serif;
              margin: 0;
              padding: 30px;
              color: #1f1f1f;
              background: #f2f2f2;
            }

            .comprobante {
              width: 800px;
              max-width: 100%;
              margin: 0 auto;
              background: #ffffff;
              border: 1px solid #cfcfcf;
              padding: 35px;
            }

            .encabezado {
              text-align: center;
              border-bottom: 3px solid #0f7b3f;
              padding-bottom: 15px;
              margin-bottom: 25px;
            }

            .empresa {
              font-size: 24px;
              font-weight: bold;
              color: #0f7b3f;
              letter-spacing: 1px;
              margin-bottom: 5px;
            }

            .titulo {
              font-size: 17px;
              font-weight: bold;
              color: #222;
            }

            .subtitulo {
              font-size: 12px;
              color: #555;
              margin-top: 5px;
            }

            .bloque {
              margin-bottom: 20px;
            }

            .bloque h3 {
              font-size: 15px;
              color: #0f7b3f;
              margin-bottom: 8px;
              border-bottom: 1px solid #dcdcdc;
              padding-bottom: 5px;
            }

            .datos {
              width: 100%;
              border-collapse: collapse;
              font-size: 13px;
            }

            .datos td {
              padding: 6px 4px;
              vertical-align: top;
            }

            .datos strong {
              color: #222;
            }

            table.detalle {
              width: 100%;
              border-collapse: collapse;
              margin-top: 10px;
              font-size: 13px;
            }

            table.detalle th {
              background: #0f7b3f;
              color: #ffffff;
              border: 1px solid #0f7b3f;
              padding: 8px;
              text-align: left;
            }

            table.detalle td {
              border: 1px solid #cfcfcf;
              padding: 8px;
            }

            .valor {
              text-align: right;
              white-space: nowrap;
            }

            .resumen-final {
              margin-top: 20px;
              width: 100%;
              border-collapse: collapse;
              font-size: 14px;
            }

            .resumen-final td {
              border: 1px solid #cfcfcf;
              padding: 9px;
            }

            .resumen-final .etiqueta {
              font-weight: bold;
              background: #f5f5f5;
            }

            .total-pagar {
              font-size: 18px;
              font-weight: bold;
              color: #0f7b3f;
            }

            .observacion {
              margin-top: 20px;
              font-size: 12px;
              color: #555;
              text-align: justify;
              border: 1px solid #e0e0e0;
              padding: 10px;
              background: #fafafa;
            }

            .firmas {
              margin-top: 70px;
              display: flex;
              justify-content: space-between;
              gap: 50px;
            }

            .firma {
              width: 50%;
              text-align: center;
              font-size: 12px;
            }

            .linea-firma {
              border-top: 1px solid #222;
              margin-bottom: 6px;
              padding-top: 6px;
            }

            .acciones {
              text-align: center;
              margin-top: 25px;
            }

            .btn-imprimir {
              background: #0f7b3f;
              color: white;
              border: none;
              padding: 10px 25px;
              border-radius: 5px;
              cursor: pointer;
              font-size: 14px;
            }

            .btn-imprimir:hover {
              background: #0b5f30;
            }

            .pie {
              margin-top: 25px;
              font-size: 11px;
              color: #777;
              text-align: center;
            }

            @media print {
              body {
                background: #ffffff;
                padding: 0;
              }

              .comprobante {
                width: 100%;
                border: none;
                padding: 20px;
              }

              .acciones {
                display: none;
              }

              @page {
                size: A4;
                margin: 15mm;
              }
            }
          </style>
        </head>

        <body>
          <div class="comprobante">
            <div class="encabezado">
              <div class="empresa">PILADORA DON GUILLO</div>
              <div class="titulo">COMPROBANTE DE ROL DE PAGO</div>
              <div class="subtitulo">Documento generado desde el módulo de Talento Humano</div>
            </div>

            <div class="bloque">
              <h3>Datos del trabajador</h3>
              <table class="datos">
                <tr>
                  <td><strong>Empleado:</strong> ${empleado}</td>
                  <td><strong>Cédula:</strong> ${cedula}</td>
                </tr>
                <tr>
                  <td><strong>Cargo:</strong> ${cargo}</td>
                  <td><strong>Área:</strong> ${area}</td>
                </tr>
                <tr>
                  <td><strong>Periodo:</strong> ${periodo}</td>
                  <td><strong>Fecha de generación:</strong> ${fechaGeneracion}</td>
                </tr>
              </table>
            </div>

            <div class="bloque">
              <h3>Detalle de ingresos</h3>
              <table class="detalle">
                <thead>
                  <tr>
                    <th>Concepto</th>
                    <th class="valor">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Sueldo base</td>
                    <td class="valor">${formatearDinero(sueldoBase)}</td>
                  </tr>
                  <tr>
                    <td>Horas extras</td>
                    <td class="valor">${formatearDinero(horasExtras)}</td>
                  </tr>
                  <tr>
                    <td>Bonificaciones</td>
                    <td class="valor">${formatearDinero(bonificaciones)}</td>
                  </tr>
                  <tr>
                    <td><strong>Total ingresos</strong></td>
                    <td class="valor"><strong>${formatearDinero(totalIngresos)}</strong></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="bloque">
              <h3>Detalle de egresos / deducciones</h3>
              <table class="detalle">
                <thead>
                  <tr>
                    <th>Concepto</th>
                    <th class="valor">Valor</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Sanciones</td>
                    <td class="valor">${formatearDinero(sanciones)}</td>
                  </tr>
                  <tr>
                    <td>Descuentos</td>
                    <td class="valor">${formatearDinero(descuentos)}</td>
                  </tr>
                  <tr>
                    <td><strong>Total egresos</strong></td>
                    <td class="valor"><strong>${formatearDinero(totalEgresos)}</strong></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <table class="resumen-final">
              <tr>
                <td class="etiqueta">Total ingresos</td>
                <td class="valor">${formatearDinero(totalIngresos)}</td>
              </tr>
              <tr>
                <td class="etiqueta">Total egresos</td>
                <td class="valor">${formatearDinero(totalEgresos)}</td>
              </tr>
              <tr>
                <td class="etiqueta total-pagar">TOTAL A RECIBIR</td>
                <td class="valor total-pagar">${formatearDinero(totalPagar)}</td>
              </tr>
            </table>

            <div class="observacion">
              <strong>Observación:</strong>
              Este comprobante corresponde al rol de pago generado para el periodo indicado.
              Los valores de sueldo base, horas extras, bonificaciones, sanciones y descuentos
              fueron calculados con base en la información registrada en el módulo de Talento Humano.
            </div>

            <div class="firmas">
              <div class="firma">
                <div class="linea-firma">Firma del trabajador</div>
                ${empleado}
              </div>

              <div class="firma">
                <div class="linea-firma">Firma del responsable</div>
                Piladora Don Guillo
              </div>
            </div>

            <div class="pie">
              Comprobante generado automáticamente por el ERP Piladora Don Guillo.
            </div>

            <div class="acciones">
              <button class="btn-imprimir" onclick="window.print()">
                Imprimir / Guardar como PDF
              </button>
            </div>
          </div>
        </body>
      </html>
    `;

    const ventana = window.open("", "_blank");

    if (!ventana) {
      alert("El navegador bloqueó la ventana emergente. Permita ventanas emergentes para generar el comprobante.");
      return;
    }

    ventana.document.open();
    ventana.document.write(contenido);
    ventana.document.close();
    ventana.focus();
  };

  // ============================================================
  // CARGA INICIAL
  // ============================================================

  configurarLimitesFechas();
  limpiarFormularioEmpleado();
  limpiarFormularioAsistencia();
  limpiarFormularioRolPago();

  cargarResumenEmpleados();
  cargarEmpleados();
  cargarRolesPago();
  cargarAsistencia();
});