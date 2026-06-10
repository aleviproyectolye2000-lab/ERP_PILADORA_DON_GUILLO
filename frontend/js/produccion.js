/* ---------------------------------------------------- */
/* MÓDULO DE PRODUCCIÓN Y PILADO                        */
/* ERP PILADORA DON GUILLO                              */
/* Frontend conectado con FastAPI + PostgreSQL          */
/* ---------------------------------------------------- */

let idOrdenEditando = null;
let cantidadAnteriorEditando = 0;
let loteAnteriorEditando = "";
let inventarioProduccion = [];
let ordenesProduccion = [];

/* ---------------------------------------------------- */
/* FUNCIONES GENERALES                                  */
/* ---------------------------------------------------- */

function numeroProduccion(valor) {
  const numero = Number(String(valor || "").replace(",", "."));
  return Number.isFinite(numero) ? numero : 0;
}

function formatoProduccion(valor) {
  return numeroProduccion(valor).toFixed(2);
}

function limpiarTextoProduccion(valor) {
  return String(valor || "").trim();
}

function normalizarTextoProduccion(valor) {
  return String(valor || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function fechaActualProduccion() {
  if (typeof obtenerFechaActualISO === "function") {
    return obtenerFechaActualISO();
  }

  const hoy = new Date();
  const anio = hoy.getFullYear();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");

  return `${anio}-${mes}-${dia}`;
}

function idUsuarioProduccion() {
  return Number(localStorage.getItem("idUsuarioERP") || 1);
}

function mostrarMensajeProduccion(tipo, mensaje) {
  const mensajeProduccion = document.getElementById("mensajeProduccion");

  if (!mensajeProduccion) {
    alert(mensaje);
    return;
  }

  mensajeProduccion.classList.remove(
    "d-none",
    "alert-success",
    "alert-danger",
    "alert-warning",
    "alert-info"
  );

  mensajeProduccion.classList.add(`alert-${tipo}`);
  mensajeProduccion.textContent = mensaje;
}

function ocultarMensajeProduccion() {
  const mensajeProduccion = document.getElementById("mensajeProduccion");

  if (!mensajeProduccion) return;

  mensajeProduccion.classList.add("d-none");
  mensajeProduccion.textContent = "";
}

/* ---------------------------------------------------- */
/* CÁLCULOS ESTRICTOS DE PRODUCCIÓN                     */
/* ---------------------------------------------------- */

function calcularProduccion() {
  const cantidadProcesada = document.getElementById("cantidadProcesada");
  const arrozPiladoObtenido = document.getElementById("arrozPiladoObtenido");
  const arrocilloObtenido = document.getElementById("arrocilloObtenido");
  const polvilloObtenido = document.getElementById("polvilloObtenido");
  const cascarillaObtenida = document.getElementById("cascarillaObtenida");
  const tamoObtenido = document.getElementById("tamoObtenido");
  const mermaPilado = document.getElementById("mermaPilado");
  const rendimientoPilado = document.getElementById("rendimientoPilado");

  if (!cantidadProcesada) return;

  const procesado = numeroProduccion(cantidadProcesada.value);
  const pilado = numeroProduccion(arrozPiladoObtenido?.value);
  const arrocillo = numeroProduccion(arrocilloObtenido?.value);
  const polvillo = numeroProduccion(polvilloObtenido?.value);
  const cascarilla = numeroProduccion(cascarillaObtenida?.value);
  const tamo = numeroProduccion(tamoObtenido?.value);

  const totalSalidaSinMerma = pilado + arrocillo + polvillo + cascarilla + tamo;
  const merma = procesado - totalSalidaSinMerma;

  if (mermaPilado) {
    if (procesado > 0) {
      mermaPilado.value = formatoProduccion(merma);
      // Alerta visual si la merma es negativa (ley de conservación de masa)
      if (merma < 0) {
        mermaPilado.classList.add("is-invalid", "text-danger");
        mostrarMensajeProduccion("danger", "¡Alerta! La suma de productos obtenidos supera la cantidad ingresada a procesar (Merma negativa).");
      } else {
        mermaPilado.classList.remove("is-invalid", "text-danger");
        ocultarMensajeProduccion();
      }
    } else {
      mermaPilado.value = "";
      mermaPilado.classList.remove("is-invalid", "text-danger");
    }
  }

  if (rendimientoPilado) {
    const rendimiento = procesado > 0 ? (pilado / procesado) * 100 : 0;
    rendimientoPilado.value = procesado > 0 ? formatoProduccion(rendimiento) : "";
  }
}

/* ---------------------------------------------------- */
/* LOTES DE ARROZ EN CÁSCARA DESDE INVENTARIO           */
/* ---------------------------------------------------- */

async function cargarLotesArrozCascara() {
  const loteOrigen = document.getElementById("loteOrigen");

  if (!loteOrigen) return;

  inventarioProduccion = await window.apiGet("/api/inventario/");

  const lotesCascara = inventarioProduccion.filter((item) => {
    const producto = normalizarTextoProduccion(item.nombre_producto);
    const tipo = normalizarTextoProduccion(item.tipo_producto);
    const cantidad = numeroProduccion(item.cantidad_disponible);

    return (
      producto.includes("arroz en cascara") &&
      tipo.includes("materia prima") &&
      cantidad > 0
    );
  });

  loteOrigen.innerHTML = `<option value="">Seleccione un lote disponible</option>`;

  lotesCascara.forEach((item) => {
    const option = document.createElement("option");

    option.value = item.lote;
    option.textContent = `${item.lote} - ${formatoProduccion(item.cantidad_disponible)} qq disponibles`;
    option.dataset.stock = item.cantidad_disponible;
    option.dataset.idInventario = item.id_inventario;

    loteOrigen.appendChild(option);
  });
}

function obtenerStockLoteSeleccionado() {
  const loteOrigen = document.getElementById("loteOrigen");

  if (!loteOrigen || !loteOrigen.value) return 0;

  const option = loteOrigen.options[loteOrigen.selectedIndex];

  return numeroProduccion(option?.dataset?.stock);
}

function asegurarLoteEnSelect(lote, cantidad) {
  const loteOrigen = document.getElementById("loteOrigen");

  if (!loteOrigen || !lote) return;

  const existe = Array.from(loteOrigen.options).some((option) => {
    return option.value === lote;
  });

  if (!existe) {
    const option = document.createElement("option");
    option.value = lote;
    option.textContent = `${lote} - lote de orden existente`;
    option.dataset.stock = cantidad || 0;
    loteOrigen.appendChild(option);
  }

  loteOrigen.value = lote;
}

/* ---------------------------------------------------- */
/* NÚMERO DE ORDEN AUTOMÁTICO                           */
/* ---------------------------------------------------- */

async function generarNumeroOrdenAutomatico() {
  const numeroOrden = document.getElementById("numeroOrden");

  if (!numeroOrden || idOrdenEditando) return;

  try {
    const respuesta = await window.apiGet("/api/produccion/siguiente-numero");
    numeroOrden.value = respuesta.numero_orden || "";
  } catch {
    const fecha = fechaActualProduccion().replaceAll("-", "");
    const aleatorio = Math.random().toString(36).substring(2, 7).toUpperCase();
    numeroOrden.value = `OP-${fecha}-${aleatorio}`;
  }
}

/* ---------------------------------------------------- */
/* TARJETAS                                             */
/* ---------------------------------------------------- */

function actualizarResumenProduccion() {
  const totalOrdenesPilado = document.getElementById("totalOrdenesPilado");
  const totalProcesado = document.getElementById("totalProcesado");
  const totalPilado = document.getElementById("totalPilado");
  const rendimientoPromedio = document.getElementById("rendimientoPromedio");

  if (!totalOrdenesPilado || !totalProcesado || !totalPilado || !rendimientoPromedio) {
    return;
  }

  const ordenesActivas = ordenesProduccion.filter((orden) => {
    return orden.estado !== false && orden.estado_pilado !== "Anulado";
  });

  const totalOrdenes = ordenesActivas.length;

  const procesado = ordenesActivas.reduce((acum, orden) => {
    return acum + numeroProduccion(orden.cantidad_procesada);
  }, 0);

  const pilado = ordenesActivas.reduce((acum, orden) => {
    return acum + numeroProduccion(orden.arroz_pilado_obtenido);
  }, 0);

  const rendimientoTotal = ordenesActivas.reduce((acum, orden) => {
    return acum + numeroProduccion(orden.rendimiento_porcentaje);
  }, 0);

  const rendimientoProm = totalOrdenes > 0 ? rendimientoTotal / totalOrdenes : 0;

  totalOrdenesPilado.textContent = totalOrdenes;
  totalProcesado.textContent = `${formatoProduccion(procesado)} qq`;
  totalPilado.textContent = `${formatoProduccion(pilado)} qq`;
  rendimientoPromedio.textContent = `${formatoProduccion(rendimientoProm)}%`;
}

/* ---------------------------------------------------- */
/* TABLA                                                */
/* ---------------------------------------------------- */

function renderizarTablaProduccion() {
  const tablaProduccion = document.getElementById("tablaProduccion");

  if (!tablaProduccion) return;

  if (!ordenesProduccion || ordenesProduccion.length === 0) {
    tablaProduccion.innerHTML = `
      <tr>
        <td colspan="12" class="text-center text-muted">
          No existen órdenes de pilado registradas.
        </td>
      </tr>
    `;
    actualizarResumenProduccion();
    return;
  }

  tablaProduccion.innerHTML = "";

  ordenesProduccion.forEach((orden, index) => {
    const subproductos =
      numeroProduccion(orden.arrocillo_obtenido) +
      numeroProduccion(orden.polvillo_obtenido) +
      numeroProduccion(orden.cascarilla_obtenida) +
      numeroProduccion(orden.tamo_obtenido);

    const anulada = orden.estado === false || orden.estado_pilado === "Anulado";

    let estadoClase = "badge bg-success";
    let estadoTexto = orden.estado_pilado || "Finalizado";

    if (estadoTexto === "En proceso") {
      estadoClase = "badge bg-warning text-dark";
    }

    if (estadoTexto === "Observado") {
      estadoClase = "badge bg-danger";
    }

    if (anulada) {
      estadoClase = "badge bg-danger";
      estadoTexto = "Anulado";
    }

    const fila = document.createElement("tr");

    if (anulada) {
      fila.classList.add("table-danger");
    }

    fila.innerHTML = `
      <td>${index + 1}</td>
      <td>${orden.numero_orden || "-"}</td>
      <td>${orden.fecha_pilado || "-"}</td>
      <td>${orden.lote_origen || "-"}</td>
      <td>${orden.tipo_arroz_procesado || "-"}</td>
      <td>${formatoProduccion(orden.cantidad_procesada)} qq</td>
      <td>${formatoProduccion(orden.arroz_pilado_obtenido)} qq</td>
      <td>${formatoProduccion(subproductos)} qq</td>
      <td>${formatoProduccion(orden.merma)} qq</td>
      <td>${formatoProduccion(orden.rendimiento_porcentaje)}%</td>
      <td><span class="${estadoClase}">${estadoTexto}</span></td>
      <td>
        ${
          anulada
            ? `<span class="text-danger fw-bold">Orden anulada</span>`
            : `
              <button 
                type="button" 
                class="btn btn-sm btn-warning me-1"
                onclick="editarOrdenProduccion(${orden.id_orden_pilado})">
                Editar
              </button>
              <button 
                type="button" 
                class="btn btn-sm btn-danger"
                onclick="anularOrdenProduccion(${orden.id_orden_pilado})">
                Anular
              </button>
            `
        }
      </td>
    `;

    tablaProduccion.appendChild(fila);
  });

  actualizarResumenProduccion();
}

async function cargarProduccion() {
  const tablaProduccion = document.getElementById("tablaProduccion");

  if (!tablaProduccion) return;

  try {
    ordenesProduccion = await window.apiGet("/api/produccion/");
    renderizarTablaProduccion();
  } catch (error) {
    tablaProduccion.innerHTML = `
      <tr>
        <td colspan="12" class="text-center text-danger">
          Error al cargar producción: ${error.message}
        </td>
      </tr>
    `;
  }
}

/* ---------------------------------------------------- */
/* LIMPIAR FORMULARIO                                   */
/* ---------------------------------------------------- */

async function limpiarFormularioProduccion() {
  const formProduccion = document.getElementById("formProduccion");

  if (formProduccion) {
    formProduccion.reset();
  }

  idOrdenEditando = null;
  cantidadAnteriorEditando = 0;
  loteAnteriorEditando = "";

  const boton = document.querySelector("#formProduccion button[type='submit']");

  if (boton) {
    boton.textContent = "Registrar pilado";
    boton.classList.remove("btn-warning");
    boton.classList.add("btn-success");
  }

  const fechaPilado = document.getElementById("fechaPilado");
  const estadoPilado = document.getElementById("estadoPilado");
  const mermaPilado = document.getElementById("mermaPilado");

  if (fechaPilado) {
    fechaPilado.max = fechaActualProduccion();
  }

  if (estadoPilado) {
    estadoPilado.value = "";
  }
  
  if (mermaPilado) {
    mermaPilado.classList.remove("is-invalid", "text-danger");
  }

  ocultarMensajeProduccion();

  await cargarLotesArrozCascara();
  await generarNumeroOrdenAutomatico();
}

/* ---------------------------------------------------- */
/* EDITAR                                               */
/* ---------------------------------------------------- */

async function editarOrdenProduccion(idOrden) {
  try {
    const orden = await window.apiGet(`/api/produccion/${idOrden}`);

    if (orden.estado === false || orden.estado_pilado === "Anulado") {
      alert("No se puede editar una orden anulada.");
      return;
    }

    idOrdenEditando = idOrden;
    cantidadAnteriorEditando = numeroProduccion(orden.cantidad_procesada);
    loteAnteriorEditando = orden.lote_origen || "";

    document.getElementById("numeroOrden").value = orden.numero_orden || "";
    document.getElementById("fechaPilado").value = orden.fecha_pilado || "";

    asegurarLoteEnSelect(orden.lote_origen, orden.cantidad_procesada);

    document.getElementById("maquinaUtilizada").value = orden.maquina_utilizada || "";
    document.getElementById("operadorPilado").value = orden.operador || "";
    document.getElementById("tipoArrozProcesado").value = orden.tipo_arroz_procesado || "";
    document.getElementById("cantidadProcesada").value = numeroProduccion(orden.cantidad_procesada);
    document.getElementById("arrozPiladoObtenido").value = numeroProduccion(orden.arroz_pilado_obtenido);
    document.getElementById("arrocilloObtenido").value = numeroProduccion(orden.arrocillo_obtenido);
    document.getElementById("polvilloObtenido").value = numeroProduccion(orden.polvillo_obtenido);
    document.getElementById("cascarillaObtenida").value = numeroProduccion(orden.cascarilla_obtenida);
    document.getElementById("tamoObtenido").value = numeroProduccion(orden.tamo_obtenido);
    document.getElementById("mermaPilado").value = numeroProduccion(orden.merma);
    document.getElementById("rendimientoPilado").value = numeroProduccion(orden.rendimiento_porcentaje);
    document.getElementById("estadoPilado").value = orden.estado_pilado || "Finalizado";

    const observacionPilado = document.getElementById("observacionPilado");

    if (observacionPilado) {
      observacionPilado.value = orden.observacion || "";
    }

    calcularProduccion();

    const boton = document.querySelector("#formProduccion button[type='submit']");

    if (boton) {
      boton.textContent = "Actualizar pilado";
      boton.classList.remove("btn-success");
      boton.classList.add("btn-warning");
    }

    mostrarMensajeProduccion(
      "warning",
      `Editando orden de pilado N° ${orden.numero_orden}. Realice los cambios y presione Actualizar pilado.`
    );

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });

  } catch (error) {
    alert(`Error al cargar la orden para editar: ${error.message}`);
  }
}

