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
    prefix="/api/produccion",
    tags=["Producción y Pilado"]
)


class OrdenPiladoCreate(BaseModel):
    numero_orden: str
    id_usuario: int
    fecha_pilado: date
    lote_origen: str
    tipo_arroz_procesado: str
    cantidad_procesada: float = Field(gt=0)
    maquina_utilizada: Optional[str] = None
    operador: str
    arroz_pilado_obtenido: float = Field(ge=0)
    arrocillo_obtenido: float = Field(ge=0)
    polvillo_obtenido: float = Field(ge=0)
    cascarilla_obtenida: float = Field(ge=0)
    tamo_obtenido: float = Field(ge=0)
    merma: float = Field(ge=0)
    estado_pilado: str = "Finalizado"
    observacion: Optional[str] = None


class DetalleProduccionCreate(BaseModel):
    id_orden_pilado: int
    id_producto: int
    id_bodega: int
    lote_destino: Optional[str] = None
    tipo_resultado: str
    cantidad_obtenida: float = Field(gt=0)
    observacion: Optional[str] = None


def validar_orden(orden: OrdenPiladoCreate):
    total_salida = (
        orden.arroz_pilado_obtenido
        + orden.arrocillo_obtenido
        + orden.polvillo_obtenido
        + orden.cascarilla_obtenida
        + orden.tamo_obtenido
        + orden.merma
    )

    if orden.fecha_pilado > date.today():
        raise HTTPException(
            status_code=400,
            detail="No se permite registrar producción con fecha futura."
        )

    if orden.arroz_pilado_obtenido <= 0:
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar la cantidad de arroz pilado obtenido."
        )

    if total_salida > orden.cantidad_procesada:
        raise HTTPException(
            status_code=400,
            detail="La suma de arroz pilado, subproductos y merma no puede superar la cantidad procesada."
        )

    if orden.estado_pilado not in ["Finalizado", "En proceso", "Observado", "Anulado"]:
        raise HTTPException(
            status_code=400,
            detail="Estado de pilado no válido. Use Finalizado, En proceso, Observado o Anulado."
        )


def verificar_numero_orden_unico(
    db: Session,
    numero_orden: str,
    id_orden_ignorar: Optional[int] = None
):
    consulta = """
        SELECT id_orden_pilado
        FROM ordenes_pilado
        WHERE LOWER(numero_orden) = LOWER(:numero_orden)
          AND estado = TRUE
    """

    parametros = {"numero_orden": numero_orden}

    if id_orden_ignorar is not None:
        consulta += " AND id_orden_pilado <> :id_orden_pilado"
        parametros["id_orden_pilado"] = id_orden_ignorar

    resultado = db.execute(text(consulta), parametros).mappings().first()

    if resultado:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una orden activa con ese número."
        )


def obtener_lote_arroz_cascara(db: Session, lote_origen: str):
    resultado = db.execute(
        text("""
            SELECT
                i.id_inventario,
                i.id_producto,
                i.id_bodega,
                i.lote,
                i.cantidad_disponible,
                i.estado_producto,
                p.nombre_producto,
                p.tipo_producto,
                b.nombre_bodega
            FROM inventario i
            INNER JOIN productos p ON i.id_producto = p.id_producto
            INNER JOIN bodegas b ON i.id_bodega = b.id_bodega
            WHERE i.lote = :lote_origen
              AND LOWER(p.nombre_producto) LIKE '%arroz en cáscara%'
              AND LOWER(p.tipo_producto) LIKE '%materia prima%'
            LIMIT 1;
        """),
        {"lote_origen": lote_origen}
    ).mappings().first()

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe inventario de arroz en cáscara para el lote {lote_origen}."
        )

    return dict(resultado)


def validar_stock_lote(db: Session, lote_origen: str, cantidad_procesada: float):
    lote = obtener_lote_arroz_cascara(db, lote_origen)
    stock_actual = float(lote["cantidad_disponible"] or 0)

    if stock_actual < cantidad_procesada:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Lote {lote_origen}: {stock_actual:.2f} qq disponibles, solicitado {cantidad_procesada:.2f} qq."
        )

    return lote


