/* ---------------------------------------------------- */
/* MÓDULO DE COMPRAS, RECEPCIÓN Y BÁSCULA               */
/* Compras separado de main.js                          */
/* ---------------------------------------------------- */

let idCompraEditando = null;

const FACTOR_KG_A_LIBRAS = 2.20462;
const FACTOR_TON_A_LIBRAS = 2204.62;
const LIBRAS_POR_QUINTAL = 100;
const LIBRAS_POR_SACA = 200;

function fechaActualISOCompras() {
  const hoy = new Date();
  const anio = hoy.getFullYear();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");
  return `${anio}-${mes}-${dia}`;
}

function numero(valor) {
  return Number(valor || 0);
}

function redondear(valor) {
  return Number(valor || 0).toFixed(2);
}

function mostrarMensajeCompra(tipo, mensaje) {
  const mensajeCompra = document.getElementById("mensajeCompra");

  if (!mensajeCompra) return;

  mensajeCompra.classList.remove(
    "d-none",
    "alert-success",
    "alert-danger",
    "alert-warning",
    "alert-info"
  );

  mensajeCompra.classList.add(`alert-${tipo}`);
  mensajeCompra.textContent = mensaje;
}

function limpiarMensajeCompra() {
  const mensajeCompra = document.getElementById("mensajeCompra");

  if (!mensajeCompra) return;

  mensajeCompra.classList.add("d-none");
  mensajeCompra.textContent = "";
}

function convertirPesoALibras(peso, unidad) {
  if (unidad === "Libras") return peso;
  if (unidad === "Kilogramos") return peso * FACTOR_KG_A_LIBRAS;
  if (unidad === "Toneladas") return peso * FACTOR_TON_A_LIBRAS;
  return peso;
}

function convertirLibrasAUnidad(libras, unidad) {
  if (unidad === "Libras") return libras;
  if (unidad === "Kilogramos") return libras / FACTOR_KG_A_LIBRAS;
  if (unidad === "Toneladas") return libras / FACTOR_TON_A_LIBRAS;
  return libras;
}

function actualizarLabelsUnidad() {
  const unidadBascula = document.getElementById("unidadBascula");
  const labelDescuentoHumedad = document.getElementById("labelDescuentoHumedad");
  const labelDescuentoImpureza = document.getElementById("labelDescuentoImpureza");

  if (!unidadBascula) return;

  const unidad = unidadBascula.value;

  if (labelDescuentoHumedad) {
    labelDescuentoHumedad.textContent = `Descuento por humedad (${unidad})`;
  }

  if (labelDescuentoImpureza) {
    labelDescuentoImpureza.textContent = `Descuento por impureza (${unidad})`;
  }
}

function actualizarLabelPrecio() {
  const tipoPagoCompra = document.getElementById("tipoPagoCompra");
  const labelPrecioPactado = document.getElementById("labelPrecioPactado");

  if (!tipoPagoCompra || !labelPrecioPactado) return;

  if (tipoPagoCompra.value === "Por quintal") {
    labelPrecioPactado.textContent = "Precio pactado por quintal";
  } else {
    labelPrecioPactado.textContent = "Precio pactado por saca";
  }
}

