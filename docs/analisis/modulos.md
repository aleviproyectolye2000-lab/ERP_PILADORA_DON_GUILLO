# Módulos del Sistema ERP - Piladora Don Guillo

## 1. Descripción general de los módulos

El sistema ERP de la Piladora Don Guillo estará dividido en módulos funcionales que representan las principales áreas de trabajo de la empresa. Cada módulo tendrá funciones específicas y estará relacionado con los demás para mantener la información integrada.

La finalidad del ERP es controlar el proceso completo del arroz, desde la compra del arroz en cáscara hasta el pilado, almacenamiento, venta del arroz procesado y comercialización de subproductos como polvillo, arrocillo, cascarilla y tamo.

---

## 2. Módulo de Seguridad, Usuarios y Auditoría

Este módulo será el encargado de controlar el acceso al sistema.

### Funciones principales

- Registrar usuarios del sistema.
- Asignar perfiles o roles.
- Permitir inicio de sesión.
- Permitir cierre de sesión.
- Controlar acceso por módulo.
- Registrar fecha y hora de ingreso.
- Registrar fecha y hora de salida.
- Calcular tiempo conectado.
- Registrar acciones realizadas por cada usuario.
- Consultar historial de accesos.
- Consultar auditoría de cambios.

### Usuarios relacionados

- Administrador del sistema.
- Gerente.
- Operadores de cada área.

### Importancia

Este módulo permite garantizar la seguridad del sistema, evitando que un usuario acceda a información o funciones que no le corresponden.

---

## 3. Módulo de Compras, Recepción y Báscula

Este módulo controla el ingreso del arroz en cáscara a la piladora.

### Funciones principales

- Registrar proveedores o agricultores.
- Registrar datos del vehículo.
- Registrar datos del chofer.
- Registrar fecha de ingreso.
- Registrar producto recibido.
- Registrar peso bruto.
- Registrar peso tara.
- Calcular peso neto.
- Registrar humedad.
- Registrar impurezas.
- Registrar precio por quintal.
- Calcular total a pagar.
- Generar comprobante de recepción.
- Enviar la compra al inventario.

### Datos principales

- Proveedor.
- Cédula o RUC.
- Producto.
- Fecha.
- Peso bruto.
- Peso tara.
- Peso neto.
- Humedad.
- Impurezas.
- Precio.
- Total.

### Relación con otros módulos

Este módulo se conecta directamente con inventario, porque cada compra de arroz en cáscara aumenta el stock de materia prima.

---

## 4. Módulo de Inventario y Bodega

Este módulo controla todo el producto almacenado dentro de la piladora.

### Funciones principales

- Registrar productos.
- Consultar stock disponible.
- Controlar arroz en cáscara.
- Controlar arroz pilado.
- Controlar arroz clasificado.
- Controlar arroz corriente.
- Controlar arroz envejecido.
- Controlar arrocillo.
- Controlar polvillo.
- Controlar cascarilla.
- Controlar tamo.
- Controlar stock por lote.
- Controlar stock por bodega.
- Registrar entradas de inventario.
- Registrar salidas de inventario.
- Generar alertas de bajo stock.
- Generar alertas de productos agotados.
- Realizar ajustes autorizados.
- Generar reportes de inventario.

### Productos principales

- Arroz en cáscara.
- Arroz pilado.
- Arroz pilado clasificado.
- Arroz pilado corriente.
- Arroz envejecido.
- Arrocillo.
- Polvillo.
- Cascarilla.
- Tamo.

### Relación con otros módulos

El inventario aumenta cuando se registra una compra, cambia cuando se realiza el pilado y disminuye cuando se registra una venta.

---

## 5. Módulo de Producción y Pilado

Este módulo controla el proceso de transformación del arroz en cáscara en arroz pilado y subproductos.

### Funciones principales