def actualizar_estado_inventario(db: Session, id_inventario: int):
    db.execute(
        text("""
            UPDATE inventario
            SET estado_producto = CASE
                WHEN cantidad_disponible <= 0 THEN 'Agotado'
                ELSE 'Disponible'
            END
            WHERE id_inventario = :id_inventario;
        """),
        {"id_inventario": id_inventario}
    )


def aumentar_inventario_por_id(db: Session, id_inventario: int, cantidad: float):
    db.execute(
        text("""
            UPDATE inventario
            SET
                cantidad_disponible = cantidad_disponible + :cantidad,
                estado_producto = 'Disponible',
                observacion = 'Inventario reversado por anulación o actualización de producción'
            WHERE id_inventario = :id_inventario;
        """),
        {
            "id_inventario": id_inventario,
            "cantidad": cantidad
        }
    )

    actualizar_estado_inventario(db, id_inventario)


def descontar_inventario_por_id(db: Session, id_inventario: int, cantidad: float):
    inventario = db.execute(
        text("""
            SELECT id_inventario, cantidad_disponible
            FROM inventario
            WHERE id_inventario = :id_inventario;
        """),
        {"id_inventario": id_inventario}
    ).mappings().first()

    if not inventario:
        raise HTTPException(
            status_code=404,
            detail="No existe el inventario que se desea descontar."
        )

    stock_actual = float(inventario["cantidad_disponible"] or 0)

    if stock_actual < cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede reversar o descontar inventario. Stock actual {stock_actual:.2f} qq, cantidad requerida {cantidad:.2f} qq. Puede que ese producto ya haya sido vendido o usado."
        )

    db.execute(
        text("""
            UPDATE inventario
            SET
                cantidad_disponible = cantidad_disponible - :cantidad,
                observacion = 'Inventario descontado por reverso o actualización de producción'
            WHERE id_inventario = :id_inventario;
        """),
        {
            "id_inventario": id_inventario,
            "cantidad": cantidad
        }
    )

    actualizar_estado_inventario(db, id_inventario)


def buscar_producto_por_codigo(db: Session, codigo: str):
    resultado = db.execute(
        text("""
            SELECT id_producto, codigo, nombre_producto, tipo_producto
            FROM productos
            WHERE UPPER(codigo) = UPPER(:codigo)
              AND estado = TRUE
            LIMIT 1;
        """),
        {"codigo": codigo}
    ).mappings().first()

    return dict(resultado) if resultado else None


def buscar_producto_por_nombre(db: Session, nombre: str):
    resultado = db.execute(
        text("""
            SELECT id_producto, codigo, nombre_producto, tipo_producto
            FROM productos
            WHERE LOWER(nombre_producto) LIKE LOWER(:nombre)
              AND estado = TRUE
            LIMIT 1;
        """),
        {"nombre": f"%{nombre}%"}
    ).mappings().first()

    return dict(resultado) if resultado else None


def buscar_bodega_por_nombre(db: Session, nombre: str):
    resultado = db.execute(
        text("""
            SELECT id_bodega, nombre_bodega
            FROM bodegas
            WHERE LOWER(nombre_bodega) LIKE LOWER(:nombre)
              AND estado = TRUE
            LIMIT 1;
        """),
        {"nombre": f"%{nombre}%"}
    ).mappings().first()

    return dict(resultado) if resultado else None


def obtener_producto_arroz_pilado(db: Session, tipo_arroz_procesado: str):
    tipo = str(tipo_arroz_procesado or "").lower()

    if "clasificado" in tipo or "viejo" in tipo or "natural" in tipo:
        producto = buscar_producto_por_codigo(db, "ARZ-PIL-CLA")
        if producto:
            return producto

    if "corriente" in tipo or "fresco" in tipo:
        producto = buscar_producto_por_codigo(db, "ARZ-PIL-COR")
        if producto:
            return producto

    if "envejecido" in tipo or "horno" in tipo or "procesado" in tipo:
        producto = buscar_producto_por_codigo(db, "ARZ-ENV")
        if producto:
            return producto

    producto = buscar_producto_por_nombre(db, "arroz pilado")
    if producto:
        return producto

    raise HTTPException(
        status_code=400,
        detail="No existe el producto terminado correspondiente al tipo de arroz procesado."
    )


