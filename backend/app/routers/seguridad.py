from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from app.database import get_db


router = APIRouter(
    prefix="/api/seguridad",
    tags=["Seguridad y Usuarios"]
)


# ----------------------------------------------------
# MODELOS
# ----------------------------------------------------

class UsuarioCreate(BaseModel):
    id_perfil: int
    nombres: str
    apellidos: str
    usuario: str
    correo: Optional[EmailStr] = None
    contrasena: str
    estado: bool = True
    id_admin: Optional[int] = None


class UsuarioUpdate(BaseModel):
    id_perfil: int
    nombres: str
    apellidos: str
    usuario: str
    correo: Optional[EmailStr] = None
    estado: bool = True
    id_admin: Optional[int] = None


class CambiarContrasena(BaseModel):
    nueva_contrasena: str
    id_admin: Optional[int] = None


class EstadoUsuarioUpdate(BaseModel):
    estado: bool
    id_admin: Optional[int] = None


class LoginCreate(BaseModel):
    usuario: str
    contrasena: str


class LogoutCreate(BaseModel):
    id_usuario: int
    id_acceso: Optional[int] = None


class PermisoModuloUpdate(BaseModel):
    id_modulo: int
    puede_ver: bool = False
    puede_crear: bool = False
    puede_editar: bool = False
    puede_eliminar: bool = False
    puede_consultar: bool = False
    puede_generar_reporte: bool = False


class PermisosUsuarioUpdate(BaseModel):
    id_usuario: int
    permisos: List[PermisoModuloUpdate]
    id_admin: Optional[int] = None


# ----------------------------------------------------
# FUNCIÓN INTERNA PARA AUDITORÍA
# ----------------------------------------------------

def limpiar_valor_ip(valor: Optional[str]) -> Optional[str]:
    """
    Limpia valores recibidos desde headers de proxy.
    Evita guardar valores vacíos, desconocidos o demasiado largos.
    La columna auditoria_accesos.ip_equipo ya soporta hasta VARCHAR(100).
    """
    if valor is None:
        return None

    valor_limpio = valor.strip()

    if not valor_limpio:
        return None

    if valor_limpio.lower() in ["unknown", "null", "none", "undefined"]:
        return None

    return valor_limpio[:100]


def obtener_ip_cliente(request: Request) -> str:
    """
    Obtiene la IP real del cliente desde FastAPI.

    En producción, Render trabaja detrás de proxy, por eso se revisan primero
    los headers más comunes:

    1. cf-connecting-ip
    2. x-forwarded-for
    3. x-real-ip
    4. request.client.host
    5. 127.0.0.1 como respaldo final

    No se depende del frontend para conocer la IP real.
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


def registrar_auditoria_seguridad(
    db: Session,
    id_usuario: Optional[int],
    accion: str,
    descripcion: str,
    tabla_afectada: Optional[str] = None,
    id_registro_afectado: Optional[int] = None
):
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
                    'Seguridad y Usuarios',
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
                "accion": accion.strip().upper(),
                "descripcion": descripcion,
                "tabla_afectada": tabla_afectada,
                "id_registro_afectado": id_registro_afectado
            }
        )
    except Exception:
        pass


def registrar_auditoria_login(
    db: Session,
    id_usuario: int,
    usuario: str
):
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
                    'Login',
                    'LOGIN',
                    :descripcion,
                    CURRENT_DATE,
                    CURRENT_TIME,
                    'usuarios',
                    :id_usuario
                );
            """),
            {
                "id_usuario": id_usuario,
                "descripcion": f"El usuario {usuario} inició sesión en el sistema."
            }
        )
    except Exception:
        pass