- Crear órdenes de pilado.
- Seleccionar lote de arroz en cáscara.
- Registrar cantidad procesada.
- Registrar fecha del proceso.
- Registrar operador responsable.
- Registrar maquinaria utilizada.
- Registrar arroz pilado obtenido.
- Registrar arrocillo obtenido.
- Registrar polvillo obtenido.
- Registrar cascarilla obtenida.
- Registrar tamo obtenido.
- Registrar merma o pérdida.
- Calcular rendimiento del pilado.
- Actualizar inventario automáticamente.
- Generar reporte de producción.

### Ejemplo del proceso

Si se procesan 100 quintales de arroz en cáscara, el sistema permitirá registrar la cantidad obtenida de:

- Arroz pilado.
- Arrocillo.
- Polvillo.
- Cascarilla.
- Tamo.
- Merma.

### Relación con otros módulos

Este módulo disminuye el inventario de arroz en cáscara y aumenta el inventario de arroz pilado y subproductos.

---

## 6. Módulo de Ventas y Comercialización

Este módulo controla las ventas de arroz procesado y subproductos.

### Funciones principales

- Registrar clientes.
- Registrar datos del cliente.
- Registrar producto vendido.
- Registrar cantidad vendida.
- Registrar precio unitario.
- Calcular subtotal.
- Calcular IVA cuando corresponda.
- Calcular total de venta.
- Registrar forma de pago.
- Registrar estado de pago.
- Generar comprobante de venta.
- Descontar automáticamente del inventario.
- Consultar historial de ventas.
- Generar reporte de ventas.
- Exportar reportes en PDF.
- Exportar reportes en Excel.

### Productos que se pueden vender

- Arroz pilado.
- Arroz pilado clasificado.
- Arroz pilado corriente.
- Arroz envejecido.
- Arrocillo.
- Polvillo.
- Cascarilla.
- Tamo.

### Relación con otros módulos

Este módulo se conecta con inventario, porque cada venta reduce el stock disponible. También alimenta los reportes gerenciales y el análisis de inteligencia artificial.

---

## 7. Módulo de Talento Humano

Este módulo controla la información del personal de la piladora.

### Funciones principales

- Registrar empleados.
- Registrar cargos.
- Registrar áreas de trabajo.
- Registrar sueldo.
- Registrar asistencia.
- Registrar atrasos.
- Registrar faltas.
- Registrar sanciones.
- Registrar horas extras.
- Registrar bonificaciones.
- Generar roles de pago.
- Consultar historial laboral.
- Generar reportes de talento humano.

### Cargos principales

- Gerente.
- Administrador.
- Operador de báscula.
- Operador de piladora.
- Bodeguero.
- Vendedor.
- Chofer.
- Personal de campo.
- Personal de limpieza.
- Guardia.

### Relación con otros módulos

Este módulo permite conocer qué trabajadores participan en los procesos de recepción, producción, ventas y administración.

---

## 8. Módulo de Maquinaria, Vehículos y Activos

Este módulo controla los bienes físicos de la piladora.

### Funciones principales

- Registrar maquinaria.
- Registrar vehículos.
- Registrar báscula.
- Registrar bodegas.
- Registrar terrenos.
- Registrar herramientas.
- Registrar mantenimientos.
- Registrar reparaciones.
- Registrar gasto de combustible.
- Registrar responsable del activo.
- Consultar estado del activo.
- Generar alertas de mantenimiento.
- Generar reportes de maquinaria y vehículos.

### Activos principales

- Piladora.
- Báscula.
- Secadora.
- Motores.
- Bandas transportadoras.
- Camiones.
- Camionetas.
- Terrenos.
- Bodegas.
- Herramientas.

### Relación con otros módulos

Este módulo se relaciona con producción, porque la maquinaria participa en el proceso de pilado. También se relaciona con reportes, debido a los gastos de mantenimiento.

---

## 9. Módulo de Reportes, Gráficos y Panel Gerencial

Este módulo será utilizado principalmente por el gerente o dueño de la piladora.

