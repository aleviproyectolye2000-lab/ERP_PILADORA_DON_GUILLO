/* ---------------------------------------------------- */
/* MÓDULO DE INVENTARIO Y BODEGA                        */
/* ERP PILADORA DON GUILLO                              */
/* CRUD real con FastAPI + PostgreSQL                   */
/* Vista consolidada + detalle por lote                 */
/* ---------------------------------------------------- */

let idInventarioEditando = null;
let productosInventarioBackend = [];
let bodegasInventarioBackend = [];
let inventarioActual = [];

/* ---------------------------------------------------- */
/* FUNCIONES GENERALES                                  */
/* ---------------------------------------------------- */

function numeroInventario(valor) {
  const numero = Number(valor);
  return Number.isFinite(numero) ? numero : 0;
}

function formatoDecimal(valor) {
  return numeroInventario(valor).toFixed(2);
}

function formatoDinero(valor) {
  return `$ ${numeroInventario(valor).toFixed(2)}`;
}

function calcularSacas(cantidadQuintales) {
  return numeroInventario(cantidadQuintales) / 2;
}

function limpiarTextoInventario(valor) {
  return String(valor || "").trim();
}

function limpiarLoteInventario(valor) {
  const lote = limpiarTextoInventario(valor).toUpperCase();
  return lote === "" ? "SIN-LOTE" : lote;
}

function mostrarMensajeInventario(tipo, mensaje) {
  const mensajeInventario = document.getElementById("mensajeInventario");

  if (!mensajeInventario) return;

  mensajeInventario.classList.remove(
    "d-none",
    "alert-success",
    "alert-danger",
    "alert-warning",
    "alert-info"
  );

  mensajeInventario.classList.add(`alert-${tipo}`);
  mensajeInventario.textContent = mensaje;
}

function ocultarMensajeInventario() {
  const mensajeInventario = document.getElementById("mensajeInventario");

  if (!mensajeInventario) return;

  mensajeInventario.classList.add("d-none");
  mensajeInventario.textContent = "";
}

function limpiarModoEdicionInventario() {
  idInventarioEditando = null;

  const boton = document.querySelector("#formInventario button[type='submit']");

  if (boton) {
    boton.textContent = "Registrar producto";
    boton.classList.remove("btn-warning");
    boton.classList.add("btn-success");
  }
}

function obtenerEstadoVisualInventario(item) {
  const cantidad = numeroInventario(item.cantidad_disponible);
  const minimo = numeroInventario(item.stock_minimo);

  if (cantidad <= 0) {
    return {
      texto: "Agotado",
      clase: "badge bg-danger"
    };
  }

  if (cantidad <= minimo) {
    return {
      texto: "Stock bajo",
      clase: "badge bg-warning text-dark"
    };
  }

  return {
    texto: "Disponible",
    clase: "badge bg-success"
  };
}

function obtenerEstadoConsolidado(cantidad, minimo) {
  if (cantidad <= 0) {
    return {
      texto: "Agotado",
      clase: "badge bg-danger"
    };
  }

  if (cantidad <= minimo) {
    return {
      texto: "Stock bajo",
      clase: "badge bg-warning text-dark"
    };
  }

  return {
    texto: "Disponible",
    clase: "badge bg-success"
  };
}

function obtenerClaseFilaPorTipo(tipoProducto) {
  const tipo = limpiarTextoInventario(tipoProducto).toLowerCase();

  if (tipo === "materia prima") {
    return "table-warning";
  }

  if (tipo === "producto terminado") {
    return "table-success";
  }

  if (tipo === "subproducto") {
    return "table-info";
  }

  return "";
}

/* ---------------------------------------------------- */
/* TARJETAS DEL INVENTARIO                              */
/* ---------------------------------------------------- */

