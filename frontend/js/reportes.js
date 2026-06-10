console.log("REPORTES.JS NUEVO CARGADO - VERSION 5");

/* ---------------------------------------------------- */
/* MÓDULO REPORTES E INTELIGENCIA ARTIFICIAL            */
/* ERP PILADORA DON GUILLO                              */
/* Frontend conectado con FastAPI y PostgreSQL          */
/* ---------------------------------------------------- */

/* ---------------------------------------------------- */
/* FUNCIONES AUXILIARES                                 */
/* ---------------------------------------------------- */

function formatearDinero(valor) {
  return `$ ${Number(valor || 0).toFixed(2)}`;
}

function formatearCantidad(valor) {
  return `${Number(valor || 0).toFixed(2)} qq`;
}

function formatearPorcentaje(valor) {
  return `${Number(valor || 0).toFixed(2)}%`;
}

function textoSeguro(valor) {
  if (valor === null || valor === undefined || valor === "") {
    return "-";
  }

  return String(valor)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizarTexto(valor) {
  return String(valor || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function obtenerValor(item, campos) {
  for (const campo of campos) {
    if (item && item[campo] !== undefined && item[campo] !== null && item[campo] !== "") {
      return item[campo];
    }
  }

  return "";
}

function obtenerMesNombre(fechaTexto) {
  if (!fechaTexto) return "Sin fecha";

  const fecha = new Date(fechaTexto + "T00:00:00");

  if (isNaN(fecha.getTime())) {
    return "Sin fecha";
  }

  const meses = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre"
  ];

  return meses[fecha.getMonth()];
}

function agruparPorMes(datos, campoFecha, campoValor) {
  const mesesOrden = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre"
  ];

  const acumulado = {};

  datos.forEach((item) => {
    const mes = obtenerMesNombre(item[campoFecha]);
    const valor = Number(item[campoValor] || 0);

    if (!acumulado[mes]) {
      acumulado[mes] = 0;
    }

    acumulado[mes] += valor;
  });

  return mesesOrden
    .filter((mes) => acumulado[mes] !== undefined)
    .map((mes) => ({
      mes: mes,
      valor: acumulado[mes]
    }));
}

function agruparInventarioPorProducto(datos) {
  const acumulado = {};

  datos.forEach((item) => {
    const producto = item.nombre_producto || item.producto || "Sin producto";
    const cantidad = Number(item.cantidad_disponible || 0);

    if (!acumulado[producto]) {
      acumulado[producto] = 0;
    }

    acumulado[producto] += cantidad;
  });

  return Object.keys(acumulado).map((producto) => ({
    producto: producto,
    cantidad: acumulado[producto]
  }));
}

function limpiarGrafico(nombreGrafico) {
  if (!window.graficosReportes) {
    window.graficosReportes = {};
  }

  if (window.graficosReportes[nombreGrafico]) {
    window.graficosReportes[nombreGrafico].destroy();
  }
}

function obtenerFechaItem(item, modulo) {
  const camposFechaPorModulo = {
    general: [],
    compras: ["fecha_compra", "fecha"],
    ventas: ["fecha_venta", "fecha"],
    inventario: ["fecha_ingreso", "fecha_creacion", "fecha"],
    produccion: ["fecha_pilado", "fecha"],
    "talento-humano": ["fecha", "fecha_ingreso", "fecha_rol", "fecha_asistencia"],
    auditoria: ["fecha_accion", "fecha_ingreso", "fecha_salida", "fecha"],
    activos: ["fecha_compra", "fecha_adquisicion", "fecha_mantenimiento", "fecha"]
  };

  const campos = camposFechaPorModulo[modulo] || ["fecha"];
  return obtenerValor(item, campos);
}

function convertirFechaComparable(fechaTexto) {
  if (!fechaTexto) {
    return null;
  }

  const fecha = new Date(fechaTexto + "T00:00:00");

  if (isNaN(fecha.getTime())) {
    return null;
  }

  return fecha;
}

function cumpleFiltroFecha(item, modulo, fechaDesde, fechaHasta) {
  if (!fechaDesde && !fechaHasta) {
    return true;
  }

  const fechaItemTexto = obtenerFechaItem(item, modulo);
  const fechaItem = convertirFechaComparable(fechaItemTexto);

  if (!fechaItem) {
    return true;
  }

  if (fechaDesde) {
    const desde = convertirFechaComparable(fechaDesde);
    if (desde && fechaItem < desde) {
      return false;
    }
  }

  if (fechaHasta) {
    const hasta = convertirFechaComparable(fechaHasta);
    if (hasta && fechaItem > hasta) {
      return false;
    }
  }

  return true;
}

function cumpleFiltroUsuario(item, usuarioFiltro) {
  if (!usuarioFiltro) {
    return true;
  }

  const usuarioItem = obtenerValor(item, [
    "usuario_registra",
    "usuario",
    "nombre_usuario",
    "usuario_accion",
    "usuario_creacion",
    "creado_por",
    "registrado_por"
  ]);

  return normalizarTexto(usuarioItem).includes(normalizarTexto(usuarioFiltro));
}

function cumpleFiltroPerfil(item, perfilFiltro) {
  if (!perfilFiltro) {
    return true;
  }

  const perfilItem = obtenerValor(item, [
    "perfil",
    "nombre_perfil",
    "perfil_usuario",
    "rol",
    "tipo_usuario"
  ]);

  if (!perfilItem) {
    return true;
  }

  return normalizarTexto(perfilItem).includes(normalizarTexto(perfilFiltro));
}

function formatearValorTabla(valor, tipo) {
  if (tipo === "dinero") {
    return formatearDinero(valor);
  }

  if (tipo === "cantidad") {
    return formatearCantidad(valor);
  }

  if (tipo === "porcentaje") {
    return formatearPorcentaje(valor);
  }

  return textoSeguro(valor);
}

/* ---------------------------------------------------- */
/* CONFIGURACIÓN DE REPORTES FILTRADOS                  */
/* ---------------------------------------------------- */

const configuracionReportes = {
  general: {
    titulo: "Reporte general del ERP",
    endpoint: "/api/reportes/resumen",
    tipoRespuesta: "objeto",
    columnas: [
      { titulo: "Total compras", campos: ["total_compras"] },
      { titulo: "Monto compras", campos: ["monto_total_compras"], tipo: "dinero" },
      { titulo: "Total ventas", campos: ["total_ventas"] },
      { titulo: "Monto ventas", campos: ["monto_total_ventas"], tipo: "dinero" },
      { titulo: "Inventario total", campos: ["cantidad_total_inventario"], tipo: "cantidad" },
      { titulo: "Empleados", campos: ["total_empleados"] },
      { titulo: "Activos", campos: ["total_activos"] },
      { titulo: "Rendimiento promedio", campos: ["rendimiento_promedio"], tipo: "porcentaje" }
    ]
  },

  compras: {
    titulo: "Reporte de compras y báscula",
    endpoint: "/api/reportes/compras",
    tipoRespuesta: "lista",
    columnas: [
      { titulo: "Fecha", campos: ["fecha_compra"] },
      { titulo: "Proveedor", campos: ["proveedor", "nombres"] },
      { titulo: "Usuario", campos: ["usuario_registra", "usuario"] },
      { titulo: "Placa", campos: ["placa_vehiculo"] },
      { titulo: "Chofer", campos: ["chofer"] },
      { titulo: "Peso neto", campos: ["peso_neto"], tipo: "cantidad" },
      { titulo: "Precio qq", campos: ["precio_quintal"], tipo: "dinero" },
      { titulo: "Total compra", campos: ["total_compra"], tipo: "dinero" },
      { titulo: "Estado pago", campos: ["estado_pago"] }
    ]
  },

  ventas: {
    titulo: "Reporte de ventas",
    endpoint: "/api/reportes/ventas",
    tipoRespuesta: "lista",
    columnas: [
      { titulo: "Fecha", campos: ["fecha_venta"] },
      { titulo: "Cliente", campos: ["cliente", "nombres"] },
      { titulo: "Usuario", campos: ["usuario_registra", "usuario"] },
      { titulo: "Comprobante", campos: ["tipo_comprobante"] },
      { titulo: "Forma pago", campos: ["forma_pago"] },
      { titulo: "Estado pago", campos: ["estado_pago"] },
      { titulo: "Producto", campos: ["nombre_producto", "producto"] },
      { titulo: "Cantidad", campos: ["cantidad"], tipo: "cantidad" },
      { titulo: "Precio unitario", campos: ["precio_unitario"], tipo: "dinero" },
      { titulo: "Total", campos: ["total_linea", "total_venta"], tipo: "dinero" }
    ]
  },

  inventario: {
    titulo: "Reporte de inventario",
    endpoint: "/api/reportes/inventario",
    tipoRespuesta: "lista",
    columnas: [
      { titulo: "Código", campos: ["codigo", "codigo_producto"] },
      { titulo: "Producto", campos: ["nombre_producto", "producto"] },
      { titulo: "Tipo", campos: ["tipo_producto"] },
      { titulo: "Bodega", campos: ["nombre_bodega", "bodega"] },
      { titulo: "Lote", campos: ["lote"] },
      { titulo: "Cantidad disponible", campos: ["cantidad_disponible"], tipo: "cantidad" },
      { titulo: "Stock mínimo", campos: ["stock_minimo"], tipo: "cantidad" },
      { titulo: "Valor estimado", campos: ["valor_estimado"], tipo: "dinero" },
      { titulo: "Estado stock", campos: ["estado_stock", "estado_producto"] }
    ]
  },

  produccion: {
    titulo: "Reporte de producción y pilado",
    endpoint: "/api/reportes/produccion",
    tipoRespuesta: "lista",
    columnas: [
      { titulo: "Fecha", campos: ["fecha_pilado"] },
      { titulo: "Orden", campos: ["numero_orden"] },
      { titulo: "Usuario", campos: ["usuario_registra", "usuario"] },
      { titulo: "Lote origen", campos: ["lote_origen"] },
      { titulo: "Tipo arroz", campos: ["tipo_arroz_procesado"] },
      { titulo: "Cantidad procesada", campos: ["cantidad_procesada"], tipo: "cantidad" },
      { titulo: "Máquina", campos: ["maquina_utilizada"] },
      { titulo: "Operador", campos: ["operador"] },
      { titulo: "Arroz pilado", campos: ["arroz_pilado_obtenido"], tipo: "cantidad" },
      { titulo: "Rendimiento", campos: ["rendimiento_porcentaje"], tipo: "porcentaje" },
      { titulo: "Estado", campos: ["estado_pilado"] }
    ]
  },

  "talento-humano": {
    titulo: "Reporte de talento humano",
    endpoint: "/api/reportes/talento-humano",
    tipoRespuesta: "lista",
    columnas: [
      { titulo: "Empleado", campos: ["empleado", "nombres_completos", "nombre_empleado", "nombres"] },
      { titulo: "Cédula", campos: ["cedula", "identificacion"] },
      { titulo: "Cargo", campos: ["cargo"] },
      { titulo: "Área", campos: ["area"] },
      { titulo: "Fecha", campos: ["fecha", "fecha_ingreso", "fecha_rol"] },
      { titulo: "Sueldo", campos: ["sueldo", "sueldo_base"], tipo: "dinero" },
      { titulo: "Ingresos", campos: ["total_ingresos", "ingresos"], tipo: "dinero" },
      { titulo: "Descuentos", campos: ["total_descuentos", "descuentos"], tipo: "dinero" },
      { titulo: "Neto pagar", campos: ["neto_pagar", "total_pagar"], tipo: "dinero" },
      { titulo: "Estado", campos: ["estado", "estado_empleado"] }
    ]
  },

  auditoria: {
    titulo: "Reporte de auditoría por usuario y perfil",
    endpoint: "/api/reportes/auditoria",
    tipoRespuesta: "lista",
    columnas: [
      { titulo: "Fecha", campos: ["fecha_accion", "fecha"] },
      { titulo: "Hora", campos: ["hora_accion", "hora"] },
      { titulo: "Usuario", campos: ["usuario", "nombre_usuario", "usuario_accion"] },
      { titulo: "Perfil", campos: ["perfil", "nombre_perfil"] },
      { titulo: "Módulo", campos: ["modulo", "nombre_modulo"] },
      { titulo: "Acción", campos: ["accion", "tipo_accion"] },
      { titulo: "Descripción", campos: ["descripcion", "detalle", "observacion"] },
      { titulo: "Tabla afectada", campos: ["tabla_afectada", "tabla"] },
      { titulo: "IP", campos: ["ip_equipo", "ip"] }
    ]
  },

  activos: {
    titulo: "Reporte de activos y mantenimientos",
    endpoint: "/api/reportes/activos",
    tipoRespuesta: "lista",
    columnas: [
      { titulo: "Activo", campos: ["nombre_activo", "activo", "descripcion_activo"] },
      { titulo: "Tipo", campos: ["tipo_activo", "tipo"] },
      { titulo: "Código", campos: ["codigo_activo", "codigo"] },
      { titulo: "Fecha", campos: ["fecha_compra", "fecha_adquisicion", "fecha_mantenimiento"] },
      { titulo: "Valor", campos: ["valor_adquisicion", "costo_adquisicion", "valor"], tipo: "dinero" },
      { titulo: "Mantenimiento", campos: ["tipo_mantenimiento", "descripcion_mantenimiento"] },
      { titulo: "Costo mantenimiento", campos: ["costo_mantenimiento"], tipo: "dinero" },
      { titulo: "Estado", campos: ["estado", "estado_activo"] }
    ]
  }
};

/* ---------------------------------------------------- */
/* RENDERIZADO DEL REPORTE FILTRADO                     */
/* ---------------------------------------------------- */

function renderizarCabeceraReporte(columnas) {
  const tablaHead = document.getElementById("tablaReporteFiltradoHead");

  if (!tablaHead) {
    return;
  }

  tablaHead.innerHTML = `
    <tr>
      ${columnas.map((columna) => `<th>${textoSeguro(columna.titulo)}</th>`).join("")}
    </tr>
  `;
}

function renderizarCuerpoReporte(datos, columnas) {
  const tablaBody = document.getElementById("tablaReporteFiltradoBody");

  if (!tablaBody) {
    return;
  }

  if (!datos || datos.length === 0) {
    tablaBody.innerHTML = `
      <tr>
        <td colspan="${columnas.length}" class="text-center">
          No existen datos para los filtros seleccionados.
        </td>
      </tr>
    `;
    return;
  }

  tablaBody.innerHTML = "";

  datos.forEach((item) => {
    const fila = document.createElement("tr");

    fila.innerHTML = columnas
      .map((columna) => {
        const valor = obtenerValor(item, columna.campos);
        return `<td>${formatearValorTabla(valor, columna.tipo)}</td>`;
      })
      .join("");

    tablaBody.appendChild(fila);
  });
}

function mostrarMensajeReporte(tipo, mensaje) {
  const contenedor = document.getElementById("mensajeReporteFiltrado");

  if (!contenedor) {
    return;
  }

  if (!mensaje) {
    contenedor.innerHTML = "";
    return;
  }

  contenedor.innerHTML = `
    <div class="alert alert-${tipo} mb-0">
      ${textoSeguro(mensaje)}
    </div>
  `;
}

function filtrarDatosReporte(datos, modulo, fechaDesde, fechaHasta, usuarioFiltro, perfilFiltro) {
  return datos.filter((item) => {
    return (
      cumpleFiltroFecha(item, modulo, fechaDesde, fechaHasta) &&
      cumpleFiltroUsuario(item, usuarioFiltro) &&
      cumpleFiltroPerfil(item, perfilFiltro)
    );
  });
}

async function consultarReporteFiltrado() {
  const filtroModulo = document.getElementById("filtroModuloReporte");
  const filtroFechaDesde = document.getElementById("filtroFechaDesdeReporte");
  const filtroFechaHasta = document.getElementById("filtroFechaHastaReporte");
  const filtroUsuario = document.getElementById("filtroUsuarioReporte");
  const filtroPerfil = document.getElementById("filtroPerfilReporte");
  const tituloReporte = document.getElementById("tituloReporteFiltrado");

  if (!filtroModulo) {
    return;
  }

  const modulo = filtroModulo.value || "general";
  const fechaDesde = filtroFechaDesde ? filtroFechaDesde.value : "";
  const fechaHasta = filtroFechaHasta ? filtroFechaHasta.value : "";
  const usuarioFiltro = filtroUsuario ? filtroUsuario.value.trim() : "";
  const perfilFiltro = filtroPerfil ? filtroPerfil.value : "";

  if (fechaDesde && fechaHasta && fechaDesde > fechaHasta) {
    mostrarMensajeReporte("warning", "La fecha desde no puede ser mayor que la fecha hasta.");
    return;
  }

  const configuracion = configuracionReportes[modulo];

  if (!configuracion) {
    mostrarMensajeReporte("danger", "No existe configuración para el módulo seleccionado.");
    return;
  }

  if (tituloReporte) {
    tituloReporte.textContent = configuracion.titulo;
  }

  renderizarCabeceraReporte(configuracion.columnas);

  const tablaBody = document.getElementById("tablaReporteFiltradoBody");

  if (tablaBody) {
    tablaBody.innerHTML = `
      <tr>
        <td colspan="${configuracion.columnas.length}" class="text-center">
          Consultando datos reales desde PostgreSQL...
        </td>
      </tr>
    `;
  }

  mostrarMensajeReporte("", "");

  try {
    const respuesta = await window.apiGet(configuracion.endpoint);

    let datos = [];

    if (configuracion.tipoRespuesta === "objeto") {
      datos = respuesta ? [respuesta] : [];
    } else {
      datos = Array.isArray(respuesta) ? respuesta : [];
    }

    const datosFiltrados = filtrarDatosReporte(
      datos,
      modulo,
      fechaDesde,
      fechaHasta,
      usuarioFiltro,
      perfilFiltro
    );

    renderizarCuerpoReporte(datosFiltrados, configuracion.columnas);

    let mensaje = `Reporte generado correctamente. Registros encontrados: ${datosFiltrados.length}.`;

    if (perfilFiltro && modulo !== "auditoria") {
      mensaje += " Nota: el filtro por perfil se aplica cuando el reporte trae información de perfil desde el backend.";
    }

    mostrarMensajeReporte("success", mensaje);

  } catch (error) {
    renderizarCuerpoReporte([], configuracion.columnas);
    mostrarMensajeReporte("danger", `Error al consultar el reporte: ${error.message}`);
  }
}

function limpiarReporteFiltrado() {
  const filtroModulo = document.getElementById("filtroModuloReporte");
  const filtroFechaDesde = document.getElementById("filtroFechaDesdeReporte");
  const filtroFechaHasta = document.getElementById("filtroFechaHastaReporte");
  const filtroUsuario = document.getElementById("filtroUsuarioReporte");
  const filtroPerfil = document.getElementById("filtroPerfilReporte");
  const tituloReporte = document.getElementById("tituloReporteFiltrado");

  if (filtroModulo) filtroModulo.value = "general";
  if (filtroFechaDesde) filtroFechaDesde.value = "";
  if (filtroFechaHasta) filtroFechaHasta.value = "";
  if (filtroUsuario) filtroUsuario.value = "";
  if (filtroPerfil) filtroPerfil.value = "";

  if (tituloReporte) {
    tituloReporte.textContent = "Resultado del reporte";
  }

  const tablaHead = document.getElementById("tablaReporteFiltradoHead");
  const tablaBody = document.getElementById("tablaReporteFiltradoBody");

  if (tablaHead) {
    tablaHead.innerHTML = `
      <tr>
        <th>Seleccione un módulo y consulte el reporte</th>
      </tr>
    `;
  }

  if (tablaBody) {
    tablaBody.innerHTML = `
      <tr>
        <td class="text-center">
          No se ha consultado ningún reporte filtrado.
        </td>
      </tr>
    `;
  }

  mostrarMensajeReporte("", "");
}

function imprimirReporteFiltrado() {
  const titulo = document.getElementById("tituloReporteFiltrado");
  const tablaHead = document.getElementById("tablaReporteFiltradoHead");
  const tablaBody = document.getElementById("tablaReporteFiltradoBody");
  const mensaje = document.getElementById("mensajeReporteFiltrado");

  if (!tablaHead || !tablaBody) {
    window.print();
    return;
  }

  const ventana = window.open("", "_blank");

  if (!ventana) {
    window.print();
    return;
  }

  ventana.document.write(`
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="UTF-8">
        <title>Reporte filtrado - ERP Piladora Don Guillo</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            margin: 30px;
            color: #111;
          }

          h1 {
            color: #0b7a34;
            margin-bottom: 5px;
          }

          h2 {
            margin-top: 20px;
            color: #0b7a34;
          }

          p {
            margin: 4px 0;
          }

          table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 12px;
          }

          th {
            background: #d8eadf;
            color: #111;
          }

          th, td {
            border: 1px solid #777;
            padding: 6px;
            text-align: left;
          }

          .encabezado {
            border-bottom: 2px solid #0b7a34;
            padding-bottom: 10px;
            margin-bottom: 15px;
          }

          .mensaje {
            margin-top: 10px;
            font-size: 12px;
          }

          @media print {
            button {
              display: none;
            }
          }
        </style>
      </head>
      <body>
        <div class="encabezado">
          <h1>ERP Piladora Don Guillo</h1>
          <p><strong>Módulo:</strong> Reportes e Inteligencia Artificial</p>
          <p><strong>Fecha de impresión:</strong> ${new Date().toLocaleString()}</p>
        </div>

        <h2>${textoSeguro(titulo ? titulo.textContent : "Reporte filtrado")}</h2>

        <div class="mensaje">
          ${mensaje ? mensaje.innerHTML : ""}
        </div>

        <table>
          <thead>
            ${tablaHead.innerHTML}
          </thead>
          <tbody>
            ${tablaBody.innerHTML}
          </tbody>
        </table>

        <script>
          window.onload = function () {
            window.print();
          };
        </script>
      </body>
    </html>
  `);

  ventana.document.close();
}

/* ---------------------------------------------------- */
/* EVENTOS DEL GENERADOR DE REPORTES FILTRADOS          */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", function () {
  const btnConsultar = document.getElementById("btnConsultarReporteFiltrado");
  const btnLimpiar = document.getElementById("btnLimpiarReporteFiltrado");
  const btnImprimir = document.getElementById("btnImprimirReporteFiltrado");

  if (btnConsultar) {
    btnConsultar.addEventListener("click", consultarReporteFiltrado);
  }

  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", limpiarReporteFiltrado);
  }

  if (btnImprimir) {
    btnImprimir.addEventListener("click", imprimirReporteFiltrado);
  }
});