def registrar_auditoria_logout(
    db: Session,
    id_usuario: int,
    usuario: str
):
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
                    'Login',
                    'LOGOUT',
                    :descripcion,
                    CURRENT_DATE,
                    CURRENT_TIME,
                    'auditoria_accesos',
                    NULL
                );
            """),
            {
                "id_usuario": id_usuario,
                "descripcion": f"El usuario {usuario} cerró sesión en el sistema."
            }
        )
    except Exception:
        pass


def cerrar_sesiones_activas_usuario_seguridad(
    db: Session,
    id_usuario: int
):
    """
    Cierra sesiones activas anteriores del usuario antes de crear una nueva.
    Esto evita que queden muchas sesiones abiertas cuando el usuario entra varias veces.
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

def registrar_acceso_login_seguridad(
    db: Session,
    id_usuario: int,
    ip_cliente: str
):
    """
    Registra una nueva sesión activa en auditoria_accesos.
    """
    ahora = datetime.now()
    fecha_ingreso = ahora.date()
    hora_ingreso = ahora.time().replace(microsecond=0)

    resultado = db.execute(
        text("""
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
                'Activa'
            )
            RETURNING id_acceso;
        """),
        {
            "id_usuario": id_usuario,
            "fecha_ingreso": fecha_ingreso,
            "hora_ingreso": hora_ingreso,
            "ip_equipo": ip_cliente or "127.0.0.1"
        }
    )

    fila = resultado.mappings().first()

    if fila is None:
        return None

    return fila["id_acceso"]


def obtener_usuario_por_id(
    db: Session,
    id_usuario: int
):
    resultado = db.execute(
        text("""
            SELECT
                id_usuario,
                usuario
            FROM usuarios
            WHERE id_usuario = :id_usuario
              AND estado = TRUE;
        """),
        {"id_usuario": id_usuario}
    )

    return resultado.mappings().first()


# ----------------------------------------------------
# PERFILES
# ----------------------------------------------------

