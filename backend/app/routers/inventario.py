from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db


router = APIRouter(
    prefix="/api/inventario",
    tags=["Inventario y Bodega"]
)


# ======================================================
# MODELOS PYDANTIC
# ======================================================

class ProductoCreate(BaseModel):
    codigo: str
    nombre_producto: str
    tipo_producto: str
    unidad_medida: str
    precio_referencial: float = Field(ge=0)
    stock_minimo: float = Field(ge=0)


class ProductoUpdate(BaseModel):
    codigo: str
    nombre_producto: str
    tipo_producto: str
    unidad_medida: str
    precio_referencial: float = Field(ge=0)
    stock_minimo: float = Field(ge=0)


class BodegaCreate(BaseModel):
    nombre_bodega: str
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = None


class BodegaUpdate(BaseModel):
    nombre_bodega: str
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = None


class InventarioCreate(BaseModel):
    id_producto: int
    id_bodega: int
    lote: Optional[str] = None
    cantidad_disponible: float = Field(ge=0)
    stock_minimo: Optional[float] = Field(default=None, ge=0)
    precio_referencial: Optional[float] = Field(default=None, ge=0)
    estado_producto: str = "Disponible"
    observacion: Optional[str] = None


class InventarioUpdate(BaseModel):
    id_producto: int
    id_bodega: int
    lote: Optional[str] = None
    cantidad_disponible: float = Field(ge=0)
    stock_minimo: float = Field(ge=0)
    precio_referencial: float = Field(ge=0)
    estado_producto: str = "Disponible"
    observacion: Optional[str] = None


# ======================================================
# FUNCIONES AUXILIARES
# ======================================================

def validar_estado_producto(estado: str):
    estados_validos = ["Disponible", "Reservado", "Agotado", "Inactivo"]

    if estado not in estados_validos:
        raise HTTPException(
            status_code=400,
            detail="Estado de inventario no válido. Use Disponible, Reservado, Agotado o Inactivo."
        )


def validar_tipo_producto(tipo_producto: str):
    tipos_validos = ["Materia prima", "Producto terminado", "Subproducto"]

    if tipo_producto not in tipos_validos:
        raise HTTPException(
            status_code=400,
            detail="Tipo de producto no válido. Use Materia prima, Producto terminado o Subproducto."
        )


def validar_producto_existe(db: Session, id_producto: int):
    producto = db.execute(
        text("""
            SELECT id_producto
            FROM productos
            WHERE id_producto = :id_producto
              AND estado = TRUE;
        """),
        {"id_producto": id_producto}
    ).first()

    if producto is None:
        raise HTTPException(
            status_code=404,
            detail="El producto no existe o está inactivo."
        )


def validar_bodega_existe(db: Session, id_bodega: int):
    bodega = db.execute(
        text("""
            SELECT id_bodega
            FROM bodegas
            WHERE id_bodega = :id_bodega
              AND estado = TRUE;
        """),
        {"id_bodega": id_bodega}
    ).first()

    if bodega is None:
        raise HTTPException(
            status_code=404,
            detail="La bodega no existe o está inactiva."
        )


def limpiar_lote(lote: Optional[str]):
    if lote is None:
        return "SIN-LOTE"

    lote_limpio = lote.strip().upper()

    if lote_limpio == "":
        return "SIN-LOTE"

    return lote_limpio


# ======================================================
# PRODUCTOS
# ======================================================