/* ---------------------------------------------------- */
/* RESUMEN GERENCIAL Y TARJETAS                         */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  const tablaResumenGerencial = document.getElementById("tablaResumenGerencial");
  const reporteTotalCompras = document.getElementById("reporteTotalCompras");
  const reporteMontoVentas = document.getElementById("reporteMontoVentas");
  const reporteInventarioTotal = document.getElementById("reporteInventarioTotal");
  const reporteRendimiento = document.getElementById("reporteRendimiento");

  if (tablaResumenGerencial) {
    try {
      const resumen = await window.apiGet("/api/reportes/resumen");

      if (reporteTotalCompras) {
        reporteTotalCompras.textContent = resumen.total_compras ?? 0;
      }

      if (reporteMontoVentas) {
        reporteMontoVentas.textContent = formatearDinero(resumen.monto_total_ventas);
      }

      if (reporteInventarioTotal) {
        reporteInventarioTotal.textContent = formatearCantidad(resumen.cantidad_total_inventario);
      }

      if (reporteRendimiento) {
        reporteRendimiento.textContent = formatearPorcentaje(resumen.rendimiento_promedio);
      }

      tablaResumenGerencial.innerHTML = `
        <tr>
          <td>${resumen.total_compras ?? 0}</td>
          <td>${formatearDinero(resumen.monto_total_compras)}</td>
          <td>${resumen.total_ventas ?? 0}</td>
          <td>${formatearDinero(resumen.monto_total_ventas)}</td>
          <td>${formatearCantidad(resumen.cantidad_total_inventario)}</td>
          <td>${resumen.total_empleados ?? 0}</td>
          <td>${resumen.total_activos ?? 0}</td>
          <td>${formatearPorcentaje(resumen.rendimiento_promedio)}</td>
        </tr>
      `;

    } catch (error) {
      tablaResumenGerencial.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-danger">
            Error al cargar resumen gerencial: ${error.message}
          </td>
        </tr>
      `;
    }
  }
});

/* ---------------------------------------------------- */
/* VENTAS POR PRODUCTO                                  */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  const tablaVentasProducto = document.getElementById("tablaVentasProducto");

  if (tablaVentasProducto) {
    try {
      const ventasProducto = await window.apiGet("/api/reportes/ventas-producto");

      if (!ventasProducto || ventasProducto.length === 0) {
        tablaVentasProducto.innerHTML = `
          <tr>
            <td colspan="4" class="text-center">No existen ventas por producto.</td>
          </tr>
        `;
        return;
      }

      tablaVentasProducto.innerHTML = "";

      ventasProducto.forEach((item) => {
        const fila = document.createElement("tr");

        fila.innerHTML = `
          <td>${textoSeguro(item.nombre_producto || item.producto || "-")}</td>
          <td>${textoSeguro(item.codigo_producto || item.codigo || item.tipo_producto || "-")}</td>
          <td>${formatearCantidad(item.cantidad_vendida)}</td>
          <td>${formatearDinero(item.total_vendido)}</td>
        `;

        tablaVentasProducto.appendChild(fila);
      });

    } catch (error) {
      tablaVentasProducto.innerHTML = `
        <tr>
          <td colspan="4" class="text-center text-danger">
            Error al cargar ventas por producto: ${error.message}
          </td>
        </tr>
      `;
    }
  }
});

/* ---------------------------------------------------- */
/* STOCK BAJO                                           */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  const tablaStockBajo = document.getElementById("tablaStockBajo");

  if (tablaStockBajo) {
    try {
      const stockBajo = await window.apiGet("/api/reportes/stock-bajo");

      if (!stockBajo || stockBajo.length === 0) {
        tablaStockBajo.innerHTML = `
          <tr>
            <td colspan="7" class="text-center">No existen productos con stock bajo.</td>
          </tr>
        `;
        return;
      }

      tablaStockBajo.innerHTML = "";

      stockBajo.forEach((item) => {
        const fila = document.createElement("tr");

        fila.innerHTML = `
          <td>${textoSeguro(item.producto || item.nombre_producto || "-")}</td>
          <td>${textoSeguro(item.tipo_producto || "-")}</td>
          <td>${textoSeguro(item.bodega || item.nombre_bodega || "-")}</td>
          <td>${textoSeguro(item.lote || "-")}</td>
          <td>${formatearCantidad(item.cantidad_disponible)}</td>
          <td>${formatearCantidad(item.stock_minimo)}</td>
          <td>${textoSeguro(item.estado_stock || "-")}</td>
        `;

        tablaStockBajo.appendChild(fila);
      });

    } catch (error) {
      tablaStockBajo.innerHTML = `
        <tr>
          <td colspan="7" class="text-center text-danger">
            Error al cargar stock bajo: ${error.message}
          </td>
        </tr>
      `;
    }
  }
});

/* ---------------------------------------------------- */
/* RECOMENDACIONES IA GUARDADAS                         */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  const tablaRecomendacionesIA = document.getElementById("tablaRecomendacionesIA");

  if (tablaRecomendacionesIA) {
    try {
      const recomendaciones = await window.apiGet("/api/reportes/ia-guardadas");

      if (!recomendaciones || recomendaciones.length === 0) {
        tablaRecomendacionesIA.innerHTML = `
          <tr>
            <td colspan="6" class="text-center">No existen recomendaciones de IA guardadas.</td>
          </tr>
        `;
        return;
      }

      tablaRecomendacionesIA.innerHTML = "";

      recomendaciones.forEach((item) => {
        const fila = document.createElement("tr");

        fila.innerHTML = `
          <td>${textoSeguro(item.area || "-")}</td>
          <td>${textoSeguro(item.tipo_analisis || "-")}</td>
          <td>${textoSeguro(item.recomendacion || "-")}</td>
          <td>${textoSeguro(item.nivel_importancia || "-")}</td>
          <td>${textoSeguro(item.estado_recomendacion || "-")}</td>
          <td>${textoSeguro(item.fecha_recomendacion || "-")}</td>
        `;

        tablaRecomendacionesIA.appendChild(fila);
      });

    } catch (error) {
      tablaRecomendacionesIA.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-danger">
            Error al cargar recomendaciones de IA: ${error.message}
          </td>
        </tr>
      `;
    }
  }
});