function obtenerInventarioConsolidado(inventario) {
  const mapa = new Map();

  inventario.forEach((item) => {
    const idProducto = item.id_producto || item.codigo || item.nombre_producto;
    const clave = String(idProducto);

    const cantidad = numeroInventario(item.cantidad_disponible);
    const minimo = numeroInventario(item.stock_minimo);
    const precio = numeroInventario(item.precio_referencial);
    const valor = cantidad * precio;

    if (!mapa.has(clave)) {
      mapa.set(clave, {
        id_producto: item.id_producto,
        codigo: item.codigo || "-",
        nombre_producto: item.nombre_producto || "-",
        tipo_producto: item.tipo_producto || "-",
        unidad_medida: item.unidad_medida || "qq",
        cantidad_total: 0,
        stock_minimo_total: 0,
        valor_total: 0,
        lotes: new Set(),
        bodegas: new Set()
      });
    }

    const producto = mapa.get(clave);

    producto.cantidad_total += cantidad;
    producto.stock_minimo_total += minimo;
    producto.valor_total += valor;

    if (item.lote) {
      producto.lotes.add(item.lote);
    }

    if (item.nombre_bodega) {
      producto.bodegas.add(item.nombre_bodega);
    }
  });

  return Array.from(mapa.values()).map((item) => {
    return {
      ...item,
      total_lotes: item.lotes.size,
      total_bodegas: item.bodegas.size,
      lotes_texto: Array.from(item.lotes).join(", "),
      bodegas_texto: Array.from(item.bodegas).join(", ")
    };
  });
}

function actualizarTarjetasInventario(inventario) {
  const totalProductos = document.getElementById("totalProductos");
  const totalStockBajo = document.getElementById("totalStockBajo");
  const totalAgotados = document.getElementById("totalAgotados");
  const valorInventario = document.getElementById("valorInventario");

  if (!totalProductos || !totalStockBajo || !totalAgotados || !valorInventario) {
    return;
  }

  const consolidado = obtenerInventarioConsolidado(inventario);

  const totalProductosUnicos = consolidado.length;
  const totalRegistrosLote = inventario.length;

  const totalQuintales = inventario.reduce((acumulado, item) => {
    return acumulado + numeroInventario(item.cantidad_disponible);
  }, 0);

  const totalSacas = calcularSacas(totalQuintales);

  const stockBajo = consolidado.filter((item) => {
    return (
      numeroInventario(item.cantidad_total) > 0 &&
      numeroInventario(item.cantidad_total) <= numeroInventario(item.stock_minimo_total)
    );
  });

  const agotados = consolidado.filter((item) => {
    return numeroInventario(item.cantidad_total) <= 0;
  });

  const valorTotal = consolidado.reduce((acumulado, item) => {
    return acumulado + numeroInventario(item.valor_total);
  }, 0);

  totalProductos.innerHTML = `
    ${totalProductosUnicos}
    <small class="d-block text-muted" style="font-size: 11px;">
      ${formatoDecimal(totalQuintales)} qq / ${formatoDecimal(totalSacas)} sacas
    </small>
    <small class="d-block text-muted" style="font-size: 11px;">
      ${totalRegistrosLote} registros por lote
    </small>
  `;

  totalStockBajo.innerHTML = `
    ${stockBajo.length}
    <small class="d-block text-muted" style="font-size: 11px;">
      productos por reponer
    </small>
    <small class="d-block text-muted" style="font-size: 11px;">
      ${stockBajo.map((p) => p.nombre_producto).join(", ") || "Sin stock bajo"}
    </small>
  `;

  totalAgotados.innerHTML = `
    ${agotados.length}
    <small class="d-block text-muted" style="font-size: 11px;">
      sin existencia
    </small>
    <small class="d-block text-muted" style="font-size: 11px;">
      ${agotados.map((p) => p.nombre_producto).join(", ") || "Sin agotados"}
    </small>
  `;

  valorInventario.textContent = formatoDinero(valorTotal);
}

/* ---------------------------------------------------- */
/* RESUMEN CONSOLIDADO POR PRODUCTO                     */
/* ---------------------------------------------------- */

