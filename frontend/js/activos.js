

/* ---------------------------------------------------- */
/* MÓDULO DE MAQUINARIA, VEHÍCULOS Y ACTIVOS            */
/* ---------------------------------------------------- */

const formActivos = document.getElementById("formActivos");

if (formActivos) {
  const codigoActivo = document.getElementById("codigoActivo");
  const nombreActivo = document.getElementById("nombreActivo");
  const tipoActivo = document.getElementById("tipoActivo");
  const estadoActivo = document.getElementById("estadoActivo");
  const fechaAdquisicionActivo = document.getElementById("fechaAdquisicionActivo");
  const valorActivo = document.getElementById("valorActivo");
  const responsableActivo = document.getElementById("responsableActivo");
  const ubicacionActivo = document.getElementById("ubicacionActivo");
  const ultimoMantenimientoActivo = document.getElementById("ultimoMantenimientoActivo");
  const proximoMantenimientoActivo = document.getElementById("proximoMantenimientoActivo");
  const costoMantenimientoActivo = document.getElementById("costoMantenimientoActivo");
  const gastoCombustibleActivo = document.getElementById("gastoCombustibleActivo");
  const tablaActivos = document.getElementById("tablaActivos");

  const totalActivos = document.getElementById("totalActivos");
  const totalMantenimiento = document.getElementById("totalMantenimiento");
  const totalDanados = document.getElementById("totalDanados");
  const valorTotalActivos = document.getElementById("valorTotalActivos");

  let activos = [];

  if (fechaAdquisicionActivo) {
    fechaAdquisicionActivo.max = obtenerFechaActualISO();
  }

  if (ultimoMantenimientoActivo) {
    ultimoMantenimientoActivo.max = obtenerFechaActualISO();
  }

  function actualizarResumenActivos() {
    totalActivos.textContent = activos.length;

    const mantenimiento = activos.filter(function (activo) {
      return activo.estado === "Mantenimiento";
    }).length;

    const danados = activos.filter(function (activo) {
      return activo.estado === "Dañado";
    }).length;

    const valorTotal = activos.reduce(function (acumulado, activo) {
      return acumulado + activo.valor;
    }, 0);

    totalMantenimiento.textContent = mantenimiento;
    totalDanados.textContent = danados;
    valorTotalActivos.textContent = "$ " + valorTotal.toFixed(2);
  }

  function renderizarTablaActivos() {
    if (activos.length === 0) {
      tablaActivos.innerHTML = `
        <tr>
          <td colspan="9" class="text-center text-muted">No existen activos registrados</td>
        </tr>
      `;
      actualizarResumenActivos();
      return;
    }

    tablaActivos.innerHTML = "";

    activos.forEach(function (activo) {
      let estadoBadge = "bg-success";

      if (activo.estado === "Mantenimiento") {
        estadoBadge = "bg-warning text-dark";
      }

      if (activo.estado === "Dañado" || activo.estado === "Inactivo") {
        estadoBadge = "bg-danger";
      }

      const gastos = activo.costoMantenimiento + activo.gastoCombustible;

      const fila = document.createElement("tr");

      fila.innerHTML = `
        <td>${activo.codigo}</td>
        <td>${activo.nombre}</td>
        <td>${activo.tipo}</td>
        <td><span class="badge ${estadoBadge}">${activo.estado}</span></td>
        <td>${activo.responsable}</td>
        <td>${activo.ubicacion || "Sin ubicación"}</td>
        <td>$ ${activo.valor.toFixed(2)}</td>
        <td>${activo.proximoMantenimiento || "No definido"}</td>
        <td>$ ${gastos.toFixed(2)}</td>
      `;

      tablaActivos.appendChild(fila);
    });

    actualizarResumenActivos();
  }

  formActivos.addEventListener("submit", function (event) {
    event.preventDefault();

    const codigo = codigoActivo.value.trim();
    const nombre = nombreActivo.value.trim();
    const tipo = tipoActivo.value;
    const estado = estadoActivo.value;
    const fechaAdquisicion = fechaAdquisicionActivo.value;
    const valor = parseFloat(valorActivo.value) || 0;
    const responsable = responsableActivo.value.trim();
    const ubicacion = ubicacionActivo.value.trim();
    const ultimoMantenimiento = ultimoMantenimientoActivo.value;
    const proximoMantenimiento = proximoMantenimientoActivo.value;
    const costoMantenimiento = parseFloat(costoMantenimientoActivo.value) || 0;
    const gastoCombustible = parseFloat(gastoCombustibleActivo.value) || 0;
    const fechaActual = obtenerFechaActualISO();

    if (
      codigo === "" ||
      nombre === "" ||
      tipo === "" ||
      estado === "" ||
      fechaAdquisicion === "" ||
      valor <= 0 ||
      responsable === ""
    ) {
      alert("Complete todos los campos obligatorios correctamente.");
      return;
    }

    if (fechaAdquisicion > fechaActual) {
      alert("No se permite registrar activos con fecha de adquisición futura.");
      return;
    }

    if (ultimoMantenimiento && ultimoMantenimiento > fechaActual) {
      alert("La fecha del último mantenimiento no puede ser futura.");
      return;
    }

    if (valor < 0 || costoMantenimiento < 0 || gastoCombustible < 0) {
      alert("No se permiten valores negativos en valor, mantenimiento o combustible.");
      return;
    }

    const codigoExiste = activos.some(function (activo) {
      return activo.codigo.toLowerCase() === codigo.toLowerCase();
    });

    if (codigoExiste) {
      alert("Ya existe un activo registrado con ese código.");
      return;
    }

    const nuevoActivo = {
      codigo: codigo,
      nombre: nombre,
      tipo: tipo,
      estado: estado,
      fechaAdquisicion: fechaAdquisicion,
      valor: valor,
      responsable: responsable,
      ubicacion: ubicacion,
      ultimoMantenimiento: ultimoMantenimiento,
      proximoMantenimiento: proximoMantenimiento,
      costoMantenimiento: costoMantenimiento,
      gastoCombustible: gastoCombustible
    };

    activos.push(nuevoActivo);

    renderizarTablaActivos();

    alert("Activo registrado correctamente.");

    formActivos.reset();

    if (fechaAdquisicionActivo) {
      fechaAdquisicionActivo.max = obtenerFechaActualISO();
    }

    if (ultimoMantenimientoActivo) {
      ultimoMantenimientoActivo.max = obtenerFechaActualISO();
    }
  });

  renderizarTablaActivos();
}




