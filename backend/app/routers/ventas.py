from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
import random
import string

from app.database import get_db

router = APIRouter(
    prefix="/api/ventas",
    tags=["Ventas y Comercialización"]
)

# ============================================================
# MODELOS
# ============================================================

class VentaCompletaCreate(BaseModel):
    numero_comprobante: Optional[str] = None

    cliente: str
    identificacion: str
    id_usuario: int = 1
    fecha_venta: date
    tipo_comprobante: str = "Factura"
    forma_pago: str
    estado_pago: str

    id_inventario: int
    unidad_medida: str

    cantidad: float = Field(gt=0)
    cantidad_unidad: float = Field(gt=0)
    cantidad_quintales: float = Field(gt=0) 

    precio_unitario: float = Field(gt=0)
    descuento: float = Field(ge=0, default=0)
    iva_porcentaje: float = Field(ge=0, default=0)

    subtotal: Optional[float] = None
    total_venta: Optional[float] = None
    valor_recibido: float = Field(ge=0, default=0)
    saldo_pendiente: float = Field(ge=0, default=0)
    observacion: Optional[str] = None

class VentaUpdate(BaseModel):
    numero_comprobante: Optional[str] = None
    cliente: str
    identificacion: str
    id_usuario: int = 1
    fecha_venta: date
    tipo_comprobante: str = "Factura"
    forma_pago: str
    estado_pago: str

    id_inventario: int
    unidad_medida: str
    cantidad: float = Field(gt=0)          
    cantidad_unidad: float = Field(gt=0)   
    cantidad_quintales: float = Field(gt=0) 
    precio_unitario: float = Field(gt=0)
    descuento: float = Field(ge=0, default=0)
    iva_porcentaje: float = Field(ge=0, default=0)

    subtotal: Optional[float] = None
    total_venta: Optional[float] = None
    valor_recibido: float = Field(ge=0, default=0)
    saldo_pendiente: float = Field(ge=0, default=0)
    observacion: Optional[str] = None


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def generar_numero_comprobante():
    fecha_actual = datetime.now().strftime("%Y%m%d")
    aleatorio = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"FAC-{fecha_actual}-{aleatorio}"


def validar_opciones(tipo_comprobante: str, forma_pago: str, estado_pago: str, unidad_medida: str, iva_porcentaje: float):
    formas_pago_validas = ["Efectivo", "Transferencia", "Crédito"]
    estados_pago_validos = ["Pagado", "Pendiente", "Parcial"]
    unidades_validas = ["Libra", "Arroba", "Medio quintal", "Quintal"]
    iva_validos = [0, 15]

    if tipo_comprobante != "Factura":
        raise HTTPException(
            status_code=400,
            detail="El sistema solo permite registrar ventas con comprobante Factura."
        )

    if forma_pago not in formas_pago_validas:
        raise HTTPException(
            status_code=400,
            detail="Forma de pago no válida."
        )

    if estado_pago not in estados_pago_validos:
        raise HTTPException(
            status_code=400,
            detail="Estado de pago no válido."
        )

    if unidad_medida not in unidades_validas:
        raise HTTPException(
            status_code=400,
            detail="Unidad de venta no válida."
        )

    if float(iva_porcentaje) not in iva_validos:
        raise HTTPException(
            status_code=400,
            detail="IVA no válido. Use 0 o 15."
        )


