from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional

from app.database import get_db


router = APIRouter(
    prefix="/api/auditoria",
    tags=["Auditoría del Sistema"]
)


# =====================================================
# MODELOS
# =====================================================

class AccesoCreate(BaseModel):
    id_usuario: int
    fecha_ingreso: Optional[date] = None
    hora_ingreso: Optional[time] = None
    ip_equipo: Optional[str] = "127.0.0.1"
    estado_sesion: str = "Activa"


class CierreSesionCreate(BaseModel):
    id_acceso: int
    fecha_salida: Optional[date] = None
    hora_salida: Optional[time] = None


class CierreSesionUsuarioCreate(BaseModel):
    id_usuario: int
    fecha_salida: Optional[date] = None
    hora_salida: Optional[time] = None


class AccionCreate(BaseModel):
    id_usuario: int
    modulo: str
    accion: str
    descripcion: str
    tabla_afectada: Optional[str] = None
    id_registro_afectado: Optional[int] = None


class CerrarSesionesAntiguasCreate(BaseModel):
    horas_antiguedad: int = 12


class ArchivarAuditoriaCreate(BaseModel):
    dias_antiguedad: int = 30
    id_usuario_admin: Optional[int] = None


# =====================================================
# FUNCIONES INTERNAS
# =====================================================

def normalizar_estado_sesion(estado: str) -> str:
    if not estado:
        return "Activa"

    estado_limpio = estado.strip().lower()

    if estado_limpio in ["abierta", "activo", "activa"]:
        return "Activa"

    if estado_limpio in ["cerrada", "cerrado"]:
        return "Cerrada"

    return "Activa"


def validar_usuario_activo(id_usuario: int, db: Session):
    usuario = db.execute(
        text("""
            SELECT id_usuario
            FROM usuarios
            WHERE id_usuario = :id_usuario
              AND estado = TRUE;
        """),
        {"id_usuario": id_usuario}
    ).first()

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="El usuario no existe o está inactivo."
        )


def crear_tablas_historicas_si_no_existen(db: Session):
    """
    Crea tablas históricas si no existen.
    No borra información.
    Sirve para archivar accesos y acciones antiguas.
    """
    db.execute(
        text("""
            CREATE TABLE IF NOT EXISTS auditoria_accesos_historico
            (LIKE auditoria_accesos INCLUDING ALL);
        """)
    )

    db.execute(
        text("""
            CREATE TABLE IF NOT EXISTS auditoria_acciones_historico
            (LIKE auditoria_acciones INCLUDING ALL);
        """)
    )


def registrar_accion_interna(
    db: Session,
    id_usuario: Optional[int],
    modulo: str,
    accion: str,
    descripcion: str,
    tabla_afectada: Optional[str] = None,
    id_registro_afectado: Optional[int] = None
):
    """
    Registra acciones internas del propio módulo Auditoría.
    No rompe si no se envía id_usuario.
    """
    if id_usuario is None:
        return

    try:
        db.execute(
            text("""
                INSERT INTO auditoria_acciones (
                    id_usuario,
                    modulo,
                    accion,
                    descripcion,
                    fecha_accion,
                    hora_accion,
                    tabla_afectada,
                    id_registro_afectado
                )
                VALUES (
                    :id_usuario,
                    :modulo,
                    :accion,
                    :descripcion,
                    CURRENT_DATE,
                    CURRENT_TIME,
                    :tabla_afectada,
                    :id_registro_afectado
                );
            """),
            {
                "id_usuario": id_usuario,
                "modulo": modulo,
                "accion": accion.strip().upper(),
                "descripcion": descripcion,
                "tabla_afectada": tabla_afectada,
                "id_registro_afectado": id_registro_afectado
            }
        )
    except Exception:
        pass


def cerrar_sesiones_activas_usuario(id_usuario: int, db: Session):
    """
    Cierra sesiones anteriores activas o abiertas del mismo usuario.
    Se corrigió CAST para evitar error con SQLAlchemy y PostgreSQL.
    """
    ahora = datetime.now()
    fecha_salida = ahora.date()
    hora_salida = ahora.time().replace(microsecond=0)

    db.execute(
        text("""
            UPDATE auditoria_accesos
            SET
                fecha_salida = :fecha_salida,
                hora_salida = :hora_salida,
                tiempo_conectado = (
                    CAST(:fecha_salida AS timestamp)
                    + CAST(:hora_salida AS time)
                    -
                    (fecha_ingreso::timestamp + hora_ingreso)
                ),
                estado_sesion = 'Cerrada'
            WHERE id_usuario = :id_usuario
              AND LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
              AND fecha_salida IS NULL;
        """),
        {
            "id_usuario": id_usuario,
            "fecha_salida": fecha_salida,
            "hora_salida": hora_salida
        }
    )


