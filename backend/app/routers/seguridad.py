from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import hashlib
import hmac

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
# FUNCIONES DE ESTRUCTURA
# ----------------------------------------------------

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


def asegurar_estructura_seguridad(db: Session):
    """
    Prepara columnas necesarias para auditoría de seguridad.
    No elimina datos ni cambia lógica existente.
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

        db.commit()

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo preparar la estructura de seguridad/auditoría. Detalle: {str(error)}"
        )


# ----------------------------------------------------
# FUNCIONES INTERNAS PARA AUDITORÍA
# ----------------------------------------------------

def limpiar_texto(valor: Optional[str]) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


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


def normalizar_accion_auditoria(accion: str) -> str:
    accion_limpia = str(accion or "").strip().upper().replace(" ", "_")

    equivalencias = {
        "ACCESO_MODULO": "INGRESO_MODULO",
        "ENTRAR_MODULO": "INGRESO_MODULO",
        "INGRESAR_MODULO": "INGRESO_MODULO",
        "REGISTRAR": "CREAR",
        "REGISTRADO": "CREAR",
        "CREADO": "CREAR",
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


def verificar_contrasena(contrasena_ingresada: str, contrasena_guardada: str) -> bool:
    """
    Mantiene compatibilidad con tu sistema actual, donde contrasena_hash
    puede estar guardada como texto directo. También soporta hashes simples.
    """
    contrasena_ingresada = limpiar_texto(contrasena_ingresada)
    contrasena_guardada = limpiar_texto(contrasena_guardada)

    if contrasena_ingresada == "" or contrasena_guardada == "":
        return False

    if hmac.compare_digest(contrasena_ingresada, contrasena_guardada):
        return True

    try:
        sha256 = hashlib.sha256(contrasena_ingresada.encode("utf-8")).hexdigest()
        if hmac.compare_digest(sha256, contrasena_guardada):
            return True
    except Exception:
        pass

    try:
        sha512 = hashlib.sha512(contrasena_ingresada.encode("utf-8")).hexdigest()
        if hmac.compare_digest(sha512, contrasena_guardada):
            return True
    except Exception:
        pass

    try:
        md5 = hashlib.md5(contrasena_ingresada.encode("utf-8")).hexdigest()
        if hmac.compare_digest(md5, contrasena_guardada):
            return True
    except Exception:
        pass

    return False


def accion_reciente_existe(
    db: Session,
    id_usuario: int,
    modulo: str,
    accion: str,
    segundos: int = 5
) -> Optional[int]:
    """
    Evita duplicados rápidos de acciones como LOGIN, LOGOUT,
    INGRESO_MODULO o ACCESO_DENEGADO.
    """
    resultado = db.execute(
        text("""
            SELECT id_accion
            FROM auditoria_acciones
            WHERE id_usuario = :id_usuario
              AND modulo = :modulo
              AND accion = :accion
              AND (fecha_accion::timestamp + hora_accion) >= (NOW() - (:segundos * INTERVAL '1 second'))
            ORDER BY id_accion DESC
            LIMIT 1;
        """),
        {
            "id_usuario": id_usuario,
            "modulo": modulo,
            "accion": accion,
            "segundos": segundos
        }
    ).mappings().first()

    if resultado is None:
        return None

    return resultado["id_accion"]


def registrar_auditoria_general(
    db: Session,
    id_usuario: Optional[int],
    modulo: str,
    accion: str,
    descripcion: str,
    tabla_afectada: Optional[str] = None,
    id_registro_afectado: Optional[int] = None,
    ip_equipo: Optional[str] = None,
    navegador: Optional[str] = None,
    evitar_duplicado: bool = False
):
    """
    Función general reutilizable para registrar auditoría desde cualquier módulo.
    Puede ser usada por compras.py, ventas.py, inventario.py, talento_humano.py, etc.
    """
    if id_usuario is None:
        return None

    modulo = limpiar_texto(modulo)
    accion_normalizada = normalizar_accion_auditoria(accion)
    descripcion = limpiar_texto(descripcion)

    if modulo == "" or accion_normalizada == "" or descripcion == "":
        return None

    try:
        if evitar_duplicado:
            accion_existente = accion_reciente_existe(
                db=db,
                id_usuario=id_usuario,
                modulo=modulo,
                accion=accion_normalizada,
                segundos=5
            )

            if accion_existente is not None:
                return accion_existente

        resultado = db.execute(
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
                )
                RETURNING id_accion;
            """),
            {
                "id_usuario": id_usuario,
                "modulo": modulo,
                "accion": accion_normalizada,
                "descripcion": descripcion,
                "tabla_afectada": tabla_afectada,
                "id_registro_afectado": id_registro_afectado,
                "ip_equipo": limpiar_valor_ip(ip_equipo),
                "navegador": limpiar_navegador(navegador)
            }
        )

        fila = resultado.mappings().first()

        if fila:
            return fila["id_accion"]

        return None

    except Exception:
        return None