function crearResumenConsolidadoInventario() {
  const tablaInventario = document.getElementById("tablaInventario");

  if (!tablaInventario) return;

  const cardBody = tablaInventario.closest(".card-body");

  if (!cardBody) return;

  if (document.getElementById("contenedorResumenConsolidadoInventario")) return;

  const contenedor = document.createElement("div");
  contenedor.id = "contenedorResumenConsolidadoInventario";
  contenedor.className = "mb-4";

  contenedor.innerHTML = `
    <h6 class="fw-bold text-success mb-2">
      Resumen consolidado por producto
    </h6>

    <div class="table-responsive">
      <table class="table table-bordered table-hover align-middle">
        <thead class="table-success">
          <tr>
            <th>N°</th>
            <th>Código</th>
            <th>Producto</th>
            <th>Tipo</th>
            <th>Total disponible</th>
            <th>Total sacas</th>
            <th>Valor estimado</th>
            <th>Lotes</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody id="tablaResumenConsolidadoInventario">
          <tr>
            <td colspan="9" class="text-center text-muted">
              Cargando resumen consolidado...
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <hr>
    <h6 class="fw-bold text-success mb-2">
      Detalle de inventario por lote
    </h6>
  `;

  cardBody.insertBefore(contenedor, cardBody.firstChild);
}

function renderizarResumenConsolidadoInventario(inventario) {
  const tablaResumen = document.getElementById("tablaResumenConsolidadoInventario");

  if (!tablaResumen) return;

  const consolidado = obtenerInventarioConsolidado(inventario);

  if (!consolidado || consolidado.length === 0) {
    tablaResumen.innerHTML = `
      <tr>
        <td colspan="9" class="text-center text-muted">
          No existe inventario consolidado para mostrar.
        </td>
      </tr>
    `;
    return;
  }

  tablaResumen.innerHTML = "";

  consolidado.forEach((item, index) => {
    const cantidad = numeroInventario(item.cantidad_total);
    const minimo = numeroInventario(item.stock_minimo_total);
    const sacas = calcularSacas(cantidad);
    const estado = obtenerEstadoConsolidado(cantidad, minimo);

    const fila = document.createElement("tr");
    fila.className = obtenerClaseFilaPorTipo(item.tipo_producto);

    fila.innerHTML = `
      <td>${index + 1}</td>
      <td>${item.codigo || "-"}</td>
      <td>
        <strong>${item.nombre_producto || "-"}</strong>
        <br>
        <small class="text-muted">
          ${item.total_bodegas} bodega(s)
        </small>
      </td>
      <td>${item.tipo_producto || "-"}</td>
      <td>
        ${formatoDecimal(cantidad)} ${item.unidad_medida || "qq"}
      </td>
      <td>${formatoDecimal(sacas)} sacas</td>
      <td>${formatoDinero(item.valor_total)}</td>
      <td>
        ${item.total_lotes}
        <br>
        <small class="text-muted">
          ${item.lotes_texto || "SIN-LOTE"}
        </small>
      </td>
      <td><span class="${estado.clase}">${estado.texto}</span></td>
    `;

    tablaResumen.appendChild(fila);
  });
}

/* ---------------------------------------------------- */
/* FILTROS DE CONSULTA                                  */
/* ---------------------------------------------------- */