# =====================================================
# LISTAR ACCIONES DE AUDITORÍA
# Por defecto trae los últimos 50 registros.
# =====================================================

@router.get("/acciones")
def listar_acciones(
    limite: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    try:
        resultado = db.execute(
            text("""
                SELECT *
                FROM vista_auditoria_general
                ORDER BY fecha_accion DESC, hora_accion DESC, id_accion DESC
                LIMIT :limite OFFSET :offset;
            """),
            {
                "limite": limite,
                "offset": offset
            }
        )

        filas = resultado.mappings().all()
        return [dict(fila) for fila in filas]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar acciones de auditoría: {str(error)}"
        )


# =====================================================
# LISTAR ACCESOS AL SISTEMA
# Por defecto trae los últimos 50 registros.
# =====================================================

@router.get("/accesos")
def listar_accesos(
    limite: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    try:
        resultado = db.execute(
            text("""
                SELECT
                    aa.id_acceso,
                    u.usuario,
                    p.nombre_perfil,
                    aa.fecha_ingreso,
                    aa.hora_ingreso,
                    aa.fecha_salida,
                    aa.hora_salida,
                    COALESCE(aa.tiempo_conectado::text, '-') AS tiempo_conectado,
                    COALESCE(aa.ip_equipo, '127.0.0.1') AS ip_equipo,
                    CASE
                        WHEN LOWER(COALESCE(aa.estado_sesion, '')) IN ('activa', 'abierta', 'activo')
                            THEN 'Activa'
                        WHEN LOWER(COALESCE(aa.estado_sesion, '')) IN ('cerrada', 'cerrado')
                            THEN 'Cerrada'
                        ELSE COALESCE(aa.estado_sesion, 'Activa')
                    END AS estado_sesion
                FROM auditoria_accesos aa
                INNER JOIN usuarios u ON aa.id_usuario = u.id_usuario
                INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
                ORDER BY aa.fecha_ingreso DESC, aa.hora_ingreso DESC, aa.id_acceso DESC
                LIMIT :limite OFFSET :offset;
            """),
            {
                "limite": limite,
                "offset": offset
            }
        )

        filas = resultado.mappings().all()
        return [dict(fila) for fila in filas]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar accesos de auditoría: {str(error)}"
        )


# =====================================================
# RESUMEN GENERAL DE AUDITORÍA
# =====================================================

@router.get("/resumen")
def resumen_auditoria(db: Session = Depends(get_db)):
    try:
        resultado = db.execute(
            text("""
                SELECT
                    (
                        SELECT COUNT(*)
                        FROM auditoria_accesos
                        WHERE LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
                          AND fecha_salida IS NULL
                    ) AS usuarios_conectados,

                    (
                        SELECT COUNT(*)
                        FROM auditoria_accesos
                    ) AS ingresos_registrados,

                    (
                        SELECT COUNT(*)
                        FROM auditoria_acciones
                    ) AS acciones_registradas,

                    (
                        SELECT COUNT(*)
                        FROM auditoria_acciones
                        WHERE UPPER(accion) LIKE '%ACCESO_DENEGADO%'
                    ) AS accesos_denegados,

                    (
                        SELECT COUNT(*)
                        FROM auditoria_acciones
                        WHERE
                            UPPER(accion) LIKE '%ELIMINAR%'
                            OR UPPER(accion) LIKE '%ANULAR%'
                            OR UPPER(accion) LIKE '%EDITAR%'
                            OR UPPER(accion) LIKE '%MODIFICAR%'
                            OR UPPER(accion) LIKE '%ACTUALIZAR%'
                    ) AS acciones_criticas,

                    (
                        SELECT MAX(fecha_ingreso)
                        FROM auditoria_accesos
                    ) AS ultimo_acceso,

                    (
                        SELECT COUNT(*)
                        FROM auditoria_accesos_historico
                    ) AS accesos_historicos,

                    (
                        SELECT COUNT(*)
                        FROM auditoria_acciones_historico
                    ) AS acciones_historicas;
            """)
        )

        fila = resultado.mappings().first()
        return dict(fila)

    except Exception:
        try:
            crear_tablas_historicas_si_no_existen(db)
            db.commit()

            resultado = db.execute(
                text("""
                    SELECT
                        (
                            SELECT COUNT(*)
                            FROM auditoria_accesos
                            WHERE LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
                              AND fecha_salida IS NULL
                        ) AS usuarios_conectados,

                        (
                            SELECT COUNT(*)
                            FROM auditoria_accesos
                        ) AS ingresos_registrados,

                        (
                            SELECT COUNT(*)
                            FROM auditoria_acciones
                        ) AS acciones_registradas,

                        (
                            SELECT COUNT(*)
                            FROM auditoria_acciones
                            WHERE UPPER(accion) LIKE '%ACCESO_DENEGADO%'
                        ) AS accesos_denegados,

                        (
                            SELECT COUNT(*)
                            FROM auditoria_acciones
                            WHERE
                                UPPER(accion) LIKE '%ELIMINAR%'
                                OR UPPER(accion) LIKE '%ANULAR%'
                                OR UPPER(accion) LIKE '%EDITAR%'
                                OR UPPER(accion) LIKE '%MODIFICAR%'
                                OR UPPER(accion) LIKE '%ACTUALIZAR%'
                        ) AS acciones_criticas,

                        (
                            SELECT MAX(fecha_ingreso)
                            FROM auditoria_accesos
                        ) AS ultimo_acceso,

                        0 AS accesos_historicos,

                        0 AS acciones_historicas;
                """)
            )

            fila = resultado.mappings().first()
            return dict(fila)

        except Exception as error:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener resumen de auditoría: {str(error)}"
            )


