from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
    ip_equipo: Optional[str] = None
    navegador: Optional[str] = None
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
    ip_equipo: Optional[str] = None
    navegador: Optional[str] = None


class CerrarSesionesAntiguasCreate(BaseModel):
    horas_antiguedad: int = 12


class ArchivarAuditoriaCreate(BaseModel):
    dias_antiguedad: int = 30
    id_usuario_admin: Optional[int] = None


# =====================================================
# FUNCIONES INTERNAS DE ESTRUCTURA
# =====================================================

def tabla_existe(db: Session, nombre_tabla: str) -> bool:
    resultado = db.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = :nombre_tabla
            ) AS existe;
        """),
        {"nombre_tabla": nombre_tabla}
    ).mappings().first()

    return bool(resultado["existe"])


def columna_existe(db: Session, nombre_tabla: str, nombre_columna: str) -> bool:
    resultado = db.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :nombre_tabla
                  AND column_name = :nombre_columna
            ) AS existe;
        """),
        {
            "nombre_tabla": nombre_tabla,
            "nombre_columna": nombre_columna
        }
    ).mappings().first()

    return bool(resultado["existe"])


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


def asegurar_estructura_auditoria(db: Session):
    """
    Asegura columnas necesarias para auditoría en producción.
    No elimina datos.
    Solo agrega columnas si faltan.
    """
    try:
        if tabla_existe(db, "auditoria_accesos"):
            db.execute(text("""
                ALTER TABLE auditoria_accesos
                ADD COLUMN IF NOT EXISTS navegador VARCHAR(300);
            """))

            db.execute(text("""
                ALTER TABLE auditoria_accesos
                ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();
            """))

            db.execute(text("""
                UPDATE auditoria_accesos
                SET estado_sesion = 'Activa'
                WHERE LOWER(COALESCE(estado_sesion, '')) IN ('abierta', 'activo');
            """))

            db.execute(text("""
                UPDATE auditoria_accesos
                SET estado_sesion = 'Cerrada'
                WHERE LOWER(COALESCE(estado_sesion, '')) = 'cerrado';
            """))

        if tabla_existe(db, "auditoria_acciones"):
            db.execute(text("""
                ALTER TABLE auditoria_acciones
                ADD COLUMN IF NOT EXISTS ip_equipo VARCHAR(100);
            """))

            db.execute(text("""
                ALTER TABLE auditoria_acciones
                ADD COLUMN IF NOT EXISTS navegador VARCHAR(300);
            """))

            db.execute(text("""
                ALTER TABLE auditoria_acciones
                ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();
            """))

            db.execute(text("""
                UPDATE auditoria_acciones
                SET accion = 'INGRESO_MODULO'
                WHERE UPPER(COALESCE(accion, '')) = 'ACCESO_MODULO';
            """))

        if tabla_existe(db, "auditoria_accesos") and tabla_existe(db, "auditoria_acciones"):
            crear_tablas_historicas_si_no_existen(db)

            if tabla_existe(db, "auditoria_accesos_historico"):
                db.execute(text("""
                    ALTER TABLE auditoria_accesos_historico
                    ADD COLUMN IF NOT EXISTS navegador VARCHAR(300);
                """))

                db.execute(text("""
                    ALTER TABLE auditoria_accesos_historico
                    ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();
                """))

            if tabla_existe(db, "auditoria_acciones_historico"):
                db.execute(text("""
                    ALTER TABLE auditoria_acciones_historico
                    ADD COLUMN IF NOT EXISTS ip_equipo VARCHAR(100);
                """))

                db.execute(text("""
                    ALTER TABLE auditoria_acciones_historico
                    ADD COLUMN IF NOT EXISTS navegador VARCHAR(300);
                """))

                db.execute(text("""
                    ALTER TABLE auditoria_acciones_historico
                    ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();
                """))

        db.commit()

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo preparar la estructura de auditoría. Detalle: {str(error)}"
        )


# =====================================================
# FUNCIONES INTERNAS GENERALES
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