/* ---------------------------------------------------- */
/* GRÁFICOS CON DATOS REALES DESDE POSTGRESQL            */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", async function () {
  if (typeof Chart === "undefined") {
    return;
  }

  const graficoComprasVentas = document.getElementById("graficoComprasVentas");
  const graficoProduccion = document.getElementById("graficoProduccion");
  const graficoInventario = document.getElementById("graficoInventario");
  const graficoVentasProducto = document.getElementById("graficoVentasProducto");

  if (
    !graficoComprasVentas &&
    !graficoProduccion &&
    !graficoInventario &&
    !graficoVentasProducto
  ) {
    return;
  }

  try {
    const compras = await window.apiGet("/api/reportes/compras");
    const ventas = await window.apiGet("/api/reportes/ventas");
    const inventario = await window.apiGet("/api/reportes/inventario");
    const produccion = await window.apiGet("/api/reportes/produccion");
    const ventasProducto = await window.apiGet("/api/reportes/ventas-producto");

    if (graficoComprasVentas) {
      const comprasPorMes = agruparPorMes(compras || [], "fecha_compra", "total_compra");
      const ventasPorMes = agruparPorMes(ventas || [], "fecha_venta", "total_linea");

      const meses = Array.from(
        new Set([
          ...comprasPorMes.map((item) => item.mes),
          ...ventasPorMes.map((item) => item.mes)
        ])
      );

      const datosCompras = meses.map((mes) => {
        const encontrado = comprasPorMes.find((item) => item.mes === mes);
        return encontrado ? encontrado.valor : 0;
      });

      const datosVentas = meses.map((mes) => {
        const encontrado = ventasPorMes.find((item) => item.mes === mes);
        return encontrado ? encontrado.valor : 0;
      });

      limpiarGrafico("comprasVentas");

      window.graficosReportes.comprasVentas = new Chart(graficoComprasVentas, {
        type: "bar",
        data: {
          labels: meses.length > 0 ? meses : ["Sin datos"],
          datasets: [
            {
              label: "Compras $",
              data: datosCompras.length > 0 ? datosCompras : [0],
              backgroundColor: "rgba(25, 135, 84, 0.7)"
            },
            {
              label: "Ventas $",
              data: datosVentas.length > 0 ? datosVentas : [0],
              backgroundColor: "rgba(13, 110, 253, 0.7)"
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "bottom"
            }
          }
        }
      });
    }

    if (graficoProduccion) {
      let arrozPilado = 0;
      let arrocillo = 0;
      let polvillo = 0;
      let cascarilla = 0;
      let tamo = 0;
      let merma = 0;

      (produccion || []).forEach((item) => {
        arrozPilado += Number(item.arroz_pilado_obtenido || 0);
        arrocillo += Number(item.arrocillo_obtenido || 0);
        polvillo += Number(item.polvillo_obtenido || 0);
        cascarilla += Number(item.cascarilla_obtenida || 0);
        tamo += Number(item.tamo_obtenido || 0);
        merma += Number(item.merma || 0);
      });

      limpiarGrafico("produccion");

      window.graficosReportes.produccion = new Chart(graficoProduccion, {
        type: "doughnut",
        data: {
          labels: ["Arroz pilado", "Arrocillo", "Polvillo", "Cascarilla", "Tamo", "Merma"],
          datasets: [
            {
              data: [arrozPilado, arrocillo, polvillo, cascarilla, tamo, merma],
              backgroundColor: [
                "#198754",
                "#20c997",
                "#ffc107",
                "#6c757d",
                "#0dcaf0",
                "#dc3545"
              ]
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "bottom"
            }
          }
        }
      });
    }

    if (graficoInventario) {
      const inventarioAgrupado = agruparInventarioPorProducto(inventario || []);

      limpiarGrafico("inventario");

      window.graficosReportes.inventario = new Chart(graficoInventario, {
        type: "bar",
        data: {
          labels: inventarioAgrupado.length > 0
            ? inventarioAgrupado.map((item) => item.producto)
            : ["Sin datos"],
          datasets: [
            {
              label: "Stock disponible qq",
              data: inventarioAgrupado.length > 0
                ? inventarioAgrupado.map((item) => item.cantidad)
                : [0],
              backgroundColor: "rgba(25, 135, 84, 0.7)"
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "bottom"
            }
          }
        }
      });
    }

    if (graficoVentasProducto) {
      limpiarGrafico("ventasProducto");

      window.graficosReportes.ventasProducto = new Chart(graficoVentasProducto, {
        type: "pie",
        data: {
          labels: ventasProducto && ventasProducto.length > 0
            ? ventasProducto.map((item) => item.nombre_producto || item.producto || "Sin producto")
            : ["Sin datos"],
          datasets: [
            {
              data: ventasProducto && ventasProducto.length > 0
                ? ventasProducto.map((item) => Number(item.total_vendido || 0))
                : [0],
              backgroundColor: [
                "#198754",
                "#ffc107",
                "#20c997",
                "#6c757d",
                "#0dcaf0",
                "#dc3545",
                "#6610f2",
                "#fd7e14"
              ]
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "bottom"
            }
          }
        }
      });
    }

  } catch (error) {
    console.error("Error al cargar gráficos de reportes:", error);
  }
});