def insertar_detalle_produccion(
    db: Session,
    id_orden_pilado: int,
    id_producto: int,
    id_bodega: int,
    lote_destino: str,
    tipo_resultado: str,
    cantidad_obtenida: float,
    observacion: str
):
    if cantidad_obtenida <= 0:
        return

    db.execute(
        text("""
            INSERT INTO detalle_produccion (
                id_orden_pilado,
                id_producto,
                id_bodega,
                lote_destino,
                tipo_resultado,
                cantidad_obtenida,
                observacion
            )
            VALUES (
                :id_orden_pilado,
                :id_producto,
                :id_bodega,
                :lote_destino,
                :tipo_resultado,
                :cantidad_obtenida,
                :observacion
            );
        """),
        {
            "id_orden_pilado": id_orden_pilado,
            "id_producto": id_producto,
            "id_bodega": id_bodega,
            "lote_destino": lote_destino,
            "tipo_resultado": tipo_resultado,
            "cantidad_obtenida": cantidad_obtenida,
            "observacion": observacion
        }
    )


def crear_detalles_automaticos(db: Session, id_orden_pilado: int, orden: OrdenPiladoCreate):
    bodega_producto = buscar_bodega_por_nombre(db, "producto terminado")
    bodega_subproducto = buscar_bodega_por_nombre(db, "subproductos")

    if not bodega_producto:
        raise HTTPException(
            status_code=400,
            detail="No existe la bodega de producto terminado."
        )

    if not bodega_subproducto:
        raise HTTPException(
            status_code=400,
            detail="No existe la bodega de subproductos."
        )

    producto_pilado = obtener_producto_arroz_pilado(db, orden.tipo_arroz_procesado)

    lote_base = f"PROD-{orden.lote_origen}"

    insertar_detalle_produccion(
        db=db,
        id_orden_pilado=id_orden_pilado,
        id_producto=producto_pilado["id_producto"],
        id_bodega=bodega_producto["id_bodega"],
        lote_destino=f"{lote_base}-PILADO",
        tipo_resultado="Producto terminado",
        cantidad_obtenida=orden.arroz_pilado_obtenido,
        observacion="Arroz pilado generado automáticamente por producción"
    )

    subproductos = [
        ("ARROCILLO", "Arrocillo", orden.arrocillo_obtenido),
        ("POLVILLO", "Polvillo", orden.polvillo_obtenido),
        ("CASCARILLA", "Cascarilla", orden.cascarilla_obtenida),
        ("TAMO", "Tamo", orden.tamo_obtenido),
    ]

    for codigo, nombre, cantidad in subproductos:
        if cantidad > 0:
            producto = buscar_producto_por_codigo(db, codigo)

            if not producto:
                producto = buscar_producto_por_nombre(db, nombre)

            if not producto:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ingresó {cantidad} qq de {nombre}, pero ese producto no existe en productos."
                )

            insertar_detalle_produccion(
                db=db,
                id_orden_pilado=id_orden_pilado,
                id_producto=producto["id_producto"],
                id_bodega=bodega_subproducto["id_bodega"],
                lote_destino=f"{lote_base}-{codigo}",
                tipo_resultado="Subproducto",
                cantidad_obtenida=cantidad,
                observacion=f"{nombre} generado automáticamente por producción"
            )


def obtener_detalles_orden(db: Session, id_orden_pilado: int):
    resultado = db.execute(
        text("""
            SELECT
                id_detalle_produccion,
                id_producto,
                id_bodega,
                lote_destino,
                tipo_resultado,
                cantidad_obtenida
            FROM detalle_produccion
            WHERE id_orden_pilado = :id_orden_pilado;
        """),
        {"id_orden_pilado": id_orden_pilado}
    ).mappings().all()

    return [dict(fila) for fila in resultado]