def normalizar_accion_auditoria(accion: str) -> str:
    accion_limpia = str(accion or "").strip().upper().replace(" ", "_")

    equivalencias = {
        "ACCESO_MODULO": "INGRESO_MODULO",
        "ENTRAR_MODULO": "INGRESO_MODULO",
        "INGRESAR_MODULO": "INGRESO_MODULO",
        "CREADO": "CREAR",
        "REGISTRAR": "CREAR",
        "REGISTRADO": "CREAR",
        "INSERT": "CREAR",
        "INSERTAR": "CREAR",
        "UPDATE": "EDITAR",
        "ACTUALIZAR": "EDITAR",
        "MODIFICAR": "EDITAR",
        "BORRAR": "ELIMINAR",
        "DELETE": "ELIMINAR",
        "DESACTIVAR": "INACTIVAR"
    }

    return equivalencias.get(accion_limpia, accion_limpia)


def limpiar_valor_ip(valor: Optional[str]) -> Optional[str]:
    """
    Limpia valores recibidos desde headers de proxy.
    Evita guardar valores vacíos, desconocidos o demasiado largos.
    """
    if valor is None:
        return None

    valor_limpio = valor.strip()

    if not valor_limpio:
        return None

    if valor_limpio.lower() in ["unknown", "null", "none", "undefined"]:
        return None

    return valor_limpio[:100]


def limpiar_navegador(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None

    valor_limpio = valor.strip()

    if not valor_limpio:
        return None

    if valor_limpio.lower() in ["unknown", "null", "none", "undefined"]:
        return None

    return valor_limpio[:300]


def obtener_ip_cliente(request: Request) -> str:
    """
    Obtiene la IP real del cliente desde FastAPI.
    En producción, Render trabaja detrás de proxy.
    """
    cf_ip = limpiar_valor_ip(request.headers.get("cf-connecting-ip"))
    if cf_ip:
        return cf_ip

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ips = forwarded_for.split(",")
        for ip in ips:
            ip_limpia = limpiar_valor_ip(ip)
            if ip_limpia:
                return ip_limpia

    real_ip = limpiar_valor_ip(request.headers.get("x-real-ip"))
    if real_ip:
        return real_ip

    if request.client and request.client.host:
        ip_cliente = limpiar_valor_ip(request.client.host)
        if ip_cliente:
            return ip_cliente

    return "127.0.0.1"


def obtener_navegador_cliente(request: Request) -> str:
    navegador = limpiar_navegador(request.headers.get("user-agent"))
    return navegador or "No identificado"


def validar_usuario_activo(id_usuario: int, db: Session):
    usuario = db.execute(
        text("""
            SELECT
                u.id_usuario,
                u.usuario,
                u.nombres,
                u.apellidos,
                u.id_perfil,
                p.nombre_perfil
            FROM usuarios u
            INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
            WHERE u.id_usuario = :id_usuario
              AND u.estado = TRUE;
        """),
        {"id_usuario": id_usuario}
    ).mappings().first()

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="El usuario no existe o está inactivo."
        )

    return usuario


def construir_where_acciones(
    usuario: Optional[str],
    perfil: Optional[str],
    modulo: Optional[str],
    accion: Optional[str],
    fecha_desde: Optional[date],
    fecha_hasta: Optional[date]
):
    condiciones = []
    parametros = {}

    if usuario:
        condiciones.append("u.usuario ILIKE :usuario")
        parametros["usuario"] = f"%{usuario.strip()}%"

    if perfil and perfil.lower() not in ["todos", "todas"]:
        condiciones.append("p.nombre_perfil ILIKE :perfil")
        parametros["perfil"] = f"%{perfil.strip()}%"

    if modulo and modulo.lower() not in ["todos", "todas"]:
        condiciones.append("aa.modulo ILIKE :modulo")
        parametros["modulo"] = f"%{modulo.strip()}%"

    if accion and accion.lower() not in ["todos", "todas"]:
        condiciones.append("aa.accion ILIKE :accion")
        parametros["accion"] = f"%{accion.strip()}%"

    if fecha_desde:
        condiciones.append("aa.fecha_accion >= :fecha_desde")
        parametros["fecha_desde"] = fecha_desde

    if fecha_hasta:
        condiciones.append("aa.fecha_accion <= :fecha_hasta")
        parametros["fecha_hasta"] = fecha_hasta

    where_sql = ""

    if condiciones:
        where_sql = "WHERE " + " AND ".join(condiciones)

    return where_sql, parametros