/* ---------------------------------------------------- */
/* ANÁLISIS AUTOMÁTICO GERENCIAL                        */
/* NOTA: ESTO AÚN NO ES API EXTERNA DE IA REAL           */
/* LA IA REAL SE CONECTARÁ DESPUÉS DESDE EL BACKEND      */
/* ---------------------------------------------------- */

document.addEventListener("DOMContentLoaded", function () {
  const btnAnalizarIA = document.getElementById("btnAnalizarIA");
  const resultadoIA = document.getElementById("resultadoIA");

  if (!btnAnalizarIA || !resultadoIA) {
    return;
  }

  btnAnalizarIA.addEventListener("click", async function () {
    resultadoIA.innerHTML = `
      <div class="alert alert-info">
        Analizando datos reales del ERP, espere un momento...
      </div>
    `;

    try {
      const resumen = await window.apiGet("/api/reportes/resumen");
      const stockBajo = await window.apiGet("/api/reportes/stock-bajo");
      const ventasProducto = await window.apiGet("/api/reportes/ventas-producto");
      const produccion = await window.apiGet("/api/reportes/produccion");

      const recomendaciones = [];

      const rendimientoPromedio = Number(resumen.rendimiento_promedio || 0);
      const totalVentas = Number(resumen.monto_total_ventas || 0);
      const totalCompras = Number(resumen.monto_total_compras || 0);
      const inventarioTotal = Number(resumen.cantidad_total_inventario || 0);

      if (stockBajo && stockBajo.length > 0) {
        recomendaciones.push({
          tipo: "Inventario",
          mensaje:
            "Existen productos con stock bajo. Se recomienda revisar reposición, producción o compras para evitar falta de disponibilidad."
        });
      }

      if (rendimientoPromedio > 0 && rendimientoPromedio < 65) {
        recomendaciones.push({
          tipo: "Producción",
          mensaje:
            "El rendimiento promedio de pilado es menor al 65%. Se recomienda revisar humedad del arroz, calidad de materia prima y estado de maquinaria."
        });
      }

      if (rendimientoPromedio >= 65) {
        recomendaciones.push({
          tipo: "Producción",
          mensaje:
            "El rendimiento promedio de pilado se mantiene en un nivel aceptable. Se recomienda continuar controlando merma, calidad y subproductos."
        });
      }

      if (totalCompras > 0 && totalVentas < totalCompras) {
        recomendaciones.push({
          tipo: "Finanzas",
          mensaje:
            "El monto total de compras es mayor que el monto total de ventas registrado. Se recomienda revisar rotación de inventario y ventas pendientes."
        });
      }

      if (inventarioTotal > 0 && totalVentas === 0) {
        recomendaciones.push({
          tipo: "Ventas",
          mensaje:
            "Existe inventario disponible, pero no se registran ingresos por ventas. Se recomienda revisar comercialización de arroz pilado y subproductos."
        });
      }

      if (ventasProducto && ventasProducto.length > 0) {
        const productoMayorVenta = ventasProducto.reduce((mayor, item) => {
          return Number(item.total_vendido || 0) > Number(mayor.total_vendido || 0)
            ? item
            : mayor;
        }, ventasProducto[0]);

        recomendaciones.push({
          tipo: "Ventas por producto",
          mensaje:
            "El producto con mayor venta registrada es " +
            (productoMayorVenta.nombre_producto || productoMayorVenta.producto || "sin nombre") +
            " con un total vendido de " +
            formatearDinero(productoMayorVenta.total_vendido) +
            "."
        });
      }

      if (produccion && produccion.length === 0) {
        recomendaciones.push({
          tipo: "Producción",
          mensaje:
            "No existen registros de producción. Se recomienda registrar órdenes de pilado para alimentar los reportes gerenciales."
        });
      }

      if (recomendaciones.length === 0) {
        recomendaciones.push({
          tipo: "General",
          mensaje:
            "Los datos generales del ERP se encuentran estables. Se recomienda mantener el control de compras, producción, inventario y ventas."
        });
      }

      let html = `
        <div class="alert alert-success">
          <h5 class="fw-bold">Resultado del análisis gerencial</h5>
          <p class="mb-0">
            El sistema generó recomendaciones utilizando datos reales de PostgreSQL.
            La conexión con IA real por API se realizará en el siguiente paso.
          </p>
        </div>
      `;

      recomendaciones.forEach((recomendacion) => {
        html += `
          <div class="card border-success mb-3">
            <div class="card-body">
              <h6 class="fw-bold text-success">${textoSeguro(recomendacion.tipo)}</h6>
              <p class="mb-0">${textoSeguro(recomendacion.mensaje)}</p>
            </div>
          </div>
        `;
      });

      resultadoIA.innerHTML = html;

    } catch (error) {
      resultadoIA.innerHTML = `
        <div class="alert alert-danger">
          Error al generar análisis gerencial: ${error.message}
        </div>
      `;
    }
  });
});