def reversar_detalles_produccion(db: Session, id_orden_pilado: int):
    detalles = obtener_detalles_orden(db, id_orden_pilado)

    for detalle in detalles:
        inventario = db.execute(
            text("""
                SELECT id_inventario, cantidad_disponible
                FROM inventario
                WHERE id_producto = :id_producto
                  AND id_bodega = :id_bodega
                  AND lote = :lote
                LIMIT 1;
            """),
            {
                "id_producto": detalle["id_producto"],
                "id_bodega": detalle["id_bodega"],
                "lote": detalle["lote_destino"]
            }
        ).mappings().first()

        if inventario:
            descontar_inventario_por_id(
                db=db,
                id_inventario=int(inventario["id_inventario"]),
                cantidad=float(detalle["cantidad_obtenida"] or 0)
            )

    db.execute(
        text("""
            DELETE FROM detalle_produccion
            WHERE id_orden_pilado = :id_orden_pilado;
        """),
        {"id_orden_pilado": id_orden_pilado}
    )


def reversar_arroz_cascara(db: Session, orden_anterior):
    lote = obtener_lote_arroz_cascara(db, orden_anterior["lote_origen"])

    aumentar_inventario_por_id(
        db=db,
        id_inventario=int(lote["id_inventario"]),
        cantidad=float(orden_anterior["cantidad_procesada"] or 0)
    )


def descontar_arroz_cascara_para_actualizacion(db: Session, orden_nueva: OrdenPiladoCreate):
    lote = validar_stock_lote(
        db=db,
        lote_origen=orden_nueva.lote_origen,
        cantidad_procesada=orden_nueva.cantidad_procesada
    )

    descontar_inventario_por_id(
        db=db,
        id_inventario=int(lote["id_inventario"]),
        cantidad=float(orden_nueva.cantidad_procesada)
    )


def obtener_orden_directa(db: Session, id_orden_pilado: int):
    resultado = db.execute(
        text("""
            SELECT *
            FROM ordenes_pilado
            WHERE id_orden_pilado = :id_orden_pilado;
        """),
        {"id_orden_pilado": id_orden_pilado}
    ).mappings().first()

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Orden de pilado no encontrada."
        )

    return dict(resultado)


@router.get("/")
def listar_produccion(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                id_orden_pilado,
                numero_orden,
                id_usuario,
                fecha_pilado,
                lote_origen,
                tipo_arroz_procesado,
                cantidad_procesada,
                maquina_utilizada,
                operador,
                arroz_pilado_obtenido,
                arrocillo_obtenido,
                polvillo_obtenido,
                cascarilla_obtenida,
                tamo_obtenido,
                merma,
                rendimiento_porcentaje,
                estado_pilado,
                observacion,
                estado
            FROM ordenes_pilado
            ORDER BY fecha_pilado DESC, id_orden_pilado DESC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.get("/siguiente-numero")
def generar_siguiente_numero(db: Session = Depends(get_db)):
    fecha = datetime.now().strftime("%Y%m%d")
    caracteres = string.ascii_uppercase + string.digits

    while True:
        codigo = "".join(random.choices(caracteres, k=6))
        numero_orden = f"OP-{fecha}-{codigo}"

        existe = db.execute(
            text("""
                SELECT id_orden_pilado
                FROM ordenes_pilado
                WHERE numero_orden = :numero_orden
                LIMIT 1;
            """),
            {"numero_orden": numero_orden}
        ).mappings().first()

        if not existe:
            return {"numero_orden": numero_orden}


@router.get("/{id_orden_pilado}")
def obtener_orden_pilado(id_orden_pilado: int, db: Session = Depends(get_db)):
    orden = obtener_orden_directa(db, id_orden_pilado)
    orden["detalles"] = obtener_detalles_orden(db, id_orden_pilado)
    return orden


@router.post("/")
def crear_orden_pilado(orden: OrdenPiladoCreate, db: Session = Depends(get_db)):
    validar_orden(orden)
    verificar_numero_orden_unico(db, orden.numero_orden)
    validar_stock_lote(db, orden.lote_origen, orden.cantidad_procesada)

    consulta = text("""
        INSERT INTO ordenes_pilado (
            numero_orden,
            id_usuario,
            fecha_pilado,
            lote_origen,
            tipo_arroz_procesado,
            cantidad_procesada,
            maquina_utilizada,
            operador,
            arroz_pilado_obtenido,
            arrocillo_obtenido,
            polvillo_obtenido,
            cascarilla_obtenida,
            tamo_obtenido,
            merma,
            estado_pilado,
            observacion
        )
        VALUES (
            :numero_orden,
            :id_usuario,
            :fecha_pilado,
            :lote_origen,
            :tipo_arroz_procesado,
            :cantidad_procesada,
            :maquina_utilizada,
            :operador,
            :arroz_pilado_obtenido,
            :arrocillo_obtenido,
            :polvillo_obtenido,
            :cascarilla_obtenida,
            :tamo_obtenido,
            :merma,
            :estado_pilado,
            :observacion
        )
        RETURNING id_orden_pilado, numero_orden, rendimiento_porcentaje;
    """)

    try:
        resultado = db.execute(consulta, orden.model_dump())
        nueva_orden = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Orden de pilado registrada correctamente.",
            "orden": dict(nueva_orden)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar la orden de pilado. Detalle: {str(error)}"
        )