def validar_reglas_pago(estado_pago: str, forma_pago: str, total: float, valor_recibido: float):
    total = round(float(total or 0), 2)
    valor_recibido = round(float(valor_recibido or 0), 2)

    if estado_pago == "Pagado":
        if forma_pago not in ["Efectivo", "Transferencia"]:
            raise HTTPException(
                status_code=400,
                detail="Si la venta está pagada, la forma de pago debe ser Efectivo o Transferencia."
            )
        valor_recibido = total
        saldo_pendiente = 0

    elif estado_pago == "Pendiente":
        if forma_pago != "Crédito":
            raise HTTPException(
                status_code=400,
                detail="Si la venta está pendiente, la forma de pago debe ser Crédito."
            )
        valor_recibido = 0
        saldo_pendiente = total

    elif estado_pago == "Parcial":
        if forma_pago not in ["Efectivo", "Transferencia", "Crédito"]:
            raise HTTPException(
                status_code=400,
                detail="Si la venta es parcial, seleccione una forma de pago válida."
            )
        if valor_recibido <= 0:
            raise HTTPException(
                status_code=400,
                detail="En pago parcial debe ingresar un abono mayor a 0."
            )
        if valor_recibido >= total:
            raise HTTPException(
                status_code=400,
                detail="En pago parcial el abono debe ser menor al total."
            )
        saldo_pendiente = total - valor_recibido

    else:
        raise HTTPException(
            status_code=400,
            detail="Estado de pago no válido."
        )

    return round(valor_recibido, 2), round(saldo_pendiente, 2)


def calcular_totales(cantidad_unidad: float, precio_unitario: float, descuento: float, iva_porcentaje: float):
    cantidad_unidad = float(cantidad_unidad or 0)
    precio_unitario = float(precio_unitario or 0)
    descuento = float(descuento or 0)
    iva_porcentaje = float(iva_porcentaje or 0)

    if cantidad_unidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad vendida debe ser mayor a 0.")

    if precio_unitario <= 0:
        raise HTTPException(status_code=400, detail="El precio unitario debe ser mayor a 0.")

    if descuento < 0:
        raise HTTPException(status_code=400, detail="El descuento no puede ser negativo.")

    subtotal = round(cantidad_unidad * precio_unitario, 2)

    if descuento > subtotal:
        raise HTTPException(status_code=400, detail="El descuento no puede ser mayor al subtotal.")

    base = round(subtotal - descuento, 2)
    iva = round(base * (iva_porcentaje / 100), 2)
    total = round(base + iva, 2)

    return subtotal, iva, total


def buscar_o_crear_cliente(db: Session, nombre: str, identificacion: str):
    nombre = nombre.strip().upper()
    identificacion = identificacion.strip()

    if not nombre:
        raise HTTPException(status_code=400, detail="Debe ingresar el nombre del cliente.")

    if not identificacion.isdigit():
        raise HTTPException(status_code=400, detail="La identificación solo debe contener números.")

    if len(identificacion) not in [10, 13]:
        raise HTTPException(status_code=400, detail="La identificación debe tener 10 o 13 dígitos.")

    cliente = db.execute(
        text("""
            SELECT id_cliente 
            FROM clientes
            WHERE identificacion = :identificacion
            LIMIT 1;
        """),
        {"identificacion": identificacion}
    ).mappings().first()

    if cliente:
        db.execute(
            text("""
                UPDATE clientes
                SET nombres = :nombres
                WHERE id_cliente = :id_cliente;
            """),
            {
                "nombres": nombre,
                "id_cliente": cliente["id_cliente"]
            }
        )
        return cliente["id_cliente"]

    nuevo = db.execute(
        text("""
            INSERT INTO clientes (
                identificacion,
                nombres
            )
            VALUES (
                :identificacion,
                :nombres
            )
            RETURNING id_cliente;
        """),
        {
            "identificacion": identificacion,
            "nombres": nombre
        }
    ).mappings().first()

    return nuevo["id_cliente"]


def obtener_inventario_para_venta(db: Session, id_inventario: int):
    inventario = db.execute(
        text("""
            SELECT
                i.id_inventario,
                i.id_producto,
                i.id_bodega,
                i.lote,
                i.cantidad_disponible,
                i.estado_producto,
                p.codigo,
                p.nombre_producto,
                p.tipo_producto,
                COALESCE(p.precio_referencial, 0) AS precio_referencial,
                b.nombre_bodega
            FROM inventario i
            INNER JOIN productos p ON i.id_producto = p.id_producto
            INNER JOIN bodegas b ON i.id_bodega = b.id_bodega
            WHERE i.id_inventario = :id_inventario;
        """), 
        {"id_inventario": id_inventario}
    ).mappings().first()

    if inventario is None:
        raise HTTPException(status_code=404, detail="No existe el inventario seleccionado.")

    if inventario["estado_producto"] == "Eliminado":
        raise HTTPException(status_code=400, detail="El producto seleccionado está eliminado.")

    return inventario