/* ---------------------------------------------------- */
/* IA REAL CONECTADA AL BACKEND FASTAPI                 */
/* ERP PILADORA DON GUILLO                              */
/* ---------------------------------------------------- */

function obtenerSesionParaIA() {
  const usuarioTexto = document.getElementById("usuarioActual")
    ? document.getElementById("usuarioActual").textContent.trim()
    : "";

  const perfilTexto = document.getElementById("perfilActual")
    ? document.getElementById("perfilActual").textContent.trim()
    : "";

  let usuario = usuarioTexto && usuarioTexto !== "Usuario" ? usuarioTexto : "";
  let perfil = perfilTexto && perfilTexto !== "Perfil" ? perfilTexto : "";

  const posiblesClaves = [
    "usuario",
    "usuarioActual",
    "sesionUsuario",
    "erp_usuario",
    "datosUsuario"
  ];

  posiblesClaves.forEach((clave) => {
    try {
      const valor = localStorage.getItem(clave);

      if (!valor) {
        return;
      }

      const objeto = JSON.parse(valor);

      if (!usuario) {
        usuario =
          objeto.usuario ||
          objeto.nombre_usuario ||
          objeto.nombres ||
          objeto.nombre ||
          "";
      }

      if (!perfil) {
        perfil =
          objeto.perfil ||
          objeto.nombre_perfil ||
          objeto.rol ||
          objeto.tipo_usuario ||
          "";
      }

    } catch (error) {
      const valorPlano = localStorage.getItem(clave);

      if (!usuario && valorPlano) {
        usuario = valorPlano;
      }
    }
  });

  return {
    usuario: usuario || "Usuario no identificado",
    perfil: perfil || "Sin perfil"
  };
}