@router.post("/registrar-completa")
def registrar_produccion_completa(orden: OrdenPiladoCreate, db: Session = Depends(get_db)):
    validar_orden(orden)
    verificar_numero_orden_unico(db, orden.numero_orden)
    validar_stock_lote(db, orden.lote_origen, orden.cantidad_procesada)

    consulta = text("""
        INSERT INTO ordenes_pilado (
            numero_orden,
            id_usuario,
            fecha_pilado,
            lote_origen,
            tipo_arroz_procesado,
            cantidad_procesada,
            maquina_utilizada,
            operador,
            arroz_pilado_obtenido,
            arrocillo_obtenido,
            polvillo_obtenido,
            cascarilla_obtenida,
            tamo_obtenido,
            merma,
            estado_pilado,
            observacion
        )
        VALUES (
            :numero_orden,
            :id_usuario,
            :fecha_pilado,
            :lote_origen,
            :tipo_arroz_procesado,
            :cantidad_procesada,
            :maquina_utilizada,
            :operador,
            :arroz_pilado_obtenido,
            :arrocillo_obtenido,
            :polvillo_obtenido,
            :cascarilla_obtenida,
            :tamo_obtenido,
            :merma,
            :estado_pilado,
            :observacion
        )
        RETURNING id_orden_pilado, numero_orden, rendimiento_porcentaje;
    """)

    try:
        resultado = db.execute(consulta, orden.model_dump())
        nueva_orden = resultado.mappings().first()
        id_orden_pilado = int(nueva_orden["id_orden_pilado"])

        crear_detalles_automaticos(
            db=db,
            id_orden_pilado=id_orden_pilado,
            orden=orden
        )

        db.commit()

        return {
            "mensaje": "Producción registrada correctamente. El trigger descontó arroz en cáscara y los detalles agregaron productos al inventario.",
            "orden": dict(nueva_orden)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar la producción completa. Detalle: {str(error)}"
        )


@router.post("/detalle")
def crear_detalle_produccion(detalle: DetalleProduccionCreate, db: Session = Depends(get_db)):
    if detalle.tipo_resultado not in ["Producto terminado", "Subproducto", "Merma"]:
        raise HTTPException(
            status_code=400,
            detail="Tipo de resultado no válido. Use Producto terminado, Subproducto o Merma."
        )

    consulta_orden = db.execute(
        text("""
            SELECT id_orden_pilado
            FROM ordenes_pilado
            WHERE id_orden_pilado = :id_orden_pilado
              AND estado = TRUE;
        """),
        {"id_orden_pilado": detalle.id_orden_pilado}
    ).first()

    if consulta_orden is None:
        raise HTTPException(
            status_code=404,
            detail="La orden de pilado no existe o está anulada."
        )

    consulta = text("""
        INSERT INTO detalle_produccion (
            id_orden_pilado,
            id_producto,
            id_bodega,
            lote_destino,
            tipo_resultado,
            cantidad_obtenida,
            observacion
        )
        VALUES (
            :id_orden_pilado,
            :id_producto,
            :id_bodega,
            :lote_destino,
            :tipo_resultado,
            :cantidad_obtenida,
            :observacion
        )
        RETURNING id_detalle_produccion;
    """)

    try:
        resultado = db.execute(consulta, detalle.model_dump())
        nuevo_detalle = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Detalle de producción registrado correctamente.",
            "detalle": dict(nuevo_detalle)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar el detalle de producción. Detalle: {str(error)}"
        )