# =====================================================
# RESUMEN DE MANTENIMIENTO
# =====================================================

@router.get("/mantenimiento/resumen")
def resumen_mantenimiento_auditoria(db: Session = Depends(get_db)):
    try:
        crear_tablas_historicas_si_no_existen(db)
        db.commit()

        resultado = db.execute(
            text("""
                SELECT
                    (SELECT COUNT(*) FROM auditoria_accesos) AS accesos_actuales,
                    (SELECT COUNT(*) FROM auditoria_acciones) AS acciones_actuales,
                    (SELECT COUNT(*) FROM auditoria_accesos_historico) AS accesos_historicos,
                    (SELECT COUNT(*) FROM auditoria_acciones_historico) AS acciones_historicas,
                    (
                        SELECT COUNT(*)
                        FROM auditoria_accesos
                        WHERE LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
                          AND fecha_salida IS NULL
                    ) AS sesiones_activas,
                    (
                        SELECT COUNT(*)
                        FROM auditoria_accesos
                        WHERE LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
                          AND fecha_salida IS NULL
                          AND (fecha_ingreso::timestamp + hora_ingreso) < (NOW() - INTERVAL '12 hours')
                    ) AS sesiones_activas_antiguas;
            """)
        )

        fila = resultado.mappings().first()

        return {
            "mensaje": "Resumen de mantenimiento obtenido correctamente",
            "resumen": dict(fila)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener resumen de mantenimiento: {str(error)}"
        )


# =====================================================
# REGISTRAR ACCESO / INICIO DE SESIÓN
# =====================================================

@router.post("/accesos")
def registrar_acceso(acceso: AccesoCreate, db: Session = Depends(get_db)):
    try:
        validar_usuario_activo(acceso.id_usuario, db)

        estado_sesion = normalizar_estado_sesion(acceso.estado_sesion)

        ahora = datetime.now()
        fecha_ingreso = acceso.fecha_ingreso or ahora.date()
        hora_ingreso = acceso.hora_ingreso or ahora.time().replace(microsecond=0)

        cerrar_sesiones_activas_usuario(acceso.id_usuario, db)

        consulta = text("""
            INSERT INTO auditoria_accesos (
                id_usuario,
                fecha_ingreso,
                hora_ingreso,
                ip_equipo,
                estado_sesion
            )
            VALUES (
                :id_usuario,
                :fecha_ingreso,
                :hora_ingreso,
                :ip_equipo,
                :estado_sesion
            )
            RETURNING id_acceso;
        """)

        resultado = db.execute(
            consulta,
            {
                "id_usuario": acceso.id_usuario,
                "fecha_ingreso": fecha_ingreso,
                "hora_ingreso": hora_ingreso,
                "ip_equipo": acceso.ip_equipo or "127.0.0.1",
                "estado_sesion": estado_sesion
            }
        )

        nuevo_acceso = resultado.mappings().first()

        db.commit()

        return {
            "mensaje": "Acceso registrado correctamente",
            "id_acceso": nuevo_acceso["id_acceso"],
            "estado_sesion": estado_sesion
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar acceso: {str(error)}"
        )