function convertirRespuestaIAMarkdownSimple(texto) {
  const contenidoSeguro = textoSeguro(texto || "");

  return contenidoSeguro
    .replace(/\n### (.*?)\n/g, "<h5 class='text-success fw-bold mt-3'>$1</h5>")
    .replace(/\n## (.*?)\n/g, "<h5 class='text-success fw-bold mt-3'>$1</h5>")
    .replace(/\n# (.*?)\n/g, "<h5 class='text-success fw-bold mt-3'>$1</h5>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n- /g, "<br>• ")
    .replace(/\n/g, "<br>");
}

async function consultarIAReal() {
  const preguntaIA = document.getElementById("preguntaIA");
  const resultadoIA = document.getElementById("resultadoIA");
  const btnConsultarIA = document.getElementById("btnConsultarIA");

  if (!preguntaIA || !resultadoIA) {
    return;
  }

  const pregunta = preguntaIA.value.trim();

  if (!pregunta) {
    resultadoIA.innerHTML = `
      <div class="alert alert-warning">
        Escriba una pregunta para consultar la IA.
      </div>
    `;
    return;
  }

  const sesion = obtenerSesionParaIA();

  if (
    normalizarTexto(sesion.perfil) !== "administrador" &&
    normalizarTexto(sesion.perfil) !== "gerente"
  ) {
    resultadoIA.innerHTML = `
      <div class="alert alert-danger">
        Acceso denegado. La IA solo está disponible para Administrador y Gerente.
      </div>
    `;
    return;
  }

  resultadoIA.innerHTML = `
    <div class="alert alert-info">
      Consultando IA real desde FastAPI y analizando datos de PostgreSQL...
    </div>
  `;

  if (btnConsultarIA) {
    btnConsultarIA.disabled = true;
    btnConsultarIA.textContent = "Consultando...";
  }

  try {
    const respuesta = await fetch("https://erp-piladora-don-guillo.onrender.com/api/ia/consultar", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        pregunta: pregunta,
        usuario: sesion.usuario,
        perfil: sesion.perfil
      })
    });

    const datos = await respuesta.json();

    if (!respuesta.ok) {
      throw new Error(datos.detail || "No se pudo consultar la IA.");
    }

    const respuestaIA = datos.respuesta || "La IA no devolvió respuesta.";
    ultimaConsultaIA = {
  pregunta: pregunta,
  respuesta: respuestaIA,
  proveedor: datos.proveedor || "IA",
  modelo: datos.modelo || "-"
};

    let claseAlerta = "success";

    if (datos.estado === "bloqueado") {
      claseAlerta = "warning";
    }

    if (datos.estado === "error") {
      claseAlerta = "danger";
    }
    activarBotonGuardarIA(datos.estado === "ok");
mostrarMensajeGuardarIA("", "");

    resultadoIA.innerHTML = `
      <div class="alert alert-${claseAlerta}">
        <h5 class="fw-bold mb-2">Respuesta de IA Gerencial</h5>
        <p class="mb-1">
          <strong>Proveedor:</strong> ${textoSeguro(datos.proveedor || "IA")}
        </p>
        <p class="mb-0">
          <strong>Modelo:</strong> ${textoSeguro(datos.modelo || "-")}
        </p>
      </div>

      <div class="card border-success">
        <div class="card-body">
          ${convertirRespuestaIAMarkdownSimple(respuestaIA)}
        </div>
      </div>
    `;

  } catch (error) {
    resultadoIA.innerHTML = `
      <div class="alert alert-danger">
        Error al consultar la IA real: ${textoSeguro(error.message)}
      </div>
    `;

  } finally {
    if (btnConsultarIA) {
      btnConsultarIA.disabled = false;
      btnConsultarIA.textContent = "Consultar IA real";
    }
  }
}