function calcularCompraFormulario() {
  const unidadBascula = document.getElementById("unidadBascula");
  const pesoEntrada = document.getElementById("pesoEntrada");
  const pesoSalida = document.getElementById("pesoSalida");
  const pesoNeto = document.getElementById("pesoNeto");

  const pesoNetoLibras = document.getElementById("pesoNetoLibras");
  const quintalesBrutos = document.getElementById("quintalesBrutos");
  const sacasBrutas = document.getElementById("sacasBrutas");

  const humedadCompra = document.getElementById("humedadCompra");
  const humedadBase = document.getElementById("humedadBase");
  const descuentoHumedad = document.getElementById("descuentoHumedad");

  const impurezasCompra = document.getElementById("impurezasCompra");
  const impurezaBase = document.getElementById("impurezaBase");
  const descuentoImpureza = document.getElementById("descuentoImpureza");

  const pesoLiquidoLibras = document.getElementById("pesoLiquidoLibras");
  const quintalesLiquidos = document.getElementById("quintalesLiquidos");
  const sacasLiquidas = document.getElementById("sacasLiquidas");

  const tipoPagoCompra = document.getElementById("tipoPagoCompra");
  const precioPactado = document.getElementById("precioPactado");
  const totalBruto = document.getElementById("totalBruto");
  const totalDescuento = document.getElementById("totalDescuento");
  const totalCompra = document.getElementById("totalCompra");

  if (
    !unidadBascula ||
    !pesoEntrada ||
    !pesoSalida ||
    !pesoNeto ||
    !precioPactado ||
    !totalCompra
  ) {
    return;
  }

  const unidad = unidadBascula.value;
  const entrada = numero(pesoEntrada.value);
  const salida = numero(pesoSalida.value);
  const precio = numero(precioPactado.value);

  const humedad = numero(humedadCompra?.value);
  const humedadBaseValor = numero(humedadBase?.value || 14);

  const impurezas = numero(impurezasCompra?.value);
  const impurezaBaseValor = numero(impurezaBase?.value || 5);

  if (entrada <= 0 || salida < 0 || salida >= entrada) {
    pesoNeto.value = "";
    pesoNetoLibras.value = "";
    quintalesBrutos.value = "";
    sacasBrutas.value = "";
    descuentoHumedad.value = "";
    descuentoImpureza.value = "";
    pesoLiquidoLibras.value = "";
    quintalesLiquidos.value = "";
    sacasLiquidas.value = "";
    totalBruto.value = "";
    totalDescuento.value = "";
    totalCompra.value = "";
    return;
  }

  const netoOriginal = entrada - salida;
  const netoLibras = convertirPesoALibras(netoOriginal, unidad);

  const quintalesBrutosValor = netoLibras / LIBRAS_POR_QUINTAL;
  const sacasBrutasValor = netoLibras / LIBRAS_POR_SACA;

  const excesoHumedad = Math.max(0, humedad - humedadBaseValor);
  const excesoImpureza = Math.max(0, impurezas - impurezaBaseValor);

  const descuentoHumedadLibras = netoLibras * (excesoHumedad / 100);
  const descuentoImpurezaLibras = netoLibras * (excesoImpureza / 100);

  const descuentoHumedadUnidad = convertirLibrasAUnidad(descuentoHumedadLibras, unidad);
  const descuentoImpurezaUnidad = convertirLibrasAUnidad(descuentoImpurezaLibras, unidad);

  const liquidoLibras = Math.max(
    0,
    netoLibras - descuentoHumedadLibras - descuentoImpurezaLibras
  );

  const quintalesLiquidosValor = liquidoLibras / LIBRAS_POR_QUINTAL;
  const sacasLiquidasValor = liquidoLibras / LIBRAS_POR_SACA;

  let totalBrutoValor = 0;
  let totalPagarValor = 0;

  if (tipoPagoCompra.value === "Por quintal") {
    totalBrutoValor = quintalesBrutosValor * precio;
    totalPagarValor = quintalesLiquidosValor * precio;
  } else {
    totalBrutoValor = sacasBrutasValor * precio;
    totalPagarValor = sacasLiquidasValor * precio;
  }

  const totalDescuentoValor = Math.max(0, totalBrutoValor - totalPagarValor);

  pesoNeto.value = redondear(netoOriginal);
  pesoNetoLibras.value = redondear(netoLibras);
  quintalesBrutos.value = redondear(quintalesBrutosValor);
  sacasBrutas.value = redondear(sacasBrutasValor);

  descuentoHumedad.value = redondear(descuentoHumedadUnidad);
  descuentoImpureza.value = redondear(descuentoImpurezaUnidad);

  pesoLiquidoLibras.value = redondear(liquidoLibras);
  quintalesLiquidos.value = redondear(quintalesLiquidosValor);
  sacasLiquidas.value = redondear(sacasLiquidasValor);

  totalBruto.value = redondear(totalBrutoValor);
  totalDescuento.value = redondear(totalDescuentoValor);
  totalCompra.value = redondear(totalPagarValor);
}

function limpiarModoEdicionCompra() {
  idCompraEditando = null;

  const botonRegistrar = document.querySelector("#formCompra button[type='submit']");

  if (botonRegistrar) {
    botonRegistrar.textContent = "Registrar compra";
    botonRegistrar.classList.remove("btn-warning");
    botonRegistrar.classList.add("btn-success");
  }
}