function crearFiltrosInventario() {
  const tablaInventario = document.getElementById("tablaInventario");

  if (!tablaInventario) return;

  const cardBody = tablaInventario.closest(".card-body");

  if (!cardBody) return;

  if (document.getElementById("filtrosInventario")) return;

  const filtros = document.createElement("div");
  filtros.id = "filtrosInventario";
  filtros.className = "row g-2 mb-3";

  filtros.innerHTML = `
    <div class="col-md-4">
      <label class="form-label">Consultar por producto</label>
      <input type="text" class="form-control" id="filtroProductoInventario" placeholder="Ejemplo: arroz, polvillo, arrocillo">
    </div>

    <div class="col-md-4">
      <label class="form-label">Consultar por bodega</label>
      <input type="text" class="form-control" id="filtroBodegaInventario" placeholder="Ejemplo: materia prima, subproductos">
    </div>

    <div class="col-md-3">
      <label class="form-label">Consultar por lote</label>
      <input type="text" class="form-control" id="filtroLoteInventario" placeholder="Ejemplo: LOTE-COMPRA-1">
    </div>

    <div class="col-md-1 d-flex align-items-end">
      <button type="button" class="btn btn-secondary w-100" id="btnLimpiarFiltrosInventario">
        Limpiar
      </button>
    </div>
  `;

  const resumen = document.getElementById("contenedorResumenConsolidadoInventario");

  if (resumen) {
    resumen.insertAdjacentElement("afterend", filtros);
  } else {
    cardBody.insertBefore(filtros, cardBody.firstChild);
  }

  const filtroProducto = document.getElementById("filtroProductoInventario");
  const filtroBodega = document.getElementById("filtroBodegaInventario");
  const filtroLote = document.getElementById("filtroLoteInventario");
  const btnLimpiar = document.getElementById("btnLimpiarFiltrosInventario");

  [filtroProducto, filtroBodega, filtroLote].forEach((input) => {
    if (input) {
      input.addEventListener("input", aplicarFiltrosInventario);
    }
  });

  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", function () {
      filtroProducto.value = "";
      filtroBodega.value = "";
      filtroLote.value = "";
      aplicarFiltrosInventario();
    });
  }
}

function aplicarFiltrosInventario() {
  const filtroProducto = limpiarTextoInventario(
    document.getElementById("filtroProductoInventario")?.value
  ).toLowerCase();

  const filtroBodega = limpiarTextoInventario(
    document.getElementById("filtroBodegaInventario")?.value
  ).toLowerCase();

  const filtroLote = limpiarTextoInventario(
    document.getElementById("filtroLoteInventario")?.value
  ).toLowerCase();

  const inventarioFiltrado = inventarioActual.filter((item) => {
    const producto = limpiarTextoInventario(item.nombre_producto).toLowerCase();
    const bodega = limpiarTextoInventario(item.nombre_bodega).toLowerCase();
    const lote = limpiarTextoInventario(item.lote).toLowerCase();

    const coincideProducto =
      filtroProducto === "" || producto.includes(filtroProducto);

    const coincideBodega =
      filtroBodega === "" || bodega.includes(filtroBodega);

    const coincideLote =
      filtroLote === "" || lote.includes(filtroLote);

    return coincideProducto && coincideBodega && coincideLote;
  });

  renderizarResumenConsolidadoInventario(inventarioFiltrado);
  renderizarTablaInventario(inventarioFiltrado);
}

/* ---------------------------------------------------- */
/* CARGAR SELECTS                                       */
/* ---------------------------------------------------- */

async function cargarProductosInventario() {
  const selectProducto = document.getElementById("nombreProducto");

  if (!selectProducto) return;

  productosInventarioBackend = await window.apiGet("/api/inventario/productos");

  selectProducto.innerHTML = `<option value="">Seleccione</option>`;

  productosInventarioBackend.forEach((producto) => {
    const option = document.createElement("option");

    option.value = producto.id_producto;
    option.textContent = `${producto.nombre_producto} (${producto.tipo_producto})`;

    option.dataset.codigo = producto.codigo || "";
    option.dataset.tipo = producto.tipo_producto || "";
    option.dataset.unidad = producto.unidad_medida || "";
    option.dataset.precio = producto.precio_referencial || 0;
    option.dataset.stock = producto.stock_minimo || 0;

    selectProducto.appendChild(option);
  });
}

async function cargarBodegasInventario() {
  const selectBodega = document.getElementById("bodegaProducto");

  if (!selectBodega) return;

  bodegasInventarioBackend = await window.apiGet("/api/inventario/bodegas");

  selectBodega.innerHTML = `<option value="">Seleccione</option>`;

  bodegasInventarioBackend.forEach((bodega) => {
    const option = document.createElement("option");

    option.value = bodega.id_bodega;
    option.textContent = bodega.nombre_bodega;

    selectBodega.appendChild(option);
  });
}

/* ---------------------------------------------------- */
/* RENDERIZAR TABLA DETALLADA POR LOTE                  */
/* ---------------------------------------------------- */