@router.get("/productos")
def listar_productos(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                id_producto,
                codigo,
                nombre_producto,
                tipo_producto,
                unidad_medida,
                precio_referencial,
                stock_minimo,
                estado
            FROM productos
            WHERE estado = TRUE
            ORDER BY tipo_producto ASC, nombre_producto ASC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.post("/productos")
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    codigo = producto.codigo.strip().upper()
    nombre_producto = producto.nombre_producto.strip()
    unidad_medida = producto.unidad_medida.strip()

    if codigo == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar el código del producto."
        )

    if nombre_producto == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar el nombre del producto."
        )

    if unidad_medida == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar la unidad de medida."
        )

    validar_tipo_producto(producto.tipo_producto)

    try:
        resultado = db.execute(
            text("""
                INSERT INTO productos (
                    codigo,
                    nombre_producto,
                    tipo_producto,
                    unidad_medida,
                    precio_referencial,
                    stock_minimo,
                    estado
                )
                VALUES (
                    :codigo,
                    :nombre_producto,
                    :tipo_producto,
                    :unidad_medida,
                    :precio_referencial,
                    :stock_minimo,
                    TRUE
                )
                RETURNING id_producto, codigo, nombre_producto;
            """),
            {
                "codigo": codigo,
                "nombre_producto": nombre_producto,
                "tipo_producto": producto.tipo_producto,
                "unidad_medida": unidad_medida,
                "precio_referencial": producto.precio_referencial,
                "stock_minimo": producto.stock_minimo
            }
        )

        nuevo_producto = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Producto registrado correctamente.",
            "producto": dict(nuevo_producto)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar el producto. Verifique que el código no esté duplicado. Detalle: {str(error)}"
        )


@router.put("/productos/{id_producto}")
def actualizar_producto(id_producto: int, producto: ProductoUpdate, db: Session = Depends(get_db)):
    validar_producto_existe(db, id_producto)
    validar_tipo_producto(producto.tipo_producto)

    codigo = producto.codigo.strip().upper()
    nombre_producto = producto.nombre_producto.strip()
    unidad_medida = producto.unidad_medida.strip()

    if codigo == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar el código del producto."
        )

    if nombre_producto == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar el nombre del producto."
        )

    if unidad_medida == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar la unidad de medida."
        )

    try:
        resultado = db.execute(
            text("""
                UPDATE productos
                SET
                    codigo = :codigo,
                    nombre_producto = :nombre_producto,
                    tipo_producto = :tipo_producto,
                    unidad_medida = :unidad_medida,
                    precio_referencial = :precio_referencial,
                    stock_minimo = :stock_minimo
                WHERE id_producto = :id_producto
                  AND estado = TRUE
                RETURNING id_producto;
            """),
            {
                "id_producto": id_producto,
                "codigo": codigo,
                "nombre_producto": nombre_producto,
                "tipo_producto": producto.tipo_producto,
                "unidad_medida": unidad_medida,
                "precio_referencial": producto.precio_referencial,
                "stock_minimo": producto.stock_minimo
            }
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado."
            )

        db.commit()

        return {
            "mensaje": "Producto actualizado correctamente.",
            "id_producto": id_producto
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo actualizar el producto. Detalle: {str(error)}"
        )


@router.delete("/productos/{id_producto}")
def eliminar_producto(id_producto: int, db: Session = Depends(get_db)):
    validar_producto_existe(db, id_producto)

    usado = db.execute(
        text("""
            SELECT id_inventario
            FROM inventario
            WHERE id_producto = :id_producto
            LIMIT 1;
        """),
        {"id_producto": id_producto}
    ).first()

    if usado is not None:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar este producto porque ya tiene inventario relacionado."
        )

    try:
        db.execute(
            text("""
                DELETE FROM productos
                WHERE id_producto = :id_producto;
            """),
            {"id_producto": id_producto}
        )

        db.commit()

        return {
            "mensaje": "Producto eliminado definitivamente.",
            "id_producto": id_producto
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo eliminar el producto. Detalle: {str(error)}"
        )


# ======================================================
# BODEGAS
# ======================================================