@router.get("/perfiles")
def listar_perfiles(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                id_perfil,
                nombre_perfil,
                descripcion,
                estado,
                fecha_creacion
            FROM perfiles
            WHERE estado = TRUE
            ORDER BY id_perfil ASC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


# ----------------------------------------------------
# MÓDULOS DEL SISTEMA
# ----------------------------------------------------

@router.get("/modulos")
def listar_modulos(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                id_modulo,
                nombre_modulo,
                ruta_html,
                descripcion,
                estado,
                fecha_creacion
            FROM modulos_sistema
            WHERE estado = TRUE
            ORDER BY id_modulo ASC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


# ----------------------------------------------------
# USUARIOS
# ----------------------------------------------------

@router.get("/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                u.id_usuario,
                u.nombres,
                u.apellidos,
                u.usuario,
                u.correo,
                u.estado,
                u.fecha_creacion,
                p.id_perfil,
                p.nombre_perfil
            FROM usuarios u
            INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
            ORDER BY u.id_usuario ASC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.get("/usuarios/{id_usuario}")
def obtener_usuario(id_usuario: int, db: Session = Depends(get_db)):
    resultado = db.execute(
        text("""
            SELECT
                u.id_usuario,
                u.nombres,
                u.apellidos,
                u.usuario,
                u.correo,
                u.estado,
                u.fecha_creacion,
                p.id_perfil,
                p.nombre_perfil
            FROM usuarios u
            INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
            WHERE u.id_usuario = :id_usuario;
        """),
        {"id_usuario": id_usuario}
    )

    fila = resultado.mappings().first()

    if fila is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    return dict(fila)


@router.post("/usuarios")
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        existe_perfil = db.execute(
            text("""
                SELECT id_perfil
                FROM perfiles
                WHERE id_perfil = :id_perfil
                  AND estado = TRUE;
            """),
            {"id_perfil": usuario.id_perfil}
        ).first()

        if existe_perfil is None:
            raise HTTPException(
                status_code=404,
                detail="El perfil seleccionado no existe o está inactivo."
            )

        existe_usuario = db.execute(
            text("""
                SELECT id_usuario
                FROM usuarios
                WHERE usuario = :usuario;
            """),
            {"usuario": usuario.usuario}
        ).first()

        if existe_usuario is not None:
            raise HTTPException(
                status_code=400,
                detail="Ya existe un usuario con ese nombre de usuario."
            )

        if usuario.correo:
            existe_correo = db.execute(
                text("""
                    SELECT id_usuario
                    FROM usuarios
                    WHERE correo = :correo;
                """),
                {"correo": usuario.correo}
            ).first()

            if existe_correo is not None:
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe un usuario con ese correo."
                )

        resultado = db.execute(
            text("""
                INSERT INTO usuarios (
                    id_perfil,
                    nombres,
                    apellidos,
                    usuario,
                    correo,
                    contrasena_hash,
                    estado
                )
                VALUES (
                    :id_perfil,
                    :nombres,
                    :apellidos,
                    :usuario,
                    :correo,
                    :contrasena_hash,
                    :estado
                )
                RETURNING id_usuario, usuario, nombres, apellidos;
            """),
            {
                "id_perfil": usuario.id_perfil,
                "nombres": usuario.nombres.strip(),
                "apellidos": usuario.apellidos.strip(),
                "usuario": usuario.usuario.strip(),
                "correo": usuario.correo,
                "contrasena_hash": usuario.contrasena,
                "estado": usuario.estado
            }
        )

        nuevo_usuario = resultado.mappings().first()

        registrar_auditoria_seguridad(
            db=db,
            id_usuario=usuario.id_admin,
            accion="CREAR",
            descripcion=f"Creó el usuario {nuevo_usuario['usuario']} en el sistema.",
            tabla_afectada="usuarios",
            id_registro_afectado=nuevo_usuario["id_usuario"]
        )

        db.commit()

        return {
            "mensaje": "Usuario registrado correctamente",
            "usuario": dict(nuevo_usuario)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo registrar el usuario. Detalle: {str(error)}"
        )


@router.put("/usuarios/{id_usuario}")
def actualizar_usuario(
    id_usuario: int,
    usuario: UsuarioUpdate,
    db: Session = Depends(get_db)
):
    try:
        existe = db.execute(
            text("""
                SELECT id_usuario
                FROM usuarios
                WHERE id_usuario = :id_usuario;
            """),
            {"id_usuario": id_usuario}
        ).first()

        if existe is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        existe_perfil = db.execute(
            text("""
                SELECT id_perfil
                FROM perfiles
                WHERE id_perfil = :id_perfil
                  AND estado = TRUE;
            """),
            {"id_perfil": usuario.id_perfil}
        ).first()

        if existe_perfil is None:
            raise HTTPException(
                status_code=404,
                detail="El perfil seleccionado no existe o está inactivo."
            )

        duplicado_usuario = db.execute(
            text("""
                SELECT id_usuario
                FROM usuarios
                WHERE usuario = :usuario
                  AND id_usuario <> :id_usuario;
            """),
            {
                "usuario": usuario.usuario,
                "id_usuario": id_usuario
            }
        ).first()

        if duplicado_usuario is not None:
            raise HTTPException(
                status_code=400,
                detail="Ya existe otro usuario con ese nombre de usuario."
            )

        resultado = db.execute(
            text("""
                UPDATE usuarios
                SET
                    id_perfil = :id_perfil,
                    nombres = :nombres,
                    apellidos = :apellidos,
                    usuario = :usuario,
                    correo = :correo,
                    estado = :estado
                WHERE id_usuario = :id_usuario
                RETURNING id_usuario, usuario, nombres, apellidos, estado;
            """),
            {
                "id_usuario": id_usuario,
                "id_perfil": usuario.id_perfil,
                "nombres": usuario.nombres.strip(),
                "apellidos": usuario.apellidos.strip(),
                "usuario": usuario.usuario.strip(),
                "correo": usuario.correo,
                "estado": usuario.estado
            }
        )

        usuario_actualizado = resultado.mappings().first()

        registrar_auditoria_seguridad(
            db=db,
            id_usuario=usuario.id_admin,
            accion="EDITAR",
            descripcion=f"Actualizó los datos del usuario {usuario_actualizado['usuario']}.",
            tabla_afectada="usuarios",
            id_registro_afectado=id_usuario
        )

        db.commit()

        return {
            "mensaje": "Usuario actualizado correctamente",
            "usuario": dict(usuario_actualizado)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo actualizar el usuario. Detalle: {str(error)}"
        )


@router.put("/usuarios/{id_usuario}/estado")
def cambiar_estado_usuario(
    id_usuario: int,
    datos: EstadoUsuarioUpdate,
    db: Session = Depends(get_db)
):
    try:
        resultado = db.execute(
            text("""
                UPDATE usuarios
                SET estado = :estado
                WHERE id_usuario = :id_usuario
                RETURNING id_usuario, usuario, estado;
            """),
            {
                "id_usuario": id_usuario,
                "estado": datos.estado
            }
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        accion = "ACTIVAR" if datos.estado else "INACTIVAR"
        estado_texto = "activó" if datos.estado else "desactivó"

        registrar_auditoria_seguridad(
            db=db,
            id_usuario=datos.id_admin,
            accion=accion,
            descripcion=f"{estado_texto.capitalize()} el usuario {fila['usuario']}.",
            tabla_afectada="usuarios",
            id_registro_afectado=id_usuario
        )

        db.commit()

        return {
            "mensaje": "Estado de usuario actualizado correctamente",
            "usuario": dict(fila)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo cambiar el estado del usuario. Detalle: {str(error)}"
        )


@router.put("/usuarios/{id_usuario}/contrasena")
def cambiar_contrasena_usuario(
    id_usuario: int,
    datos: CambiarContrasena,
    db: Session = Depends(get_db)
):
    try:
        if datos.nueva_contrasena.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="La nueva contraseña no puede estar vacía."
            )

        resultado = db.execute(
            text("""
                UPDATE usuarios
                SET contrasena_hash = :contrasena
                WHERE id_usuario = :id_usuario
                RETURNING id_usuario, usuario;
            """),
            {
                "id_usuario": id_usuario,
                "contrasena": datos.nueva_contrasena
            }
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        registrar_auditoria_seguridad(
            db=db,
            id_usuario=datos.id_admin,
            accion="EDITAR",
            descripcion=f"Cambió la contraseña del usuario {fila['usuario']}.",
            tabla_afectada="usuarios",
            id_registro_afectado=id_usuario
        )

        db.commit()

        return {
            "mensaje": "Contraseña actualizada correctamente",
            "usuario": dict(fila)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo cambiar la contraseña. Detalle: {str(error)}"
        )


@router.delete("/usuarios/{id_usuario}")
def desactivar_usuario(
    id_usuario: int,
    id_admin: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        resultado = db.execute(
            text("""
                UPDATE usuarios
                SET estado = FALSE
                WHERE id_usuario = :id_usuario
                RETURNING id_usuario, usuario;
            """),
            {"id_usuario": id_usuario}
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        registrar_auditoria_seguridad(
            db=db,
            id_usuario=id_admin,
            accion="INACTIVAR",
            descripcion=f"Desactivó el usuario {fila['usuario']}.",
            tabla_afectada="usuarios",
            id_registro_afectado=id_usuario
        )

        db.commit()

        return {
            "mensaje": "Usuario desactivado correctamente",
            "usuario": dict(fila)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo desactivar el usuario. Detalle: {str(error)}"
        )


# ----------------------------------------------------
# LOGIN
# ----------------------------------------------------

@router.post("/login")
def login(
    datos: LoginCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        resultado = db.execute(
            text("""
                SELECT
                    u.id_usuario,
                    u.usuario,
                    u.nombres,
                    u.apellidos,
                    u.estado,
                    p.id_perfil,
                    p.nombre_perfil
                FROM usuarios u
                INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
                WHERE u.usuario = :usuario
                  AND u.contrasena_hash = :contrasena
                  AND u.estado = TRUE;
            """),
            {
                "usuario": datos.usuario,
                "contrasena": datos.contrasena
            }
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(
                status_code=401,
                detail="Usuario o contraseña incorrectos."
            )

        usuario_login = dict(fila)

        ip_cliente = obtener_ip_cliente(request)

        cerrar_sesiones_activas_usuario_seguridad(
            db=db,
            id_usuario=usuario_login["id_usuario"]
        )

        id_acceso = registrar_acceso_login_seguridad(
            db=db,
            id_usuario=usuario_login["id_usuario"],
            ip_cliente=ip_cliente
        )

        registrar_auditoria_login(
            db=db,
            id_usuario=usuario_login["id_usuario"],
            usuario=usuario_login["usuario"]
        )

        db.commit()

        usuario_login["id_acceso"] = id_acceso
        usuario_login["ip_equipo"] = ip_cliente

        return {
            "mensaje": "Inicio de sesión correcto",
            "usuario": usuario_login,
            "id_acceso": id_acceso
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo iniciar sesión. Detalle: {str(error)}"
        )


# ----------------------------------------------------
# LOGOUT / CERRAR SESIÓN
# ----------------------------------------------------

@router.post("/logout")
def logout(datos: LogoutCreate, db: Session = Depends(get_db)):
    try:
        usuario = obtener_usuario_por_id(
            db=db,
            id_usuario=datos.id_usuario
        )

        if usuario is None:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado o inactivo."
            )

        ahora = datetime.now()
        fecha_salida = ahora.date()
        hora_salida = ahora.time().replace(microsecond=0)

        if datos.id_acceso is not None:
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
                    WHERE id_acceso = :id_acceso
                      AND id_usuario = :id_usuario
                    RETURNING id_acceso;
                """),
                {
                    "id_acceso": datos.id_acceso,
                    "id_usuario": datos.id_usuario,
                    "fecha_salida": fecha_salida,
                    "hora_salida": hora_salida
                }
            )
        else:
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
                    WHERE id_acceso = (
                        SELECT id_acceso
                        FROM auditoria_accesos
                        WHERE id_usuario = :id_usuario
                          AND LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
                          AND fecha_salida IS NULL
                        ORDER BY fecha_ingreso DESC, hora_ingreso DESC
                        LIMIT 1
                    )
                    RETURNING id_acceso;
                """),
                {
                    "id_usuario": datos.id_usuario,
                    "fecha_salida": fecha_salida,
                    "hora_salida": hora_salida
                }
            )

        acceso_cerrado = resultado.mappings().first()

        registrar_auditoria_logout(
            db=db,
            id_usuario=datos.id_usuario,
            usuario=usuario["usuario"]
        )

        db.commit()

        return {
            "mensaje": "Sesión cerrada correctamente",
            "id_acceso": acceso_cerrado["id_acceso"] if acceso_cerrado else None
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo cerrar sesión. Detalle: {str(error)}"
        )
# ----------------------------------------------------
# PERMISOS POR USUARIO
# ----------------------------------------------------

@router.get("/permisos-usuario/{id_usuario}")
def listar_permisos_usuario(id_usuario: int, db: Session = Depends(get_db)):
    usuario_existe = db.execute(
        text("""
            SELECT id_usuario
            FROM usuarios
            WHERE id_usuario = :id_usuario;
        """),
        {"id_usuario": id_usuario}
    ).first()

    if usuario_existe is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    resultado = db.execute(
        text("""
            SELECT
                pu.id_permiso,
                u.id_usuario,
                u.usuario,
                p.nombre_perfil,
                m.id_modulo,
                m.nombre_modulo,
                m.ruta_html,
                pu.puede_ver,
                pu.puede_crear,
                pu.puede_editar,
                pu.puede_eliminar,
                pu.puede_consultar,
                pu.puede_generar_reporte,
                pu.estado
            FROM permisos_usuario pu
            INNER JOIN usuarios u ON pu.id_usuario = u.id_usuario
            INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
            INNER JOIN modulos_sistema m ON pu.id_modulo = m.id_modulo
            WHERE pu.id_usuario = :id_usuario
            ORDER BY m.id_modulo ASC;
        """),
        {"id_usuario": id_usuario}
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.put("/permisos-usuario/{id_usuario}")
def actualizar_permisos_usuario(
    id_usuario: int,
    datos: PermisosUsuarioUpdate,
    db: Session = Depends(get_db)
):
    try:
        if id_usuario != datos.id_usuario:
            raise HTTPException(
                status_code=400,
                detail="El id del usuario no coincide con el cuerpo de la solicitud."
            )

        usuario_objetivo = db.execute(
            text("""
                SELECT id_usuario, usuario
                FROM usuarios
                WHERE id_usuario = :id_usuario;
            """),
            {"id_usuario": id_usuario}
        ).mappings().first()

        if usuario_objetivo is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        for permiso in datos.permisos:
            existe_modulo = db.execute(
                text("""
                    SELECT id_modulo
                    FROM modulos_sistema
                    WHERE id_modulo = :id_modulo
                      AND estado = TRUE;
                """),
                {"id_modulo": permiso.id_modulo}
            ).first()

            if existe_modulo is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"El módulo con ID {permiso.id_modulo} no existe o está inactivo."
                )

            db.execute(
                text("""
                    INSERT INTO permisos_usuario (
                        id_usuario,
                        id_modulo,
                        puede_ver,
                        puede_crear,
                        puede_editar,
                        puede_eliminar,
                        puede_consultar,
                        puede_generar_reporte,
                        estado
                    )
                    VALUES (
                        :id_usuario,
                        :id_modulo,
                        :puede_ver,
                        :puede_crear,
                        :puede_editar,
                        :puede_eliminar,
                        :puede_consultar,
                        :puede_generar_reporte,
                        TRUE
                    )
                    ON CONFLICT (id_usuario, id_modulo) DO UPDATE
                    SET
                        puede_ver = EXCLUDED.puede_ver,
                        puede_crear = EXCLUDED.puede_crear,
                        puede_editar = EXCLUDED.puede_editar,
                        puede_eliminar = EXCLUDED.puede_eliminar,
                        puede_consultar = EXCLUDED.puede_consultar,
                        puede_generar_reporte = EXCLUDED.puede_generar_reporte,
                        estado = TRUE;
                """),
                {
                    "id_usuario": id_usuario,
                    "id_modulo": permiso.id_modulo,
                    "puede_ver": permiso.puede_ver,
                    "puede_crear": permiso.puede_crear,
                    "puede_editar": permiso.puede_editar,
                    "puede_eliminar": permiso.puede_eliminar,
                    "puede_consultar": permiso.puede_consultar,
                    "puede_generar_reporte": permiso.puede_generar_reporte
                }
            )

        registrar_auditoria_seguridad(
            db=db,
            id_usuario=datos.id_admin,
            accion="EDITAR",
            descripcion=f"Actualizó los permisos del usuario {usuario_objetivo['usuario']}.",
            tabla_afectada="permisos_usuario",
            id_registro_afectado=id_usuario
        )

        db.commit()

        return {
            "mensaje": "Permisos actualizados correctamente."
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudieron actualizar los permisos. Detalle: {str(error)}"
        )


# ----------------------------------------------------
# VALIDAR ACCESO A MÓDULO
# ----------------------------------------------------

@router.get("/validar-modulo")
def validar_modulo(
    id_usuario: int,
    ruta_html: str,
    db: Session = Depends(get_db)
):
    resultado = db.execute(
        text("""
            SELECT
                u.id_usuario,
                u.usuario,
                p.nombre_perfil,
                m.id_modulo,
                m.nombre_modulo,
                m.ruta_html,
                pu.puede_ver,
                pu.puede_crear,
                pu.puede_editar,
                pu.puede_eliminar,
                pu.puede_consultar,
                pu.puede_generar_reporte
            FROM usuarios u
            INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
            INNER JOIN permisos_usuario pu ON u.id_usuario = pu.id_usuario
            INNER JOIN modulos_sistema m ON pu.id_modulo = m.id_modulo
            WHERE u.id_usuario = :id_usuario
              AND u.estado = TRUE
              AND m.ruta_html = :ruta_html
              AND m.estado = TRUE
              AND pu.estado = TRUE;
        """),
        {
            "id_usuario": id_usuario,
            "ruta_html": ruta_html
        }
    )

    permiso = resultado.mappings().first()

    if permiso is None:
        registrar_auditoria_seguridad(
            db=db,
            id_usuario=id_usuario,
            accion="ACCESO_DENEGADO",
            descripcion=f"Intentó acceder sin permiso al módulo {ruta_html}.",
            tabla_afectada="modulos_sistema",
            id_registro_afectado=None
        )
        db.commit()

        return {
            "permitido": False,
            "permiso": None,
            "mensaje": "El usuario no tiene permisos para este módulo."
        }

    permitido = bool(permiso["puede_ver"])

    if not permitido:
        registrar_auditoria_seguridad(
            db=db,
            id_usuario=id_usuario,
            accion="ACCESO_DENEGADO",
            descripcion=f"Intentó acceder sin permiso al módulo {ruta_html}.",
            tabla_afectada="modulos_sistema",
            id_registro_afectado=permiso["id_modulo"]
        )
        db.commit()

    return {
        "permitido": permitido,
        "permiso": dict(permiso),
        "mensaje": "Acceso permitido." if permitido else "Acceso denegado."
    }


# ----------------------------------------------------
# DEPENDENCIA DE SEGURIDAD PARA RUTAS DEL BACKEND
# ----------------------------------------------------

def verificar_permiso_backend(
    id_usuario: int,
    ruta_html: str,
    accion_requerida: str,
    db: Session
):
    """
    Candado backend para usar dentro de endpoints de compras, ventas,
    inventario, producción, talento humano, activos, etc.

    accion_requerida permitida:
    - puede_ver
    - puede_crear
    - puede_editar
    - puede_eliminar
    - puede_consultar
    - puede_generar_reporte
    """

    acciones_validas = [
        "puede_ver",
        "puede_crear",
        "puede_editar",
        "puede_eliminar",
        "puede_consultar",
        "puede_generar_reporte"
    ]

    if accion_requerida not in acciones_validas:
        raise HTTPException(
            status_code=400,
            detail="Acción de permiso no válida."
        )

    resultado = db.execute(
        text(f"""
            SELECT
                pu.{accion_requerida} AS permiso_accion,
                p.nombre_perfil,
                m.nombre_modulo,
                m.ruta_html
            FROM usuarios u
            INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
            INNER JOIN permisos_usuario pu ON u.id_usuario = pu.id_usuario
            INNER JOIN modulos_sistema m ON pu.id_modulo = m.id_modulo
            WHERE u.id_usuario = :id_usuario
              AND u.estado = TRUE
              AND m.ruta_html = :ruta_html
              AND m.estado = TRUE
              AND pu.estado = TRUE;
        """),
        {
            "id_usuario": id_usuario,
            "ruta_html": ruta_html
        }
    ).mappings().first()

    if resultado is None or not bool(resultado["permiso_accion"]):
        registrar_auditoria_seguridad(
            db=db,
            id_usuario=id_usuario,
            accion="ACCESO_DENEGADO",
            descripcion=f"Intentó ejecutar {accion_requerida} en {ruta_html} sin permisos.",
            tabla_afectada="permisos_usuario",
            id_registro_afectado=None
        )
        db.commit()

        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. No tienes permisos para esta acción."
        )

    return True