function calcularDatosCompraParaTabla(compra) {
  const unidad = compra.unidad_bascula || "Libras";

  const pesoEntrada = Number(compra.peso_bruto || 0);
  const pesoSalida = Number(compra.peso_tara || 0);

  let pesoNetoOriginal = Number(compra.peso_neto || 0);

  if (pesoNetoOriginal <= 0 && pesoEntrada > pesoSalida) {
    pesoNetoOriginal = pesoEntrada - pesoSalida;
  }

  const pesoNetoLibras = Number(
    compra.peso_neto_libras || convertirPesoALibras(pesoNetoOriginal, unidad)
  );

  const quintalesBrutos = Number(
    compra.quintales_brutos || pesoNetoLibras / LIBRAS_POR_QUINTAL
  );

  const sacasBrutas = Number(
    compra.sacas_brutas || pesoNetoLibras / LIBRAS_POR_SACA
  );

  const humedad = Number(compra.humedad || 0);
  const humedadBase = Number(compra.humedad_base ?? 14);

  const impurezas = Number(compra.impurezas || 0);
  const impurezaBase = Number(compra.impureza_base ?? 5);

  const excesoHumedad = Math.max(0, humedad - humedadBase);
  const excesoImpureza = Math.max(0, impurezas - impurezaBase);

  const descuentoHumedadLibras = Number(
    compra.descuento_humedad_libras || pesoNetoLibras * (excesoHumedad / 100)
  );

  const descuentoImpurezaLibras = Number(
    compra.descuento_impureza_libras || pesoNetoLibras * (excesoImpureza / 100)
  );

  const pesoLiquidoLibras = Number(
    compra.peso_liquido_libras ||
      Math.max(0, pesoNetoLibras - descuentoHumedadLibras - descuentoImpurezaLibras)
  );

  const quintalesLiquidos = Number(
    compra.quintales_liquidos || pesoLiquidoLibras / LIBRAS_POR_QUINTAL
  );

  const sacasLiquidas = Number(
    compra.sacas_liquidas || pesoLiquidoLibras / LIBRAS_POR_SACA
  );

  const tipoPago = compra.tipo_pago || "Por quintal";

  const precioPactado = Number(
    compra.precio_pactado ?? compra.precio_quintal ?? 0
  );

  let totalBruto = Number(compra.total_bruto || 0);
  let totalPagar = Number(compra.total_compra || 0);
  let totalDescuento = Number(compra.total_descuento || 0);

  if (totalBruto <= 0) {
    if (tipoPago === "Por saca") {
      totalBruto = sacasBrutas * precioPactado;
    } else {
      totalBruto = quintalesBrutos * precioPactado;
    }
  }

  if (totalPagar <= 0) {
    if (tipoPago === "Por saca") {
      totalPagar = sacasLiquidas * precioPactado;
    } else {
      totalPagar = quintalesLiquidos * precioPactado;
    }
  }

  if (totalDescuento <= 0) {
    totalDescuento = Math.max(0, totalBruto - totalPagar);
  }

  return {
    unidad,
    quintalesBrutos,
    quintalesLiquidos,
    sacasLiquidas,
    tipoPago,
    precioPactado,
    totalBruto,
    totalDescuento,
    totalPagar
  };
}


