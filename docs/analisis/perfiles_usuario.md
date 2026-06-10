# Perfiles de Usuario del Sistema ERP - Piladora Don Guillo

## 1. Descripción general

El sistema ERP de la Piladora Don Guillo contará con diferentes perfiles de usuario, con el objetivo de controlar el acceso a los módulos y proteger la información de la empresa.

Cada usuario tendrá permisos según su área de trabajo. La parte operativa podrá registrar, consultar, modificar y eliminar información dentro de su módulo asignado. En cambio, la parte directiva o gerencial solo podrá consultar reportes, gráficos, métricas y recomendaciones del sistema.

---

## 2. Perfil Administrador del Sistema

El administrador del sistema será el encargado de gestionar la seguridad, usuarios, permisos y configuración general del ERP.

### Permisos

- Crear usuarios.
- Modificar usuarios.
- Activar usuarios.
- Desactivar usuarios.
- Asignar perfiles.
- Restablecer contraseñas.
- Configurar permisos.
- Consultar auditoría de accesos.
- Consultar acciones realizadas por los usuarios.
- Ver registros de ingreso y salida del sistema.

### Restricciones

- No debe alterar información operativa sin autorización.
- No debe modificar compras, ventas o producción si no forma parte de su función.
- Toda acción realizada debe quedar registrada en auditoría.

---

## 3. Perfil Gerente o Dueño

El gerente o dueño tendrá acceso global al sistema, pero únicamente en modo consulta. Este perfil está orientado a la toma de decisiones.

### Permisos

- Consultar compras.
- Consultar ventas.
- Consultar inventario.
- Consultar producción.
- Consultar talento humano.
- Consultar maquinaria y activos.
- Consultar reportes generales.
- Visualizar gráficos.
- Visualizar métricas.
- Exportar reportes en PDF.
- Exportar reportes en Excel.
- Consultar recomendaciones de inteligencia artificial.
- Consultar auditoría general del sistema.

### Restricciones

- No puede registrar compras.
- No puede modificar compras.
- No puede eliminar compras.
- No puede registrar ventas.
- No puede modificar ventas.
- No puede eliminar ventas.
- No puede modificar inventario.
- No puede crear órdenes de pilado.
- No puede registrar trabajadores.
- No puede modificar datos operativos.

### Objetivo del perfil

Permitir que el gerente supervise el funcionamiento total de la piladora sin intervenir directamente en los registros operativos.

---

## 4. Perfil Operador de Báscula y Compras

Este usuario será responsable de registrar el ingreso del arroz en cáscara cuando llega a la piladora.

### Permisos

- Registrar proveedores o agricultores.
- Consultar proveedores.
- Registrar vehículos.
- Registrar chofer.
- Registrar fecha de recepción.
- Registrar peso bruto.
- Registrar peso tara.
- Calcular peso neto.
- Registrar humedad.
- Registrar impurezas.
- Registrar precio por quintal.
- Calcular total de compra.
- Generar comprobante de recepción.
- Consultar compras registradas por su área.

### Restricciones

- No puede registrar ventas.
- No puede modificar ventas.
- No puede crear órdenes de pilado.
- No puede modificar roles de pago.
- No puede crear usuarios.
- No puede cambiar permisos.
- No puede acceder al módulo de talento humano.
- No puede acceder al panel administrativo.

### Relación con otros módulos

Las compras registradas por este perfil aumentan el inventario de arroz en cáscara.

---

## 5. Perfil Operador de Bodega e Inventario

Este usuario será responsable de controlar el stock y ubicación de los productos dentro de la piladora.

### Permisos

- Consultar inventario.
- Registrar ubicación de lotes.
- Registrar entradas de inventario autorizadas.
- Registrar salidas de inventario autorizadas.
- Controlar arroz en cáscara.
- Controlar arroz pilado.
- Controlar arrocillo.
- Controlar polvillo.
- Controlar cascarilla.
- Controlar tamo.
- Consultar stock disponible.
- Consultar productos agotados.
- Consultar productos con bajo stock.
- Generar reportes de inventario.