function limpiarIAReal() {
  const preguntaIA = document.getElementById("preguntaIA");
  const resultadoIA = document.getElementById("resultadoIA");

  if (preguntaIA) {
    preguntaIA.value = "";
  }

  if (resultadoIA) {
    resultadoIA.innerHTML = "";
  }

  ultimaConsultaIA = {
    pregunta: "",
    respuesta: "",
    proveedor: "",
    modelo: ""
  };

  activarBotonGuardarIA(false);
  mostrarMensajeGuardarIA("", "");
}

document.addEventListener("DOMContentLoaded", function () {
  const btnConsultarIA = document.getElementById("btnConsultarIA");
  const btnLimpiarIA = document.getElementById("btnLimpiarIA");
  const preguntaIA = document.getElementById("preguntaIA");

  if (btnConsultarIA) {
    btnConsultarIA.addEventListener("click", consultarIAReal);
  }

  if (btnLimpiarIA) {
    btnLimpiarIA.addEventListener("click", limpiarIAReal);
  }

  if (preguntaIA) {
    preguntaIA.addEventListener("keydown", function (evento) {
      if (evento.ctrlKey && evento.key === "Enter") {
        consultarIAReal();
      }
    });
  }
});


/* ---------------------------------------------------- */
/* HISTORIAL E IMPRESIÓN DE REPORTE IA REAL             */
/* ERP PILADORA DON GUILLO                              */
/* ---------------------------------------------------- */

let ultimaConsultaIA = {
  pregunta: "",
  respuesta: "",
  proveedor: "",
  modelo: ""
};

function mostrarMensajeGuardarIA(tipo, mensaje) {
  const contenedor = document.getElementById("mensajeGuardarIA");

  if (!contenedor) {
    return;
  }

  if (!mensaje) {
    contenedor.innerHTML = "";
    return;
  }

  contenedor.innerHTML = `
    <div class="alert alert-${tipo} mb-0">
      ${textoSeguro(mensaje)}
    </div>
  `;
}

function activarBotonGuardarIA(activar) {
  const btnGuardar = document.getElementById("btnGuardarHistorialIA");

  if (btnGuardar) {
    btnGuardar.disabled = !activar;
  }
}