# =====================================================
# CERRAR SESIÓN POR ID DE ACCESO
# =====================================================

@router.put("/cerrar-sesion")
def cerrar_sesion(datos: CierreSesionCreate, db: Session = Depends(get_db)):
    try:
        ahora = datetime.now()

        fecha_salida = datos.fecha_salida or ahora.date()
        hora_salida = datos.hora_salida or ahora.time().replace(microsecond=0)

        consulta = text("""
            UPDATE auditoria_accesos
            SET
                fecha_salida = :fecha_salida,
                hora_salida = :hora_salida,
                tiempo_conectado = (
                    CAST(:fecha_salida AS timestamp)
                    + CAST(:hora_salida AS time)
                    -
                    (fecha_ingreso::timestamp + hora_ingreso)
                ),
                estado_sesion = 'Cerrada'
            WHERE id_acceso = :id_acceso
            RETURNING
                id_acceso,
                id_usuario,
                fecha_ingreso,
                hora_ingreso,
                fecha_salida,
                hora_salida,
                tiempo_conectado::text AS tiempo_conectado,
                estado_sesion;
        """)

        resultado = db.execute(
            consulta,
            {
                "id_acceso": datos.id_acceso,
                "fecha_salida": fecha_salida,
                "hora_salida": hora_salida
            }
        )

        acceso = resultado.mappings().first()

        if acceso is None:
            raise HTTPException(
                status_code=404,
                detail="Acceso no encontrado."
            )

        db.commit()

        return {
            "mensaje": "Sesión cerrada correctamente",
            "acceso": dict(acceso)
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al cerrar sesión: {str(error)}"
        )


# =====================================================
# CERRAR ÚLTIMA SESIÓN ACTIVA POR USUARIO
# =====================================================

@router.put("/cerrar-sesion-usuario")
def cerrar_sesion_usuario(datos: CierreSesionUsuarioCreate, db: Session = Depends(get_db)):
    try:
        validar_usuario_activo(datos.id_usuario, db)

        ahora = datetime.now()

        fecha_salida = datos.fecha_salida or ahora.date()
        hora_salida = datos.hora_salida or ahora.time().replace(microsecond=0)

        consulta = text("""
            UPDATE auditoria_accesos
            SET
                fecha_salida = :fecha_salida,
                hora_salida = :hora_salida,
                tiempo_conectado = (
                    CAST(:fecha_salida AS timestamp)
                    + CAST(:hora_salida AS time)
                    -
                    (fecha_ingreso::timestamp + hora_ingreso)
                ),
                estado_sesion = 'Cerrada'
            WHERE id_acceso = (
                SELECT id_acceso
                FROM auditoria_accesos
                WHERE id_usuario = :id_usuario
                  AND LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
                  AND fecha_salida IS NULL
                ORDER BY fecha_ingreso DESC, hora_ingreso DESC
                LIMIT 1
            )
            RETURNING
                id_acceso,
                id_usuario,
                fecha_ingreso,
                hora_ingreso,
                fecha_salida,
                hora_salida,
                tiempo_conectado::text AS tiempo_conectado,
                estado_sesion;
        """)

        resultado = db.execute(
            consulta,
            {
                "id_usuario": datos.id_usuario,
                "fecha_salida": fecha_salida,
                "hora_salida": hora_salida
            }
        )

        acceso = resultado.mappings().first()

        if acceso is None:
            raise HTTPException(
                status_code=404,
                detail="No existe una sesión activa para este usuario."
            )

        db.commit()

        return {
            "mensaje": "Sesión del usuario cerrada correctamente",
            "acceso": dict(acceso)
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al cerrar sesión del usuario: {str(error)}"
        )


# =====================================================
# CERRAR SESIONES ACTIVAS ANTIGUAS
# =====================================================

