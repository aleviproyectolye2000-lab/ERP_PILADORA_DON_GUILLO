/* ============================================================
   MÓDULO DE VENTAS Y COMERCIALIZACIÓN
   ERP PILADORA DON GUILLO
   Frontend conectado con FastAPI + PostgreSQL
   ============================================================ */

document.addEventListener("DOMContentLoaded", async function () {
  const formVenta = document.getElementById("formVenta");

  if (!formVenta) {
    return;
  }

  function $(...ids) {
    for (const id of ids) {
      const elemento = document.getElementById(id);
      if (elemento) return elemento;
    }
    return null;
  }

  const clienteVenta = $("clienteVenta");
  const identificacionCliente = $("identificacionCliente");
  const fechaVenta = $("fechaVenta");
  const tipoComprobante = $("tipoComprobante");

  const productoVenta = $("productoVenta");
  const unidadVenta = $("unidadVenta", "unidadMedidaVenta");
  const cantidadVenta = $("cantidadVenta");
  const cantidadEquivalente = $("cantidadEquivalente", "cantidadEquivalenteVenta", "cantidadQuintalesVenta");
  const precioVenta = $("precioVenta", "precioUnitario", "precioUnitarioVenta", "precioVentaUnitario");

  const bodegaVenta = $("bodegaVenta", "nombreBodegaVenta");
  const loteVenta = $("loteVenta", "loteProductoVenta");
  const stockDisponibleVenta = $("stockDisponibleVenta", "stockVenta", "stockDisponible");

  const descuentoVenta = $("descuentoVenta", "descuento");
  const subtotalVenta = $("subtotalVenta", "subtotal");
  const ivaVenta = $("ivaVenta", "iva");
  const totalVenta = $("totalVenta", "totalPagarVenta", "totalPagar");

  const estadoPagoVenta = $("estadoPagoVenta", "estadoPago");
  const formaPagoVenta = $("formaPagoVenta", "formaPago");
  const valorRecibidoVenta = $("valorRecibidoVenta", "valorRecibido");
  const saldoPendienteVenta = $("saldoPendienteVenta", "saldoPendiente");

  const observacionVenta = $("observacionVenta");
  const tablaVentas = $("tablaVentas");
  const mensajeVenta = $("mensajeVenta");

  // CORRECCIÓN DE IDs PARA EL DASHBOARD
  const totalVentasRegistradas = $("totalVentas", "totalVentasRegistradas");
  const ingresosTotales = $("ingresosCobrados", "ingresosTotales");
  const cuentasPorCobrar = $("cuentasPorCobrar");
  const productoMasVendido = $("productoMasVendido");
  const ventasPendientes = $("clientesPorCobrar", "ventasPendientes");

  const botonSubmit = formVenta.querySelector('button[type="submit"]');

  let productosDisponibles = [];
  let ventasRegistradas = [];
  let ventaEditandoId = null;

  if (fechaVenta) {
    fechaVenta.max = obtenerFechaActualISO();
  }

  // Filtros de escritura en tiempo real
  if (clienteVenta) {
    clienteVenta.addEventListener("input", function () {
      this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]/g, "");
    });
  }

  if (identificacionCliente) {
    identificacionCliente.setAttribute("maxlength", "13");
    identificacionCliente.addEventListener("input", function () {
      this.value = this.value.replace(/\D/g, "");
    });
  }

  configurarComprobanteFactura();
  configurarUnidadesVenta();
  configurarFormaPagoInicial();

  agregarEventos();
  await cargarProductosDisponibles();
  await cargarVentas();
  await generarNumeroComprobante();

  function obtenerFechaActualISO() {
    const hoy = new Date();
    const anio = hoy.getFullYear();
    const mes = String(hoy.getMonth() + 1).padStart(2, "0");
    const dia = String(hoy.getDate()).padStart(2, "0");
    return `${anio}-${mes}-${dia}`;
  }

  function convertirNumero(valor) {
    if (valor === null || valor === undefined || valor === "") return 0;
    if (typeof valor === "number") return valor;
    return Number(String(valor).replace(",", ".")) || 0;
  }

  function formatearNumero(valor) {
    return convertirNumero(valor).toFixed(2).replace(".", ",");
  }

  function formatearDinero(valor) {
    return "$ " + convertirNumero(valor).toFixed(2);
  }

  function mostrarMensaje(tipo, texto) {
    if (!mensajeVenta) {
      alert(texto);
      return;
    }
    mensajeVenta.className = `alert mt-3 alert-${tipo}`;
    mensajeVenta.textContent = texto;
    mensajeVenta.classList.remove("d-none");
  }

  function ocultarMensaje() {
    if (!mensajeVenta) return;
    mensajeVenta.className = "alert d-none mt-3";
    mensajeVenta.textContent = "";
  }

  function limpiarCampo(campo) {
    if (campo) campo.value = "";
  }

  /* ---------------------------------------------------- */
  /* VALIDACIÓN ESTRICTA DE CÉDULA Y RUC ECUADOR          */
  /* ---------------------------------------------------- */
  function validarCedulaEcuador(cedula) {
    if (!/^\d{10}$/.test(cedula)) return false;
    
    const provincia = parseInt(cedula.substring(0, 2), 10);
    if (provincia < 1 || provincia > 24) return false;

    const tercerDigito = parseInt(cedula[2], 10);
    if (tercerDigito >= 6) return false;

    const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
    let suma = 0;

    for (let i = 0; i < 9; i++) {
      let valor = parseInt(cedula[i], 10) * coeficientes[i];
      if (valor >= 10) valor -= 9;
      suma += valor;
    }

    const digitoVerificador = parseInt(cedula[9], 10);
    const decenaSuperior = Math.ceil(suma / 10) * 10;
    let digitoCalculado = decenaSuperior - suma;

    if (digitoCalculado === 10) digitoCalculado = 0;

    return digitoCalculado === digitoVerificador;
  }

  function validarRucPersonaNatural(ruc) {
    if (!/^\d{13}$/.test(ruc)) return false;
    const cedula = ruc.substring(0, 10);
    const establecimiento = ruc.substring(10, 13);
    return validarCedulaEcuador(cedula) && establecimiento === "001";
  }

  function validarIdentificacionEcuador(valor) {
    const identificacion = String(valor || "").trim();
    if (/^\d{10}$/.test(identificacion)) {
      return validarCedulaEcuador(identificacion);
    }
    if (/^\d{13}$/.test(identificacion)) {
      return validarRucPersonaNatural(identificacion);
    }
    return false;
  }
  /* ---------------------------------------------------- */

  function obtenerMensajeError(error) {
    if (!error) return "Error desconocido.";
    if (typeof error === "string") return error;
    if (error.message) return error.message;
    return JSON.stringify(error);
  }

  function configurarComprobanteFactura() {
    if (!tipoComprobante) return;
    tipoComprobante.innerHTML = `<option value="Factura">Factura</option>`;
    tipoComprobante.value = "Factura";
    tipoComprobante.disabled = true;
  }

  function obtenerCampoNumeroComprobante() {
    let campo = document.getElementById("numeroComprobanteVenta");
    if (campo) return campo;

    const contenedor = document.createElement("div");
    contenedor.className = "col-md-3";
    contenedor.innerHTML = `
      <label class="form-label">N.º factura</label>
      <input type="text" class="form-control" id="numeroComprobanteVenta" readonly />
    `;

    const referencia = tipoComprobante ? tipoComprobante.closest(".col-md-3, .col-lg-3, .col") : null;
    if (referencia) {
      referencia.before(contenedor);
    } else {
      formVenta.prepend(contenedor);
    }
    return document.getElementById("numeroComprobanteVenta");
  }

  async function generarNumeroComprobante() {
    const campo = obtenerCampoNumeroComprobante();
    try {
      const respuesta = await window.apiGet("/api/ventas/siguiente-comprobante");
      campo.value = respuesta.numero_comprobante || respuesta.numero || respuesta.comprobante || generarFacturaLocal();
    } catch (error) {
      campo.value = generarFacturaLocal();
    }
  }

  function generarFacturaLocal() {
    const fecha = obtenerFechaActualISO().replaceAll("-", "");
    const aleatorio = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `FAC-${fecha}-${aleatorio}`;
  }

  function configurarUnidadesVenta() {
    if (!unidadVenta) return;
    unidadVenta.innerHTML = `
      <option value="">Seleccione</option>
      <option value="Quintal">Quintal - 100 lb</option>
      <option value="Medio quintal">Medio quintal - 50 lb</option>
      <option value="Arroba">Arroba - 25 lb</option>
      <option value="Libra">Libra</option>
    `;
  }

  function convertirCantidadAQuintales(cantidad, unidad) {
    const cantidadNumero = convertirNumero(cantidad);
    const unidadTexto = String(unidad || "").toLowerCase();

    if (unidadTexto.includes("quintal") && !unidadTexto.includes("medio")) return cantidadNumero;
    if (unidadTexto.includes("medio")) return cantidadNumero * 0.5;
    if (unidadTexto.includes("arroba")) return cantidadNumero * 0.25;
    if (unidadTexto.includes("libra")) return cantidadNumero / 100;
    return 0;
  }

  async function cargarProductosDisponibles() {
    try {
      productosDisponibles = await window.apiGet("/api/ventas/productos-disponibles");
      if (!Array.isArray(productosDisponibles)) productosDisponibles = [];
      renderizarSelectProductos();
    } catch (error) {
      productosDisponibles = [];
      if (productoVenta) productoVenta.innerHTML = `<option value="">Error al cargar productos</option>`;
      mostrarMensaje("danger", "Error al cargar productos disponibles: " + obtenerMensajeError(error));
    }
  }

  function renderizarSelectProductos() {
    if (!productoVenta) return;
    productoVenta.innerHTML = `<option value="">Seleccione un producto disponible</option>`;

    productosDisponibles.forEach((producto) => {
      const idInventario = producto.id_inventario;
      const nombreProducto = producto.nombre_producto || producto.producto || producto.nombre || "Producto sin nombre";
      const lote = producto.lote || "-";
      const disponible = convertirNumero(producto.cantidad_disponible);
      const precio = convertirNumero(producto.precio_referencial || producto.precio_unitario || producto.precio || 0);

      const option = document.createElement("option");
      option.value = idInventario;
      option.textContent = `${nombreProducto} | ${lote} | ${disponible.toFixed(2)} qq disponibles`;

      option.dataset.idInventario = idInventario;
      option.dataset.idProducto = producto.id_producto || "";
      option.dataset.idBodega = producto.id_bodega || "";
      option.dataset.producto = nombreProducto;
      option.dataset.bodega = producto.nombre_bodega || producto.bodega || "";
      option.dataset.lote = lote;
      option.dataset.stock = disponible;
      option.dataset.precio = precio;

      productoVenta.appendChild(option);
    });
  }

  function obtenerProductoSeleccionado() {
    if (!productoVenta || !productoVenta.value) return null;
    return productosDisponibles.find((producto) => String(producto.id_inventario) === String(productoVenta.value)) || null;
  }

  function limpiarDatosProducto() {
    limpiarCampo(bodegaVenta);
    limpiarCampo(loteVenta);
    limpiarCampo(stockDisponibleVenta);
    limpiarCampo(precioVenta);
    limpiarCampo(cantidadVenta);
    limpiarCampo(cantidadEquivalente);
    limpiarCampo(subtotalVenta);
    limpiarCampo(totalVenta);
    limpiarCampo(valorRecibidoVenta);
    limpiarCampo(saldoPendienteVenta);
    if (descuentoVenta) descuentoVenta.value = "0";
  }

  function cargarDatosProductoSeleccionado() {
    const producto = obtenerProductoSeleccionado();
    if (!producto) {
      limpiarDatosProducto();
      return;
    }

    const bodega = producto.nombre_bodega || producto.bodega || "";
    const lote = producto.lote || "";
    const stock = convertirNumero(producto.cantidad_disponible);
    const precio = convertirNumero(producto.precio_referencial || producto.precio_unitario || producto.precio || 0);

    if (bodegaVenta) bodegaVenta.value = bodega;
    if (loteVenta) loteVenta.value = lote;
    if (stockDisponibleVenta) stockDisponibleVenta.value = stock.toFixed(2);
    if (precioVenta && precio > 0) precioVenta.value = precio.toFixed(2);

    calcularVenta();
  }

  function calcularVenta() {
    if (!cantidadVenta || !unidadVenta || !precioVenta || !descuentoVenta || !ivaVenta || !subtotalVenta || !totalVenta) return;

    const cantidad = convertirNumero(cantidadVenta.value);
    const unidad = unidadVenta.value;
    const precioUnitario = convertirNumero(precioVenta.value);
    const descuento = convertirNumero(descuentoVenta.value);
    const ivaPorcentaje = convertirNumero(ivaVenta.value);

    if (cantidad < 0 || precioUnitario < 0 || descuento < 0) {
      if (cantidadEquivalente) cantidadEquivalente.value = "0.00";
      subtotalVenta.value = "0.00";
      totalVenta.value = "0.00";
      if (valorRecibidoVenta) valorRecibidoVenta.value = "0.00";
      if (saldoPendienteVenta) saldoPendienteVenta.value = "0.00";
      return;
    }

    const cantidadEquivalenteQQ = convertirCantidadAQuintales(cantidad, unidad);
    if (cantidadEquivalente) cantidadEquivalente.value = cantidadEquivalenteQQ.toFixed(2);

    const subtotalBruto = cantidad * precioUnitario;

    if (descuento > subtotalBruto) {
      subtotalVenta.value = "0.00";
      totalVenta.value = "0.00";
      aplicarReglasPago();
      return;
    }

    const subtotal = subtotalBruto - descuento;
    const ivaCalculado = subtotal * (ivaPorcentaje / 100);
    const total = subtotal + ivaCalculado;

    subtotalVenta.value = subtotal.toFixed(2);
    totalVenta.value = total.toFixed(2);

    aplicarReglasPago();
  }

  function configurarFormaPagoInicial() {
    if (!formaPagoVenta) return;
    formaPagoVenta.innerHTML = `
      <option value="">Seleccione</option>
      <option value="Efectivo">Efectivo</option>
      <option value="Transferencia">Transferencia</option>
      <option value="Crédito">Crédito</option>
    `;
  }

  function aplicarReglasPago() {
    if (!estadoPagoVenta || !formaPagoVenta || !valorRecibidoVenta || !saldoPendienteVenta || !totalVenta) return;

    const estadoPago = estadoPagoVenta.value;
    const total = convertirNumero(totalVenta.value);

    formaPagoVenta.disabled = false;
    valorRecibidoVenta.readOnly = false;
    saldoPendienteVenta.readOnly = true;

    Array.from(formaPagoVenta.options).forEach(opcion => opcion.disabled = false);

    if (estadoPago === "Pagado") {
      valorRecibidoVenta.value = total.toFixed(2);
      saldoPendienteVenta.value = "0.00";
      Array.from(formaPagoVenta.options).forEach(opcion => {
        if (opcion.value === "Crédito") opcion.disabled = true;
      });
      if (formaPagoVenta.value === "" || formaPagoVenta.value === "Crédito") formaPagoVenta.value = "Efectivo";
      valorRecibidoVenta.readOnly = true;
      return;
    }

    if (estadoPago === "Pendiente") {
      valorRecibidoVenta.value = "0.00";
      saldoPendienteVenta.value = total.toFixed(2);
      Array.from(formaPagoVenta.options).forEach(opcion => {
        opcion.disabled = opcion.value !== "Crédito";
      });
      formaPagoVenta.value = "Crédito";
      valorRecibidoVenta.readOnly = true;
      return;
    }

    if (estadoPago === "Parcial") {
      let recibido = convertirNumero(valorRecibidoVenta.value);
      if (recibido < 0) { recibido = 0; valorRecibidoVenta.value = "0.00"; }
      if (recibido >= total && total > 0) { recibido = 0; valorRecibidoVenta.value = "0.00"; }
      saldoPendienteVenta.value = (total - recibido).toFixed(2);
      valorRecibidoVenta.readOnly = false;
      return;
    }

    valorRecibidoVenta.value = "0.00";
    saldoPendienteVenta.value = "0.00";
  }

  function validarPagoAntesDeGuardar() {
    const estado = estadoPagoVenta ? estadoPagoVenta.value : "";
    const total = convertirNumero(totalVenta ? totalVenta.value : 0);
    const recibido = convertirNumero(valorRecibidoVenta ? valorRecibidoVenta.value : 0);

    if (estado === "Pagado") {
      if (recibido < total) {
        mostrarMensaje("danger", "Si la venta está pagada, el valor recibido debe cubrir todo el total.");
        return false;
      }
      if (formaPagoVenta && formaPagoVenta.value === "Crédito") {
        mostrarMensaje("danger", "Una venta pagada no puede tener forma de pago Crédito.");
        return false;
      }
    }

    if (estado === "Pendiente") {
      if (recibido !== 0) {
        mostrarMensaje("danger", "Si la venta está pendiente, el valor recibido debe ser 0.");
        return false;
      }
      if (formaPagoVenta && formaPagoVenta.value !== "Crédito") {
        mostrarMensaje("danger", "Si la venta está pendiente, la forma de pago debe ser Crédito.");
        return false;
      }
    }

    if (estado === "Parcial") {
      if (recibido <= 0 || recibido >= total) {
        mostrarMensaje("danger", "Si la venta es parcial, el abono debe ser mayor a 0 y menor que el total.");
        return false;
      }
    }

    return true;
  }

  async function cargarVentas() {
    if (!tablaVentas) return;
    try {
      tablaVentas.innerHTML = `<tr><td colspan="19" class="text-center text-muted">Cargando ventas...</td></tr>`;
      ventasRegistradas = await window.apiGet("/api/ventas/");
      if (!Array.isArray(ventasRegistradas)) ventasRegistradas = [];
      
      renderizarTablaVentas();
      actualizarTarjetasVentas();
    } catch (error) {
      ventasRegistradas = [];
      tablaVentas.innerHTML = `<tr><td colspan="19" class="text-center text-danger">Error al cargar ventas: ${obtenerMensajeError(error)}</td></tr>`;
    }
  }

  function renderizarTablaVentas() {
    if (!tablaVentas) return;
    if (!ventasRegistradas || ventasRegistradas.length === 0) {
      tablaVentas.innerHTML = `<tr><td colspan="19" class="text-center text-muted">No existen ventas registradas.</td></tr>`;
      return;
    }

    tablaVentas.innerHTML = "";

    ventasRegistradas.forEach((venta, index) => {
      const anulada = venta.estado === false || venta.estado_pago === "Anulado";
      const fila = document.createElement("tr");
      if (anulada) fila.classList.add("table-danger");

      const idVenta = venta.id_venta;
      const numeroFactura = venta.numero_comprobante || venta.numero_factura || "-";
      const cliente = venta.cliente || venta.nombre_cliente || "-";
      const producto = venta.nombre_producto || venta.producto || "-";
      const bodega = venta.nombre_bodega || venta.bodega || "-";
      const lote = venta.lote || "-";
      const unidad = venta.unidad_medida || venta.unidad || "-";
      const cantidad = convertirNumero(venta.cantidad_unidad || venta.cantidad || 0);
      const precio = convertirNumero(venta.precio_unitario || 0);
      const subtotal = convertirNumero(venta.subtotal || venta.subtotal_venta || 0);
      const descuento = convertirNumero(venta.descuento || 0);
      const iva = convertirNumero(venta.iva_porcentaje || 0);
      const total = convertirNumero(venta.total_linea || venta.total_venta || 0);
      const recibido = convertirNumero(venta.valor_recibido || 0);
      const saldo = convertirNumero(venta.saldo_pendiente || 0);
      const estadoPago = anulada ? "Anulado" : venta.estado_pago || "-";
      const formaPago = venta.forma_pago || "-";

      fila.innerHTML = `
        <td>${index + 1}</td>
        <td>${venta.fecha_venta || "-"}</td>
        <td>${numeroFactura}</td>
        <td>${cliente}</td>
        <td>${producto}</td>
        <td>${bodega}</td>
        <td>${lote}</td>
        <td>${unidad}</td>
        <td>${cantidad.toFixed(2)}</td>
        <td>${formatearDinero(precio)}</td>
        <td>${formatearDinero(subtotal)}</td>
        <td>${formatearDinero(descuento)}</td>
        <td>${iva.toFixed(2)}%</td>
        <td>${formatearDinero(total)}</td>
        <td>${formatearDinero(recibido)}</td>
        <td>${formatearDinero(saldo)}</td>
        <td><span class="badge ${anulada ? "bg-danger" : estadoPago === "Pagado" ? "bg-success" : estadoPago === "Parcial" ? "bg-warning text-dark" : "bg-secondary"}">${estadoPago}</span></td>
        <td>${formaPago}</td>
        <td>
          ${anulada ? `<span class="text-danger fw-bold d-block mb-1">Venta anulada</span>` : `
            <button class="btn btn-warning btn-sm mb-1" onclick="editarVenta(${idVenta})">Editar</button>
            <button class="btn btn-danger btn-sm mb-1" onclick="anularVenta(${idVenta})">Anular</button>
          `}
          <button class="btn btn-primary btn-sm mb-1" onclick="imprimirFacturaVenta(${idVenta})">Imprimir</button>
        </td>
      `;
      tablaVentas.appendChild(fila);
    });
  }

  function actualizarTarjetasVentas() {
    const ventasActivas = ventasRegistradas.filter(venta => venta.estado !== false && venta.estado_pago !== "Anulado");
    const totalComprobantes = ventasActivas.length;
    const ingresosCobrados = ventasActivas.reduce((acumulado, venta) => acumulado + convertirNumero(venta.valor_recibido || 0), 0);
    const totalPorCobrar = ventasActivas.reduce((acumulado, venta) => acumulado + convertirNumero(venta.saldo_pendiente || 0), 0);
    const clientesPendientes = ventasActivas.filter(venta => venta.estado_pago === "Pendiente" || venta.estado_pago === "Parcial").length;

    // Actualización de las tarjetas corrigiendo los IDs
    if (totalVentasRegistradas) totalVentasRegistradas.textContent = totalComprobantes;
    if (ingresosTotales) ingresosTotales.textContent = formatearDinero(ingresosCobrados);
    if (cuentasPorCobrar) cuentasPorCobrar.textContent = formatearDinero(totalPorCobrar);
    if (ventasPendientes) ventasPendientes.textContent = `${clientesPendientes} clientes pendientes`;
    if (productoMasVendido) productoMasVendido.textContent = obtenerProductoMasVendido(ventasActivas);
  }

  function obtenerProductoMasVendido(ventas) {
    if (!ventas || ventas.length === 0) return "---";
    const acumulado = {};
    ventas.forEach((venta) => {
      const producto = venta.nombre_producto || venta.producto || "Sin producto";
      const cantidad = convertirNumero(venta.cantidad_quintales || venta.cantidad || 0);
      if (!acumulado[producto]) acumulado[producto] = 0;
      acumulado[producto] += cantidad;
    });

    let productoMayor = "---";
    let cantidadMayor = 0;
    Object.keys(acumulado).forEach((producto) => {
      if (acumulado[producto] > cantidadMayor) {
        cantidadMayor = acumulado[producto];
        productoMayor = producto;
      }
    });
    return productoMayor;
  }

  function obtenerPayloadVenta() {
    const producto = obtenerProductoSeleccionado();
    const numeroComprobante = obtenerCampoNumeroComprobante().value;
    const unidad = unidadVenta ? unidadVenta.value : "";
    const cantidadUnidad = convertirNumero(cantidadVenta.value);
    const cantidadQuintales = convertirCantidadAQuintales(cantidadUnidad, unidad);

    return {
      numero_comprobante: numeroComprobante,
      cliente: clienteVenta ? clienteVenta.value.trim() : "",
      identificacion: identificacionCliente ? identificacionCliente.value.trim() : "",
      id_usuario: Number(localStorage.getItem("id_usuario")) || 1,
      fecha_venta: fechaVenta ? fechaVenta.value : "",
      tipo_comprobante: "Factura",
      id_inventario: Number(productoVenta ? productoVenta.value : 0),
      id_producto: producto ? Number(producto.id_producto) : null,
      id_bodega: producto ? Number(producto.id_bodega) : null,
      lote: producto ? producto.lote : "",
      unidad_medida: unidad,
      cantidad: cantidadUnidad,
      cantidad_unidad: cantidadUnidad,
      cantidad_quintales: cantidadQuintales,
      precio_unitario: convertirNumero(precioVenta ? precioVenta.value : 0),
      descuento: convertirNumero(descuentoVenta ? descuentoVenta.value : 0),
      iva_porcentaje: convertirNumero(ivaVenta ? ivaVenta.value : 0),
      subtotal: convertirNumero(subtotalVenta ? subtotalVenta.value : 0),
      total_venta: convertirNumero(totalVenta ? totalVenta.value : 0),
      total_linea: convertirNumero(totalVenta ? totalVenta.value : 0),
      estado_pago: estadoPagoVenta ? estadoPagoVenta.value : "",
      forma_pago: formaPagoVenta ? formaPagoVenta.value : "",
      valor_recibido: convertirNumero(valorRecibidoVenta ? valorRecibidoVenta.value : 0),
      saldo_pendiente: convertirNumero(saldoPendienteVenta ? saldoPendienteVenta.value : 0),
      observacion: observacionVenta ? observacionVenta.value.trim() : null
    };
  }

  function validarFormularioVenta() {
    ocultarMensaje();
    const producto = obtenerProductoSeleccionado();
    const fechaActual = obtenerFechaActualISO();

    if (!clienteVenta || !clienteVenta.value.trim()) {
      mostrarMensaje("danger", "Ingrese el nombre del cliente.");
      return false;
    }

    if (!identificacionCliente || !identificacionCliente.value.trim()) {
      mostrarMensaje("danger", "Ingrese la cédula o RUC del cliente.");
      return false;
    }

    if (!validarIdentificacionEcuador(identificacionCliente.value)) {
      mostrarMensaje("danger", "La identificación del cliente no es válida. Use cédula de 10 dígitos o RUC de 13 dígitos terminado en 001, registrados en Ecuador.");
      return false;
    }

    if (!fechaVenta || !fechaVenta.value) {
      mostrarMensaje("danger", "Seleccione la fecha de venta.");
      return false;
    }

    if (fechaVenta.value > fechaActual) {
      mostrarMensaje("danger", "No se permite registrar ventas con fecha futura.");
      return false;
    }

    if (!producto || !productoVenta || !productoVenta.value) {
      mostrarMensaje("danger", "Seleccione un producto válido desde inventario.");
      return false;
    }

    if (!producto.id_inventario) {
      mostrarMensaje("danger", "El producto seleccionado no tiene id_inventario válido.");
      return false;
    }

    if (!unidadVenta || !unidadVenta.value) {
      mostrarMensaje("danger", "Seleccione la unidad de venta.");
      return false;
    }

    const cantidadUnidad = convertirNumero(cantidadVenta ? cantidadVenta.value : 0);
    const cantidadQuintales = convertirCantidadAQuintales(cantidadUnidad, unidadVenta.value);
    const stock = convertirNumero(producto.cantidad_disponible);

    if (cantidadUnidad <= 0 || cantidadQuintales <= 0) {
      mostrarMensaje("danger", "La cantidad vendida debe ser mayor a cero.");
      return false;
    }

    // Validación estricta contra el stock de inventario
    if (cantidadQuintales > stock) {
      mostrarMensaje("danger", `Stock insuficiente. Disponible: ${stock.toFixed(2)} qq. Solicitado: ${cantidadQuintales.toFixed(2)} qq.`);
      return false;
    }

    if (convertirNumero(precioVenta ? precioVenta.value : 0) <= 0) {
      mostrarMensaje("danger", "El precio unitario debe ser mayor a cero.");
      return false;
    }

    if (convertirNumero(descuentoVenta ? descuentoVenta.value : 0) < 0) {
      mostrarMensaje("danger", "El descuento no puede ser negativo.");
      return false;
    }

    if (!estadoPagoVenta || !estadoPagoVenta.value) {
      mostrarMensaje("danger", "Seleccione el estado de pago.");
      return false;
    }

    if (!formaPagoVenta || !formaPagoVenta.value) {
      mostrarMensaje("danger", "Seleccione la forma de pago.");
      return false;
    }

    return validarPagoAntesDeGuardar();
  }

  formVenta.addEventListener("submit", async function (event) {
    event.preventDefault();
    calcularVenta();
    if (!validarFormularioVenta()) return;

    const payload = obtenerPayloadVenta();
    try {
      if (ventaEditandoId) {
        await window.apiPut(`/api/ventas/${ventaEditandoId}`, payload);
        mostrarMensaje("success", "Venta actualizada correctamente. El inventario fue recalculado.");
      } else {
        await window.apiPost("/api/ventas/registrar-completa", payload);
        mostrarMensaje("success", "Venta registrada correctamente. El inventario fue descontado.");
      }
      await limpiarFormularioVentaCompleto();
      await cargarProductosDisponibles();
      await cargarVentas();
    } catch (error) {
      mostrarMensaje("danger", "Error al guardar venta: " + obtenerMensajeError(error));
    }
  });

  async function limpiarFormularioVentaCompleto() {
    formVenta.reset();
    ventaEditandoId = null;

    if (botonSubmit) {
      botonSubmit.textContent = "Registrar venta";
      botonSubmit.classList.remove("btn-warning");
      botonSubmit.classList.add("btn-success");
    }

    configurarComprobanteFactura();
    configurarUnidadesVenta();
    configurarFormaPagoInicial();
    limpiarDatosProducto();

    if (descuentoVenta) descuentoVenta.value = "0";
    if (valorRecibidoVenta) {
      valorRecibidoVenta.value = "0";
      valorRecibidoVenta.readOnly = false;
    }
    if (saldoPendienteVenta) {
      saldoPendienteVenta.value = "";
      saldoPendienteVenta.readOnly = true;
    }
    if (fechaVenta) fechaVenta.max = obtenerFechaActualISO();
    if (formaPagoVenta) formaPagoVenta.disabled = false;

    await generarNumeroComprobante();
  }

  window.editarVenta = async function (idVenta) {
    ocultarMensaje();
    try {
      const venta = await window.apiGet(`/api/ventas/${idVenta}`);
      const dato = Array.isArray(venta) ? venta[0] : venta;

      if (!dato) {
        mostrarMensaje("danger", "No se encontró la venta seleccionada.");
        return;
      }
      if (dato.estado === false || dato.estado_pago === "Anulado") {
        mostrarMensaje("danger", "No se puede editar una venta anulada.");
        return;
      }

      ventaEditandoId = idVenta;

      if (clienteVenta) clienteVenta.value = dato.cliente || dato.nombre_cliente || "";
      if (identificacionCliente) identificacionCliente.value = dato.identificacion_cliente || dato.identificacion || dato.cedula_ruc || "";
      if (fechaVenta) fechaVenta.value = dato.fecha_venta || "";
      if (tipoComprobante) tipoComprobante.value = "Factura";

      const campoFactura = obtenerCampoNumeroComprobante();
      campoFactura.value = dato.numero_comprobante || dato.numero_factura || generarFacturaLocal();

      await cargarProductosDisponibles();
      const idInventario = dato.id_inventario;

      if (idInventario && productoVenta) {
        productoVenta.value = String(idInventario);
        cargarDatosProductoSeleccionado();
      }

      if (unidadVenta) unidadVenta.value = dato.unidad_medida || "Quintal";
      if (cantidadVenta) cantidadVenta.value = convertirNumero(dato.cantidad_unidad || dato.cantidad || 0);
      if (cantidadEquivalente) cantidadEquivalente.value = formatearNumero(dato.cantidad_quintales || dato.cantidad || 0);
      if (precioVenta) precioVenta.value = convertirNumero(dato.precio_unitario || 0).toFixed(2);
      if (descuentoVenta) descuentoVenta.value = convertirNumero(dato.descuento || 0).toFixed(2);
      if (ivaVenta) ivaVenta.value = String(convertirNumero(dato.iva_porcentaje || 0));
      if (estadoPagoVenta) estadoPagoVenta.value = dato.estado_pago || "Pagado";

      calcularVenta();

      if (valorRecibidoVenta) valorRecibidoVenta.value = formatearNumero(dato.valor_recibido || 0);
      if (saldoPendienteVenta) saldoPendienteVenta.value = formatearNumero(dato.saldo_pendiente || 0);

      aplicarReglasPago();
      if (formaPagoVenta && dato.forma_pago) formaPagoVenta.value = dato.forma_pago;
      if (observacionVenta) observacionVenta.value = dato.observacion || "";

      if (botonSubmit) {
        botonSubmit.textContent = "Actualizar venta";
        botonSubmit.classList.remove("btn-success");
        botonSubmit.classList.add("btn-warning");
      }

      mostrarMensaje("warning", `Editando venta N.º ${idVenta}. Realice los cambios y presione Actualizar venta.`);
      window.scrollTo({ top: 0, behavior: "smooth" });

    } catch (error) {
      mostrarMensaje("danger", "Error al cargar la venta para editar: " + obtenerMensajeError(error));
    }
  };

  window.anularVenta = async function (idVenta) {
    const confirmar = confirm("¿Seguro que deseas anular esta venta? El inventario será revertido automáticamente.");
    if (!confirmar) return;

    try {
      await window.apiDelete(`/api/ventas/${idVenta}`);
      mostrarMensaje("success", "Venta anulada correctamente. El inventario fue revertido.");
      await limpiarFormularioVentaCompleto();
      await cargarProductosDisponibles();
      await cargarVentas();
    } catch (error) {
      mostrarMensaje("danger", "Error al anular venta: " + obtenerMensajeError(error));
    }
  };

  window.imprimirFacturaVenta = function (idVenta) {
    const venta = ventasRegistradas.find((item) => Number(item.id_venta) === Number(idVenta));
    if (!venta) {
      alert("No se encontró la venta para imprimir.");
      return;
    }

    const anulada = venta.estado === false || venta.estado_pago === "Anulado";
    const factura = `
      <!doctype html>
      <html lang="es">
      <head>
        <meta charset="UTF-8">
        <title>Factura ${venta.numero_comprobante || ""}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 30px; color: #222; }
          .encabezado { text-align: center; border-bottom: 2px solid #0b7a38; padding-bottom: 10px; margin-bottom: 20px; }
          .encabezado h1 { color: #0b7a38; margin: 0; }
          .info { margin-bottom: 20px; font-size: 14px; }
          table { width: 100%; border-collapse: collapse; margin-top: 15px; }
          th, td { border: 1px solid #999; padding: 8px; font-size: 13px; }
          th { background: #dceee4; }
          .totales { width: 40%; margin-left: auto; margin-top: 20px; }
          .anulada { color: #c00; font-size: 22px; font-weight: bold; text-align: center; border: 2px solid #c00; padding: 10px; margin-bottom: 15px; }
          .firma { margin-top: 60px; display: flex; justify-content: space-between; }
          .linea { width: 220px; border-top: 1px solid #000; text-align: center; padding-top: 5px; }
        </style>
      </head>
      <body>
        <div class="encabezado">
          <h1>Piladora Don Guillo</h1>
          <p>Factura de venta</p>
          <strong>N.º ${venta.numero_comprobante || venta.numero_factura || "-"}</strong>
        </div>

        ${anulada ? `<div class="anulada">VENTA ANULADA</div>` : ""}

        <div class="info">
          <p><strong>Fecha:</strong> ${venta.fecha_venta || "-"}</p>
          <p><strong>Cliente:</strong> ${venta.cliente || venta.nombre_cliente || "-"}</p>
          <p><strong>Cédula/RUC:</strong> ${venta.identificacion_cliente || venta.identificacion || venta.cedula_ruc || "-"}</p>
          <p><strong>Comprobante:</strong> Factura</p>
          <p><strong>Estado de pago:</strong> ${venta.estado_pago || "-"}</p>
          <p><strong>Forma de pago:</strong> ${venta.forma_pago || "-"}</p>
        </div>

        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>Unidad</th>
              <th>Cantidad</th>
              <th>Precio</th>
              <th>Descuento</th>
              <th>IVA</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>${venta.nombre_producto || venta.producto || "-"}</td>
              <td>${venta.unidad_medida || venta.unidad || "-"}</td>
              <td>${convertirNumero(venta.cantidad_unidad || venta.cantidad || 0).toFixed(2)}</td>
              <td>${formatearDinero(venta.precio_unitario || 0)}</td>
              <td>${formatearDinero(venta.descuento || 0)}</td>
              <td>${convertirNumero(venta.iva_porcentaje || 0).toFixed(2)}%</td>
              <td>${formatearDinero(venta.total_linea || venta.total_venta || 0)}</td>
            </tr>
          </tbody>
        </table>

        <table class="totales">
          <tr><th>Subtotal</th><td>${formatearDinero(venta.subtotal || venta.subtotal_venta || 0)}</td></tr>
          <tr><th>Total</th><td>${formatearDinero(venta.total_linea || venta.total_venta || 0)}</td></tr>
          <tr><th>Valor recibido</th><td>${formatearDinero(venta.valor_recibido || 0)}</td></tr>
          <tr><th>Saldo pendiente</th><td>${formatearDinero(venta.saldo_pendiente || 0)}</td></tr>
        </table>

        <p><strong>Observación:</strong> ${venta.observacion || "-"}</p>

        <div class="firma">
          <div class="linea">Entregué conforme</div>
          <div class="linea">Recibí conforme</div>
        </div>

        <script> window.print(); </script>
      </body>
      </html>
    `;

    const ventana = window.open("", "_blank");
    ventana.document.open();
    ventana.document.write(factura);
    ventana.document.close();
  };

  function agregarEventos() {
    if (productoVenta) {
      productoVenta.addEventListener("change", function () {
        cargarDatosProductoSeleccionado();
        calcularVenta();
      });
    }

    if (unidadVenta) unidadVenta.addEventListener("change", calcularVenta);
    if (cantidadVenta) cantidadVenta.addEventListener("input", calcularVenta);
    if (precioVenta) precioVenta.addEventListener("input", calcularVenta);
    if (descuentoVenta) descuentoVenta.addEventListener("input", calcularVenta);
    if (ivaVenta) ivaVenta.addEventListener("change", calcularVenta);
    if (estadoPagoVenta) estadoPagoVenta.addEventListener("change", calcularVenta);
    if (formaPagoVenta) formaPagoVenta.addEventListener("change", aplicarReglasPago);
    if (valorRecibidoVenta) valorRecibidoVenta.addEventListener("input", aplicarReglasPago);

    const botonLimpiar = formVenta.querySelector('button[type="reset"], button.btn-secondary');
    if (botonLimpiar) {
      botonLimpiar.addEventListener("click", async function (event) {
        event.preventDefault();
        ocultarMensaje();
        await limpiarFormularioVentaCompleto();
      });
    }
  }
});