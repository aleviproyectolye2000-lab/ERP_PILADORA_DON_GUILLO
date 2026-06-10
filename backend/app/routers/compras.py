from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

from app.database import get_db


router = APIRouter(
    prefix="/api/compras",
    tags=["Compras y Báscula"]
)


class CompraCreate(BaseModel):
    id_proveedor: int
    id_usuario: int
    fecha_compra: date
    placa_vehiculo: Optional[str] = None
    chofer: Optional[str] = None
    peso_bruto: float = Field(gt=0)
    peso_tara: float = Field(ge=0)
    humedad: float = Field(ge=0, le=100)
    impurezas: float = Field(ge=0, le=100)
    precio_quintal: float = Field(gt=0)
    estado_pago: str = "Pendiente"
    observacion: Optional[str] = None


class DetalleCompraCreate(BaseModel):
    id_compra: int
    id_producto: int
    id_bodega: int
    lote: Optional[str] = None
    cantidad: float = Field(gt=0)
    precio_unitario: float = Field(gt=0)
    observacion: Optional[str] = None


class CompraCompletaCreate(BaseModel):
    nombre_proveedor: str
    identificacion: str
    id_usuario: int
    fecha_compra: date
    placa_vehiculo: Optional[str] = None
    chofer: Optional[str] = None

    peso_bruto: float = Field(gt=0)
    peso_tara: float = Field(ge=0)
    humedad: float = Field(ge=0, le=100)
    impurezas: float = Field(ge=0, le=100)

    precio_quintal: float = Field(gt=0)
    estado_pago: str = "Pendiente"
    observacion: Optional[str] = None

    id_producto: int
    id_bodega: int

    unidad_bascula: str = "Libras"
    peso_neto_libras: float = Field(gt=0)
    quintales_brutos: float = Field(gt=0)
    sacas_brutas: float = Field(gt=0)

    humedad_base: float = Field(default=14, ge=0, le=100)
    impureza_base: float = Field(default=5, ge=0, le=100)
    descuento_humedad_libras: float = Field(default=0, ge=0)
    descuento_impureza_libras: float = Field(default=0, ge=0)

    peso_liquido_libras: float = Field(gt=0)
    quintales_liquidos: float = Field(gt=0)
    sacas_liquidas: float = Field(gt=0)

    tipo_pago: str = "Por saca"
    precio_pactado: float = Field(gt=0)
    total_bruto: float = Field(ge=0)
    total_descuento: float = Field(default=0, ge=0)


class CompraUpdate(CompraCompletaCreate):
    pass


SQL_LISTAR_COMPRAS = """
    SELECT
        c.id_compra,
        c.fecha_compra,
        c.id_proveedor,
        p.nombres AS proveedor,
        p.identificacion AS identificacion_proveedor,
        c.id_usuario,
        c.placa_vehiculo,
        c.chofer,

        c.peso_bruto,
        c.peso_tara,
        c.peso_neto,

        c.humedad,
        c.impurezas,
        c.precio_quintal,

        COALESCE(c.unidad_bascula, 'Libras') AS unidad_bascula,
        COALESCE(c.peso_neto_libras, c.peso_neto) AS peso_neto_libras,
        COALESCE(c.quintales_brutos, c.peso_neto / 100) AS quintales_brutos,
        COALESCE(c.sacas_brutas, c.peso_neto / 200) AS sacas_brutas,

        COALESCE(c.humedad_base, 14) AS humedad_base,
        COALESCE(c.impureza_base, 5) AS impureza_base,
        COALESCE(c.descuento_humedad_libras, 0) AS descuento_humedad_libras,
        COALESCE(c.descuento_impureza_libras, 0) AS descuento_impureza_libras,

        COALESCE(c.peso_liquido_libras, c.peso_neto) AS peso_liquido_libras,
        COALESCE(c.quintales_liquidos, c.peso_neto / 100) AS quintales_liquidos,
        COALESCE(c.sacas_liquidas, c.peso_neto / 200) AS sacas_liquidas,

        COALESCE(c.tipo_pago, 'Por saca') AS tipo_pago,
        COALESCE(c.precio_pactado, c.precio_quintal, 0) AS precio_pactado,

        COALESCE(
            c.total_bruto,
            CASE
                WHEN COALESCE(c.tipo_pago, 'Por saca') = 'Por saca'
                    THEN COALESCE(c.sacas_brutas, c.peso_neto / 200) * COALESCE(c.precio_pactado, c.precio_quintal, 0)
                ELSE COALESCE(c.quintales_brutos, c.peso_neto / 100) * COALESCE(c.precio_pactado, c.precio_quintal, 0)
            END
        ) AS total_bruto,

        COALESCE(c.total_descuento, 0) AS total_descuento,

        CASE
            WHEN COALESCE(c.tipo_pago, 'Por saca') = 'Por saca'
                THEN COALESCE(c.sacas_liquidas, c.peso_neto / 200) * COALESCE(c.precio_pactado, c.precio_quintal, 0)
            ELSE COALESCE(c.quintales_liquidos, c.peso_neto / 100) * COALESCE(c.precio_pactado, c.precio_quintal, 0)
        END AS total_compra,

        c.estado_pago,
        c.observacion,
        c.estado

    FROM compras c
    INNER JOIN proveedores p ON c.id_proveedor = p.id_proveedor
"""


