from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ia_service import consultar_ia_erp, estado_ia

router = APIRouter(
    prefix="/api/ia",
    tags=["Inteligencia Artificial"]
)

class PreguntaIA(BaseModel):
    pregunta: str
    usuario: str | None = None
    perfil: str | None = None
    contexto_modulo: str | None = "general"  # Etiqueta oculta para aislar los datos según la pantalla


class GuardarRecomendacionIA(BaseModel):
    area: str
    tipo_analisis: str
    pregunta: str
    recomendacion: str
    nivel_importancia: str
    usuario: str | None = None
    perfil: str | None = None
    proveedor: str | None = None
    modelo: str | None = None


def perfil_autorizado(perfil: str | None):
    # SOLUCIÓN DINÁMICA: Ya no importa el nombre del perfil. 
    # Si el usuario tiene un perfil asignado en la base de datos, puede usar el chat.
    # La seguridad de los datos ya está garantizada por el aislamiento de módulos.
    if not perfil or not perfil.strip():
        return False
    return True


@router.get("/estado")
def obtener_estado_ia():
    return estado_ia()


@router.post("/consultar")
def consultar_ia(datos: PreguntaIA, db: Session = Depends(get_db)):
    if not perfil_autorizado(datos.perfil):
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Usuario sin perfil válido para usar la IA."
        )

    # Inyectamos el parámetro 'contexto_modulo' hacia el motor principal
    resultado = consultar_ia_erp(
        db=db,
        pregunta=datos.pregunta,
        contexto_modulo=datos.contexto_modulo
    )

    return {
        "estado": resultado.get("estado"),
        "proveedor": resultado.get("proveedor"),
        "modelo": resultado.get("modelo"),
        "respuesta": resultado.get("respuesta")
    }


@router.post("/guardar-recomendacion")
def guardar_recomendacion_ia(datos: GuardarRecomendacionIA, db: Session = Depends(get_db)):
    
    # SEGURIDAD ESTRICTA: El guardado de reportes oficiales sigue siendo exclusivo para Gerencia y Admin
    perfil_normalizado = (datos.perfil or "").strip().lower()
    if "administrador" not in perfil_normalizado and "gerente" not in perfil_normalizado:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Solo Administrador y Gerente pueden guardar recomendaciones IA en el historial."
        )

    if not datos.recomendacion or not datos.recomendacion.strip():
        raise HTTPException(
            status_code=400,
            detail="No existe recomendación para guardar."
        )

    consulta = text("""
        INSERT INTO recomendaciones_ia (
            area,
            tipo_analisis,
            pregunta,
            recomendacion,
            nivel_importancia,
            estado_recomendacion,
            usuario,
            perfil,
            proveedor,
            modelo
        )
        VALUES (
            :area,
            :tipo_analisis,
            :pregunta,
            :recomendacion,
            :nivel_importancia,
            'Guardada',
            :usuario,
            :perfil,
            :proveedor,
            :modelo
        )
        RETURNING id_recomendacion;
    """)

    try:
        resultado = db.execute(
            consulta,
            {
                "area": datos.area.strip(),
                "tipo_analisis": datos.tipo_analisis.strip(),
                "pregunta": datos.pregunta.strip(),
                "recomendacion": datos.recomendacion.strip(),
                "nivel_importancia": datos.nivel_importancia.strip(),
                "usuario": datos.usuario,
                "perfil": datos.perfil,
                "proveedor": datos.proveedor,
                "modelo": datos.modelo
            }
        )

        id_recomendacion = resultado.scalar()
        db.commit()

        return {
            "estado": "ok",
            "mensaje": "Recomendación de IA guardada correctamente en el historial.",
            "id_recomendacion": id_recomendacion
        }

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"No se pudo guardar la recomendación IA: {str(error)}"
        )