@router.post("/mantenimiento/cerrar-sesiones-antiguas")
def cerrar_sesiones_antiguas(
    datos: CerrarSesionesAntiguasCreate,
    db: Session = Depends(get_db)
):
    try:
        if datos.horas_antiguedad < 1:
            raise HTTPException(
                status_code=400,
                detail="Las horas de antigüedad deben ser mayores o iguales a 1."
            )

        ahora = datetime.now()
        fecha_salida = ahora.date()
        hora_salida = ahora.time().replace(microsecond=0)

        resultado = db.execute(
            text("""
                UPDATE auditoria_accesos
                SET
                    fecha_salida = :fecha_salida,
                    hora_salida = :hora_salida,
                    tiempo_conectado = (
                        CAST(:fecha_salida AS timestamp)
                        + CAST(:hora_salida AS time)
                        -
                        (fecha_ingreso::timestamp + hora_ingreso)
                    ),
                    estado_sesion = 'Cerrada'
                WHERE LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
                  AND fecha_salida IS NULL
                  AND (fecha_ingreso::timestamp + hora_ingreso) < (NOW() - (:horas_antiguedad * INTERVAL '1 hour'))
                RETURNING id_acceso;
            """),
            {
                "fecha_salida": fecha_salida,
                "hora_salida": hora_salida,
                "horas_antiguedad": datos.horas_antiguedad
            }
        )

        filas = resultado.mappings().all()
        total_cerradas = len(filas)

        db.commit()

        return {
            "mensaje": "Sesiones antiguas cerradas correctamente",
            "sesiones_cerradas": total_cerradas
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al cerrar sesiones antiguas: {str(error)}"
        )


# =====================================================
# REGISTRAR ACCIÓN AUTOMÁTICA
# =====================================================

@router.post("/registrar-accion")
def registrar_accion(datos: AccionCreate, db: Session = Depends(get_db)):
    try:
        validar_usuario_activo(datos.id_usuario, db)

        if not datos.modulo.strip():
            raise HTTPException(
                status_code=400,
                detail="El módulo es obligatorio."
            )

        if not datos.accion.strip():
            raise HTTPException(
                status_code=400,
                detail="La acción es obligatoria."
            )

        if not datos.descripcion.strip():
            raise HTTPException(
                status_code=400,
                detail="La descripción es obligatoria."
            )

        ahora = datetime.now()

        consulta = text("""
            INSERT INTO auditoria_acciones (
                id_usuario,
                modulo,
                accion,
                descripcion,
                fecha_accion,
                hora_accion,
                tabla_afectada,
                id_registro_afectado
            )
            VALUES (
                :id_usuario,
                :modulo,
                :accion,
                :descripcion,
                :fecha_accion,
                :hora_accion,
                :tabla_afectada,
                :id_registro_afectado
            )
            RETURNING id_accion;
        """)

        resultado = db.execute(
            consulta,
            {
                "id_usuario": datos.id_usuario,
                "modulo": datos.modulo.strip(),
                "accion": datos.accion.strip().upper(),
                "descripcion": datos.descripcion.strip(),
                "fecha_accion": ahora.date(),
                "hora_accion": ahora.time().replace(microsecond=0),
                "tabla_afectada": datos.tabla_afectada,
                "id_registro_afectado": datos.id_registro_afectado
            }
        )

        nueva_accion = resultado.mappings().first()

        db.commit()

        return {
            "mensaje": "Acción registrada correctamente en auditoría",
            "id_accion": nueva_accion["id_accion"]
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar acción de auditoría: {str(error)}"
        )


# =====================================================
# ARCHIVAR AUDITORÍA ANTIGUA
# =====================================================