def obtener_columnas_tabla(db: Session, tabla: str):
    resultado = db.execute(
        text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :tabla;
        """),
        {"tabla": tabla}
    ).mappings().all()

    return [fila["column_name"] for fila in resultado]


def obtener_columna_existente(columnas, posibles):
    for columna in posibles:
        if columna in columnas:
            return columna
    return None


def buscar_o_crear_proveedor_interno(
    db: Session,
    identificacion: str,
    nombre_proveedor: str
):
    columnas = obtener_columnas_tabla(db, "proveedores")

    if "id_proveedor" not in columnas:
        raise HTTPException(
            status_code=500,
            detail="La tabla proveedores no tiene la columna id_proveedor."
        )

    columna_identificacion = obtener_columna_existente(
        columnas,
        [
            "identificacion",
            "cedula_ruc",
            "ruc",
            "cedula",
            "documento",
            "numero_identificacion"
        ]
    )

    columna_nombre = obtener_columna_existente(
        columnas,
        [
            "nombres",
            "nombre_proveedor",
            "proveedor",
            "nombre",
            "razon_social",
            "nombre_completo",
            "apellidos_nombres"
        ]
    )

    if columna_identificacion is None:
        raise HTTPException(
            status_code=500,
            detail="La tabla proveedores no tiene una columna de identificación reconocida."
        )

    if columna_nombre is None:
        raise HTTPException(
            status_code=500,
            detail="La tabla proveedores no tiene una columna de nombre reconocida."
        )

    proveedor_existente = db.execute(
        text(f"""
            SELECT id_proveedor
            FROM proveedores
            WHERE {columna_identificacion} = :identificacion
            LIMIT 1;
        """),
        {"identificacion": identificacion}
    ).mappings().first()

    if proveedor_existente:
        db.execute(
            text(f"""
                UPDATE proveedores
                SET {columna_nombre} = :nombre_proveedor
                WHERE id_proveedor = :id_proveedor;
            """),
            {
                "nombre_proveedor": nombre_proveedor,
                "id_proveedor": proveedor_existente["id_proveedor"]
            }
        )

        return proveedor_existente["id_proveedor"]

    columnas_insert = [columna_nombre, columna_identificacion]
    valores_insert = [":nombre_proveedor", ":identificacion"]

    parametros = {
        "nombre_proveedor": nombre_proveedor,
        "identificacion": identificacion
    }

    if "tipo_proveedor" in columnas:
        columnas_insert.append("tipo_proveedor")
        valores_insert.append(":tipo_proveedor")
        parametros["tipo_proveedor"] = "Agricultor"

    if "estado" in columnas:
        columnas_insert.append("estado")
        valores_insert.append("TRUE")

    consulta = f"""
        INSERT INTO proveedores (
            {", ".join(columnas_insert)}
        )
        VALUES (
            {", ".join(valores_insert)}
        )
        RETURNING id_proveedor;
    """

    nuevo_proveedor = db.execute(
        text(consulta),
        parametros
    ).mappings().first()

    return nuevo_proveedor["id_proveedor"]


def validar_datos_compra(datos):
    identificacion = datos.identificacion.strip()
    nombre_proveedor = datos.nombre_proveedor.strip().upper()

    if nombre_proveedor == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar el nombre del proveedor o agricultor."
        )

    if identificacion == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar la cédula o RUC del proveedor."
        )

    if not identificacion.isdigit():
        raise HTTPException(
            status_code=400,
            detail="La identificación solo debe contener números."
        )

    if len(identificacion) not in [10, 13]:
        raise HTTPException(
            status_code=400,
            detail="La identificación debe tener 10 dígitos si es cédula o 13 dígitos si es RUC."
        )

    if datos.fecha_compra > date.today():
        raise HTTPException(
            status_code=400,
            detail="No se permite registrar o actualizar compras con fecha futura."
        )

    if datos.peso_tara >= datos.peso_bruto:
        raise HTTPException(
            status_code=400,
            detail="El peso de salida no puede ser mayor o igual al peso de entrada."
        )

    peso_neto = datos.peso_bruto - datos.peso_tara

    if peso_neto <= 0:
        raise HTTPException(
            status_code=400,
            detail="El peso neto debe ser mayor a cero."
        )

    if datos.estado_pago not in ["Pagado", "Pendiente", "Parcial"]:
        raise HTTPException(
            status_code=400,
            detail="Estado de pago no válido. Use Pagado, Pendiente o Parcial."
        )

    if datos.unidad_bascula not in ["Libras", "Kilogramos", "Toneladas"]:
        raise HTTPException(
            status_code=400,
            detail="Unidad de báscula no válida."
        )

    if datos.tipo_pago not in ["Por saca", "Por quintal"]:
        raise HTTPException(
            status_code=400,
            detail="Tipo de pago no válido. Use Por saca o Por quintal."
        )

    if datos.precio_pactado <= 0:
        raise HTTPException(
            status_code=400,
            detail="El precio pactado debe ser mayor a cero."
        )

    if datos.peso_neto_libras <= 0:
        raise HTTPException(
            status_code=400,
            detail="El peso neto en libras debe ser mayor a cero."
        )

    if datos.peso_liquido_libras <= 0:
        raise HTTPException(
            status_code=400,
            detail="El peso líquido en libras debe ser mayor a cero."
        )

    if datos.quintales_liquidos <= 0:
        raise HTTPException(
            status_code=400,
            detail="Los quintales líquidos deben ser mayores a cero."
        )

    if datos.sacas_liquidas <= 0:
        raise HTTPException(
            status_code=400,
            detail="Las sacas líquidas deben ser mayores a cero."
        )

    return identificacion, nombre_proveedor, peso_neto


def calcular_precio_unitario_inventario(datos):
    if datos.tipo_pago == "Por saca":
        return round(float(datos.precio_pactado) / 2, 2)

    return round(float(datos.precio_pactado), 2)


def calcular_total_compra_correcto(datos):
    if datos.tipo_pago == "Por saca":
        return round(float(datos.sacas_liquidas) * float(datos.precio_pactado), 2)

    return round(float(datos.quintales_liquidos) * float(datos.precio_pactado), 2)


def revertir_inventario_compra(db: Session, id_compra: int):
    detalles = db.execute(
        text("""
            SELECT
                id_producto,
                id_bodega,
                lote,
                cantidad
            FROM detalle_compras
            WHERE id_compra = :id_compra;
        """),
        {"id_compra": id_compra}
    ).mappings().all()

    for detalle in detalles:
        db.execute(
            text("""
                UPDATE inventario
                SET cantidad_disponible = cantidad_disponible - :cantidad
                WHERE id_producto = :id_producto
                  AND id_bodega = :id_bodega
                  AND lote = :lote;
            """),
            {
                "cantidad": detalle["cantidad"],
                "id_producto": detalle["id_producto"],
                "id_bodega": detalle["id_bodega"],
                "lote": detalle["lote"]
            }
        )

    db.execute(
        text("""
            DELETE FROM inventario
            WHERE cantidad_disponible <= 0;
        """)
    )


def ajustar_inventario_compra_por_diferencia(
    db: Session,
    id_compra: int,
    nueva_cantidad: float,
    nuevo_id_producto: int,
    nuevo_id_bodega: int
):
    detalle_anterior = db.execute(
        text("""
            SELECT
                id_detalle_compra,
                id_producto,
                id_bodega,
                lote,
                cantidad
            FROM detalle_compras
            WHERE id_compra = :id_compra
            LIMIT 1;
        """),
        {"id_compra": id_compra}
    ).mappings().first()

    lote_reconstruido = f"LOTE-COMPRA-{id_compra}"

    if detalle_anterior is None:
        db.execute(
            text("""
                INSERT INTO detalle_compras (
                    id_compra,
                    id_producto,
                    id_bodega,
                    lote,
                    cantidad,
                    precio_unitario,
                    observacion
                )
                VALUES (
                    :id_compra,
                    :id_producto,
                    :id_bodega,
                    :lote,
                    :cantidad,
                    0,
                    'Detalle reconstruido automáticamente al actualizar compra'
                );
            """),
            {
                "id_compra": id_compra,
                "id_producto": nuevo_id_producto,
                "id_bodega": nuevo_id_bodega,
                "lote": lote_reconstruido,
                "cantidad": nueva_cantidad
            }
        )

        return {
            "id_producto": nuevo_id_producto,
            "id_bodega": nuevo_id_bodega,
            "lote": lote_reconstruido,
            "cantidad": nueva_cantidad
        }

    cantidad_anterior = float(detalle_anterior["cantidad"])
    diferencia = float(nueva_cantidad) - cantidad_anterior
    lote_actual = detalle_anterior["lote"] or lote_reconstruido

    inventario_actual = db.execute(
        text("""
            SELECT cantidad_disponible
            FROM inventario
            WHERE id_producto = :id_producto
              AND id_bodega = :id_bodega
              AND lote = :lote
            FOR UPDATE;
        """),
        {
            "id_producto": detalle_anterior["id_producto"],
            "id_bodega": detalle_anterior["id_bodega"],
            "lote": lote_actual
        }
    ).mappings().first()

    if inventario_actual is None:
        db.execute(
            text("""
                INSERT INTO inventario (
                    id_producto,
                    id_bodega,
                    lote,
                    cantidad_disponible,
                    estado_producto,
                    observacion
                )
                VALUES (
                    :id_producto,
                    :id_bodega,
                    :lote,
                    :cantidad_disponible,
                    'Disponible',
                    'Inventario reconstruido automáticamente desde actualización de compra'
                );
            """),
            {
                "id_producto": nuevo_id_producto,
                "id_bodega": nuevo_id_bodega,
                "lote": lote_actual,
                "cantidad_disponible": nueva_cantidad
            }
        )

        return detalle_anterior

    cantidad_disponible_actual = float(inventario_actual["cantidad_disponible"])
    nueva_cantidad_disponible = cantidad_disponible_actual + diferencia

    if nueva_cantidad_disponible < 0:
        cantidad_consumida = cantidad_anterior - cantidad_disponible_actual

        raise HTTPException(
            status_code=400,
            detail=(
                "No se puede reducir esta compra porque parte del arroz de este lote "
                "ya fue consumido en producción o salida de inventario. "
                f"Cantidad anterior: {cantidad_anterior} qq. "
                f"Stock actual: {cantidad_disponible_actual} qq. "
                f"Cantidad ya consumida: {cantidad_consumida} qq. "
                f"Nueva cantidad solicitada: {nueva_cantidad} qq."
            )
        )

    db.execute(
        text("""
            UPDATE inventario
            SET
                id_producto = :nuevo_id_producto,
                id_bodega = :nuevo_id_bodega,
                cantidad_disponible = :nueva_cantidad_disponible,
                fecha_ingreso = CURRENT_DATE,
                estado_producto = CASE
                    WHEN :nueva_cantidad_disponible <= 0 THEN 'Agotado'
                    ELSE 'Disponible'
                END,
                observacion = 'Inventario ajustado automáticamente por actualización de compra'
            WHERE id_producto = :id_producto_anterior
              AND id_bodega = :id_bodega_anterior
              AND lote = :lote;
        """),
        {
            "nuevo_id_producto": nuevo_id_producto,
            "nuevo_id_bodega": nuevo_id_bodega,
            "nueva_cantidad_disponible": nueva_cantidad_disponible,
            "id_producto_anterior": detalle_anterior["id_producto"],
            "id_bodega_anterior": detalle_anterior["id_bodega"],
            "lote": lote_actual
        }
    )

    return detalle_anterior


@router.get("/")
def listar_compras(db: Session = Depends(get_db)):
    try:
        resultado = db.execute(
            text(SQL_LISTAR_COMPRAS + """
                WHERE c.estado = TRUE
                ORDER BY c.id_compra DESC;
            """)
        )

        filas = resultado.mappings().all()
        return [dict(fila) for fila in filas]

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar compras. Detalle: {str(error)}"
        )


@router.get("/{id_compra}")
def obtener_compra(id_compra: int, db: Session = Depends(get_db)):
    resultado = db.execute(
        text(SQL_LISTAR_COMPRAS + """
            WHERE c.id_compra = :id_compra;
        """),
        {"id_compra": id_compra}
    )

    fila = resultado.mappings().first()

    if fila is None:
        raise HTTPException(status_code=404, detail="Compra no encontrada.")

    return dict(fila)


@router.post("/registrar-completa")
def registrar_compra_completa(
    datos: CompraCompletaCreate,
    db: Session = Depends(get_db)
):
    identificacion, nombre_proveedor, peso_neto_original = validar_datos_compra(datos)

    usuario = db.execute(
        text("""
            SELECT id_usuario
            FROM usuarios
            WHERE id_usuario = :id_usuario
              AND estado = TRUE;
        """),
        {"id_usuario": datos.id_usuario}
    ).first()

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="El usuario no existe o está inactivo."
        )

    producto = db.execute(
        text("""
            SELECT id_producto
            FROM productos
            WHERE id_producto = :id_producto
              AND estado = TRUE;
        """),
        {"id_producto": datos.id_producto}
    ).first()

    if producto is None:
        raise HTTPException(
            status_code=404,
            detail="El producto no existe o está inactivo."
        )

    bodega = db.execute(
        text("""
            SELECT id_bodega
            FROM bodegas
            WHERE id_bodega = :id_bodega
              AND estado = TRUE;
        """),
        {"id_bodega": datos.id_bodega}
    ).first()

    if bodega is None:
        raise HTTPException(
            status_code=404,
            detail="La bodega no existe o está inactiva."
        )

    try:
        id_proveedor = buscar_o_crear_proveedor_interno(
            db,
            identificacion,
            nombre_proveedor
        )

        total_compra_correcto = calcular_total_compra_correcto(datos)
        precio_unitario_inventario = calcular_precio_unitario_inventario(datos)

        compra_creada = db.execute(
            text("""
                INSERT INTO compras (
                    id_proveedor,
                    id_usuario,
                    fecha_compra,
                    placa_vehiculo,
                    chofer,
                    peso_bruto,
                    peso_tara,
                    humedad,
                    impurezas,
                    precio_quintal,
                    estado_pago,
                    observacion,
                    estado,

unidad_bascula,
peso_neto_libras,
quintales_brutos,
quintales_liquidos,
sacas_liquidas,
tipo_pago,
precio_pactado,
total_bruto,
total_descuento,
sacas_brutas,
humedad_base,
impureza_base,
descuento_humedad_libras,
descuento_impureza_libras,
peso_liquido_libras
                )
                VALUES (
                    :id_proveedor,
                    :id_usuario,
                    :fecha_compra,
                    :placa_vehiculo,
                    :chofer,
                    :peso_bruto,
                    :peso_tara,
                    :humedad,
                    :impurezas,
                    :precio_quintal,
                    :estado_pago,
                    :observacion,
                    TRUE,

            :unidad_bascula,
:peso_neto_libras,
:quintales_brutos,
:quintales_liquidos,
:sacas_liquidas,
:tipo_pago,
:precio_pactado,
:total_bruto,
:total_descuento,
:sacas_brutas,
:humedad_base,
:impureza_base,
:descuento_humedad_libras,
:descuento_impureza_libras,
:peso_liquido_libras
                )
                RETURNING
                    id_compra,
                    peso_neto,
                    precio_pactado,
                    total_bruto,
                    total_descuento;
            """),
            {
                "id_proveedor": id_proveedor,
                "id_usuario": datos.id_usuario,
                "fecha_compra": datos.fecha_compra,
                "placa_vehiculo": datos.placa_vehiculo,
                "chofer": datos.chofer,
                "peso_bruto": datos.peso_bruto,
                "peso_tara": datos.peso_tara,
                "humedad": datos.humedad,
                "impurezas": datos.impurezas,
                "precio_quintal": datos.precio_quintal,
                "estado_pago": datos.estado_pago,
                "observacion": datos.observacion,
                
                "unidad_bascula": datos.unidad_bascula,
                "peso_neto_libras": datos.peso_neto_libras,
                "quintales_brutos": datos.quintales_brutos,
                "quintales_liquidos": datos.quintales_liquidos,
                "sacas_liquidas": datos.sacas_liquidas,
                "tipo_pago": datos.tipo_pago,
                "precio_pactado": datos.precio_pactado,
                "total_bruto": datos.total_bruto,
                "total_descuento": datos.total_descuento,
                "sacas_brutas": datos.sacas_brutas,
                "humedad_base": datos.humedad_base,
                "impureza_base": datos.impureza_base,
                "descuento_humedad_libras": datos.descuento_humedad_libras,
                "descuento_impureza_libras": datos.descuento_impureza_libras,
                "peso_liquido_libras": datos.peso_liquido_libras
            }
        ).mappings().first()

        id_compra = compra_creada["id_compra"]
        lote_generado = f"LOTE-COMPRA-{id_compra}"

        detalle_creado = db.execute(
            text("""
                INSERT INTO detalle_compras (
                    id_compra,
                    id_producto,
                    id_bodega,
                    lote,
                    cantidad,
                    precio_unitario,
                    observacion
                )
                VALUES (
                    :id_compra,
                    :id_producto,
                    :id_bodega,
                    :lote,
                    :cantidad,
                    :precio_unitario,
                    :observacion
                )
                RETURNING id_detalle_compra, subtotal;
            """),
            {
                "id_compra": id_compra,
                "id_producto": datos.id_producto,
                "id_bodega": datos.id_bodega,
                "lote": lote_generado,
                "cantidad": datos.quintales_liquidos,
                "precio_unitario": precio_unitario_inventario,
                "observacion": (
                    "Ingreso automático desde compras y báscula. "
                    f"Total calculado: ${total_compra_correcto}"
                )
            }
        ).mappings().first()

        db.commit()

        return {
            "mensaje": "Compra completa registrada correctamente",
            "compra": dict(compra_creada),
            "detalle": dict(detalle_creado),
            "id_proveedor": id_proveedor,
            "lote": lote_generado,
            "total_compra_correcto": total_compra_correcto
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar la compra completa. Detalle: {str(error)}"
        )


@router.put("/{id_compra}")
def actualizar_compra(
    id_compra: int,
    datos: CompraUpdate,
    db: Session = Depends(get_db)
):
    identificacion, nombre_proveedor, peso_neto_original = validar_datos_compra(datos)

    compra_existente = db.execute(
        text("""
            SELECT id_compra
            FROM compras
            WHERE id_compra = :id_compra;
        """),
        {"id_compra": id_compra}
    ).first()

    if compra_existente is None:
        raise HTTPException(
            status_code=404,
            detail="Compra no encontrada."
        )

    try:
        id_proveedor = buscar_o_crear_proveedor_interno(
            db,
            identificacion,
            nombre_proveedor
        )

        total_compra_correcto = calcular_total_compra_correcto(datos)
        precio_unitario_inventario = calcular_precio_unitario_inventario(datos)

        detalle_anterior = ajustar_inventario_compra_por_diferencia(
            db=db,
            id_compra=id_compra,
            nueva_cantidad=datos.quintales_liquidos,
            nuevo_id_producto=datos.id_producto,
            nuevo_id_bodega=datos.id_bodega
        )

        db.execute(
            text("""
                UPDATE compras
                SET
                    id_proveedor = :id_proveedor,
                    id_usuario = :id_usuario,
                    fecha_compra = :fecha_compra,
                    placa_vehiculo = :placa_vehiculo,
                    chofer = :chofer,
                    peso_bruto = :peso_bruto,
                    peso_tara = :peso_tara,
                    humedad = :humedad,
                    impurezas = :impurezas,
                    precio_quintal = :precio_quintal,
                    estado_pago = :estado_pago,
                    observacion = :observacion,
                    estado = TRUE,

                    unidad_bascula = :unidad_bascula,
                    peso_neto_libras = :peso_neto_libras,
                    quintales_brutos = :quintales_brutos,
                    quintales_liquidos = :quintales_liquidos,
                    sacas_liquidas = :sacas_liquidas,
                    tipo_pago = :tipo_pago,
                    precio_pactado = :precio_pactado,
                    total_bruto = :total_bruto,
                    total_descuento = :total_descuento,
                    sacas_brutas = :sacas_brutas,
                    humedad_base = :humedad_base,
                    impureza_base = :impureza_base,
                    descuento_humedad_libras = :descuento_humedad_libras,
                    descuento_impureza_libras = :descuento_impureza_libras,
                    peso_liquido_libras = :peso_liquido_libras
                WHERE id_compra = :id_compra;
            """),
            {
                "id_compra": id_compra,
                "id_proveedor": id_proveedor,
                "id_usuario": datos.id_usuario,
                "fecha_compra": datos.fecha_compra,
                "placa_vehiculo": datos.placa_vehiculo,
                "chofer": datos.chofer,
                "peso_bruto": datos.peso_bruto,
                "peso_tara": datos.peso_tara,
                "humedad": datos.humedad,
                "impurezas": datos.impurezas,
                "precio_quintal": datos.precio_quintal,
                "estado_pago": datos.estado_pago,
                "observacion": datos.observacion,
                "unidad_bascula": datos.unidad_bascula,
                "peso_neto_libras": datos.peso_neto_libras,
                "quintales_brutos": datos.quintales_brutos,
                "quintales_liquidos": datos.quintales_liquidos,
                "sacas_liquidas": datos.sacas_liquidas,
                "tipo_pago": datos.tipo_pago,
                "precio_pactado": datos.precio_pactado,
                "total_bruto": datos.total_bruto,
                "total_descuento": datos.total_descuento,
                "sacas_brutas": datos.sacas_brutas,
                "humedad_base": datos.humedad_base,
                "impureza_base": datos.impureza_base,
                "descuento_humedad_libras": datos.descuento_humedad_libras,
                "descuento_impureza_libras": datos.descuento_impureza_libras,
                "peso_liquido_libras": datos.peso_liquido_libras
            }
        )

        db.execute(
            text("""
                UPDATE detalle_compras
                SET
                    id_producto = :id_producto,
                    id_bodega = :id_bodega,
                    cantidad = :cantidad,
                    precio_unitario = :precio_unitario,
                    observacion = :observacion
                WHERE id_compra = :id_compra;
            """),
            {
                "id_compra": id_compra,
                "id_producto": datos.id_producto,
                "id_bodega": datos.id_bodega,
                "cantidad": datos.quintales_liquidos,
                "precio_unitario": precio_unitario_inventario,
                "observacion": (
                    "Detalle actualizado desde compras y báscula. "
                    f"Total calculado: ${total_compra_correcto}"
                )
            }
        )

        db.commit()

        return {
            "mensaje": "Compra actualizada correctamente",
            "id_compra": id_compra,
            "id_proveedor": id_proveedor,
            "peso_neto_original": peso_neto_original,
            "quintales_liquidos": datos.quintales_liquidos,
            "total_compra_correcto": total_compra_correcto,
            "lote": detalle_anterior["lote"]
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo actualizar la compra. Detalle: {str(error)}"
        )


@router.delete("/{id_compra}")
def eliminar_compra_definitiva(
    id_compra: int,
    db: Session = Depends(get_db)
):
    compra_existente = db.execute(
        text("""
            SELECT id_compra
            FROM compras
            WHERE id_compra = :id_compra;
        """),
        {"id_compra": id_compra}
    ).first()

    if compra_existente is None:
        raise HTTPException(
            status_code=404,
            detail="Compra no encontrada."
        )

    try:
        revertir_inventario_compra(db, id_compra)

        db.execute(
            text("""
                DELETE FROM detalle_compras
                WHERE id_compra = :id_compra;
            """),
            {"id_compra": id_compra}
        )

        db.execute(
            text("""
                DELETE FROM compras
                WHERE id_compra = :id_compra;
            """),
            {"id_compra": id_compra}
        )

        db.commit()

        return {
            "mensaje": "Compra eliminada definitivamente de la base de datos",
            "id_compra": id_compra
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo eliminar la compra. Detalle: {str(error)}"
        )


@router.post("/")
def crear_compra(compra: CompraCreate, db: Session = Depends(get_db)):
    if compra.fecha_compra > date.today():
        raise HTTPException(
            status_code=400,
            detail="No se permite registrar compras con fecha futura."
        )

    if compra.peso_tara >= compra.peso_bruto:
        raise HTTPException(
            status_code=400,
            detail="El peso de salida no puede ser mayor o igual al peso de entrada."
        )

    peso_neto = compra.peso_bruto - compra.peso_tara

    if peso_neto <= 0:
        raise HTTPException(
            status_code=400,
            detail="El peso neto debe ser mayor a cero."
        )

    if compra.estado_pago not in ["Pagado", "Pendiente", "Parcial"]:
        raise HTTPException(
            status_code=400,
            detail="Estado de pago no válido. Use Pagado, Pendiente o Parcial."
        )

    proveedor = db.execute(
        text("""
            SELECT id_proveedor
            FROM proveedores
            WHERE id_proveedor = :id_proveedor;
        """),
        {"id_proveedor": compra.id_proveedor}
    ).first()

    if proveedor is None:
        raise HTTPException(
            status_code=404,
            detail="El proveedor no existe."
        )

    usuario = db.execute(
        text("""
            SELECT id_usuario
            FROM usuarios
            WHERE id_usuario = :id_usuario
              AND estado = TRUE;
        """),
        {"id_usuario": compra.id_usuario}
    ).first()

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="El usuario no existe o está inactivo."
        )

    try:
        resultado = db.execute(
            text("""
                INSERT INTO compras (
                    id_proveedor,
                    id_usuario,
                    fecha_compra,
                    placa_vehiculo,
                    chofer,
                    peso_bruto,
                    peso_tara,
                    humedad,
                    impurezas,
                    precio_quintal,
                    estado_pago,
                    observacion,
                    estado
                )
                VALUES (
                    :id_proveedor,
                    :id_usuario,
                    :fecha_compra,
                    :placa_vehiculo,
                    :chofer,
                    :peso_bruto,
                    :peso_tara,
                    :humedad,
                    :impurezas,
                    :precio_quintal,
                    :estado_pago,
                    :observacion,
                    TRUE
                )
                RETURNING id_compra, peso_neto;
            """),
            compra.model_dump()
        )

        nueva_compra = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Compra registrada correctamente",
            "compra": dict(nueva_compra)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar la compra. Detalle: {str(error)}"
        )


@router.post("/detalle")
def crear_detalle_compra(
    detalle: DetalleCompraCreate,
    db: Session = Depends(get_db)
):
    compra = db.execute(
        text("""
            SELECT id_compra
            FROM compras
            WHERE id_compra = :id_compra
              AND estado = TRUE;
        """),
        {"id_compra": detalle.id_compra}
    ).first()

    if compra is None:
        raise HTTPException(
            status_code=404,
            detail="La compra no existe o está inactiva."
        )

    producto = db.execute(
        text("""
            SELECT id_producto
            FROM productos
            WHERE id_producto = :id_producto
              AND estado = TRUE;
        """),
        {"id_producto": detalle.id_producto}
    ).first()

    if producto is None:
        raise HTTPException(
            status_code=404,
            detail="El producto no existe o está inactivo."
        )

    bodega = db.execute(
        text("""
            SELECT id_bodega
            FROM bodegas
            WHERE id_bodega = :id_bodega
              AND estado = TRUE;
        """),
        {"id_bodega": detalle.id_bodega}
    ).first()

    if bodega is None:
        raise HTTPException(
            status_code=404,
            detail="La bodega no existe o está inactiva."
        )

    try:
        resultado = db.execute(
            text("""
                INSERT INTO detalle_compras (
                    id_compra,
                    id_producto,
                    id_bodega,
                    lote,
                    cantidad,
                    precio_unitario,
                    observacion
                )
                VALUES (
                    :id_compra,
                    :id_producto,
                    :id_bodega,
                    :lote,
                    :cantidad,
                    :precio_unitario,
                    :observacion
                )
                RETURNING id_detalle_compra, subtotal;
            """),
            detalle.model_dump()
        )

        nuevo_detalle = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Detalle de compra registrado correctamente. Inventario actualizado automáticamente por trigger.",
            "detalle": dict(nuevo_detalle)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar el detalle de compra. Detalle: {str(error)}"
        )