def descontar_inventario(db: Session, id_inventario: int, cantidad_quintales: float):
    inventario = obtener_inventario_para_venta(db, id_inventario)

    disponible = float(inventario["cantidad_disponible"] or 0)
    cantidad_quintales = round(float(cantidad_quintales or 0), 2)

    if cantidad_quintales <= 0:
        raise HTTPException(status_code=400, detail="La cantidad a vender debe ser mayor a 0.")

    if cantidad_quintales > disponible:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponible: {disponible:.2f} qq. Solicitado: {cantidad_quintales:.2f} qq."
        )

    nuevo_stock = round(disponible - cantidad_quintales, 2)
    estado_producto = "Disponible"

    if nuevo_stock <= 0:
        estado_producto = "Agotado"

    db.execute(
        text("""
            UPDATE inventario
            SET
                cantidad_disponible = :nuevo_stock,
                estado_producto = :estado_producto,
                observacion = COALESCE(observacion, '') || ' | Inventario descontado por venta'
            WHERE id_inventario = :id_inventario;
        """),
        {
            "nuevo_stock": nuevo_stock,
            "estado_producto": estado_producto,
            "id_inventario": id_inventario
        }
    )

    return inventario


def devolver_inventario_por_detalle(db: Session, detalle):
    id_inventario = detalle.get("id_inventario")
    cantidad_quintales = float(detalle.get("cantidad_quintales") or detalle.get("cantidad") or 0)

    if cantidad_quintales <= 0:
        return

    if id_inventario:
        inventario = db.execute(
            text("""
                SELECT
                    id_inventario,
                    cantidad_disponible
                FROM inventario
                WHERE id_inventario = :id_inventario;
            """),
            {"id_inventario": id_inventario}
        ).mappings().first()

        if inventario:
            nuevo_stock = round(float(inventario["cantidad_disponible"] or 0) + cantidad_quintales, 2)

            db.execute(
                text("""
                    UPDATE inventario
                    SET
                        cantidad_disponible = :nuevo_stock,
                        estado_producto = 'Disponible',
                        observacion = COALESCE(observacion, '') || ' | Inventario devuelto por anulación/edición de venta'
                    WHERE id_inventario = :id_inventario;
                """),
                {
                    "nuevo_stock": nuevo_stock,
                    "id_inventario": id_inventario
                }
            )
            return

    db.execute(
        text("""
            UPDATE inventario
            SET
                cantidad_disponible = cantidad_disponible + :cantidad_quintales,
                estado_producto = 'Disponible',
                observacion = COALESCE(observacion, '') || ' | Inventario devuelto por anulación/edición de venta'
            WHERE id_producto = :id_producto
              AND id_bodega = :id_bodega
              AND lote = :lote
              AND estado_producto <> 'Eliminado';
        """),
        {
            "cantidad_quintales": cantidad_quintales,
            "id_producto": detalle["id_producto"],
            "id_bodega": detalle["id_bodega"],
            "lote": detalle["lote"]
        }
    )


def formatear_error_bd(error_str: str):
    """Función para traducir errores de PostgreSQL a mensajes amigables"""
    if "fn_descontar_inventario_venta" in error_str or "RaiseException" in error_str:
        return "Conflicto de Base de Datos: Hay un Trigger intentando restar el inventario duplicado. Por favor, asegúrate de haber ejecutado el comando DROP TRIGGER en pgAdmin."
    return f"Error interno al guardar la venta. Detalle: {error_str}"


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/productos-disponibles")
def listar_productos_disponibles_para_venta(db: Session = Depends(get_db)):
    try:
        resultado = db.execute(
            text("""
                SELECT
                    i.id_inventario,
                    i.id_producto,
                    i.id_bodega,
                    i.lote,
                    i.cantidad_disponible,
                    i.estado_producto,
                    p.codigo,
                    p.nombre_producto,
                    p.tipo_producto,
                    COALESCE(p.precio_referencial, 0) AS precio_referencial,
                    b.nombre_bodega
                FROM inventario i
                INNER JOIN productos p ON i.id_producto = p.id_producto
                INNER JOIN bodegas b ON i.id_bodega = b.id_bodega
                WHERE i.cantidad_disponible > 0
                  AND i.estado_producto <> 'Eliminado'
                  AND LOWER(p.tipo_producto) IN ('producto terminado', 'subproducto')
                ORDER BY p.nombre_producto, i.lote;
            """)
        )
        return [dict(fila) for fila in resultado.mappings().all()]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error al cargar productos. Detalle: {str(error)}")