/* ---------------------------------------------------- */
/* ANULAR                                               */
/* ---------------------------------------------------- */

async function anularOrdenProduccion(idOrden) {
  const confirmar = confirm(
    "¿Seguro que deseas anular esta orden? Se reversará el inventario: volverá el arroz en cáscara y se descontarán los productos generados."
  );

  if (!confirmar) return;

  try {
    await window.apiDelete(`/api/produccion/${idOrden}`);

    alert("Orden anulada correctamente. El inventario fue reversado.");

    await cargarLotesArrozCascara();
    await cargarProduccion();
    await limpiarFormularioProduccion();

  } catch (error) {
    alert(`Error al anular orden: ${error.message}`);
  }
}

window.editarOrdenProduccion = editarOrdenProduccion;
window.anularOrdenProduccion = anularOrdenProduccion;

/* ---------------------------------------------------- */
/* INICIO DEL FORMULARIO                                */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  const formProduccion = document.getElementById("formProduccion");

  if (!formProduccion) return;

  const numeroOrden = document.getElementById("numeroOrden");
  const fechaPilado = document.getElementById("fechaPilado");
  const loteOrigen = document.getElementById("loteOrigen");
  const maquinaUtilizada = document.getElementById("maquinaUtilizada");
  const operadorPilado = document.getElementById("operadorPilado");
  const tipoArrozProcesado = document.getElementById("tipoArrozProcesado");
  const cantidadProcesada = document.getElementById("cantidadProcesada");
  const arrozPiladoObtenido = document.getElementById("arrozPiladoObtenido");
  const arrocilloObtenido = document.getElementById("arrocilloObtenido");
  const polvilloObtenido = document.getElementById("polvilloObtenido");
  const cascarillaObtenida = document.getElementById("cascarillaObtenida");
  const tamoObtenido = document.getElementById("tamoObtenido");
  const mermaPilado = document.getElementById("mermaPilado");
  const rendimientoPilado = document.getElementById("rendimientoPilado");
  const estadoPilado = document.getElementById("estadoPilado");
  const observacionPilado = document.getElementById("observacionPilado");

  // Filtros de escritura en tiempo real
  if (operadorPilado) {
    operadorPilado.addEventListener("input", function () {
      this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g, "");
    });
  }

  if (maquinaUtilizada) {
    maquinaUtilizada.addEventListener("input", function () {
      this.value = this.value.replace(/[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ\s\-\_]/g, "");
    });
  }

  if (fechaPilado) {
    fechaPilado.max = fechaActualProduccion();
  }

  if (numeroOrden) {
    numeroOrden.readOnly = true;
  }

  if (mermaPilado) {
    mermaPilado.readOnly = true;
  }

  if (rendimientoPilado) {
    rendimientoPilado.readOnly = true;
  }

  try {
    await cargarLotesArrozCascara();
    await cargarProduccion();
    await generarNumeroOrdenAutomatico();
  } catch (error) {
    mostrarMensajeProduccion(
      "danger",
      `Error al iniciar producción: ${error.message}`
    );
  }

  [
    cantidadProcesada,
    arrozPiladoObtenido,
    arrocilloObtenido,
    polvilloObtenido,
    cascarillaObtenida,
    tamoObtenido
  ].forEach((input) => {
    if (!input) return;

    input.addEventListener("input", function () {
      if (Number(this.value) < 0) {
        this.value = "";
        mostrarMensajeProduccion(
          "danger",
          "No se permiten valores negativos en producción."
        );
      }

      calcularProduccion();
    });
  });

  if (loteOrigen) {
    loteOrigen.addEventListener("change", function () {
      const stock = obtenerStockLoteSeleccionado();

      if (stock > 0) {
        mostrarMensajeProduccion(
          "info",
          `Lote seleccionado con ${formatoProduccion(stock)} qq disponibles.`
        );
      } else {
        ocultarMensajeProduccion();
      }
    });
  }

  formProduccion.addEventListener("reset", function () {
    setTimeout(async () => {
      await limpiarFormularioProduccion();
    }, 50);
  });

  formProduccion.addEventListener("submit", async function (event) {
    event.preventDefault();

    if (!window.apiPost || !window.apiPut || !window.apiGet || !window.apiDelete) {
      mostrarMensajeProduccion(
        "danger",
        "No se cargó correctamente api.js. Revise que produccion.html cargue primero js/api.js, luego js/main.js y después js/produccion.js."
      );
      return;
    }

    calcularProduccion();

    const numero = limpiarTextoProduccion(numeroOrden?.value);
    const fecha = fechaPilado?.value;
    const lote = limpiarTextoProduccion(loteOrigen?.value);
    const maquina = limpiarTextoProduccion(maquinaUtilizada?.value);
    const operador = limpiarTextoProduccion(operadorPilado?.value);
    const tipoArroz = limpiarTextoProduccion(tipoArrozProcesado?.value);
    const procesado = numeroProduccion(cantidadProcesada?.value);
    const pilado = numeroProduccion(arrozPiladoObtenido?.value);
    const arrocillo = numeroProduccion(arrocilloObtenido?.value);
    const polvillo = numeroProduccion(polvilloObtenido?.value);
    const cascarilla = numeroProduccion(cascarillaObtenida?.value);
    const tamo = numeroProduccion(tamoObtenido?.value);
    const merma = numeroProduccion(mermaPilado?.value);
    const estado = limpiarTextoProduccion(estadoPilado?.value);
    const observacion = limpiarTextoProduccion(observacionPilado?.value);
    const fechaActual = fechaActualProduccion();

    // VALIDACIÓN ESTRICTA AL MOMENTO DE GUARDAR
    if (
      numero === "" ||
      fecha === "" ||
      lote === "" ||
      operador === "" ||
      tipoArroz === "" ||
      procesado <= 0 ||
      pilado <= 0 ||
      estado === ""
    ) {
      mostrarMensajeProduccion(
        "danger",
        "Complete los campos obligatorios correctamente. La cantidad procesada y el arroz pilado deben ser mayores a cero."
      );
      return;
    }

    if (fecha > fechaActual) {
      mostrarMensajeProduccion(
        "danger",
        "No se permite registrar una orden de pilado con fecha futura."
      );
      return;
    }

    if (
      procesado < 0 ||
      pilado < 0 ||
      arrocillo < 0 ||
      polvillo < 0 ||
      cascarilla < 0 ||
      tamo < 0 
    ) {
      mostrarMensajeProduccion(
        "danger",
        "No se permiten valores negativos en producción."
      );
      return;
    }

    const totalSalida = pilado + arrocillo + polvillo + cascarilla + tamo;

    // Validación inquebrantable de la conservación de la masa
    if (totalSalida > procesado || merma < 0) {
      mostrarMensajeProduccion(
        "danger",
        "Físicamente imposible: La suma de arroz pilado y subproductos no puede ser mayor a la cantidad procesada en cáscara."
      );
      return;
    }

    const stockLote = obtenerStockLoteSeleccionado();

    if (!idOrdenEditando) {
      if (stockLote <= 0) {
        mostrarMensajeProduccion(
          "danger",
          "Seleccione un lote de arroz en cáscara con stock disponible."
        );
        return;
      }

      if (procesado > stockLote) {
        mostrarMensajeProduccion(
          "danger",
          `Stock insuficiente. El lote seleccionado tiene ${formatoProduccion(stockLote)} qq disponibles. Usted intenta procesar ${formatoProduccion(procesado)} qq.`
        );
        return;
      }
    }

    if (idOrdenEditando) {
      let stockPermitido = stockLote;

      if (lote === loteAnteriorEditando) {
        stockPermitido = stockLote + cantidadAnteriorEditando;
      }

      if (stockPermitido > 0 && procesado > stockPermitido) {
        mostrarMensajeProduccion(
          "danger",
          `Stock insuficiente para actualizar. Stock permitido máximo: ${formatoProduccion(stockPermitido)} qq.`
        );
        return;
      }
    }

    const datosProduccion = {
      numero_orden: numero,
      id_usuario: idUsuarioProduccion(),
      fecha_pilado: fecha,
      lote_origen: lote,
      tipo_arroz_procesado: tipoArroz,
      cantidad_procesada: procesado,
      maquina_utilizada: maquina,
      operador: operador,
      arroz_pilado_obtenido: pilado,
      arrocillo_obtenido: arrocillo,
      polvillo_obtenido: polvillo,
      cascarilla_obtenida: cascarilla,
      tamo_obtenido: tamo,
      merma: merma,
      estado_pilado: estado,
      observacion: observacion
    };

    try {
      if (idOrdenEditando) {
        await window.apiPut(
          `/api/produccion/${idOrdenEditando}`,
          datosProduccion
        );

        mostrarMensajeProduccion(
          "success",
          "Orden de pilado actualizada correctamente. El inventario fue recalculado."
        );
      } else {
        await window.apiPost(
          "/api/produccion/registrar-completa",
          datosProduccion
        );

        mostrarMensajeProduccion(
          "success",
          "Producción registrada correctamente. Se descontó arroz en cáscara y se agregaron productos al inventario."
        );
      }

      await cargarLotesArrozCascara();
      await cargarProduccion();
      await limpiarFormularioProduccion();

    } catch (error) {
      mostrarMensajeProduccion(
        "danger",
        `Error al guardar producción: ${error.message}`
      );
    }
  });
});