async function cargarCompras() {
  const tablaCompras = document.getElementById("tablaCompras");

  if (!tablaCompras) return;

  try {
    let compras = await window.apiGet("/api/compras/");

    if (!compras || compras.length === 0) {
      tablaCompras.innerHTML = `
        <tr>
          <td colspan="16" class="text-center">No existen compras registradas.</td>
        </tr>
      `;
      return;
    }

    compras = compras.sort((a, b) => Number(b.id_compra) - Number(a.id_compra));

    tablaCompras.innerHTML = "";

    compras.forEach((compra, index) => {
      const datos = calcularDatosCompraParaTabla(compra);

      const fila = document.createElement("tr");

      fila.innerHTML = `
        <td>${index + 1}</td>
        <td>${compra.fecha_compra || "-"}</td>
        <td>${compra.proveedor || compra.nombre_proveedor || "-"}</td>
        <td>${compra.placa_vehiculo || "-"}</td>
        <td>${compra.chofer || "-"}</td>
        <td>${datos.unidad}</td>
        <td>${datos.quintalesBrutos.toFixed(2)} qq</td>
        <td>${datos.quintalesLiquidos.toFixed(2)} qq</td>
        <td>${datos.sacasLiquidas.toFixed(2)}</td>
        <td>${datos.tipoPago}</td>
        <td>$ ${datos.precioPactado.toFixed(2)}</td>
        <td>$ ${datos.totalBruto.toFixed(2)}</td>
        <td>$ ${datos.totalDescuento.toFixed(2)}</td>
        <td>$ ${datos.totalPagar.toFixed(2)}</td>
        <td>${compra.estado_pago || "-"}</td>
        <td>
          <button 
            type="button" 
            class="btn btn-sm btn-warning me-1"
            onclick="editarCompraPendiente(${compra.id_compra})">
            Editar
          </button>

          <button 
            type="button" 
            class="btn btn-sm btn-danger"
            onclick="eliminarCompra(${compra.id_compra})">
            Eliminar
          </button>
        </td>
      `;

      tablaCompras.appendChild(fila);
    });

  } catch (error) {
    tablaCompras.innerHTML = `
      <tr>
        <td colspan="16" class="text-center text-danger">
          Error al cargar compras: ${error.message}
        </td>
      </tr>
    `;
  }
}
async function editarCompraPendiente(idCompra) {
  try {
    const compra = await window.apiGet(`/api/compras/${idCompra}`);

    idCompraEditando = idCompra;

    document.getElementById("proveedorCompra").value =
      compra.proveedor || compra.nombre_proveedor || "";

    document.getElementById("identificacionProveedor").value =
      compra.identificacion_proveedor || compra.identificacion || "";

    document.getElementById("fechaCompra").value = compra.fecha_compra || "";
    document.getElementById("placaVehiculo").value = compra.placa_vehiculo || "";
    document.getElementById("choferCompra").value = compra.chofer || "";
    document.getElementById("productoCompra").value = "1";

    document.getElementById("unidadBascula").value = compra.unidad_bascula || "Libras";

    document.getElementById("pesoEntrada").value = compra.peso_bruto || "";
    document.getElementById("pesoSalida").value = compra.peso_tara || "";
    document.getElementById("pesoNeto").value = compra.peso_neto || "";

    document.getElementById("pesoNetoLibras").value = compra.peso_neto_libras || "";
    document.getElementById("quintalesBrutos").value = compra.quintales_brutos || "";
    document.getElementById("sacasBrutas").value = compra.sacas_brutas || "";

    document.getElementById("humedadCompra").value = compra.humedad ?? "";
    document.getElementById("humedadBase").value = compra.humedad_base ?? 14;
    document.getElementById("descuentoHumedad").value = compra.descuento_humedad_libras || "";

    document.getElementById("impurezasCompra").value = compra.impurezas ?? "";
    document.getElementById("impurezaBase").value = compra.impureza_base ?? 5;
    document.getElementById("descuentoImpureza").value = compra.descuento_impureza_libras || "";

    document.getElementById("pesoLiquidoLibras").value = compra.peso_liquido_libras || "";
    document.getElementById("quintalesLiquidos").value = compra.quintales_liquidos || "";
    document.getElementById("sacasLiquidas").value = compra.sacas_liquidas || "";

    document.getElementById("tipoPagoCompra").value = compra.tipo_pago || "Por saca";
    document.getElementById("precioPactado").value =
      compra.precio_pactado ?? compra.precio_quintal ?? "";

    document.getElementById("totalBruto").value = compra.total_bruto || "";
    document.getElementById("totalDescuento").value = compra.total_descuento || "";
    document.getElementById("totalCompra").value = compra.total_compra || "";

    document.getElementById("estadoPagoCompra").value = compra.estado_pago || "Pagado";
    document.getElementById("observacionCompra").value = compra.observacion || "";

    actualizarLabelsUnidad();
    actualizarLabelPrecio();
    calcularCompraFormulario();

    const botonRegistrar = document.querySelector("#formCompra button[type='submit']");

    if (botonRegistrar) {
      botonRegistrar.textContent = "Actualizar compra";
      botonRegistrar.classList.remove("btn-success");
      botonRegistrar.classList.add("btn-warning");
    }

    mostrarMensajeCompra(
      "warning",
      `Editando compra N° ${idCompra}. Realice los cambios y presione Actualizar compra.`
    );

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });

  } catch (error) {
    alert(`Error al cargar compra para editar: ${error.message}`);
  }
}

async function eliminarCompra(idCompra) {
  const confirmar = confirm(
    "¿Seguro que deseas eliminar definitivamente esta compra de la base de datos?"
  );

  if (!confirmar) return;

  try {
    await window.apiDelete(`/api/compras/${idCompra}`);

    alert("Compra eliminada definitivamente.");
    await cargarCompras();

  } catch (error) {
    alert(`Error al eliminar compra: ${error.message}`);
  }
}

