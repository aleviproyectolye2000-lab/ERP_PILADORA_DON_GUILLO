# Requerimientos del Sistema ERP - Piladora Don Guillo

## 1. Descripción general

El sistema ERP para la Piladora Don Guillo será una plataforma web orientada a controlar los procesos principales de la empresa, desde la compra de arroz en cáscara hasta el pilado, almacenamiento, venta de arroz procesado y comercialización de subproductos.

El sistema integrará módulos de compras, recepción, báscula, inventario, producción, ventas, talento humano, maquinaria, reportes, auditoría de usuarios e inteligencia artificial para apoyar la toma de decisiones gerenciales.

## 2. Objetivo del sistema

Desarrollar un sistema ERP web que permita gestionar de manera integrada las compras, inventario, producción, ventas, reportes y toma de decisiones en la Piladora Don Guillo, mejorando el control de los procesos internos y facilitando el análisis gerencial mediante gráficos e inteligencia artificial.

## 3. Requerimientos funcionales

### RF01 - Inicio de sesión
El sistema debe permitir que los usuarios ingresen mediante usuario y contraseña.

### RF02 - Control de perfiles
El sistema debe permitir asignar perfiles de usuario según el área de trabajo.

### RF03 - Auditoría de acceso
El sistema debe registrar fecha y hora de ingreso, fecha y hora de salida y tiempo conectado de cada usuario.

### RF04 - Registro de proveedores
El sistema debe permitir registrar agricultores o proveedores que venden arroz en cáscara a la piladora.

### RF05 - Registro de compras de arroz en cáscara
El sistema debe permitir registrar la compra de arroz en cáscara con peso bruto, peso tara, peso neto, humedad, impurezas, precio por quintal y total a pagar.

### RF06 - Cálculo automático de peso neto
El sistema debe calcular automáticamente el peso neto restando el peso tara al peso bruto.

### RF07 - Actualización automática de inventario por compra
Cuando se registre una compra, el sistema debe aumentar el inventario de arroz en cáscara.

### RF08 - Registro de productos
El sistema debe permitir registrar productos como arroz pilado, arroz corriente, arroz clasificado, arrocillo, polvillo, cascarilla y tamo.

### RF09 - Control de stock
El sistema debe mostrar la cantidad disponible de cada producto en inventario.

### RF10 - Registro de órdenes de pilado
El sistema debe permitir crear órdenes de pilado usando arroz en cáscara disponible en inventario.

### RF11 - Registro de producción obtenida
El sistema debe permitir registrar la cantidad obtenida de arroz pilado, arrocillo, polvillo, cascarilla, tamo y merma.

### RF12 - Cálculo de rendimiento del pilado
El sistema debe calcular el porcentaje de rendimiento según la cantidad procesada y la cantidad obtenida.

### RF13 - Actualización automática de inventario por pilado
Cuando se registre un pilado, el sistema debe disminuir el arroz en cáscara y aumentar el arroz pilado y los subproductos.

### RF14 - Registro de clientes
El sistema debe permitir registrar clientes con identificación, nombre, dirección, teléfono y correo.

### RF15 - Registro de ventas
El sistema debe permitir vender arroz pilado y subproductos.

### RF16 - Descuento automático de inventario por venta
Cuando se registre una venta, el sistema debe descontar automáticamente la cantidad vendida del inventario.

### RF17 - Validación de stock disponible
El sistema no debe permitir vender más cantidad de la que existe en inventario.

### RF18 - Reportes de compras
El sistema debe generar reportes de compras por fecha, proveedor, producto y total comprado.

### RF19 - Reportes de ventas
El sistema debe generar reportes de ventas por fecha, cliente, producto y total vendido.

### RF20 - Reportes de inventario
El sistema debe generar reportes de stock disponible, productos agotados y productos con bajo stock.

### RF21 - Reportes de producción
El sistema debe generar reportes de pilado, rendimiento, merma y subproductos obtenidos.

### RF22 - Exportación en PDF
El sistema debe permitir exportar reportes en formato PDF.

### RF23 - Exportación en Excel
El sistema debe permitir exportar reportes en formato Excel.

### RF24 - Gráficos estadísticos
El sistema debe mostrar gráficos de compras, ventas, producción, inventario y rendimiento.

### RF25 - Panel gerencial
El sistema debe mostrar al gerente un panel con métricas generales del negocio.

### RF26 - Inteligencia artificial para decisiones
El sistema debe tener un botón de análisis inteligente que genere recomendaciones según compras, ventas, producción e inventario.

### RF27 - Registro de empleados
El sistema debe permitir registrar trabajadores de la piladora.

### RF28 - Control de asistencia y atrasos
El sistema debe permitir registrar asistencia, atrasos, faltas y sanciones.

### RF29 - Roles de pago
El sistema debe permitir generar roles de pago considerando sueldo, bonificaciones, horas extras, sanciones y descuentos.

### RF30 - Control de maquinaria y vehículos
El sistema debe permitir registrar maquinaria, vehículos, mantenimientos y responsables.

## 4. Requerimientos no funcionales

### RNF01 - Seguridad
El sistema debe proteger la información mediante usuarios, contraseñas y perfiles de acceso.

### RNF02 - Restricción por perfil
Cada usuario solo podrá acceder al módulo que le corresponde.

### RNF03 - Disponibilidad
El sistema debe estar disponible desde internet cuando sea desplegado en la nube.

### RNF04 - Rendimiento
El sistema debe responder de forma rápida en consultas, registros y reportes.

### RNF05 - Escalabilidad
El sistema debe permitir agregar nuevos módulos o productos agrícolas en el futuro.

### RNF06 - Usabilidad
La interfaz debe ser clara, ordenada y fácil de usar.

### RNF07 - Compatibilidad
El sistema debe funcionar desde navegadores como Google Chrome, Microsoft Edge o Firefox.

### RNF08 - Mantenibilidad
El código debe estar organizado para poder corregir errores o agregar nuevas funciones.

### RNF09 - Respaldo de datos
La base de datos debe permitir respaldar la información de compras, ventas, inventario, usuarios y reportes.

### RNF10 - Exportación
Los reportes deben poder descargarse en PDF y Excel.

## 5. Restricciones generales

- El gerente solo podrá consultar información, reportes, gráficos y recomendaciones.
- Los operadores solo podrán acceder al módulo asignado.
- No se podrá vender un producto sin stock suficiente.
- No se podrá procesar más arroz en cáscara del disponible en inventario.
- No se podrá registrar compras, ventas o producción con cantidades negativas.
- El peso tara no podrá ser mayor al peso bruto.
- Toda acción importante deberá quedar registrada en auditoría.
- La inteligencia artificial funcionará inicialmente con reglas, cálculos y análisis de tendencias.

## 6. Herramientas definidas

- Visual Studio Code como editor de código.
- Python 3.12.5 como lenguaje backend.
- FastAPI como framework backend.
- PostgreSQL 17.10 como base de datos local.
- Supabase PostgreSQL como base de datos en nube futura.
- HTML, CSS, JavaScript y Bootstrap 5 para frontend.
- Chart.js para gráficos.
- ReportLab para PDF.
- openpyxl para Excel.
- Git y GitHub para control de versiones.
- Render y Vercel como opciones de despliegue en nube.