@router.get("/bodegas")
def listar_bodegas(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                id_bodega,
                nombre_bodega,
                descripcion,
                ubicacion,
                estado
            FROM bodegas
            WHERE estado = TRUE
            ORDER BY id_bodega ASC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.post("/bodegas")
def crear_bodega(bodega: BodegaCreate, db: Session = Depends(get_db)):
    nombre_bodega = bodega.nombre_bodega.strip()

    if nombre_bodega == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar el nombre de la bodega."
        )

    try:
        resultado = db.execute(
            text("""
                INSERT INTO bodegas (
                    nombre_bodega,
                    descripcion,
                    ubicacion,
                    estado
                )
                VALUES (
                    :nombre_bodega,
                    :descripcion,
                    :ubicacion,
                    TRUE
                )
                RETURNING id_bodega, nombre_bodega;
            """),
            {
                "nombre_bodega": nombre_bodega,
                "descripcion": bodega.descripcion,
                "ubicacion": bodega.ubicacion
            }
        )

        nueva_bodega = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Bodega registrada correctamente.",
            "bodega": dict(nueva_bodega)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar la bodega. Verifique que el nombre no esté duplicado. Detalle: {str(error)}"
        )


@router.put("/bodegas/{id_bodega}")
def actualizar_bodega(id_bodega: int, bodega: BodegaUpdate, db: Session = Depends(get_db)):
    validar_bodega_existe(db, id_bodega)

    nombre_bodega = bodega.nombre_bodega.strip()

    if nombre_bodega == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar el nombre de la bodega."
        )

    try:
        resultado = db.execute(
            text("""
                UPDATE bodegas
                SET
                    nombre_bodega = :nombre_bodega,
                    descripcion = :descripcion,
                    ubicacion = :ubicacion
                WHERE id_bodega = :id_bodega
                  AND estado = TRUE
                RETURNING id_bodega;
            """),
            {
                "id_bodega": id_bodega,
                "nombre_bodega": nombre_bodega,
                "descripcion": bodega.descripcion,
                "ubicacion": bodega.ubicacion
            }
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="Bodega no encontrada."
            )

        db.commit()

        return {
            "mensaje": "Bodega actualizada correctamente.",
            "id_bodega": id_bodega
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo actualizar la bodega. Detalle: {str(error)}"
        )


@router.delete("/bodegas/{id_bodega}")
def eliminar_bodega(id_bodega: int, db: Session = Depends(get_db)):
    validar_bodega_existe(db, id_bodega)

    usada = db.execute(
        text("""
            SELECT id_inventario
            FROM inventario
            WHERE id_bodega = :id_bodega
            LIMIT 1;
        """),
        {"id_bodega": id_bodega}
    ).first()

    if usada is not None:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar esta bodega porque ya tiene inventario relacionado."
        )

    try:
        db.execute(
            text("""
                DELETE FROM bodegas
                WHERE id_bodega = :id_bodega;
            """),
            {"id_bodega": id_bodega}
        )

        db.commit()

        return {
            "mensaje": "Bodega eliminada definitivamente.",
            "id_bodega": id_bodega
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo eliminar la bodega. Detalle: {str(error)}"
        )


# ======================================================
# INVENTARIO
# ======================================================