async function desactivarCompra(idCompra) {
  await eliminarCompra(idCompra);
}

document.addEventListener("DOMContentLoaded", function () {
  const formCompra = document.getElementById("formCompra");

  if (!formCompra) return;

  const proveedorCompra = document.getElementById("proveedorCompra");
  const identificacionProveedor = document.getElementById("identificacionProveedor");
  const fechaCompra = document.getElementById("fechaCompra");
  const placaVehiculo = document.getElementById("placaVehiculo");
  const choferCompra = document.getElementById("choferCompra");
  const productoCompra = document.getElementById("productoCompra");

  const unidadBascula = document.getElementById("unidadBascula");
  const pesoEntrada = document.getElementById("pesoEntrada");
  const pesoSalida = document.getElementById("pesoSalida");
  const pesoNeto = document.getElementById("pesoNeto");

  const pesoNetoLibras = document.getElementById("pesoNetoLibras");
  const quintalesBrutos = document.getElementById("quintalesBrutos");
  const sacasBrutas = document.getElementById("sacasBrutas");

  const humedadCompra = document.getElementById("humedadCompra");
  const humedadBase = document.getElementById("humedadBase");
  const descuentoHumedad = document.getElementById("descuentoHumedad");

  const impurezasCompra = document.getElementById("impurezasCompra");
  const impurezaBase = document.getElementById("impurezaBase");
  const descuentoImpureza = document.getElementById("descuentoImpureza");

  const pesoLiquidoLibras = document.getElementById("pesoLiquidoLibras");
  const quintalesLiquidos = document.getElementById("quintalesLiquidos");
  const sacasLiquidas = document.getElementById("sacasLiquidas");

  const tipoPagoCompra = document.getElementById("tipoPagoCompra");
  const precioPactado = document.getElementById("precioPactado");
  const totalBruto = document.getElementById("totalBruto");
  const totalDescuento = document.getElementById("totalDescuento");
  const totalCompra = document.getElementById("totalCompra");

  const estadoPagoCompra = document.getElementById("estadoPagoCompra");
  const observacionCompra = document.getElementById("observacionCompra");

  // Validaciones en tiempo real de campos de texto
  const soloLetras = function () {
    this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g, "");
  };

  if (proveedorCompra) {
    proveedorCompra.addEventListener("input", soloLetras);
  }
  
  if (choferCompra) {
    choferCompra.addEventListener("input", soloLetras);
  }

  if (fechaCompra) {
    fechaCompra.max = fechaActualISOCompras();
  }

  if (identificacionProveedor) {
    identificacionProveedor.setAttribute("maxlength", "13");
    identificacionProveedor.addEventListener("input", function () {
      this.value = this.value.replace(/\D/g, "");
    });
  }

  if (placaVehiculo) {
      placaVehiculo.addEventListener("input", function() {
          this.value = this.value.toUpperCase();
      });
  }

  if (productoCompra) {
    productoCompra.value = "1";
  }

  actualizarLabelsUnidad();
  actualizarLabelPrecio();

  [
    unidadBascula,
    pesoEntrada,
    pesoSalida,
    humedadCompra,
    impurezasCompra,
    tipoPagoCompra,
    precioPactado
  ].forEach((campo) => {
    if (campo) {
      campo.addEventListener("input", function () {
        actualizarLabelsUnidad();
        actualizarLabelPrecio();
        calcularCompraFormulario();
      });

      campo.addEventListener("change", function () {
        actualizarLabelsUnidad();
        actualizarLabelPrecio();
        calcularCompraFormulario();
      });
    }
  });

  formCompra.addEventListener("reset", function () {
    limpiarModoEdicionCompra();

    setTimeout(() => {
      if (fechaCompra) {
        fechaCompra.max = fechaActualISOCompras();
      }

      if (productoCompra) {
        productoCompra.value = "1";
      }

      if (unidadBascula) {
        unidadBascula.value = "Libras";
      }

      if (humedadBase) {
        humedadBase.value = "14";
      }

      if (impurezaBase) {
        impurezaBase.value = "5";
      }

      if (tipoPagoCompra) {
        tipoPagoCompra.value = "Por saca";
      }

      limpiarMensajeCompra();
      actualizarLabelsUnidad();
      actualizarLabelPrecio();
    }, 50);
  });

  cargarCompras();

  formCompra.addEventListener("submit", async function (event) {
    event.preventDefault();

    if (!window.apiPost || !window.apiGet || !window.apiPut || !window.apiDelete) {
      mostrarMensajeCompra(
        "danger",
        "No se cargó api.js. Revise que compras.html tenga primero js/api.js, luego js/main.js y después js/compras.js."
      );
      return;
    }

    calcularCompraFormulario();

    const proveedorValor = proveedorCompra.value.trim().toUpperCase();
    const identificacionValor = identificacionProveedor.value.trim();
    const fechaValor = fechaCompra.value;
    const placaValor = placaVehiculo.value.trim().toUpperCase();
    const choferValor = choferCompra.value.trim().toUpperCase();

    const productoValor = productoCompra.value || "1";
    const unidadValor = unidadBascula.value;

    const entrada = numero(pesoEntrada.value);
    const salida = numero(pesoSalida.value);
    const neto = numero(pesoNeto.value);

    const pesoNetoLibrasValor = numero(pesoNetoLibras.value);
    const quintalesBrutosValor = numero(quintalesBrutos.value);
    const sacasBrutasValor = numero(sacasBrutas.value);

    const humedadValor = numero(humedadCompra.value);
    const humedadBaseValor = numero(humedadBase.value || 14);
    const descuentoHumedadValor = numero(descuentoHumedad.value);

    const impurezasValor = numero(impurezasCompra.value);
    const impurezaBaseValor = numero(impurezaBase.value || 5);
    const descuentoImpurezaValor = numero(descuentoImpureza.value);

    const pesoLiquidoLibrasValor = numero(pesoLiquidoLibras.value);
    const quintalesLiquidosValor = numero(quintalesLiquidos.value);
    const sacasLiquidasValor = numero(sacasLiquidas.value);

    const tipoPagoValor = tipoPagoCompra.value;
    const precioValor = numero(precioPactado.value);
    const totalBrutoValor = numero(totalBruto.value);
    const totalDescuentoValor = numero(totalDescuento.value);
    const totalValor = numero(totalCompra.value);

    const estadoPagoValor = estadoPagoCompra.value;
    const observacionValor = observacionCompra.value.trim();

    // LÓGICA DE VALIDACIÓN ESTRICTA
    if (!proveedorValor || !identificacionValor || !fechaValor || !productoValor) {
      mostrarMensajeCompra(
        "danger",
        "Debe completar proveedor, identificación, fecha y producto."
      );
      return;
    }

    if (!/^\d{10}$|^\d{13}$/.test(identificacionValor)) {
      mostrarMensajeCompra(
        "danger",
        "La identificación debe tener 10 dígitos si es cédula o 13 dígitos si es RUC."
      );
      return;
    }

    if (placaValor && !/^[A-Z]{3}-\d{3,4}$/.test(placaValor)) {
      mostrarMensajeCompra(
        "danger",
        "La placa ingresada no tiene un formato válido (Ej: ABC-123 o ABC-1234)."
      );
      return;
    }

    if (typeof validarIdentificacionEcuador === "function") {
      if (!validarIdentificacionEcuador(identificacionValor)) {
        mostrarMensajeCompra(
          "danger",
          "La identificación ingresada no es válida. Ingrese una cédula ecuatoriana válida o un RUC."
        );
        return;
      }
    }

    if (fechaValor > fechaActualISOCompras()) {
      mostrarMensajeCompra(
        "danger",
        "No se permite registrar compras con fecha futura."
      );
      return;
    }

    if (!["Libras", "Kilogramos", "Toneladas"].includes(unidadValor)) {
      mostrarMensajeCompra(
        "danger",
        "Debe seleccionar una unidad de báscula válida."
      );
      return;
    }

    if (entrada <= 0) {
      mostrarMensajeCompra("danger", "El peso de entrada debe ser mayor a cero.");
      return;
    }

    if (salida < 0) {
      mostrarMensajeCompra("danger", "El peso de salida no puede ser negativo.");
      return;
    }

    if (salida >= entrada) {
      mostrarMensajeCompra(
        "danger",
        "El peso de salida no puede ser mayor o igual al peso de entrada."
      );
      return;
    }

    if (neto <= 0 || pesoNetoLibrasValor <= 0) {
      mostrarMensajeCompra(
        "danger",
        "El peso neto resultante debe ser mayor a cero."
      );
      return;
    }

    if (humedadValor < 0 || humedadValor > 100 || humedadBaseValor < 0 || humedadBaseValor > 100) {
      mostrarMensajeCompra(
        "danger",
        "Los porcentajes de humedad deben estar entre 0 y 100%."
      );
      return;
    }

    if (impurezasValor < 0 || impurezasValor > 100 || impurezaBaseValor < 0 || impurezaBaseValor > 100) {
      mostrarMensajeCompra(
        "danger",
        "Los porcentajes de impurezas deben estar entre 0 y 100%."
      );
      return;
    }

    if (!["Por saca", "Por quintal"].includes(tipoPagoValor)) {
      mostrarMensajeCompra(
        "danger",
        "Debe seleccionar si el pago será por saca o por quintal."
      );
      return;
    }

    if (precioValor <= 0) {
      mostrarMensajeCompra(
        "danger",
        "El precio pactado debe ser mayor a cero."
      );
      return;
    }

    if (pesoLiquidoLibrasValor <= 0 || quintalesLiquidosValor <= 0 || sacasLiquidasValor <= 0) {
      mostrarMensajeCompra(
        "danger",
        "El peso líquido debe ser mayor a cero después de aplicar los descuentos."
      );
      return;
    }

    if (totalValor < 0) {
      mostrarMensajeCompra(
        "danger",
        "El total a pagar no puede ser negativo."
      );
      return;
    }

    if (!["Pagado", "Pendiente", "Parcial"].includes(estadoPagoValor)) {
      mostrarMensajeCompra(
        "danger",
        "Debe seleccionar un estado de pago válido."
      );
      return;
    }

    const datosCompra = {
      nombre_proveedor: proveedorValor,
      identificacion: identificacionValor,
      id_usuario: Number(localStorage.getItem("idUsuarioERP") || 1),
      fecha_compra: fechaValor,
      placa_vehiculo: placaValor,
      chofer: choferValor,

      peso_bruto: entrada,
      peso_tara: salida,
      peso_neto: neto,

      humedad: humedadValor,
      impurezas: impurezasValor,

      precio_quintal: precioValor,
      estado_pago: estadoPagoValor,
      observacion: observacionValor || `Compra de arroz en cáscara a ${proveedorValor}`,

      id_producto: Number(productoValor),
      id_bodega: 2,

      unidad_bascula: unidadValor,
      peso_neto_libras: pesoNetoLibrasValor,
      quintales_brutos: quintalesBrutosValor,
      sacas_brutas: sacasBrutasValor,

      humedad_base: humedadBaseValor,
      impureza_base: impurezaBaseValor,
      descuento_humedad_libras: convertirPesoALibras(descuentoHumedadValor, unidadValor),
      descuento_impureza_libras: convertirPesoALibras(descuentoImpurezaValor, unidadValor),

      peso_liquido_libras: pesoLiquidoLibrasValor,
      quintales_liquidos: quintalesLiquidosValor,
      sacas_liquidas: sacasLiquidasValor,

      tipo_pago: tipoPagoValor,
      precio_pactado: precioValor,
      total_bruto: totalBrutoValor,
      total_descuento: totalDescuentoValor
    };
    
    console.log("DATOS QUE SE ENVIAN A COMPRAS:", datosCompra);
    
    try {
      if (idCompraEditando) {
        await window.apiPut(`/api/compras/${idCompraEditando}`, datosCompra);

        mostrarMensajeCompra(
          "success",
          "Compra actualizada correctamente en PostgreSQL."
        );
      } else {
        await window.apiPost("/api/compras/registrar-completa", datosCompra);

        mostrarMensajeCompra(
          "success",
          "Compra registrada correctamente en PostgreSQL."
        );
      }

      formCompra.reset();

      [
        pesoNeto,
        pesoNetoLibras,
        quintalesBrutos,
        sacasBrutas,
        descuentoHumedad,
        descuentoImpureza,
        pesoLiquidoLibras,
        quintalesLiquidos,
        sacasLiquidas,
        totalBruto,
        totalDescuento,
        totalCompra
      ].forEach((campo) => {
        if (campo) campo.value = "";
      });

      limpiarModoEdicionCompra();

      await cargarCompras();

    } catch (error) {
      mostrarMensajeCompra(
        "danger",
        `Error al guardar compra: ${error.message}`
      );
    }
  });
});