def construir_where_accesos(
    usuario: Optional[str],
    perfil: Optional[str],
    fecha_desde: Optional[date],
    fecha_hasta: Optional[date],
    estado_sesion: Optional[str]
):
    condiciones = []
    parametros = {}

    if usuario:
        condiciones.append("u.usuario ILIKE :usuario")
        parametros["usuario"] = f"%{usuario.strip()}%"

    if perfil and perfil.lower() not in ["todos", "todas"]:
        condiciones.append("p.nombre_perfil ILIKE :perfil")
        parametros["perfil"] = f"%{perfil.strip()}%"

    if fecha_desde:
        condiciones.append("aa.fecha_ingreso >= :fecha_desde")
        parametros["fecha_desde"] = fecha_desde

    if fecha_hasta:
        condiciones.append("aa.fecha_ingreso <= :fecha_hasta")
        parametros["fecha_hasta"] = fecha_hasta

    if estado_sesion and estado_sesion.lower() not in ["todos", "todas"]:
        estado_normalizado = normalizar_estado_sesion(estado_sesion)
        condiciones.append("aa.estado_sesion = :estado_sesion")
        parametros["estado_sesion"] = estado_normalizado

    where_sql = ""

    if condiciones:
        where_sql = "WHERE " + " AND ".join(condiciones)

    return where_sql, parametros


def registrar_accion_interna(
    db: Session,
    id_usuario: Optional[int],
    modulo: str,
    accion: str,
    descripcion: str,
    tabla_afectada: Optional[str] = None,
    id_registro_afectado: Optional[int] = None,
    ip_equipo: Optional[str] = None,
    navegador: Optional[str] = None
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
                    id_registro_afectado,
                    ip_equipo,
                    navegador
                )
                VALUES (
                    :id_usuario,
                    :modulo,
                    :accion,
                    :descripcion,
                    CURRENT_DATE,
                    CURRENT_TIME,
                    :tabla_afectada,
                    :id_registro_afectado,
                    :ip_equipo,
                    :navegador
                );
            """),
            {
                "id_usuario": id_usuario,
                "modulo": modulo.strip(),
                "accion": normalizar_accion_auditoria(accion),
                "descripcion": descripcion.strip(),
                "tabla_afectada": tabla_afectada,
                "id_registro_afectado": id_registro_afectado,
                "ip_equipo": ip_equipo,
                "navegador": navegador
            }
        )
    except Exception:
        pass


def cerrar_sesiones_activas_usuario(id_usuario: int, db: Session):
    """
    Cierra sesiones anteriores activas o abiertas del mismo usuario.
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
# =====================================================