function renderizarTablaInventario(inventario) {
  const tablaInventario = document.getElementById("tablaInventario");

  if (!tablaInventario) return;

  if (!inventario || inventario.length === 0) {
    tablaInventario.innerHTML = `
      <tr>
        <td colspan="10" class="text-center text-muted">
          No existe inventario registrado o no hay coincidencias con la búsqueda.
        </td>
      </tr>
    `;
    return;
  }

  tablaInventario.innerHTML = "";

  inventario.forEach((item, index) => {
    const estado = obtenerEstadoVisualInventario(item);
    const cantidad = numeroInventario(item.cantidad_disponible);
    const minimo = numeroInventario(item.stock_minimo);
    const sacasDisponibles = calcularSacas(cantidad);
    const sacasMinimas = calcularSacas(minimo);
    const valorEstimado = cantidad * numeroInventario(item.precio_referencial);

    const fila = document.createElement("tr");
    fila.className = obtenerClaseFilaPorTipo(item.tipo_producto);

    fila.innerHTML = `
      <td>${index + 1}</td>
      <td>${item.codigo || "-"}</td>
      <td>
        <strong>${item.nombre_producto || "-"}</strong>
        <br>
        <small class="text-muted">Valor: ${formatoDinero(valorEstimado)}</small>
      </td>
      <td>${item.tipo_producto || "-"}</td>
      <td>${item.nombre_bodega || "-"}</td>
      <td>${item.lote || "SIN-LOTE"}</td>
      <td>
        ${formatoDecimal(cantidad)} ${item.unidad_medida || "qq"}
        <br>
        <small class="text-muted">${formatoDecimal(sacasDisponibles)} sacas</small>
      </td>
      <td>
        ${formatoDecimal(minimo)} ${item.unidad_medida || "qq"}
        <br>
        <small class="text-muted">${formatoDecimal(sacasMinimas)} sacas</small>
      </td>
      <td><span class="${estado.clase}">${estado.texto}</span></td>
      <td>
        <button 
          type="button" 
          class="btn btn-sm btn-warning me-1"
          onclick="editarInventario(${item.id_inventario})">
          Editar
        </button>

        <button 
          type="button" 
          class="btn btn-sm btn-danger"
          onclick="eliminarInventario(${item.id_inventario})">
          Eliminar
        </button>
      </td>
    `;

    tablaInventario.appendChild(fila);
  });
}

async function cargarInventario() {
  const tablaInventario = document.getElementById("tablaInventario");

  if (!tablaInventario) return;

  try {
    inventarioActual = await window.apiGet("/api/inventario/");

    actualizarTarjetasInventario(inventarioActual);
    crearResumenConsolidadoInventario();
    crearFiltrosInventario();
    renderizarResumenConsolidadoInventario(inventarioActual);
    renderizarTablaInventario(inventarioActual);

  } catch (error) {
    tablaInventario.innerHTML = `
      <tr>
        <td colspan="10" class="text-center text-danger">
          Error al cargar inventario: ${error.message}
        </td>
      </tr>
    `;

    actualizarTarjetasInventario([]);
    renderizarResumenConsolidadoInventario([]);
  }
}

/* ---------------------------------------------------- */
/* EDITAR Y ELIMINAR                                    */
/* ---------------------------------------------------- */

