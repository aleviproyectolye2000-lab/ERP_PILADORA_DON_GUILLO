from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter(
    prefix="/api/reportes",
    tags=["Reportes Gerenciales"]
)


@router.get("/resumen")
def obtener_resumen_gerencial(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM fn_resumen_gerencial();"))
    fila = resultado.mappings().first()

    if fila is None:
        return {}

    return dict(fila)


@router.get("/inventario")
def obtener_inventario_actual(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM vista_inventario_actual;"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/compras")
def obtener_compras_completas(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM vista_compras_completas ORDER BY fecha_compra DESC;"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/ventas")
def obtener_ventas_completas(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM vista_ventas_completas ORDER BY fecha_venta DESC;"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/produccion")
def obtener_produccion_rendimiento(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM vista_produccion_rendimiento ORDER BY fecha_pilado DESC;"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/talento-humano")
def obtener_talento_humano(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM vista_talento_humano_roles;"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/activos")
def obtener_activos_mantenimientos(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM vista_activos_mantenimientos;"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/auditoria")
def obtener_auditoria_general(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM vista_auditoria_general ORDER BY fecha_accion DESC, hora_accion DESC;"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/ventas-producto")
def obtener_ventas_por_producto(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM fn_ventas_por_producto();"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/stock-bajo")
def obtener_stock_bajo(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM fn_stock_bajo();"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/ia")
def obtener_recomendaciones_ia(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM fn_recomendacion_ia();"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]


@router.get("/ia-guardadas")
def obtener_recomendaciones_ia_guardadas(db: Session = Depends(get_db)):
    resultado = db.execute(text("SELECT * FROM vista_recomendaciones_ia ORDER BY fecha_recomendacion DESC, hora_recomendacion DESC;"))
    filas = resultado.mappings().all()

    return [dict(fila) for fila in filas]