async function cargarHistorialIA() {
  const tablaRecomendacionesIA = document.getElementById("tablaRecomendacionesIA");

  if (!tablaRecomendacionesIA) {
    return;
  }

  try {
    const recomendaciones = await window.apiGet("/api/reportes/ia-guardadas");

    if (!recomendaciones || recomendaciones.length === 0) {
      tablaRecomendacionesIA.innerHTML = `
        <tr>
          <td colspan="6" class="text-center">
            No existen recomendaciones de IA guardadas.
          </td>
        </tr>
      `;
      return;
    }

    tablaRecomendacionesIA.innerHTML = "";

    recomendaciones.forEach((item) => {
      const fila = document.createElement("tr");

      fila.innerHTML = `
        <td>${textoSeguro(item.area || "-")}</td>
        <td>${textoSeguro(item.tipo_analisis || "-")}</td>
        <td>${textoSeguro(item.recomendacion || "-")}</td>
        <td>${textoSeguro(item.nivel_importancia || "-")}</td>
        <td>${textoSeguro(item.estado_recomendacion || "-")}</td>
        <td>${textoSeguro(item.fecha_recomendacion || "-")}</td>
      `;

      tablaRecomendacionesIA.appendChild(fila);
    });

  } catch (error) {
    tablaRecomendacionesIA.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-danger">
          Error al cargar historial IA: ${textoSeguro(error.message)}
        </td>
      </tr>
    `;
  }
}

async function guardarHistorialIA() {
  const areaIA = document.getElementById("areaIA");
  const tipoAnalisisIA = document.getElementById("tipoAnalisisIA");
  const importanciaIA = document.getElementById("importanciaIA");
  const btnGuardar = document.getElementById("btnGuardarHistorialIA");

  if (!ultimaConsultaIA.respuesta) {
    mostrarMensajeGuardarIA("warning", "No existe una respuesta de IA para guardar.");
    return;
  }

  const sesion = obtenerSesionParaIA();

  if (
    normalizarTexto(sesion.perfil) !== "administrador" &&
    normalizarTexto(sesion.perfil) !== "gerente"
  ) {
    mostrarMensajeGuardarIA(
      "danger",
      "Solo Administrador y Gerente pueden guardar recomendaciones IA."
    );
    return;
  }

  try {
    if (btnGuardar) {
      btnGuardar.disabled = true;
      btnGuardar.textContent = "Guardando...";
    }

    mostrarMensajeGuardarIA("info", "Guardando recomendación en historial IA...");

    const respuesta = await fetch("https://erp-piladora-don-guillo.onrender.com/api/ia/guardar-recomendacion", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        area: areaIA ? areaIA.value : "Gerencial",
        tipo_analisis: tipoAnalisisIA ? tipoAnalisisIA.value : "Recomendación gerencial",
        pregunta: ultimaConsultaIA.pregunta,
        recomendacion: ultimaConsultaIA.respuesta,
        nivel_importancia: importanciaIA ? importanciaIA.value : "Media",
        usuario: sesion.usuario,
        perfil: sesion.perfil,
        proveedor: ultimaConsultaIA.proveedor,
        modelo: ultimaConsultaIA.modelo
      })
    });

    const datos = await respuesta.json();

    if (!respuesta.ok) {
      throw new Error(datos.detail || "No se pudo guardar la recomendación IA.");
    }

    mostrarMensajeGuardarIA(
      "success",
      datos.mensaje || "Recomendación IA guardada correctamente en el historial."
    );

    await cargarHistorialIA();

  } catch (error) {
    mostrarMensajeGuardarIA(
      "danger",
      `Error al guardar historial IA: ${textoSeguro(error.message)}`
    );

    activarBotonGuardarIA(true);

  } finally {
    if (btnGuardar) {
      btnGuardar.textContent = "Guardar en historial IA";
    }
  }
}

function imprimirReporteIA() {
  const preguntaIA = document.getElementById("preguntaIA");
  const resultadoIA = document.getElementById("resultadoIA");
  const areaIA = document.getElementById("areaIA");
  const tipoAnalisisIA = document.getElementById("tipoAnalisisIA");
  const importanciaIA = document.getElementById("importanciaIA");

  if (!resultadoIA || !resultadoIA.innerHTML.trim()) {
    alert("Primero consulte la IA para poder imprimir el reporte.");
    return;
  }

  const ventana = window.open("", "_blank");

  if (!ventana) {
    window.print();
    return;
  }

  ventana.document.write(`
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="UTF-8">
        <title>Reporte IA - ERP Piladora Don Guillo</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            margin: 35px;
            color: #111;
          }

          h1 {
            color: #0b7a34;
            margin-bottom: 5px;
          }

          h2 {
            color: #0b7a34;
            margin-top: 25px;
            border-bottom: 2px solid #0b7a34;
            padding-bottom: 6px;
          }

          .encabezado {
            border-bottom: 3px solid #0b7a34;
            margin-bottom: 20px;
            padding-bottom: 12px;
          }

          .bloque {
            border: 1px solid #999;
            padding: 12px;
            margin-top: 12px;
          }

          .respuesta {
            margin-top: 20px;
            line-height: 1.5;
          }

          .nota {
            font-size: 12px;
            margin-top: 25px;
            color: #444;
          }

          .alert {
            border: 1px solid #aaa;
            padding: 10px;
            margin-bottom: 15px;
          }

          @media print {
            button {
              display: none;
            }
          }
        </style>
      </head>
      <body>
        <div class="encabezado">
          <h1>ERP Piladora Don Guillo</h1>
          <p><strong>Módulo:</strong> Reportes e Inteligencia Artificial</p>
          <p><strong>Tipo de documento:</strong> Reporte de análisis generado por IA</p>
          <p><strong>Fecha de impresión:</strong> ${new Date().toLocaleString()}</p>
        </div>

        <h2>Datos del análisis</h2>

        <div class="bloque">
          <p><strong>Área:</strong> ${textoSeguro(areaIA ? areaIA.value : "Gerencial")}</p>
          <p><strong>Tipo de análisis:</strong> ${textoSeguro(tipoAnalisisIA ? tipoAnalisisIA.value : "Recomendación gerencial")}</p>
          <p><strong>Importancia:</strong> ${textoSeguro(importanciaIA ? importanciaIA.value : "Media")}</p>
          <p><strong>Proveedor IA:</strong> ${textoSeguro(ultimaConsultaIA.proveedor || "-")}</p>
          <p><strong>Modelo:</strong> ${textoSeguro(ultimaConsultaIA.modelo || "-")}</p>
        </div>

        <h2>Pregunta realizada</h2>

        <div class="bloque">
          ${textoSeguro(preguntaIA ? preguntaIA.value : ultimaConsultaIA.pregunta)}
        </div>

        <h2>Respuesta y recomendación de IA</h2>

        <div class="respuesta">
          ${resultadoIA.innerHTML}
        </div>

        <p class="nota">
          Este reporte fue generado por el módulo de Inteligencia Artificial del ERP Piladora Don Guillo.
          La IA trabaja en modo solo lectura y utiliza datos reales consultados desde PostgreSQL mediante FastAPI.
        </p>

        <script>
          window.onload = function () {
            window.print();
          };
        </script>
      </body>
    </html>
  `);

  ventana.document.close();
}

document.addEventListener("DOMContentLoaded", function () {
  const btnGuardarHistorialIA = document.getElementById("btnGuardarHistorialIA");
  const btnImprimirIA = document.getElementById("btnImprimirIA");

  if (btnGuardarHistorialIA) {
    btnGuardarHistorialIA.addEventListener("click", guardarHistorialIA);
  }

  if (btnImprimirIA) {
    btnImprimirIA.addEventListener("click", imprimirReporteIA);
  }
});