/* ---------------------------------------------------- */
/* PARA EL MANEJO DE ACTIVOS Y MANTENIMIENTOS CON FROND Y BACKEND CONECATDOS     */
/* ---------------------------------------------------- */
document.addEventListener("DOMContentLoaded", async function () {
  const tablaActivos = document.getElementById("tablaActivos");

  if (tablaActivos) {
    try {
      const activos = await window.apiGet("/api/activos/");

      if (!activos || activos.length === 0) {
        tablaActivos.innerHTML = `
          <tr>
            <td colspan="8" class="text-center">No existen activos registrados.</td>
          </tr>
        `;
        return;
      }

      tablaActivos.innerHTML = "";

      activos.forEach((activo) => {
        const fila = document.createElement("tr");

        fila.innerHTML = `
          <td>${activo.id_activo}</td>
          <td>${activo.codigo_activo}</td>
          <td>${activo.nombre_activo}</td>
          <td>${activo.tipo_activo}</td>
          <td>$ ${Number(activo.valor || 0).toFixed(2)}</td>
          <td>${activo.responsable || "-"}</td>
          <td>${activo.ubicacion || "-"}</td>
          <td>${activo.estado_activo || "-"}</td>
        `;

        tablaActivos.appendChild(fila);
      });

    } catch (error) {
      tablaActivos.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-danger">
            Error al cargar activos: ${error.message}
          </td>
        </tr>
      `;
    }
  }
});


document.addEventListener("DOMContentLoaded", async function () {
  const tablaMantenimientos = document.getElementById("tablaMantenimientos");

  if (tablaMantenimientos) {
    try {
      const mantenimientos = await window.apiGet("/api/activos/mantenimientos/listar");

      if (!mantenimientos || mantenimientos.length === 0) {
        tablaMantenimientos.innerHTML = `
          <tr>
            <td colspan="8" class="text-center">No existen mantenimientos registrados.</td>
          </tr>
        `;
        return;
      }

      tablaMantenimientos.innerHTML = "";

      mantenimientos.forEach((mantenimiento) => {
        const fila = document.createElement("tr");

        fila.innerHTML = `
          <td>${mantenimiento.id_mantenimiento || "-"}</td>
          <td>${mantenimiento.nombre_activo || "-"}</td>
          <td>${mantenimiento.tipo_mantenimiento || "-"}</td>
          <td>${mantenimiento.fecha_mantenimiento || "-"}</td>
          <td>$ ${Number(mantenimiento.costo || 0).toFixed(2)}</td>
          <td>$ ${Number(mantenimiento.gasto_combustible || 0).toFixed(2)}</td>
          <td>${mantenimiento.proximo_mantenimiento || "-"}</td>
          <td>${mantenimiento.responsable || "-"}</td>
        `;

        tablaMantenimientos.appendChild(fila);
      });

    } catch (error) {
      tablaMantenimientos.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-danger">
            Error al cargar mantenimientos: ${error.message}
          </td>
        </tr>
      `;
    }
  }
});