def registrar_auditoria_seguridad(
    db: Session,
    id_usuario: Optional[int],
    accion: str,
    descripcion: str,
    tabla_afectada: Optional[str] = None,
    id_registro_afectado: Optional[int] = None,
    ip_equipo: Optional[str] = None,
    navegador: Optional[str] = None,
    modulo: str = "Seguridad y Usuarios",
    evitar_duplicado: bool = False
):
    return registrar_auditoria_general(
        db=db,
        id_usuario=id_usuario,
        modulo=modulo,
        accion=accion,
        descripcion=descripcion,
        tabla_afectada=tabla_afectada,
        id_registro_afectado=id_registro_afectado,
        ip_equipo=ip_equipo,
        navegador=navegador,
        evitar_duplicado=evitar_duplicado
    )


def registrar_auditoria_login(
    db: Session,
    id_usuario: int,
    usuario: str,
    ip_equipo: Optional[str] = None,
    navegador: Optional[str] = None
):
    return registrar_auditoria_general(
        db=db,
        id_usuario=id_usuario,
        modulo="Login",
        accion="LOGIN",
        descripcion=f"El usuario {usuario} inició sesión en el sistema.",
        tabla_afectada="usuarios",
        id_registro_afectado=id_usuario,
        ip_equipo=ip_equipo,
        navegador=navegador,
        evitar_duplicado=True
    )


def registrar_auditoria_logout(
    db: Session,
    id_usuario: int,
    usuario: str,
    id_acceso: Optional[int] = None,
    ip_equipo: Optional[str] = None,
    navegador: Optional[str] = None
):
    return registrar_auditoria_general(
        db=db,
        id_usuario=id_usuario,
        modulo="Login",
        accion="LOGOUT",
        descripcion=f"El usuario {usuario} cerró sesión en el sistema.",
        tabla_afectada="auditoria_accesos",
        id_registro_afectado=id_acceso,
        ip_equipo=ip_equipo,
        navegador=navegador,
        evitar_duplicado=True
    )


def obtener_acceso_activo_reciente(
    db: Session,
    id_usuario: int,
    ip_cliente: str,
    segundos: int = 5
):
    resultado = db.execute(
        text("""
            SELECT id_acceso
            FROM auditoria_accesos
            WHERE id_usuario = :id_usuario
              AND LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
              AND fecha_salida IS NULL
              AND COALESCE(ip_equipo, '') = :ip_cliente
              AND (fecha_ingreso::timestamp + hora_ingreso) >= (NOW() - (:segundos * INTERVAL '1 second'))
            ORDER BY id_acceso DESC
            LIMIT 1;
        """),
        {
            "id_usuario": id_usuario,
            "ip_cliente": ip_cliente,
            "segundos": segundos
        }
    ).mappings().first()

    return resultado