@router.get("/acciones")
def listar_acciones(
    limite: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    usuario: Optional[str] = Query(None),
    perfil: Optional[str] = Query(None),
    modulo: Optional[str] = Query(None),
    accion: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        asegurar_estructura_auditoria(db)

        where_sql, parametros = construir_where_acciones(
            usuario=usuario,
            perfil=perfil,
            modulo=modulo,
            accion=accion,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        parametros["limite"] = limite
        parametros["offset"] = offset

        resultado = db.execute(
            text(f"""
                SELECT
                    aa.id_accion,
                    u.usuario,
                    p.nombre_perfil,
                    aa.modulo,
                    aa.accion,
                    aa.descripcion,
                    COALESCE(aa.tabla_afectada, '-') AS tabla_afectada,
                    aa.id_registro_afectado,
                    aa.fecha_accion,
                    aa.hora_accion,
                    COALESCE(aa.ip_equipo, '-') AS ip_equipo,
                    COALESCE(aa.navegador, '-') AS navegador
                FROM auditoria_acciones aa
                INNER JOIN usuarios u ON aa.id_usuario = u.id_usuario
                INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
                {where_sql}
                ORDER BY aa.fecha_accion DESC, aa.hora_accion DESC, aa.id_accion DESC
                LIMIT :limite OFFSET :offset;
            """),
            parametros
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
# =====================================================

@router.get("/accesos")
def listar_accesos(
    limite: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    usuario: Optional[str] = Query(None),
    perfil: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    estado_sesion: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        asegurar_estructura_auditoria(db)

        where_sql, parametros = construir_where_accesos(
            usuario=usuario,
            perfil=perfil,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            estado_sesion=estado_sesion
        )

        parametros["limite"] = limite
        parametros["offset"] = offset

        resultado = db.execute(
            text(f"""
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
                    COALESCE(aa.navegador, '-') AS navegador,
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
                {where_sql}
                ORDER BY aa.fecha_ingreso DESC, aa.hora_ingreso DESC, aa.id_acceso DESC
                LIMIT :limite OFFSET :offset;
            """),
            parametros
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
        asegurar_estructura_auditoria(db)

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
                        WHERE UPPER(accion) LIKE '%DENEGADO%'
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
                            OR UPPER(accion) LIKE '%INACTIVAR%'
                            OR UPPER(accion) LIKE '%SUSPENDER%'
                            OR UPPER(accion) LIKE '%CAMBIO_SUELDO%'
                            OR UPPER(accion) LIKE '%GENERAR_ROL%'
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
        asegurar_estructura_auditoria(db)

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
def registrar_acceso(
    acceso: AccesoCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        asegurar_estructura_auditoria(db)
        validar_usuario_activo(acceso.id_usuario, db)

        estado_sesion = normalizar_estado_sesion(acceso.estado_sesion)

        ahora = datetime.now()
        fecha_ingreso = acceso.fecha_ingreso or ahora.date()
        hora_ingreso = acceso.hora_ingreso or ahora.time().replace(microsecond=0)

        ip_cliente = obtener_ip_cliente(request)
        navegador_cliente = limpiar_navegador(acceso.navegador) or obtener_navegador_cliente(request)

        cerrar_sesiones_activas_usuario(acceso.id_usuario, db)

        consulta = text("""
            INSERT INTO auditoria_accesos (
                id_usuario,
                fecha_ingreso,
                hora_ingreso,
                ip_equipo,
                navegador,
                estado_sesion
            )
            VALUES (
                :id_usuario,
                :fecha_ingreso,
                :hora_ingreso,
                :ip_equipo,
                :navegador,
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
                "ip_equipo": ip_cliente,
                "navegador": navegador_cliente,
                "estado_sesion": estado_sesion
            }
        )

        nuevo_acceso = resultado.mappings().first()

        db.commit()

        return {
            "mensaje": "Acceso registrado correctamente",
            "id_acceso": nuevo_acceso["id_acceso"],
            "estado_sesion": estado_sesion,
            "ip_equipo": ip_cliente,
            "navegador": navegador_cliente
        }

    except HTTPException:
        db.rollback()
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
        asegurar_estructura_auditoria(db)

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

        registrar_accion_interna(
            db=db,
            id_usuario=acceso["id_usuario"],
            modulo="Seguridad",
            accion="LOGOUT",
            descripcion="El usuario cerró sesión en el sistema.",
            tabla_afectada="auditoria_accesos",
            id_registro_afectado=acceso["id_acceso"]
        )

        db.commit()

        return {
            "mensaje": "Sesión cerrada correctamente",
            "acceso": dict(acceso)
        }

    except HTTPException:
        db.rollback()
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
        asegurar_estructura_auditoria(db)
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

        registrar_accion_interna(
            db=db,
            id_usuario=acceso["id_usuario"],
            modulo="Seguridad",
            accion="LOGOUT",
            descripcion="Sesión cerrada correctamente para el usuario.",
            tabla_afectada="auditoria_accesos",
            id_registro_afectado=acceso["id_acceso"]
        )

        db.commit()

        return {
            "mensaje": "Sesión del usuario cerrada correctamente",
            "acceso": dict(acceso)
        }

    except HTTPException:
        db.rollback()
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
        asegurar_estructura_auditoria(db)

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
                RETURNING id_acceso, id_usuario;
            """),
            {
                "fecha_salida": fecha_salida,
                "hora_salida": hora_salida,
                "horas_antiguedad": datos.horas_antiguedad
            }
        )

        filas = resultado.mappings().all()
        total_cerradas = len(filas)

        id_usuario_registro = filas[0]["id_usuario"] if filas else None

        registrar_accion_interna(
            db=db,
            id_usuario=id_usuario_registro,
            modulo="Auditoría",
            accion="CERRAR_SESIONES_ANTIGUAS",
            descripcion=f"Se cerraron {total_cerradas} sesiones activas antiguas mayores a {datos.horas_antiguedad} horas.",
            tabla_afectada="auditoria_accesos",
            id_registro_afectado=None
        )

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
def registrar_accion(
    datos: AccionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        asegurar_estructura_auditoria(db)
        validar_usuario_activo(datos.id_usuario, db)

        modulo = datos.modulo.strip()
        accion_normalizada = normalizar_accion_auditoria(datos.accion)
        descripcion = datos.descripcion.strip()

        if not modulo:
            raise HTTPException(
                status_code=400,
                detail="El módulo es obligatorio."
            )

        if not accion_normalizada:
            raise HTTPException(
                status_code=400,
                detail="La acción es obligatoria."
            )

        if not descripcion:
            raise HTTPException(
                status_code=400,
                detail="La descripción es obligatoria."
            )

        ahora = datetime.now()

        ip_cliente = limpiar_valor_ip(datos.ip_equipo) or obtener_ip_cliente(request)
        navegador_cliente = limpiar_navegador(datos.navegador) or obtener_navegador_cliente(request)

        # Evita duplicar ingresos de módulo cuando main.js y otro archivo llaman al mismo tiempo.
        if accion_normalizada == "INGRESO_MODULO":
            accion_duplicada = db.execute(
                text("""
                    SELECT id_accion
                    FROM auditoria_acciones
                    WHERE id_usuario = :id_usuario
                      AND modulo = :modulo
                      AND accion = 'INGRESO_MODULO'
                      AND (fecha_accion::timestamp + hora_accion) >= (NOW() - INTERVAL '5 seconds')
                    ORDER BY id_accion DESC
                    LIMIT 1;
                """),
                {
                    "id_usuario": datos.id_usuario,
                    "modulo": modulo
                }
            ).mappings().first()

            if accion_duplicada is not None:
                return {
                    "mensaje": "Acción duplicada ignorada correctamente.",
                    "id_accion": accion_duplicada["id_accion"],
                    "duplicada": True
                }

        consulta = text("""
            INSERT INTO auditoria_acciones (
                id_usuario,
                modulo,
                accion,
                descripcion,
                fecha_accion,
                hora_accion,
                tabla_afectada,
                id_registro_afectado,
                ip_equipo,
                navegador
            )
            VALUES (
                :id_usuario,
                :modulo,
                :accion,
                :descripcion,
                :fecha_accion,
                :hora_accion,
                :tabla_afectada,
                :id_registro_afectado,
                :ip_equipo,
                :navegador
            )
            RETURNING id_accion;
        """)

        resultado = db.execute(
            consulta,
            {
                "id_usuario": datos.id_usuario,
                "modulo": modulo,
                "accion": accion_normalizada,
                "descripcion": descripcion,
                "fecha_accion": ahora.date(),
                "hora_accion": ahora.time().replace(microsecond=0),
                "tabla_afectada": datos.tabla_afectada,
                "id_registro_afectado": datos.id_registro_afectado,
                "ip_equipo": ip_cliente,
                "navegador": navegador_cliente
            }
        )

        nueva_accion = resultado.mappings().first()

        db.commit()

        return {
            "mensaje": "Acción registrada correctamente en auditoría",
            "id_accion": nueva_accion["id_accion"],
            "ip_equipo": ip_cliente,
            "accion": accion_normalizada
        }

    except HTTPException:
        db.rollback()
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
        asegurar_estructura_auditoria(db)

        if datos.dias_antiguedad < 1:
            raise HTTPException(
                status_code=400,
                detail="Los días de antigüedad deben ser mayores o iguales a 1."
            )

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
        asegurar_estructura_auditoria(db)

        resultado = db.execute(
            text("""
                SELECT
                    aa.id_accion,
                    u.usuario,
                    p.nombre_perfil,
                    aa.modulo,
                    aa.accion,
                    aa.descripcion,
                    COALESCE(aa.tabla_afectada, '-') AS tabla_afectada,
                    aa.id_registro_afectado,
                    aa.fecha_accion,
                    aa.hora_accion,
                    COALESCE(aa.ip_equipo, '-') AS ip_equipo,
                    COALESCE(aa.navegador, '-') AS navegador
                FROM auditoria_acciones aa
                INNER JOIN usuarios u ON aa.id_usuario = u.id_usuario
                INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
                WHERE aa.modulo ILIKE :modulo
                ORDER BY aa.fecha_accion DESC, aa.hora_accion DESC, aa.id_accion DESC
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
        asegurar_estructura_auditoria(db)

        resultado = db.execute(
            text("""
                SELECT
                    aa.id_accion,
                    u.usuario,
                    p.nombre_perfil,
                    aa.modulo,
                    aa.accion,
                    aa.descripcion,
                    COALESCE(aa.tabla_afectada, '-') AS tabla_afectada,
                    aa.id_registro_afectado,
                    aa.fecha_accion,
                    aa.hora_accion,
                    COALESCE(aa.ip_equipo, '-') AS ip_equipo,
                    COALESCE(aa.navegador, '-') AS navegador
                FROM auditoria_acciones aa
                INNER JOIN usuarios u ON aa.id_usuario = u.id_usuario
                INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
                WHERE u.usuario ILIKE :usuario
                ORDER BY aa.fecha_accion DESC, aa.hora_accion DESC, aa.id_accion DESC
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
        asegurar_estructura_auditoria(db)

        resultado = db.execute(
            text("""
                SELECT
                    aa.id_accion,
                    u.usuario,
                    p.nombre_perfil,
                    aa.modulo,
                    aa.accion,
                    aa.descripcion,
                    COALESCE(aa.tabla_afectada, '-') AS tabla_afectada,
                    aa.id_registro_afectado,
                    aa.fecha_accion,
                    aa.hora_accion,
                    COALESCE(aa.ip_equipo, '-') AS ip_equipo,
                    COALESCE(aa.navegador, '-') AS navegador
                FROM auditoria_acciones aa
                INNER JOIN usuarios u ON aa.id_usuario = u.id_usuario
                INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
                WHERE
                    UPPER(aa.accion) LIKE '%ELIMINAR%'
                    OR UPPER(aa.accion) LIKE '%ANULAR%'
                    OR UPPER(aa.accion) LIKE '%EDITAR%'
                    OR UPPER(aa.accion) LIKE '%MODIFICAR%'
                    OR UPPER(aa.accion) LIKE '%ACTUALIZAR%'
                    OR UPPER(aa.accion) LIKE '%INACTIVAR%'
                    OR UPPER(aa.accion) LIKE '%SUSPENDER%'
                    OR UPPER(aa.accion) LIKE '%CAMBIO_SUELDO%'
                    OR UPPER(aa.accion) LIKE '%GENERAR_ROL%'
                    OR UPPER(aa.accion) LIKE '%ACCESO_DENEGADO%'
                    OR UPPER(aa.accion) LIKE '%DENEGADO%'
                ORDER BY aa.fecha_accion DESC, aa.hora_accion DESC, aa.id_accion DESC
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