### Restricciones

- No puede registrar compras.
- No puede registrar ventas.
- No puede modificar precios de venta.
- No puede registrar empleados.
- No puede modificar usuarios.
- No puede acceder a roles de pago.
- No puede eliminar movimientos sin autorización.

### Relación con otros módulos

Este perfil se relaciona con compras, producción y ventas, porque el inventario cambia cuando ingresa arroz, cuando se procesa y cuando se vende.

---

## 6. Perfil Operador de Producción y Pilado

Este usuario será responsable de registrar el proceso de pilado del arroz.

### Permisos

- Crear órdenes de pilado.
- Seleccionar lote de arroz en cáscara.
- Registrar cantidad de arroz en cáscara procesado.
- Registrar fecha del proceso.
- Registrar máquina utilizada.
- Registrar operador responsable.
- Registrar arroz pilado obtenido.
- Registrar arrocillo obtenido.
- Registrar polvillo obtenido.
- Registrar cascarilla obtenida.
- Registrar tamo obtenido.
- Registrar merma.
- Calcular rendimiento del pilado.
- Consultar historial de producción.
- Generar reportes de producción.

### Restricciones

- No puede registrar compras.
- No puede registrar ventas.
- No puede modificar precios.
- No puede registrar empleados.
- No puede crear usuarios.
- No puede cambiar permisos.
- No puede modificar información contable.

### Relación con otros módulos

Cuando se registra una orden de pilado, el sistema disminuye el inventario de arroz en cáscara y aumenta el inventario de arroz pilado y subproductos.

---

## 7. Perfil Operador de Ventas

Este usuario será responsable de registrar las ventas de arroz pilado y subproductos.

### Permisos

- Registrar clientes.
- Consultar clientes.
- Registrar ventas.
- Seleccionar producto vendido.
- Registrar cantidad vendida.
- Registrar precio unitario.
- Calcular subtotal.
- Calcular total de venta.
- Registrar forma de pago.
- Registrar estado de pago.
- Generar comprobante de venta.
- Consultar historial de ventas.
- Exportar reportes de ventas en PDF.
- Exportar reportes de ventas en Excel.

### Productos que puede vender

- Arroz pilado.
- Arroz pilado clasificado.
- Arroz pilado corriente.
- Arroz envejecido.
- Arrocillo.
- Polvillo.
- Cascarilla.
- Tamo.

### Restricciones

- No puede vender productos sin stock disponible.
- No puede registrar compras.
- No puede crear órdenes de pilado.
- No puede modificar inventario manualmente.
- No puede registrar trabajadores.
- No puede crear usuarios.
- No puede cambiar permisos.
- No puede consultar información confidencial de talento humano.

### Relación con otros módulos

Cada venta registrada descuenta automáticamente el producto vendido del inventario.

---

## 8. Perfil Talento Humano

Este usuario será responsable del manejo del personal de la piladora.

### Permisos

- Registrar empleados.
- Consultar empleados.
- Modificar datos de empleados.
- Registrar cargos.
- Registrar áreas de trabajo.
- Registrar sueldos.
- Registrar asistencia.
- Registrar atrasos.
- Registrar faltas.
- Registrar sanciones.
- Registrar horas extras.
- Registrar bonificaciones.
- Generar roles de pago.
- Consultar historial laboral.
- Generar reportes de talento humano.

### Restricciones

- No puede registrar compras.
- No puede registrar ventas.
- No puede modificar inventario.
- No puede crear órdenes de pilado.
- No puede modificar precios.
- No puede crear usuarios.
- No puede cambiar permisos.

### Relación con otros módulos

Este perfil permite controlar el personal que trabaja en áreas como báscula, producción, bodega, ventas, campo y administración.

---

## 9. Perfil Operador de Maquinaria y Activos

Este usuario será responsable de registrar maquinaria, vehículos, terrenos y mantenimientos.

### Permisos