@router.get("/")
def listar_inventario(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                i.id_inventario,
                p.id_producto,
                p.codigo,
                p.nombre_producto,
                p.tipo_producto,
                p.unidad_medida,
                p.precio_referencial,
                p.stock_minimo,
                b.id_bodega,
                b.nombre_bodega,
                i.lote,
                i.cantidad_disponible,
                CASE
                    WHEN i.cantidad_disponible <= 0 THEN 'Agotado'
                    WHEN i.cantidad_disponible <= p.stock_minimo THEN 'Stock bajo'
                    ELSE 'Disponible'
                END AS estado_stock,
                i.estado_producto,
                i.fecha_ingreso,
                i.observacion,
                i.cantidad_disponible * p.precio_referencial AS valor_estimado
            FROM inventario i
            INNER JOIN productos p ON i.id_producto = p.id_producto
            INNER JOIN bodegas b ON i.id_bodega = b.id_bodega
            WHERE p.estado = TRUE
              AND b.estado = TRUE
              AND COALESCE(i.estado_producto, 'Disponible') <> 'Inactivo'
            ORDER BY
                p.tipo_producto ASC,
                p.nombre_producto ASC,
                i.lote ASC,
                i.id_inventario ASC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.get("/resumen-productos")
def resumen_inventario_por_producto(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                p.id_producto,
                p.codigo,
                p.nombre_producto,
                p.tipo_producto,
                p.unidad_medida,
                p.stock_minimo,
                p.precio_referencial,
                COALESCE(SUM(i.cantidad_disponible), 0) AS cantidad_disponible,
                COALESCE(SUM(i.cantidad_disponible), 0) * p.precio_referencial AS valor_estimado,
                CASE
                    WHEN COALESCE(SUM(i.cantidad_disponible), 0) <= 0 THEN 'Agotado'
                    WHEN COALESCE(SUM(i.cantidad_disponible), 0) <= p.stock_minimo THEN 'Stock bajo'
                    ELSE 'Disponible'
                END AS estado_stock
            FROM productos p
            LEFT JOIN inventario i
                ON p.id_producto = i.id_producto
               AND COALESCE(i.estado_producto, 'Disponible') <> 'Inactivo'
            WHERE p.estado = TRUE
            GROUP BY
                p.id_producto,
                p.codigo,
                p.nombre_producto,
                p.tipo_producto,
                p.unidad_medida,
                p.stock_minimo,
                p.precio_referencial
            ORDER BY
                p.tipo_producto ASC,
                p.nombre_producto ASC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.get("/stock-bajo")
def listar_stock_bajo(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                i.id_inventario,
                p.codigo,
                p.nombre_producto,
                p.tipo_producto,
                p.unidad_medida,
                p.stock_minimo,
                b.nombre_bodega,
                i.lote,
                i.cantidad_disponible,
                CASE
                    WHEN i.cantidad_disponible <= 0 THEN 'Agotado'
                    WHEN i.cantidad_disponible <= p.stock_minimo THEN 'Stock bajo'
                    ELSE 'Disponible'
                END AS estado_stock
            FROM inventario i
            INNER JOIN productos p ON i.id_producto = p.id_producto
            INNER JOIN bodegas b ON i.id_bodega = b.id_bodega
            WHERE p.estado = TRUE
              AND b.estado = TRUE
              AND COALESCE(i.estado_producto, 'Disponible') <> 'Inactivo'
              AND i.cantidad_disponible <= p.stock_minimo
            ORDER BY p.nombre_producto ASC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.get("/lote/{lote}")
def buscar_inventario_por_lote(lote: str, db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                i.id_inventario,
                p.id_producto,
                p.codigo,
                p.nombre_producto,
                p.tipo_producto,
                p.unidad_medida,
                p.precio_referencial,
                p.stock_minimo,
                b.id_bodega,
                b.nombre_bodega,
                i.lote,
                i.cantidad_disponible,
                CASE
                    WHEN i.cantidad_disponible <= 0 THEN 'Agotado'
                    WHEN i.cantidad_disponible <= p.stock_minimo THEN 'Stock bajo'
                    ELSE 'Disponible'
                END AS estado_stock,
                i.estado_producto,
                i.fecha_ingreso,
                i.observacion
            FROM inventario i
            INNER JOIN productos p ON i.id_producto = p.id_producto
            INNER JOIN bodegas b ON i.id_bodega = b.id_bodega
            WHERE UPPER(i.lote) = UPPER(:lote)
              AND COALESCE(i.estado_producto, 'Disponible') <> 'Inactivo'
            ORDER BY p.nombre_producto ASC;
        """),
        {"lote": lote}
    )

    filas = resultado.mappings().all()

    if not filas:
        raise HTTPException(
            status_code=404,
            detail="No existe inventario para ese lote."
        )

    return [dict(fila) for fila in filas]


@router.get("/{id_inventario}")
def obtener_inventario(id_inventario: int, db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                i.id_inventario,
                p.id_producto,
                p.codigo,
                p.nombre_producto,
                p.tipo_producto,
                p.unidad_medida,
                p.precio_referencial,
                p.stock_minimo,
                b.id_bodega,
                b.nombre_bodega,
                i.lote,
                i.cantidad_disponible,
                i.estado_producto,
                CASE
                    WHEN i.cantidad_disponible <= 0 THEN 'Agotado'
                    WHEN i.cantidad_disponible <= p.stock_minimo THEN 'Stock bajo'
                    ELSE 'Disponible'
                END AS estado_stock,
                i.fecha_ingreso,
                i.observacion
            FROM inventario i
            INNER JOIN productos p ON i.id_producto = p.id_producto
            INNER JOIN bodegas b ON i.id_bodega = b.id_bodega
            WHERE i.id_inventario = :id_inventario;
        """),
        {"id_inventario": id_inventario}
    )

    fila = resultado.mappings().first()

    if fila is None:
        raise HTTPException(
            status_code=404,
            detail="Inventario no encontrado."
        )

    return dict(fila)


@router.post("/")
def registrar_inventario_manual(inventario: InventarioCreate, db: Session = Depends(get_db)):
    validar_estado_producto(inventario.estado_producto)
    validar_producto_existe(db, inventario.id_producto)
    validar_bodega_existe(db, inventario.id_bodega)

    lote_limpio = limpiar_lote(inventario.lote)

    try:
        if inventario.stock_minimo is not None or inventario.precio_referencial is not None:
            datos_producto = db.execute(
                text("""
                    SELECT stock_minimo, precio_referencial
                    FROM productos
                    WHERE id_producto = :id_producto;
                """),
                {"id_producto": inventario.id_producto}
            ).mappings().first()

            if datos_producto is None:
                raise HTTPException(
                    status_code=404,
                    detail="Producto no encontrado."
                )

            nuevo_stock_minimo = (
                inventario.stock_minimo
                if inventario.stock_minimo is not None
                else datos_producto["stock_minimo"]
            )

            nuevo_precio = (
                inventario.precio_referencial
                if inventario.precio_referencial is not None
                else datos_producto["precio_referencial"]
            )

            db.execute(
                text("""
                    UPDATE productos
                    SET
                        stock_minimo = :stock_minimo,
                        precio_referencial = :precio_referencial
                    WHERE id_producto = :id_producto;
                """),
                {
                    "id_producto": inventario.id_producto,
                    "stock_minimo": nuevo_stock_minimo,
                    "precio_referencial": nuevo_precio
                }
            )

        existente = db.execute(
            text("""
                SELECT id_inventario
                FROM inventario
                WHERE id_producto = :id_producto
                  AND id_bodega = :id_bodega
                  AND UPPER(COALESCE(lote, 'SIN-LOTE')) = UPPER(:lote)
                  AND COALESCE(estado_producto, 'Disponible') <> 'Inactivo'
                LIMIT 1;
            """),
            {
                "id_producto": inventario.id_producto,
                "id_bodega": inventario.id_bodega,
                "lote": lote_limpio
            }
        ).mappings().first()

        if existente:
            resultado = db.execute(
                text("""
                    UPDATE inventario
                    SET
                        cantidad_disponible = cantidad_disponible + :cantidad_disponible,
                        estado_producto = :estado_producto,
                        observacion = :observacion,
                        fecha_ingreso = CURRENT_DATE
                    WHERE id_inventario = :id_inventario
                    RETURNING id_inventario;
                """),
                {
                    "id_inventario": existente["id_inventario"],
                    "cantidad_disponible": inventario.cantidad_disponible,
                    "estado_producto": inventario.estado_producto,
                    "observacion": inventario.observacion
                }
            )
        else:
            resultado = db.execute(
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
                        :estado_producto,
                        :observacion
                    )
                    RETURNING id_inventario;
                """),
                {
                    "id_producto": inventario.id_producto,
                    "id_bodega": inventario.id_bodega,
                    "lote": lote_limpio,
                    "cantidad_disponible": inventario.cantidad_disponible,
                    "estado_producto": inventario.estado_producto,
                    "observacion": inventario.observacion
                }
            )

        fila = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Inventario registrado o actualizado correctamente.",
            "inventario": dict(fila)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar inventario. Detalle: {str(error)}"
        )


@router.put("/{id_inventario}")
def actualizar_inventario(id_inventario: int, inventario: InventarioUpdate, db: Session = Depends(get_db)):
    validar_estado_producto(inventario.estado_producto)
    validar_producto_existe(db, inventario.id_producto)
    validar_bodega_existe(db, inventario.id_bodega)

    lote_limpio = limpiar_lote(inventario.lote)

    existe = db.execute(
        text("""
            SELECT id_inventario
            FROM inventario
            WHERE id_inventario = :id_inventario;
        """),
        {"id_inventario": id_inventario}
    ).first()

    if existe is None:
        raise HTTPException(
            status_code=404,
            detail="Inventario no encontrado."
        )

    duplicado = db.execute(
        text("""
            SELECT id_inventario
            FROM inventario
            WHERE id_producto = :id_producto
              AND id_bodega = :id_bodega
              AND UPPER(COALESCE(lote, 'SIN-LOTE')) = UPPER(:lote)
              AND id_inventario <> :id_inventario
              AND COALESCE(estado_producto, 'Disponible') <> 'Inactivo'
            LIMIT 1;
        """),
        {
            "id_producto": inventario.id_producto,
            "id_bodega": inventario.id_bodega,
            "lote": lote_limpio,
            "id_inventario": id_inventario
        }
    ).first()

    if duplicado is not None:
        raise HTTPException(
            status_code=400,
            detail="Ya existe inventario para ese mismo producto, bodega y lote. Para evitar duplicados, edite el registro existente."
        )

    try:
        db.execute(
            text("""
                UPDATE productos
                SET
                    stock_minimo = :stock_minimo,
                    precio_referencial = :precio_referencial
                WHERE id_producto = :id_producto;
            """),
            {
                "id_producto": inventario.id_producto,
                "stock_minimo": inventario.stock_minimo,
                "precio_referencial": inventario.precio_referencial
            }
        )

        estado_final = inventario.estado_producto

        if inventario.cantidad_disponible <= 0:
            estado_final = "Agotado"

        resultado = db.execute(
            text("""
                UPDATE inventario
                SET
                    id_producto = :id_producto,
                    id_bodega = :id_bodega,
                    lote = :lote,
                    cantidad_disponible = :cantidad_disponible,
                    estado_producto = :estado_producto,
                    observacion = :observacion,
                    fecha_ingreso = CURRENT_DATE
                WHERE id_inventario = :id_inventario
                RETURNING id_inventario;
            """),
            {
                "id_inventario": id_inventario,
                "id_producto": inventario.id_producto,
                "id_bodega": inventario.id_bodega,
                "lote": lote_limpio,
                "cantidad_disponible": inventario.cantidad_disponible,
                "estado_producto": estado_final,
                "observacion": inventario.observacion
            }
        )

        fila = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Inventario actualizado correctamente.",
            "inventario": dict(fila)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo actualizar inventario. Detalle: {str(error)}"
        )


@router.delete("/{id_inventario}")
def eliminar_inventario_definitivo(id_inventario: int, db: Session = Depends(get_db)):
    existe = db.execute(
        text("""
            SELECT id_inventario
            FROM inventario
            WHERE id_inventario = :id_inventario;
        """),
        {"id_inventario": id_inventario}
    ).first()

    if existe is None:
        raise HTTPException(
            status_code=404,
            detail="Inventario no encontrado."
        )

    try:
        db.execute(
            text("""
                DELETE FROM inventario
                WHERE id_inventario = :id_inventario;
            """),
            {"id_inventario": id_inventario}
        )

        db.commit()

        return {
            "mensaje": "Inventario eliminado definitivamente.",
            "id_inventario": id_inventario
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=(
                "No se pudo eliminar el inventario. Es posible que esté relacionado "
                f"con producción, ventas u otro movimiento. Detalle: {str(error)}"
            )
        )