def cerrar_sesiones_activas_usuario_seguridad(
    db: Session,
    id_usuario: int
):
    """
    Cierra sesiones activas anteriores del usuario antes de crear una nueva.
    Evita sesiones abiertas acumuladas cuando el usuario entra varias veces.
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
    ip_cliente: str,
    navegador: Optional[str] = None
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
                navegador,
                estado_sesion
            )
            VALUES (
                :id_usuario,
                :fecha_ingreso,
                :hora_ingreso,
                :ip_equipo,
                :navegador,
                'Activa'
            )
            RETURNING id_acceso;
        """),
        {
            "id_usuario": id_usuario,
            "fecha_ingreso": fecha_ingreso,
            "hora_ingreso": hora_ingreso,
            "ip_equipo": ip_cliente or "127.0.0.1",
            "navegador": limpiar_navegador(navegador)
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
        asegurar_estructura_seguridad(db)

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
            {"usuario": usuario.usuario.strip()}
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
        asegurar_estructura_seguridad(db)

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
                "usuario": usuario.usuario.strip(),
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
        asegurar_estructura_seguridad(db)

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
        asegurar_estructura_seguridad(db)

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
        asegurar_estructura_seguridad(db)

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
        asegurar_estructura_seguridad(db)

        resultado = db.execute(
            text("""
                SELECT
                    u.id_usuario,
                    u.usuario,
                    u.nombres,
                    u.apellidos,
                    u.contrasena_hash,
                    u.estado,
                    p.id_perfil,
                    p.nombre_perfil
                FROM usuarios u
                INNER JOIN perfiles p ON u.id_perfil = p.id_perfil
                WHERE u.usuario = :usuario
                  AND u.estado = TRUE;
            """),
            {
                "usuario": datos.usuario.strip()
            }
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(
                status_code=401,
                detail="Usuario o contraseña incorrectos."
            )

        if not verificar_contrasena(datos.contrasena, fila["contrasena_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Usuario o contraseña incorrectos."
            )

        usuario_login = dict(fila)
        usuario_login.pop("contrasena_hash", None)

        ip_cliente = obtener_ip_cliente(request)
        navegador_cliente = obtener_navegador_cliente(request)

        acceso_reciente = obtener_acceso_activo_reciente(
            db=db,
            id_usuario=usuario_login["id_usuario"],
            ip_cliente=ip_cliente,
            segundos=5
        )

        if acceso_reciente is not None:
            id_acceso = acceso_reciente["id_acceso"]

            usuario_login["id_acceso"] = id_acceso
            usuario_login["ip_equipo"] = ip_cliente
            usuario_login["navegador"] = navegador_cliente

            db.commit()

            return {
                "mensaje": "Inicio de sesión correcto",
                "usuario": usuario_login,
                "id_acceso": id_acceso
            }

        cerrar_sesiones_activas_usuario_seguridad(
            db=db,
            id_usuario=usuario_login["id_usuario"]
        )

        id_acceso = registrar_acceso_login_seguridad(
            db=db,
            id_usuario=usuario_login["id_usuario"],
            ip_cliente=ip_cliente,
            navegador=navegador_cliente
        )

        registrar_auditoria_login(
            db=db,
            id_usuario=usuario_login["id_usuario"],
            usuario=usuario_login["usuario"],
            ip_equipo=ip_cliente,
            navegador=navegador_cliente
        )

        db.commit()

        usuario_login["id_acceso"] = id_acceso
        usuario_login["ip_equipo"] = ip_cliente
        usuario_login["navegador"] = navegador_cliente

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
def logout(
    datos: LogoutCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        asegurar_estructura_seguridad(db)

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
                      AND LOWER(COALESCE(estado_sesion, '')) IN ('activa', 'abierta', 'activo')
                      AND fecha_salida IS NULL
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

        ip_cliente = obtener_ip_cliente(request)
        navegador_cliente = obtener_navegador_cliente(request)

        if acceso_cerrado is not None:
            registrar_auditoria_logout(
                db=db,
                id_usuario=datos.id_usuario,
                usuario=usuario["usuario"],
                id_acceso=acceso_cerrado["id_acceso"],
                ip_equipo=ip_cliente,
                navegador=navegador_cliente
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
        asegurar_estructura_seguridad(db)

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
    request: Request,
    db: Session = Depends(get_db)
):
    asegurar_estructura_seguridad(db)

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

    ip_cliente = obtener_ip_cliente(request)
    navegador_cliente = obtener_navegador_cliente(request)

    if permiso is None:
        registrar_auditoria_seguridad(
            db=db,
            id_usuario=id_usuario,
            accion="ACCESO_DENEGADO",
            descripcion=f"Intentó acceder sin permiso al módulo {ruta_html}.",
            tabla_afectada="modulos_sistema",
            id_registro_afectado=None,
            ip_equipo=ip_cliente,
            navegador=navegador_cliente,
            evitar_duplicado=True
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
            id_registro_afectado=permiso["id_modulo"],
            ip_equipo=ip_cliente,
            navegador=navegador_cliente,
            evitar_duplicado=True
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
            id_registro_afectado=None,
            evitar_duplicado=True
        )
        db.commit()

        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. No tienes permisos para esta acción."
        )

    return True