@router.put("/{id_orden_pilado}")
def actualizar_orden_pilado(
    id_orden_pilado: int,
    orden: OrdenPiladoCreate,
    db: Session = Depends(get_db)
):
    validar_orden(orden)
    verificar_numero_orden_unico(db, orden.numero_orden, id_orden_pilado)

    orden_anterior = obtener_orden_directa(db, id_orden_pilado)

    if orden_anterior.get("estado") is False or orden_anterior.get("estado_pilado") == "Anulado":
        raise HTTPException(
            status_code=400,
            detail="No se puede editar una orden anulada."
        )

    try:
        reversar_arroz_cascara(db, orden_anterior)
        reversar_detalles_produccion(db, id_orden_pilado)
        descontar_arroz_cascara_para_actualizacion(db, orden)

        db.execute(
            text("""
                UPDATE ordenes_pilado
                SET
                    numero_orden = :numero_orden,
                    id_usuario = :id_usuario,
                    fecha_pilado = :fecha_pilado,
                    lote_origen = :lote_origen,
                    tipo_arroz_procesado = :tipo_arroz_procesado,
                    cantidad_procesada = :cantidad_procesada,
                    maquina_utilizada = :maquina_utilizada,
                    operador = :operador,
                    arroz_pilado_obtenido = :arroz_pilado_obtenido,
                    arrocillo_obtenido = :arrocillo_obtenido,
                    polvillo_obtenido = :polvillo_obtenido,
                    cascarilla_obtenida = :cascarilla_obtenida,
                    tamo_obtenido = :tamo_obtenido,
                    merma = :merma,
                    estado_pilado = :estado_pilado,
                    observacion = :observacion,
                    estado = TRUE
                WHERE id_orden_pilado = :id_orden_pilado;
            """),
            {
                **orden.model_dump(),
                "id_orden_pilado": id_orden_pilado
            }
        )

        crear_detalles_automaticos(
            db=db,
            id_orden_pilado=id_orden_pilado,
            orden=orden
        )

        db.commit()

        return {
            "mensaje": "Orden de pilado actualizada correctamente. El inventario fue reversado y recalculado.",
            "id_orden_pilado": id_orden_pilado
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo actualizar la orden de pilado. Detalle: {str(error)}"
        )


@router.delete("/{id_orden_pilado}")
def anular_orden_pilado(id_orden_pilado: int, db: Session = Depends(get_db)):
    orden_anterior = obtener_orden_directa(db, id_orden_pilado)

    if orden_anterior.get("estado") is False or orden_anterior.get("estado_pilado") == "Anulado":
        raise HTTPException(
            status_code=400,
            detail="La orden de pilado ya se encuentra anulada."
        )

    try:
        reversar_arroz_cascara(db, orden_anterior)
        reversar_detalles_produccion(db, id_orden_pilado)

        db.execute(
            text("""
                UPDATE ordenes_pilado
                SET
                    estado = FALSE,
                    estado_pilado = 'Anulado',
                    observacion = COALESCE(observacion, '') || ' | ORDEN ANULADA: inventario reversado.'
                WHERE id_orden_pilado = :id_orden_pilado;
            """),
            {"id_orden_pilado": id_orden_pilado}
        )

        db.commit()

        return {
            "mensaje": "Orden de pilado anulada correctamente. El inventario fue reversado.",
            "id_orden_pilado": id_orden_pilado
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo anular la orden de pilado. Detalle: {str(error)}"
        )