async function editarInventario(idInventario) {
  try {
    const item = await window.apiGet(`/api/inventario/${idInventario}`);

    idInventarioEditando = idInventario;

    const nombreProducto = document.getElementById("nombreProducto");
    const bodegaProducto = document.getElementById("bodegaProducto");
    const codigoProducto = document.getElementById("codigoProducto");
    const tipoProducto = document.getElementById("tipoProducto");
    const unidadProducto = document.getElementById("unidadProducto");
    const cantidadProducto = document.getElementById("cantidadProducto");
    const stockMinimo = document.getElementById("stockMinimo");
    const precioReferencial = document.getElementById("precioReferencial");
    const loteProducto = document.getElementById("loteProducto");
    const estadoProducto = document.getElementById("estadoProducto");

    if (nombreProducto) nombreProducto.value = item.id_producto;
    if (bodegaProducto) bodegaProducto.value = item.id_bodega;
    if (codigoProducto) codigoProducto.value = item.codigo || "";
    if (tipoProducto) tipoProducto.value = item.tipo_producto || "";
    if (unidadProducto) unidadProducto.value = item.unidad_medida || "";
    if (cantidadProducto) cantidadProducto.value = numeroInventario(item.cantidad_disponible);
    if (stockMinimo) stockMinimo.value = numeroInventario(item.stock_minimo);
    if (precioReferencial) precioReferencial.value = numeroInventario(item.precio_referencial);
    if (loteProducto) loteProducto.value = item.lote || "SIN-LOTE";
    if (estadoProducto) estadoProducto.value = item.estado_producto || "Disponible";

    const boton = document.querySelector("#formInventario button[type='submit']");

    if (boton) {
      boton.textContent = "Actualizar inventario";
      boton.classList.remove("btn-success");
      boton.classList.add("btn-warning");
    }

    mostrarMensajeInventario(
      "warning",
      `Editando inventario N° ${idInventario}. Realice los cambios y presione Actualizar inventario.`
    );

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });

  } catch (error) {
    alert(`Error al cargar inventario para editar: ${error.message}`);
  }
}

async function eliminarInventario(idInventario) {
  const confirmar = confirm(
    "¿Seguro que deseas eliminar definitivamente este registro de inventario de PostgreSQL?"
  );

  if (!confirmar) return;

  try {
    await window.apiDelete(`/api/inventario/${idInventario}`);

    alert("Inventario eliminado definitivamente.");
    await cargarInventario();

  } catch (error) {
    alert(`Error al eliminar inventario: ${error.message}`);
  }
}

window.editarInventario = editarInventario;
window.eliminarInventario = eliminarInventario;

