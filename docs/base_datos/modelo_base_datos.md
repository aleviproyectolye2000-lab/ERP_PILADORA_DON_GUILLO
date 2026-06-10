# Modelo de Base de Datos - ERP Piladora Don Guillo

## 1. Descripción general

La base de datos del sistema ERP para la Piladora Don Guillo estará diseñada para almacenar y relacionar la información de compras, proveedores, inventario, producción, ventas, usuarios, perfiles, auditoría, talento humano, maquinaria y reportes.

El objetivo del modelo de base de datos es permitir que los módulos del sistema trabajen de manera integrada. Por ejemplo, una compra de arroz en cáscara aumentará el inventario; una orden de pilado disminuirá el arroz en cáscara y aumentará el arroz pilado junto con los subproductos; y una venta disminuirá el inventario disponible.

---

## 2. Base de datos

### Nombre de la base de datos

```sql
erp_piladora_don_guillo
Motor de base de datos
PostgreSQL 17.10
Base de datos en producción futura
Supabase PostgreSQL
3. Tablas principales del sistema

El sistema tendrá las siguientes tablas principales:

usuarios
perfiles
auditoria_accesos
auditoria_acciones
proveedores
clientes
productos
bodegas
inventario
compras
detalle_compras
ordenes_pilado
detalle_produccion
ventas
detalle_ventas
empleados
asistencia_empleados
roles_pago
maquinaria_activos
mantenimientos
4. Tabla perfiles

Esta tabla almacenará los tipos de perfiles que existirán en el sistema.

Campos principales
Campo	Tipo de dato	Descripción
id_perfil	SERIAL PK	Identificador del perfil
nombre_perfil	VARCHAR(80)	Nombre del perfil
descripcion	TEXT	Descripción del perfil
estado	BOOLEAN	Estado activo o inactivo
Ejemplos de perfiles
Administrador
Gerente
Operador de Báscula y Compras
Operador de Bodega e Inventario
Operador de Producción
Operador de Ventas
Talento Humano
Maquinaria y Activos
5. Tabla usuarios

Esta tabla almacenará los usuarios que ingresan al sistema.

Campos principales
Campo	Tipo de dato	Descripción
id_usuario	SERIAL PK	Identificador del usuario
id_perfil	INT FK	Perfil asignado
nombres	VARCHAR(100)	Nombres del usuario
apellidos	VARCHAR(100)	Apellidos del usuario
usuario	VARCHAR(50)	Nombre de usuario
correo	VARCHAR(120)	Correo electrónico
contrasena_hash	TEXT	Contraseña encriptada
estado	BOOLEAN	Estado del usuario
fecha_creacion	TIMESTAMP	Fecha de creación
Relación

Un perfil puede tener muchos usuarios.

6. Tabla auditoria_accesos

Esta tabla registrará los ingresos y salidas de los usuarios.

Campos principales
Campo	Tipo de dato	Descripción
id_acceso	SERIAL PK	Identificador del acceso
id_usuario	INT FK	Usuario que ingresó
fecha_ingreso	DATE	Fecha de ingreso
hora_ingreso	TIME	Hora de ingreso
fecha_salida	DATE	Fecha de salida
hora_salida	TIME	Hora de salida
tiempo_conectado	INTERVAL	Tiempo conectado
ip_equipo	VARCHAR(50)	Dirección IP o equipo
estado_sesion	VARCHAR(30)	Abierta o cerrada
7. Tabla auditoria_acciones

Esta tabla registrará las acciones importantes realizadas dentro del sistema.

Campos principales
Campo	Tipo de dato	Descripción
id_accion	SERIAL PK	Identificador de acción
id_usuario	INT FK	Usuario que realizó la acción
modulo	VARCHAR(80)	Módulo afectado
accion	VARCHAR(80)	Crear, modificar, eliminar o consultar
descripcion	TEXT	Descripción de la acción
fecha_accion	DATE	Fecha de la acción
hora_accion	TIME	Hora de la acción
tabla_afectada	VARCHAR(80)	Tabla afectada
id_registro_afectado	INT	Registro afectado
8. Tabla proveedores

Esta tabla almacenará los agricultores o proveedores que venden arroz en cáscara a la piladora.

Campos principales
Campo	Tipo de dato	Descripción
id_proveedor	SERIAL PK	Identificador del proveedor
identificacion	VARCHAR(20)	Cédula o RUC
nombres	VARCHAR(120)	Nombres o razón social
telefono	VARCHAR(20)	Teléfono
direccion	TEXT	Dirección
correo	VARCHAR(120)	Correo electrónico
tipo_proveedor	VARCHAR(50)	Agricultor, comerciante u otro
estado	BOOLEAN	Activo o inactivo
9. Tabla clientes

Esta tabla almacenará los clientes que compran arroz pilado o subproductos.

Campos principales
Campo	Tipo de dato	Descripción
id_cliente	SERIAL PK	Identificador del cliente
identificacion	VARCHAR(20)	Cédula o RUC
nombres	VARCHAR(120)	Nombres o razón social
telefono	VARCHAR(20)	Teléfono
direccion	TEXT	Dirección
correo	VARCHAR(120)	Correo electrónico
estado	BOOLEAN	Activo o inactivo
10. Tabla productos

Esta tabla almacenará los productos que maneja la piladora.

Campos principales
Campo	Tipo de dato	Descripción
id_producto	SERIAL PK	Identificador del producto
codigo	VARCHAR(30)	Código interno del producto
nombre_producto	VARCHAR(120)	Nombre del producto
tipo_producto	VARCHAR(60)	Materia prima, terminado o subproducto
unidad_medida	VARCHAR(30)	Quintal, libra, saco, arroba
precio_referencial	NUMERIC(10,2)	Precio referencial
stock_minimo	NUMERIC(10,2)	Stock mínimo permitido
estado	BOOLEAN	Activo o inactivo
Productos iniciales
Arroz en cáscara
Arroz pilado clasificado
Arroz pilado corriente
Arroz envejecido
Arrocillo
Polvillo
Cascarilla
Tamo
11. Tabla bodegas

Esta tabla almacenará las bodegas o áreas de almacenamiento.

Campos principales
Campo	Tipo de dato	Descripción
id_bodega	SERIAL PK	Identificador de bodega
nombre_bodega	VARCHAR(100)	Nombre de la bodega
descripcion	TEXT	Descripción
ubicacion	TEXT	Ubicación física
estado	BOOLEAN	Activa o inactiva
12. Tabla inventario

Esta tabla controlará el stock de productos por bodega y lote.

Campos principales
Campo	Tipo de dato	Descripción
id_inventario	SERIAL PK	Identificador del inventario
id_producto	INT FK	Producto
id_bodega	INT FK	Bodega
lote	VARCHAR(50)	Número o código de lote
cantidad_disponible	NUMERIC(10,2)	Cantidad disponible
fecha_ingreso	DATE	Fecha de ingreso
estado_producto	VARCHAR(50)	Nuevo, viejo, procesado, subproducto
observacion	TEXT	Observaciones
Relación

Un producto puede estar en varias bodegas o lotes.

13. Tabla compras

Esta tabla almacenará la cabecera de las compras de arroz en cáscara.

Campos principales
Campo	Tipo de dato	Descripción
id_compra	SERIAL PK	Identificador de la compra
id_proveedor	INT FK	Proveedor
id_usuario	INT FK	Usuario que registra
fecha_compra	DATE	Fecha de compra
placa_vehiculo	VARCHAR(20)	Placa del vehículo
chofer	VARCHAR(120)	Nombre del chofer
peso_bruto	NUMERIC(10,2)	Peso del vehículo cargado
peso_tara	NUMERIC(10,2)	Peso del vehículo vacío
peso_neto	NUMERIC(10,2)	Peso real recibido
humedad	NUMERIC(5,2)	Porcentaje de humedad
impurezas	NUMERIC(5,2)	Porcentaje de impurezas
precio_quintal	NUMERIC(10,2)	Precio por quintal
total_compra	NUMERIC(10,2)	Total a pagar
estado_pago	VARCHAR(30)	Pagado, pendiente o parcial
observacion	TEXT	Observaciones
14. Tabla detalle_compras

Esta tabla permitirá detallar los productos comprados.

Campos principales
Campo	Tipo de dato	Descripción
id_detalle_compra	SERIAL PK	Identificador del detalle
id_compra	INT FK	Compra relacionada
id_producto	INT FK	Producto comprado
cantidad	NUMERIC(10,2)	Cantidad comprada
precio_unitario	NUMERIC(10,2)	Precio unitario
subtotal	NUMERIC(10,2)	Subtotal
15. Tabla ordenes_pilado

Esta tabla almacenará las órdenes de producción o pilado.

Campos principales
Campo	Tipo de dato	Descripción
id_orden_pilado	SERIAL PK	Identificador de orden
id_usuario	INT FK	Usuario que registra
fecha_pilado	DATE	Fecha del proceso
lote_origen	VARCHAR(50)	Lote de arroz en cáscara
cantidad_procesada	NUMERIC(10,2)	Cantidad de arroz en cáscara procesado
maquina_utilizada	VARCHAR(100)	Máquina usada
operador	VARCHAR(120)	Operador responsable
rendimiento_porcentaje	NUMERIC(5,2)	Rendimiento del pilado
merma	NUMERIC(10,2)	Merma o pérdida
observacion	TEXT	Observaciones
16. Tabla detalle_produccion

Esta tabla almacenará los productos obtenidos del proceso de pilado.

Campos principales
Campo	Tipo de dato	Descripción
id_detalle_produccion	SERIAL PK	Identificador del detalle
id_orden_pilado	INT FK	Orden de pilado
id_producto	INT FK	Producto obtenido
cantidad_obtenida	NUMERIC(10,2)	Cantidad obtenida
tipo_resultado	VARCHAR(60)	Producto terminado, subproducto o merma
Ejemplo

Una orden de pilado puede generar:

Arroz pilado
Arrocillo
Polvillo
Cascarilla
Tamo
Merma
17. Tabla ventas

Esta tabla almacenará la cabecera de las ventas.

Campos principales
Campo	Tipo de dato	Descripción
id_venta	SERIAL PK	Identificador de venta
id_cliente	INT FK	Cliente
id_usuario	INT FK	Usuario que registra
fecha_venta	DATE	Fecha de venta
forma_pago	VARCHAR(50)	Efectivo, transferencia, crédito
estado_pago	VARCHAR(30)	Pagado, pendiente o parcial
subtotal	NUMERIC(10,2)	Subtotal
iva	NUMERIC(10,2)	IVA
total_venta	NUMERIC(10,2)	Total
observacion	TEXT	Observaciones
18. Tabla detalle_ventas

Esta tabla almacenará los productos vendidos.

Campos principales
Campo	Tipo de dato	Descripción
id_detalle_venta	SERIAL PK	Identificador del detalle
id_venta	INT FK	Venta relacionada
id_producto	INT FK	Producto vendido
cantidad	NUMERIC(10,2)	Cantidad vendida
precio_unitario	NUMERIC(10,2)	Precio unitario
descuento	NUMERIC(10,2)	Descuento
subtotal	NUMERIC(10,2)	Subtotal
19. Tabla empleados

Esta tabla almacenará los trabajadores de la piladora.

Campos principales
Campo	Tipo de dato	Descripción
id_empleado	SERIAL PK	Identificador del empleado
identificacion	VARCHAR(20)	Cédula
nombres	VARCHAR(120)	Nombres
apellidos	VARCHAR(120)	Apellidos
cargo	VARCHAR(80)	Cargo
area	VARCHAR(80)	Área
sueldo	NUMERIC(10,2)	Sueldo
telefono	VARCHAR(20)	Teléfono
direccion	TEXT	Dirección
fecha_ingreso	DATE	Fecha de ingreso
estado	BOOLEAN	Activo o inactivo
20. Tabla asistencia_empleados

Esta tabla almacenará asistencias, atrasos, faltas y sanciones.

Campos principales
Campo	Tipo de dato	Descripción
id_asistencia	SERIAL PK	Identificador
id_empleado	INT FK	Empleado
fecha	DATE	Fecha
hora_entrada	TIME	Hora de entrada
hora_salida	TIME	Hora de salida
estado_asistencia	VARCHAR(50)	Presente, atraso, falta
minutos_atraso	INT	Minutos de atraso
sancion	NUMERIC(10,2)	Valor de sanción
observacion	TEXT	Observaciones
21. Tabla roles_pago

Esta tabla almacenará los roles de pago del personal.

Campos principales
Campo	Tipo de dato	Descripción
id_rol_pago	SERIAL PK	Identificador
id_empleado	INT FK	Empleado
periodo	VARCHAR(20)	Periodo del rol
sueldo_base	NUMERIC(10,2)	Sueldo base
horas_extras	NUMERIC(10,2)	Valor de horas extras
bonificaciones	NUMERIC(10,2)	Bonificaciones
sanciones	NUMERIC(10,2)	Sanciones
descuentos	NUMERIC(10,2)	Descuentos
total_pagar	NUMERIC(10,2)	Total a pagar
fecha_generacion	DATE	Fecha de generación
22. Tabla maquinaria_activos

Esta tabla almacenará maquinaria, vehículos, terrenos y activos.

Campos principales
Campo	Tipo de dato	Descripción
id_activo	SERIAL PK	Identificador
nombre_activo	VARCHAR(120)	Nombre del activo
tipo_activo	VARCHAR(80)	Maquinaria, vehículo, terreno, bodega
descripcion	TEXT	Descripción
fecha_adquisicion	DATE	Fecha de adquisición
valor	NUMERIC(10,2)	Valor del activo
estado_activo	VARCHAR(50)	Operativo, mantenimiento, dañado
responsable	VARCHAR(120)	Responsable
23. Tabla mantenimientos

Esta tabla almacenará los mantenimientos de maquinaria y vehículos.

Campos principales
Campo	Tipo de dato	Descripción
id_mantenimiento	SERIAL PK	Identificador
id_activo	INT FK	Activo relacionado
fecha_mantenimiento	DATE	Fecha del mantenimiento
tipo_mantenimiento	VARCHAR(80)	Preventivo o correctivo
descripcion	TEXT	Descripción
costo	NUMERIC(10,2)	Costo del mantenimiento
proximo_mantenimiento	DATE	Próxima fecha
responsable	VARCHAR(120)	Responsable
24. Relaciones principales
Un perfil puede tener muchos usuarios.
Un usuario puede registrar muchas compras.
Un usuario puede registrar muchas ventas.
Un usuario puede registrar muchas órdenes de pilado.
Un proveedor puede tener muchas compras.
Un cliente puede tener muchas ventas.
Un producto puede estar en varios registros de inventario.
Una compra puede tener varios detalles de compra.
Una venta puede tener varios detalles de venta.
Una orden de pilado puede generar varios detalles de producción.
Un empleado puede tener muchas asistencias.
Un empleado puede tener muchos roles de pago.
Un activo puede tener muchos mantenimientos.
25. Reglas de negocio relacionadas con la base de datos
No se puede registrar una compra sin proveedor.
No se puede registrar una venta sin cliente.
No se puede registrar una venta sin producto.
No se puede vender más cantidad que la disponible en inventario.
No se puede procesar más arroz en cáscara que el disponible.
El peso tara no puede ser mayor al peso bruto.
El peso neto debe calcularse como peso bruto menos peso tara.
Toda compra debe aumentar el inventario de arroz en cáscara.
Toda venta debe disminuir el inventario del producto vendido.
Toda orden de pilado debe disminuir arroz en cáscara y aumentar arroz pilado y subproductos.
Toda acción importante debe quedar registrada en auditoría.
El gerente solo debe tener permisos de consulta.
Los operadores solo deben modificar información de su módulo.
26. Tablas prioritarias para la primera versión

Para iniciar el desarrollo del ERP, las tablas prioritarias serán:

perfiles
usuarios
proveedores
clientes
productos
bodegas
inventario
compras
ordenes_pilado
detalle_produccion
ventas
detalle_ventas
auditoria_accesos
auditoria_acciones

Las tablas de talento humano, maquinaria y mantenimiento pueden desarrollarse como módulos complementarios después de tener funcionando compras, inventario, producción y ventas.