- Registrar maquinaria.
- Registrar vehículos.
- Registrar terrenos.
- Registrar bodegas.
- Registrar herramientas.
- Registrar mantenimientos.
- Registrar reparaciones.
- Registrar consumo de combustible.
- Registrar responsable del activo.
- Consultar estado de los activos.
- Generar reportes de activos.
- Generar alertas de mantenimiento.

### Restricciones

- No puede registrar ventas.
- No puede registrar compras de arroz.
- No puede modificar inventario.
- No puede registrar empleados.
- No puede crear usuarios.
- No puede cambiar permisos.
- No puede modificar información del panel gerencial.

### Relación con otros módulos

Este perfil se relaciona con producción porque la maquinaria participa en el proceso de pilado. También se relaciona con reportes por los costos de mantenimiento.

---

## 10. Permisos resumidos por perfil

| Perfil | Registrar | Consultar | Modificar | Eliminar | Reportes | Acceso total |
|---|---|---|---|---|---|---|
| Administrador | Sí | Sí | Sí | Sí | Sí | Seguridad |
| Gerente | No | Sí | No | No | Sí | Solo consulta |
| Báscula y Compras | Sí | Sí | Sí | Limitado | Sí | Su módulo |
| Bodega e Inventario | Sí | Sí | Sí | Limitado | Sí | Su módulo |
| Producción y Pilado | Sí | Sí | Sí | Limitado | Sí | Su módulo |
| Ventas | Sí | Sí | Sí | Limitado | Sí | Su módulo |
| Talento Humano | Sí | Sí | Sí | Limitado | Sí | Su módulo |
| Maquinaria y Activos | Sí | Sí | Sí | Limitado | Sí | Su módulo |

---

## 11. Reglas generales de acceso

- Cada usuario debe ingresar con usuario y contraseña.
- Cada usuario debe tener un perfil asignado.
- Un usuario no puede acceder a módulos que no corresponden a su perfil.
- El gerente solo puede consultar información.
- Los operadores solo pueden trabajar en su módulo asignado.
- Toda acción importante debe quedar registrada en auditoría.
- El sistema debe registrar fecha y hora de ingreso.
- El sistema debe registrar fecha y hora de salida.
- El sistema debe calcular el tiempo conectado.
- El sistema debe registrar creación, modificación y eliminación de datos.
- El administrador puede gestionar usuarios, pero también queda registrado en auditoría.

---

## 12. Auditoría por usuario

El sistema debe guardar un historial de actividad con los siguientes datos:

- Usuario.
- Perfil.
- Módulo utilizado.
- Acción realizada.
- Fecha de acción.
- Hora de acción.
- Registro afectado.
- Dirección IP o equipo desde donde ingresó.
- Fecha y hora de inicio de sesión.
- Fecha y hora de cierre de sesión.
- Tiempo total conectado.

---

## 13. Ejemplo de auditoría

Ejemplo:

El usuario `bascula01` ingresa al sistema el día 30/05/2026 a las 08:00.

Registra una compra de arroz en cáscara de 120 quintales.

El sistema guarda:

- Usuario: bascula01.
- Perfil: Operador de Báscula y Compras.
- Acción: Registro de compra.
- Módulo: Compras, recepción y báscula.
- Fecha: 30/05/2026.
- Hora: 08:15.
- Registro afectado: Compra N.º 001.
- Resultado: Compra registrada correctamente.

Cuando el usuario cierra sesión a las 12:30, el sistema guarda:

- Hora de salida: 12:30.
- Tiempo conectado: 4 horas y 30 minutos.

---

## 14. Importancia del control de perfiles

El control de perfiles permite proteger la información de la Piladora Don Guillo y mantener un orden dentro del sistema. Cada trabajador solo podrá acceder a las funciones necesarias para su área, evitando errores, modificaciones no autorizadas o pérdida de información.

Además, el gerente podrá revisar todo el comportamiento del negocio desde el panel gerencial, sin necesidad de ingresar datos manualmente.