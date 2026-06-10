from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

from app.database import get_db


router = APIRouter(
    prefix="/api/activos",
    tags=["Activos y Mantenimientos"]
)


class ActivoCreate(BaseModel):
    codigo_activo: str
    nombre_activo: str
    tipo_activo: str
    descripcion: Optional[str] = None
    fecha_adquisicion: date
    valor: float = Field(gt=0)
    estado_activo: str = "Operativo"
    responsable: str
    ubicacion: Optional[str] = None


class MantenimientoCreate(BaseModel):
    id_activo: int
    fecha_mantenimiento: date
    tipo_mantenimiento: str
    descripcion: Optional[str] = None
    costo: float = Field(ge=0)
    gasto_combustible: float = Field(ge=0)
    proximo_mantenimiento: Optional[date] = None
    responsable: str
    observacion: Optional[str] = None


@router.get("/")
def listar_activos(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT *
            FROM maquinaria_activos
            WHERE estado = TRUE
            ORDER BY id_activo ASC;
        """)
    )
    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.get("/{id_activo}")
def obtener_activo(id_activo: int, db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT *
            FROM maquinaria_activos
            WHERE id_activo = :id_activo
              AND estado = TRUE;
        """),
        {"id_activo": id_activo}
    )

    fila = resultado.mappings().first()

    if fila is None:
        raise HTTPException(status_code=404, detail="Activo no encontrado.")

    return dict(fila)


@router.post("/")
def crear_activo(activo: ActivoCreate, db: Session = Depends(get_db)):
    if activo.tipo_activo not in ["Maquinaria", "Vehículo", "Terreno", "Bodega", "Herramienta", "Equipo"]:
        raise HTTPException(
            status_code=400,
            detail="Tipo de activo no válido. Use Maquinaria, Vehículo, Terreno, Bodega, Herramienta o Equipo."
        )

    if activo.estado_activo not in ["Operativo", "Mantenimiento", "Dañado", "Inactivo"]:
        raise HTTPException(
            status_code=400,
            detail="Estado de activo no válido. Use Operativo, Mantenimiento, Dañado o Inactivo."
        )

    consulta = text("""
        INSERT INTO maquinaria_activos (
            codigo_activo,
            nombre_activo,
            tipo_activo,
            descripcion,
            fecha_adquisicion,
            valor,
            estado_activo,
            responsable,
            ubicacion
        )
        VALUES (
            :codigo_activo,
            :nombre_activo,
            :tipo_activo,
            :descripcion,
            :fecha_adquisicion,
            :valor,
            :estado_activo,
            :responsable,
            :ubicacion
        )
        RETURNING id_activo, codigo_activo, nombre_activo, tipo_activo;
    """)

    try:
        resultado = db.execute(consulta, activo.model_dump())
        nuevo_activo = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Activo registrado correctamente",
            "activo": dict(nuevo_activo)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar el activo. Verifique que el código no esté duplicado. Detalle: {str(error)}"
        )


@router.get("/mantenimientos/listar")
def listar_mantenimientos(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT *
            FROM vista_activos_mantenimientos
            ORDER BY fecha_mantenimiento DESC NULLS LAST;
        """)
    )
    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.post("/mantenimientos")
def registrar_mantenimiento(mantenimiento: MantenimientoCreate, db: Session = Depends(get_db)):
    if mantenimiento.tipo_mantenimiento not in ["Preventivo", "Correctivo", "Reparación", "Combustible", "Otro"]:
        raise HTTPException(
            status_code=400,
            detail="Tipo de mantenimiento no válido. Use Preventivo, Correctivo, Reparación, Combustible u Otro."
        )

    existe_activo = db.execute(
        text("""
            SELECT id_activo
            FROM maquinaria_activos
            WHERE id_activo = :id_activo
              AND estado = TRUE;
        """),
        {"id_activo": mantenimiento.id_activo}
    ).first()

    if existe_activo is None:
        raise HTTPException(status_code=404, detail="El activo no existe o está inactivo.")

    consulta = text("""
        INSERT INTO mantenimientos (
            id_activo,
            fecha_mantenimiento,
            tipo_mantenimiento,
            descripcion,
            costo,
            gasto_combustible,
            proximo_mantenimiento,
            responsable,
            observacion
        )
        VALUES (
            :id_activo,
            :fecha_mantenimiento,
            :tipo_mantenimiento,
            :descripcion,
            :costo,
            :gasto_combustible,
            :proximo_mantenimiento,
            :responsable,
            :observacion
        )
        RETURNING id_mantenimiento, costo, gasto_combustible;
    """)

    resultado = db.execute(consulta, mantenimiento.model_dump())
    nuevo_mantenimiento = resultado.mappings().first()

    db.execute(
        text("""
            UPDATE maquinaria_activos
            SET estado_activo = 'Mantenimiento'
            WHERE id_activo = :id_activo;
        """),
        {"id_activo": mantenimiento.id_activo}
    )

    db.commit()

    return {
        "mensaje": "Mantenimiento registrado correctamente",
        "mantenimiento": dict(nuevo_mantenimiento)
    }


@router.put("/{id_activo}/estado")
def actualizar_estado_activo(
    id_activo: int,
    estado_activo: str,
    db: Session = Depends(get_db)
):
    if estado_activo not in ["Operativo", "Mantenimiento", "Dañado", "Inactivo"]:
        raise HTTPException(
            status_code=400,
            detail="Estado de activo no válido. Use Operativo, Mantenimiento, Dañado o Inactivo."
        )

    resultado = db.execute(
        text("""
            UPDATE maquinaria_activos
            SET estado_activo = :estado_activo
            WHERE id_activo = :id_activo
              AND estado = TRUE
            RETURNING id_activo, estado_activo;
        """),
        {
            "id_activo": id_activo,
            "estado_activo": estado_activo
        }
    )

    fila = resultado.mappings().first()

    if fila is None:
        raise HTTPException(status_code=404, detail="Activo no encontrado.")

    db.commit()

    return {
        "mensaje": "Estado del activo actualizado correctamente",
        "activo": dict(fila)
    }


@router.delete("/{id_activo}")
def desactivar_activo(id_activo: int, db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            UPDATE maquinaria_activos
            SET estado = FALSE,
                estado_activo = 'Inactivo'
            WHERE id_activo = :id_activo
            RETURNING id_activo;
        """),
        {"id_activo": id_activo}
    )

    fila = resultado.mappings().first()

    if fila is None:
        raise HTTPException(status_code=404, detail="Activo no encontrado.")

    db.commit()

    return {
        "mensaje": "Activo desactivado correctamente",
        "id_activo": id_activo
    }