@router.post("/mantenimiento/archivar")
def archivar_auditoria_antigua(
    datos: ArchivarAuditoriaCreate,
    db: Session = Depends(get_db)
):
    try:
        if datos.dias_antiguedad < 1:
            raise HTTPException(
                status_code=400,
                detail="Los días de antigüedad deben ser mayores o iguales a 1."
            )

        crear_tablas_historicas_si_no_existen(db)

        # Archivar accesos cerrados antiguos.
        accesos_insertados = db.execute(
            text("""
                INSERT INTO auditoria_accesos_historico
                SELECT *
                FROM auditoria_accesos
                WHERE estado_sesion = 'Cerrada'
                  AND fecha_salida IS NOT NULL
                  AND fecha_ingreso < (CURRENT_DATE - :dias_antiguedad)
                ON CONFLICT (id_acceso) DO NOTHING
                RETURNING id_acceso;
            """),
            {"dias_antiguedad": datos.dias_antiguedad}
        ).mappings().all()

        accesos_eliminados = db.execute(
            text("""
                DELETE FROM auditoria_accesos
                WHERE id_acceso IN (
                    SELECT id_acceso
                    FROM auditoria_accesos_historico
                    WHERE fecha_ingreso < (CURRENT_DATE - :dias_antiguedad)
                )
                RETURNING id_acceso;
            """),
            {"dias_antiguedad": datos.dias_antiguedad}
        ).mappings().all()

        # Archivar acciones antiguas.
        acciones_insertadas = db.execute(
            text("""
                INSERT INTO auditoria_acciones_historico
                SELECT *
                FROM auditoria_acciones
                WHERE fecha_accion < (CURRENT_DATE - :dias_antiguedad)
                ON CONFLICT (id_accion) DO NOTHING
                RETURNING id_accion;
            """),
            {"dias_antiguedad": datos.dias_antiguedad}
        ).mappings().all()

        acciones_eliminadas = db.execute(
            text("""
                DELETE FROM auditoria_acciones
                WHERE id_accion IN (
                    SELECT id_accion
                    FROM auditoria_acciones_historico
                    WHERE fecha_accion < (CURRENT_DATE - :dias_antiguedad)
                )
                RETURNING id_accion;
            """),
            {"dias_antiguedad": datos.dias_antiguedad}
        ).mappings().all()

        registrar_accion_interna(
            db=db,
            id_usuario=datos.id_usuario_admin,
            modulo="Auditoría",
            accion="ARCHIVAR_AUDITORIA",
            descripcion=(
                f"Archivó auditoría antigua mayor a {datos.dias_antiguedad} días. "
                f"Accesos archivados: {len(accesos_eliminados)}. "
                f"Acciones archivadas: {len(acciones_eliminadas)}."
            ),
            tabla_afectada="auditoria_historico",
            id_registro_afectado=None
        )

        db.commit()

        return {
            "mensaje": "Auditoría antigua archivada correctamente",
            "dias_antiguedad": datos.dias_antiguedad,
            "accesos_archivados": len(accesos_eliminados),
            "acciones_archivadas": len(acciones_eliminadas),
            "accesos_insertados_historico": len(accesos_insertados),
            "acciones_insertadas_historico": len(acciones_insertadas)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al archivar auditoría antigua: {str(error)}"
        )


# =====================================================
# LISTAR ACCIONES POR MÓDULO
# =====================================================

@router.get("/acciones/modulo/{modulo}")
def listar_acciones_por_modulo(
    modulo: str,
    limite: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    try:
        resultado = db.execute(
            text("""
                SELECT *
                FROM vista_auditoria_general
                WHERE modulo ILIKE :modulo
                ORDER BY fecha_accion DESC, hora_accion DESC, id_accion DESC
                LIMIT :limite OFFSET :offset;
            """),
            {
                "modulo": f"%{modulo}%",
                "limite": limite,
                "offset": offset
            }
        )

        filas = resultado.mappings().all()
        return [dict(fila) for fila in filas]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar acciones por módulo: {str(error)}"
        )


# =====================================================
# LISTAR ACCIONES POR USUARIO
# =====================================================

@router.get("/acciones/usuario/{usuario}")
def listar_acciones_por_usuario(
    usuario: str,
    limite: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    try:
        resultado = db.execute(
            text("""
                SELECT *
                FROM vista_auditoria_general
                WHERE usuario ILIKE :usuario
                ORDER BY fecha_accion DESC, hora_accion DESC, id_accion DESC
                LIMIT :limite OFFSET :offset;
            """),
            {
                "usuario": f"%{usuario}%",
                "limite": limite,
                "offset": offset
            }
        )

        filas = resultado.mappings().all()
        return [dict(fila) for fila in filas]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar acciones por usuario: {str(error)}"
        )


# =====================================================
# LISTAR ACCIONES CRÍTICAS
# =====================================================

@router.get("/acciones-criticas")
def listar_acciones_criticas(
    limite: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    try:
        resultado = db.execute(
            text("""
                SELECT *
                FROM vista_auditoria_general
                WHERE
                    UPPER(accion) LIKE '%ELIMINAR%'
                    OR UPPER(accion) LIKE '%ANULAR%'
                    OR UPPER(accion) LIKE '%EDITAR%'
                    OR UPPER(accion) LIKE '%MODIFICAR%'
                    OR UPPER(accion) LIKE '%ACTUALIZAR%'
                    OR UPPER(accion) LIKE '%ACCESO_DENEGADO%'
                ORDER BY fecha_accion DESC, hora_accion DESC, id_accion DESC
                LIMIT :limite OFFSET :offset;
            """),
            {
                "limite": limite,
                "offset": offset
            }
        )

        filas = resultado.mappings().all()
        return [dict(fila) for fila in filas]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar acciones críticas: {str(error)}"
        )