@router.get("/resumen")
def resumen_ventas(db: Session = Depends(get_db)):
    try:
        resumen = db.execute(
            text("""
                SELECT
                    COUNT(DISTINCT v.id_venta) AS total_ventas,
                    COALESCE(SUM(v.valor_recibido), 0) AS ingresos_cobrados,
                    COALESCE(SUM(v.saldo_pendiente), 0) AS cuentas_por_cobrar,
                    COUNT(DISTINCT CASE
                        WHEN v.saldo_pendiente > 0 THEN v.id_cliente
                    END) AS clientes_por_cobrar
                FROM ventas v
                WHERE v.estado = TRUE;
            """)
        ).mappings().first()

        producto = db.execute(
            text("""
                SELECT
                    p.nombre_producto,
                    COALESCE(SUM(dv.cantidad_quintales), SUM(dv.cantidad), 0) AS total_vendido
                FROM detalle_ventas dv
                INNER JOIN ventas v ON dv.id_venta = v.id_venta
                INNER JOIN productos p ON dv.id_producto = p.id_producto
                WHERE v.estado = TRUE
                GROUP BY p.nombre_producto
                ORDER BY total_vendido DESC
                LIMIT 1;
            """)
        ).mappings().first()

        return {
            "total_ventas": int(resumen["total_ventas"] or 0),
            "ingresos_cobrados": float(resumen["ingresos_cobrados"] or 0),
            "cuentas_por_cobrar": float(resumen["cuentas_por_cobrar"] or 0),
            "clientes_por_cobrar": int(resumen["clientes_por_cobrar"] or 0),
            "producto_mas_vendido": producto["nombre_producto"] if producto else "---"
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error al calcular resumen. Detalle: {str(error)}")


@router.get("/siguiente-comprobante")
def siguiente_comprobante():
    return {
        "numero_comprobante": generar_numero_comprobante()
    }


@router.get("/")
def listar_ventas(db: Session = Depends(get_db)):
    try:
        resultado = db.execute(
            text("""
                SELECT
                    v.id_venta,
                    v.numero_comprobante,
                    v.fecha_venta,
                    v.tipo_comprobante,
                    v.forma_pago,
                    v.estado_pago,
                    v.subtotal AS subtotal_venta,
                    v.iva AS iva_venta,
                    v.total_venta,
                    v.valor_recibido,
                    v.saldo_pendiente,
                    v.observacion,
                    v.estado,

                    c.nombres AS cliente,
                    c.identificacion AS identificacion,

                    dv.id_detalle_venta,
                    dv.id_inventario,
                    dv.id_producto,
                    dv.id_bodega,
                    dv.lote,
                    dv.cantidad,
                    COALESCE(dv.cantidad_unidad, dv.cantidad) AS cantidad_unidad,
                    COALESCE(dv.cantidad_quintales, dv.cantidad) AS cantidad_quintales,
                    dv.unidad_medida,
                    dv.precio_unitario,
                    dv.descuento,
                    dv.iva_porcentaje,
                    dv.subtotal,
                    dv.total_linea,

                    p.nombre_producto,
                    p.tipo_producto,
                    b.nombre_bodega
                FROM ventas v
                INNER JOIN clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
                LEFT JOIN productos p ON dv.id_producto = p.id_producto
                LEFT JOIN bodegas b ON dv.id_bodega = b.id_bodega
                ORDER BY v.id_venta DESC;
            """)
        )
        return [dict(fila) for fila in resultado.mappings().all()]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error al listar ventas. Detalle: {str(error)}")


@router.get("/{id_venta}")
def obtener_venta(id_venta: int, db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                v.id_venta,
                v.numero_comprobante,
                v.fecha_venta,
                v.tipo_comprobante,
                v.forma_pago,
                v.estado_pago,
                v.subtotal AS subtotal_venta,
                v.iva AS iva_venta,
                v.total_venta,
                v.valor_recibido,
                v.saldo_pendiente,
                v.observacion,
                v.estado,

                c.nombres AS cliente,
                c.identificacion AS identificacion,

                dv.id_detalle_venta,
                dv.id_inventario,
                dv.id_producto,
                dv.id_bodega,
                dv.lote,
                dv.cantidad,
                COALESCE(dv.cantidad_unidad, dv.cantidad) AS cantidad_unidad,
                COALESCE(dv.cantidad_quintales, dv.cantidad) AS cantidad_quintales,
                dv.unidad_medida,
                dv.precio_unitario,
                dv.descuento,
                dv.iva_porcentaje,
                dv.subtotal,
                dv.total_linea,

                p.nombre_producto,
                p.tipo_producto,
                b.nombre_bodega
            FROM ventas v
            INNER JOIN clientes c ON v.id_cliente = c.id_cliente
            LEFT JOIN detalle_ventas dv ON v.id_venta = dv.id_venta
            LEFT JOIN productos p ON dv.id_producto = p.id_producto
            LEFT JOIN bodegas b ON dv.id_bodega = b.id_bodega
            WHERE v.id_venta = :id_venta;
        """),
        {"id_venta": id_venta}
    ).mappings().all()

    if not resultado:
        raise HTTPException(status_code=404, detail="Venta no encontrada.")

    return [dict(fila) for fila in resultado]


@router.post("/registrar-completa")
def registrar_venta_completa(datos: VentaCompletaCreate, db: Session = Depends(get_db)):
    # 🔒 EL CANDADO DE SEGURIDAD SE PONE AQUÍ:
    from app.routers.seguridad import verificar_permiso_backend
    verificar_permiso_backend(datos.id_usuario, "ventas.html", "puede_crear", db)
    try:
        validar_opciones(
            datos.tipo_comprobante, datos.forma_pago, datos.estado_pago, datos.unidad_medida, datos.iva_porcentaje
        )

        if datos.fecha_venta > date.today():
            raise HTTPException(status_code=400, detail="No se permite registrar ventas con fecha futura.")

        subtotal, iva, total = calcular_totales(
            datos.cantidad_unidad, datos.precio_unitario, datos.descuento, datos.iva_porcentaje
        )

        valor_recibido, saldo_pendiente = validar_reglas_pago(
            datos.estado_pago, datos.forma_pago, total, datos.valor_recibido
        )

        id_cliente = buscar_o_crear_cliente(db, datos.cliente, datos.identificacion)

        inventario = descontar_inventario(db, datos.id_inventario, datos.cantidad_quintales)

        numero_comprobante = datos.numero_comprobante.strip() if datos.numero_comprobante else generar_numero_comprobante()

        venta = db.execute(
            text("""
                INSERT INTO ventas (
                    id_cliente, id_usuario, fecha_venta, tipo_comprobante, forma_pago, estado_pago,
                    subtotal, iva, total_venta, valor_recibido, saldo_pendiente, numero_comprobante, observacion, estado
                )
                VALUES (
                    :id_cliente, :id_usuario, :fecha_venta, :tipo_comprobante, :forma_pago, :estado_pago,
                    :subtotal, :iva, :total_venta, :valor_recibido, :saldo_pendiente, :numero_comprobante, :observacion, TRUE
                )
                RETURNING id_venta;
            """),
            {
                "id_cliente": id_cliente,
                "id_usuario": datos.id_usuario,
                "fecha_venta": datos.fecha_venta,
                "tipo_comprobante": "Factura",
                "forma_pago": datos.forma_pago,
                "estado_pago": datos.estado_pago,
                "subtotal": subtotal,
                "iva": iva,
                "total_venta": total,
                "valor_recibido": valor_recibido,
                "saldo_pendiente": saldo_pendiente,
                "numero_comprobante": numero_comprobante,
                "observacion": datos.observacion
            }
        ).mappings().first()

        db.execute(
            text("""
                INSERT INTO detalle_ventas (
                    id_venta, id_producto, id_bodega, lote, cantidad, unidad_medida, precio_unitario,
                    descuento, iva_porcentaje, observacion, id_inventario, cantidad_unidad, cantidad_quintales
                )
                VALUES (
                    :id_venta, :id_producto, :id_bodega, :lote, :cantidad, :unidad_medida, :precio_unitario,
                    :descuento, :iva_porcentaje, :observacion, :id_inventario, :cantidad_unidad, :cantidad_quintales
                );
            """),
            {
                "id_venta": venta["id_venta"],
                "id_producto": inventario["id_producto"],
                "id_bodega": inventario["id_bodega"],
                "lote": inventario["lote"],
                "cantidad": datos.cantidad,
                "unidad_medida": datos.unidad_medida,
                "precio_unitario": datos.precio_unitario,
                "descuento": datos.descuento,
                "iva_porcentaje": datos.iva_porcentaje,
                "observacion": datos.observacion,
                "id_inventario": datos.id_inventario,
                "cantidad_unidad": datos.cantidad_unidad,
                "cantidad_quintales": datos.cantidad_quintales
            }
        )

        db.commit()

        return {
            "mensaje": "Venta registrada correctamente. Inventario descontado.",
            "id_venta": venta["id_venta"],
            "numero_comprobante": numero_comprobante,
            "total_venta": total,
            "valor_recibido": valor_recibido,
            "saldo_pendiente": saldo_pendiente
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        mensaje_amigable = formatear_error_bd(str(error))
        raise HTTPException(status_code=400, detail=mensaje_amigable)


@router.put("/{id_venta}")
def actualizar_venta(id_venta: int, datos: VentaUpdate, db: Session = Depends(get_db)):
    try:
        venta_actual = db.execute(
            text("""
                SELECT id_venta, numero_comprobante, estado
                FROM ventas
                WHERE id_venta = :id_venta;
            """),
            {"id_venta": id_venta}
        ).mappings().first()

        if venta_actual is None:
            raise HTTPException(status_code=404, detail="Venta no encontrada.")

        if venta_actual["estado"] is False:
            raise HTTPException(status_code=400, detail="No se puede editar una venta anulada.")

        detalles_actuales = db.execute(
            text("SELECT * FROM detalle_ventas WHERE id_venta = :id_venta;"),
            {"id_venta": id_venta}
        ).mappings().all()

        for detalle in detalles_actuales:
            devolver_inventario_por_detalle(db, detalle)

        validar_opciones(
            datos.tipo_comprobante, datos.forma_pago, datos.estado_pago, datos.unidad_medida, datos.iva_porcentaje
        )

        if datos.fecha_venta > date.today():
            raise HTTPException(status_code=400, detail="No se permite registrar ventas con fecha futura.")

        subtotal, iva, total = calcular_totales(
            datos.cantidad_unidad, datos.precio_unitario, datos.descuento, datos.iva_porcentaje
        )

        valor_recibido, saldo_pendiente = validar_reglas_pago(
            datos.estado_pago, datos.forma_pago, total, datos.valor_recibido
        )

        id_cliente = buscar_o_crear_cliente(db, datos.cliente, datos.identificacion)

        inventario = descontar_inventario(db, datos.id_inventario, datos.cantidad_quintales)

        numero_comprobante = datos.numero_comprobante.strip() if datos.numero_comprobante else venta_actual["numero_comprobante"]

        db.execute(
            text("""
                UPDATE ventas
                SET
                    id_cliente = :id_cliente, id_usuario = :id_usuario, fecha_venta = :fecha_venta,
                    tipo_comprobante = :tipo_comprobante, forma_pago = :forma_pago, estado_pago = :estado_pago,
                    subtotal = :subtotal, iva = :iva, total_venta = :total_venta, valor_recibido = :valor_recibido,
                    saldo_pendiente = :saldo_pendiente, numero_comprobante = :numero_comprobante, observacion = :observacion
                WHERE id_venta = :id_venta;
            """),
            {
                "id_cliente": id_cliente,
                "id_usuario": datos.id_usuario,
                "fecha_venta": datos.fecha_venta,
                "tipo_comprobante": "Factura",
                "forma_pago": datos.forma_pago,
                "estado_pago": datos.estado_pago,
                "subtotal": subtotal,
                "iva": iva,
                "total_venta": total,
                "valor_recibido": valor_recibido,
                "saldo_pendiente": saldo_pendiente,
                "numero_comprobante": numero_comprobante,
                "observacion": datos.observacion,
                "id_venta": id_venta
            }
        )

        db.execute(
            text("DELETE FROM detalle_ventas WHERE id_venta = :id_venta;"),
            {"id_venta": id_venta}
        )

        db.execute(
            text("""
                INSERT INTO detalle_ventas (
                    id_venta, id_producto, id_bodega, lote, cantidad, unidad_medida, precio_unitario,
                    descuento, iva_porcentaje, observacion, id_inventario, cantidad_unidad, cantidad_quintales
                )
                VALUES (
                    :id_venta, :id_producto, :id_bodega, :lote, :cantidad, :unidad_medida, :precio_unitario,
                    :descuento, :iva_porcentaje, :observacion, :id_inventario, :cantidad_unidad, :cantidad_quintales
                );
            """),
            {
                "id_venta": id_venta,
                "id_producto": inventario["id_producto"],
                "id_bodega": inventario["id_bodega"],
                "lote": inventario["lote"],
                "cantidad": datos.cantidad,
                "unidad_medida": datos.unidad_medida,
                "precio_unitario": datos.precio_unitario,
                "descuento": datos.descuento,
                "iva_porcentaje": datos.iva_porcentaje,
                "observacion": datos.observacion,
                "id_inventario": datos.id_inventario,
                "cantidad_unidad": datos.cantidad_unidad,
                "cantidad_quintales": datos.cantidad_quintales
            }
        )

        db.commit()

        return {
            "mensaje": "Venta actualizada correctamente. Inventario recalculado.",
            "id_venta": id_venta,
            "numero_comprobante": numero_comprobante,
            "total_venta": total,
            "valor_recibido": valor_recibido,
            "saldo_pendiente": saldo_pendiente
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        mensaje_amigable = formatear_error_bd(str(error))
        raise HTTPException(status_code=400, detail=mensaje_amigable)


@router.delete("/{id_venta}")
def anular_venta(id_venta: int, db: Session = Depends(get_db)):
    try:
        venta = db.execute(
            text("SELECT id_venta, estado FROM ventas WHERE id_venta = :id_venta;"),
            {"id_venta": id_venta}
        ).mappings().first()

        if venta is None:
            raise HTTPException(status_code=404, detail="Venta no encontrada.")

        if venta["estado"] is False:
            raise HTTPException(status_code=400, detail="La venta ya está anulada.")

        detalles = db.execute(
            text("SELECT * FROM detalle_ventas WHERE id_venta = :id_venta;"),
            {"id_venta": id_venta}
        ).mappings().all()

        for detalle in detalles:
            devolver_inventario_por_detalle(db, detalle)

        db.execute(
            text("""
                UPDATE ventas
                SET
                    estado = FALSE,
                    valor_recibido = 0,
                    saldo_pendiente = 0,
                    observacion = COALESCE(observacion, '') || ' | VENTA ANULADA: inventario revertido'
                WHERE id_venta = :id_venta;
            """),
            {"id_venta": id_venta}
        )

        db.commit()

        return {
            "mensaje": "Venta anulada correctamente. El inventario fue revertido.",
            "id_venta": id_venta
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"No se pudo anular la venta. Detalle: {str(error)}")