/* ---------------------------------------------------- */
/* FORMULARIO                                           */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  const formInventario = document.getElementById("formInventario");

  if (!formInventario) return;

  const codigoProducto = document.getElementById("codigoProducto");
  const nombreProducto = document.getElementById("nombreProducto");
  const tipoProducto = document.getElementById("tipoProducto");
  const unidadProducto = document.getElementById("unidadProducto");
  const cantidadProducto = document.getElementById("cantidadProducto");
  const stockMinimo = document.getElementById("stockMinimo");
  const precioReferencial = document.getElementById("precioReferencial");
  const bodegaProducto = document.getElementById("bodegaProducto");
  const loteProducto = document.getElementById("loteProducto");
  const estadoProducto = document.getElementById("estadoProducto");

  try {
    await cargarProductosInventario();
    await cargarBodegasInventario();
    await cargarInventario();
  } catch (error) {
    mostrarMensajeInventario(
      "danger",
      `Error al iniciar inventario: ${error.message}`
    );
  }

  if (nombreProducto) {
    nombreProducto.addEventListener("change", function () {
      const option = nombreProducto.options[nombreProducto.selectedIndex];

      if (!option || !option.value) {
        if (codigoProducto) codigoProducto.value = "";
        if (tipoProducto) tipoProducto.value = "";
        if (unidadProducto) unidadProducto.value = "";
        if (stockMinimo) stockMinimo.value = "";
        if (precioReferencial) precioReferencial.value = "";
        return;
      }

      if (codigoProducto) codigoProducto.value = option.dataset.codigo || "";
      if (tipoProducto) tipoProducto.value = option.dataset.tipo || "";
      if (unidadProducto) unidadProducto.value = option.dataset.unidad || "";
      if (stockMinimo) stockMinimo.value = option.dataset.stock || "0";
      if (precioReferencial) precioReferencial.value = option.dataset.precio || "0";
    });
  }

  if (codigoProducto) {
    codigoProducto.readOnly = true;
  }

  if (tipoProducto) {
    tipoProducto.readOnly = true;
  }

  if (unidadProducto) {
    unidadProducto.readOnly = true;
  }

  [cantidadProducto, stockMinimo, precioReferencial].forEach((input) => {
    if (!input) return;

    input.addEventListener("input", function () {
      if (Number(this.value) < 0) {
        this.value = "";
        mostrarMensajeInventario(
          "danger",
          "No se permiten valores negativos en inventario."
        );
      }
    });
  });

  formInventario.addEventListener("reset", function () {
    limpiarModoEdicionInventario();

    setTimeout(() => {
      ocultarMensajeInventario();
    }, 50);
  });

  formInventario.addEventListener("submit", async function (event) {
    event.preventDefault();

    if (!window.apiPost || !window.apiPut || !window.apiGet || !window.apiDelete) {
      mostrarMensajeInventario(
        "danger",
        "No se cargó correctamente api.js. Revise que inventario.html cargue primero js/api.js, luego js/main.js y después js/inventario.js."
      );
      return;
    }

    const idProducto = Number(nombreProducto?.value || 0);
    const idBodega = Number(bodegaProducto?.value || 0);
    const cantidad = numeroInventario(cantidadProducto?.value);
    const minimo = numeroInventario(stockMinimo?.value);
    const precio = numeroInventario(precioReferencial?.value);
    const lote = limpiarLoteInventario(loteProducto?.value);
    const estadoFormulario = limpiarTextoInventario(estadoProducto?.value);

    if (!idProducto) {
      mostrarMensajeInventario("danger", "Debe seleccionar un producto.");
      return;
    }

    if (!idBodega) {
      mostrarMensajeInventario("danger", "Debe seleccionar una bodega.");
      return;
    }

    if (!estadoFormulario) {
      mostrarMensajeInventario("danger", "Debe seleccionar un estado.");
      return;
    }

    if (cantidad < 0 || minimo < 0 || precio < 0) {
      mostrarMensajeInventario(
        "danger",
        "No se permiten valores negativos en cantidad, stock mínimo o precio."
      );
      return;
    }

    if (!["Disponible", "Reservado", "Agotado"].includes(estadoFormulario)) {
      mostrarMensajeInventario(
        "danger",
        "Debe seleccionar un estado válido: Disponible, Reservado o Agotado."
      );
      return;
    }

    const duplicado = inventarioActual.find((item) => {
      const mismoProducto = Number(item.id_producto) === idProducto;
      const mismaBodega = Number(item.id_bodega) === idBodega;
      const mismoLote = limpiarLoteInventario(item.lote) === lote;
      const noEsElMismoRegistro =
        Number(item.id_inventario) !== Number(idInventarioEditando);

      return mismoProducto && mismaBodega && mismoLote && noEsElMismoRegistro;
    });

    if (duplicado) {
      mostrarMensajeInventario(
        "danger",
        "Ya existe inventario para el mismo producto, bodega y lote. Para evitar duplicados, edite el registro existente."
      );
      return;
    }

    const estadoFinal = cantidad <= 0 ? "Agotado" : estadoFormulario;

    const datosInventario = {
      id_producto: idProducto,
      id_bodega: idBodega,
      lote: lote,
      cantidad_disponible: cantidad,
      stock_minimo: minimo,
      precio_referencial: precio,
      estado_producto: estadoFinal,
      observacion: idInventarioEditando
        ? "Inventario actualizado desde frontend"
        : "Ajuste manual de inventario desde frontend"
    };

    try {
      if (idInventarioEditando) {
        await window.apiPut(
          `/api/inventario/${idInventarioEditando}`,
          datosInventario
        );

        mostrarMensajeInventario(
          "success",
          "Inventario actualizado correctamente en PostgreSQL."
        );
      } else {
        await window.apiPost(
          "/api/inventario/",
          datosInventario
        );

        mostrarMensajeInventario(
          "success",
          "Inventario registrado correctamente en PostgreSQL."
        );
      }

      formInventario.reset();
      limpiarModoEdicionInventario();
      await cargarInventario();

    } catch (error) {
      mostrarMensajeInventario(
        "danger",
        `Error al guardar inventario: ${error.message}`
      );
    }
  });
});