### Funciones principales

- Consultar compras.
- Consultar ventas.
- Consultar inventario.
- Consultar producción.
- Consultar subproductos.
- Consultar talento humano.
- Consultar maquinaria.
- Visualizar gráficos.
- Visualizar métricas.
- Exportar reportes en PDF.
- Exportar reportes en Excel.
- Acceder al análisis inteligente.

### Reportes principales

- Reporte de compras de arroz en cáscara.
- Reporte de ventas de arroz pilado.
- Reporte de ventas de subproductos.
- Reporte de inventario actual.
- Reporte de producción mensual.
- Reporte de rendimiento de pilado.
- Reporte de productos más vendidos.
- Reporte de stock bajo.
- Reporte de usuarios y auditoría.

### Gráficos principales

- Gráfico de compras mensuales.
- Gráfico de ventas mensuales.
- Gráfico de producción mensual.
- Gráfico de inventario por producto.
- Gráfico de rendimiento por lote.
- Gráfico de ventas por producto.
- Gráfico de subproductos generados.

### Restricción

El gerente solo podrá consultar información. No podrá registrar, modificar ni eliminar datos operativos.

---

## 10. Módulo de Inteligencia Artificial para Toma de Decisiones

Este módulo funcionará como apoyo al panel gerencial.

### Funciones principales

- Analizar compras mensuales.
- Analizar ventas mensuales.
- Analizar inventario disponible.
- Analizar producción.
- Analizar rendimiento del pilado.
- Analizar subproductos acumulados.
- Detectar productos con bajo stock.
- Detectar productos con poca rotación.
- Generar recomendaciones automáticas.

### Ejemplos de recomendaciones

Si las ventas aumentan y el inventario baja:

> Se recomienda aumentar la compra de arroz en cáscara para el próximo mes, debido a que las ventas han incrementado y el stock actual podría no cubrir la demanda.

Si existe demasiado inventario y pocas ventas:

> No se recomienda comprar más arroz en cáscara por el momento, debido a que existe alto inventario y baja rotación de ventas.

Si el rendimiento del pilado disminuye:

> Se recomienda revisar la humedad del arroz recibido y el estado de la maquinaria, debido a que el rendimiento del pilado está por debajo del promedio esperado.

Si existe acumulación de subproductos:

> Se recomienda aplicar estrategias de venta para mejorar la rotación de polvillo, arrocillo, cascarilla y tamo.

### Tipo de inteligencia artificial inicial

En la primera versión, la inteligencia artificial funcionará mediante reglas inteligentes, cálculos, comparaciones mensuales y análisis de tendencias.

A futuro, el sistema podrá integrarse con modelos predictivos o servicios externos de inteligencia artificial.

---

## 11. Módulos principales para el parcial

Para cumplir con el requisito mínimo del proyecto, los módulos principales serán:

1. Seguridad, usuarios y auditoría.
2. Compras, recepción y báscula.
3. Inventario, bodega y producción.
4. Ventas, reportes y panel gerencial.
5. Inteligencia artificial para toma de decisiones.

Como módulos complementarios se consideran:

- Talento humano.
- Maquinaria, vehículos y activos.
- Contabilidad y tributación.

---

## 12. Relación general entre módulos

El funcionamiento integrado del ERP será el siguiente:

1. Se registra la compra de arroz en cáscara.
2. El arroz comprado ingresa al inventario.
3. El arroz en cáscara se almacena por lote.
4. Se crea una orden de pilado.
5. El pilado consume arroz en cáscara.
6. El proceso genera arroz pilado y subproductos.
7. El inventario se actualiza automáticamente.
8. Se registran ventas de arroz o subproductos.
9. Las ventas reducen el inventario.
10. Los reportes toman información de todos los módulos.
11. El gerente consulta gráficos y métricas.
12. La inteligencia artificial genera recomendaciones.
13. La auditoría registra todas las acciones importantes.