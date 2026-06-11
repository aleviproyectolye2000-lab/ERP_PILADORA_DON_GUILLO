from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field
from datetime import date, time, datetime
from typing import Optional
import re

from app.database import get_db


router = APIRouter(
    prefix="/api/talento-humano",
    tags=["Talento Humano"]
)


# ============================================================
# CONFIGURACIÓN GENERAL DEL MÓDULO
# ============================================================

FECHA_MINIMA_EMPRESA = date(2020, 1, 1)
VALOR_HORA_EXTRA_DEFECTO = 10.00
PORCENTAJE_IESS_EMPLEADO = 9.45

CARGOS_OFICIALES = {
    "Operador de báscula": {
        "area": "Báscula y compras",
        "sueldo": 500.00
    },
    "Operador de piladora": {
        "area": "Producción",
        "sueldo": 600.00
    },
    "Supervisor de Producción": {
        "area": "Producción",
        "sueldo": 700.00
    },
    "Bodeguero": {
        "area": "Bodega",
        "sueldo": 500.00
    },
    "Vendedor": {
        "area": "Ventas",
        "sueldo": 470.00
    },
    "Chofer": {
        "area": "Campo",
        "sueldo": 550.00
    },
    "Administrador": {
        "area": "Administración",
        "sueldo": 800.00
    },
    "Personal de campo": {
        "area": "Campo",
        "sueldo": 470.00
    },
    "Guardia": {
        "area": "Seguridad",
        "sueldo": 470.00
    }
}

ALIAS_CARGOS = {
    "Operador": "Operador de piladora",
    "Operador de Piladora": "Operador de piladora",
    "Operador Piladora": "Operador de piladora",
    "Operador de bascula": "Operador de báscula",
    "Operador de Báscula": "Operador de báscula",
    "Supervisor": "Supervisor de Producción",
    "Supervisor Producción": "Supervisor de Producción",
    "Bodega": "Bodeguero",
    "Ventas": "Vendedor",
    "Administrativo": "Administrador",
    "Campo": "Personal de campo",
    "Seguridad": "Guardia"
}


# ============================================================
# MODELOS
# ============================================================

class EmpleadoCreate(BaseModel):
    identificacion: str
    nombres: str
    apellidos: str
    telefono: str
    direccion: str
    cargo: str
    area: str
    sueldo: float = Field(gt=0)
    fecha_ingreso: date
    estado_empleado: str = "Activo"


class EmpleadoUpdate(BaseModel):
    identificacion: str
    nombres: str
    apellidos: str
    telefono: str
    direccion: str
    cargo: str
    area: str
    sueldo: float = Field(gt=0)
    fecha_ingreso: date
    estado_empleado: str


class CambioSueldoCreate(BaseModel):
    nuevo_sueldo: float = Field(gt=0)
    motivo: str
    clave_autorizacion: str
    usuario_autorizacion: str
    sueldo_anterior: Optional[float] = None


class AsistenciaCreate(BaseModel):
    id_empleado: int
    fecha: date
    hora_entrada: Optional[time] = None
    hora_salida: Optional[time] = None
    estado_asistencia: str = "Presente"
    minutos_atraso: int = Field(default=0, ge=0)
    sancion: float = Field(default=0, ge=0)
    sancion_porcentaje: float = Field(default=0, ge=0)
    valor_sancion: float = Field(default=0, ge=0)
    horas_trabajadas: float = Field(default=0, ge=0)
    horas_extras: float = Field(default=0, ge=0)
    observacion: Optional[str] = None


class MarcarEntradaCreate(BaseModel):
    id_empleado: int
    fecha: Optional[date] = None
    hora_entrada: Optional[time] = None
    hora_programada_entrada: time = time(8, 0)
    sancion: float = Field(default=0, ge=0)
    sancion_porcentaje: Optional[float] = Field(default=None, ge=0)
    porcentaje_sancion: Optional[float] = Field(default=None, ge=0)
    valor_sancion: Optional[float] = Field(default=None, ge=0)
    observacion: Optional[str] = None


class MarcarSalidaUpdate(BaseModel):
    hora_salida: Optional[time] = None
    horas_jornada_normal: float = Field(default=8, gt=0)
    observacion: Optional[str] = None


class RolPagoCreate(BaseModel):
    id_empleado: int
    periodo: str

    total_horas_extras: float = Field(default=0, ge=0)
    valor_hora_extra: float = Field(default=VALOR_HORA_EXTRA_DEFECTO, gt=0)
    bonificacion_horas_extras: float = Field(default=0, ge=0)

    horas_extras: float = Field(default=0, ge=0)
    bonificaciones: float = Field(default=0, ge=0)
    sanciones: float = Field(default=0, ge=0)

    aporte_iess: float = Field(default=0, ge=0)
    descuento_iess: float = Field(default=0, ge=0)
    descuentos: float = Field(default=0, ge=0)
    otros_descuentos: float = Field(default=0, ge=0)

    total_ingresos: float = Field(default=0, ge=0)
    total_descuentos: float = Field(default=0, ge=0)
    neto_pagar: float = Field(default=0)

    clave_autorizacion_hora_extra: Optional[str] = None
    usuario_autorizacion_hora_extra: Optional[str] = None
    valor_hora_extra_modificado: Optional[bool] = False

    observacion: Optional[str] = None


# ============================================================
# FUNCIONES DE SOPORTE DE BASE DE DATOS
# ============================================================

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


def obtener_columnas_tabla(db: Session, nombre_tabla: str):
    resultado = db.execute(
        text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :nombre_tabla;
        """),
        {"nombre_tabla": nombre_tabla}
    ).mappings().all()

    return [fila["column_name"] for fila in resultado]


def primera_columna_existente(columnas, opciones):
    for columna in opciones:
        if columna in columnas:
            return columna
    return None


def asegurar_columnas_talento_humano(db: Session):
    try:
        if tabla_existe(db, "asistencia_empleados"):
            db.execute(text("""
                ALTER TABLE asistencia_empleados
                ADD COLUMN IF NOT EXISTS sancion_porcentaje NUMERIC(5,2) DEFAULT 0;
            """))

            db.execute(text("""
                ALTER TABLE asistencia_empleados
                ADD COLUMN IF NOT EXISTS valor_sancion NUMERIC(12,2) DEFAULT 0;
            """))

            db.execute(text("""
                ALTER TABLE asistencia_empleados
                ADD COLUMN IF NOT EXISTS hora_programada_entrada TIME;
            """))

            db.execute(text("""
                ALTER TABLE asistencia_empleados
                ADD COLUMN IF NOT EXISTS fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();
            """))

            db.execute(text("""
                UPDATE asistencia_empleados
                SET valor_sancion = COALESCE(valor_sancion, sancion, 0)
                WHERE valor_sancion IS NULL OR valor_sancion = 0;
            """))

            db.execute(text("""
                UPDATE asistencia_empleados
                SET sancion_porcentaje = COALESCE(sancion_porcentaje, 0)
                WHERE sancion_porcentaje IS NULL;
            """))

        if tabla_existe(db, "roles_pago"):
            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS total_horas_extras NUMERIC(12,2) DEFAULT 0;
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS valor_hora_extra NUMERIC(12,2) DEFAULT 10;
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS bonificacion_horas_extras NUMERIC(12,2) DEFAULT 0;
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS aporte_iess NUMERIC(12,2) DEFAULT 0;
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS porcentaje_iess NUMERIC(5,2) DEFAULT 9.45;
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS otros_descuentos NUMERIC(12,2) DEFAULT 0;
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS total_ingresos NUMERIC(12,2) DEFAULT 0;
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS total_descuentos NUMERIC(12,2) DEFAULT 0;
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS neto_pagar NUMERIC(12,2) DEFAULT 0;
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS usuario_autorizacion_hora_extra VARCHAR(100);
            """))

            db.execute(text("""
                ALTER TABLE roles_pago
                ADD COLUMN IF NOT EXISTS hora_extra_autorizada BOOLEAN DEFAULT FALSE;
            """))

        db.execute(text("""
            CREATE TABLE IF NOT EXISTS historial_cambios_sueldos (
                id_historial_sueldo SERIAL PRIMARY KEY,
                id_empleado INTEGER NOT NULL,
                sueldo_anterior NUMERIC(12,2) NOT NULL,
                sueldo_nuevo NUMERIC(12,2) NOT NULL,
                motivo VARCHAR(200) NOT NULL,
                usuario_autorizacion VARCHAR(100) NOT NULL,
                fecha_cambio TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                CONSTRAINT fk_historial_sueldo_empleado
                    FOREIGN KEY (id_empleado)
                    REFERENCES empleados(id_empleado)
            );
        """))

        db.commit()

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo preparar la estructura de Talento Humano. Detalle: {str(error)}"
        )


# ============================================================
# VALIDACIONES GENERALES
# ============================================================

def limpiar_texto(texto: Optional[str]) -> str:
    if texto is None:
        return ""
    return re.sub(r"\s+", " ", str(texto).strip())


def redondear(valor: float) -> float:
    return round(float(valor or 0), 2)


def normalizar_cargo(cargo: str) -> str:
    cargo_limpio = limpiar_texto(cargo)
    return ALIAS_CARGOS.get(cargo_limpio, cargo_limpio)


def obtener_configuracion_cargo(cargo: str):
    cargo_normalizado = normalizar_cargo(cargo)
    return CARGOS_OFICIALES.get(cargo_normalizado)


def validar_cedula_ecuador(cedula: str) -> bool:
    if not cedula or not cedula.isdigit() or len(cedula) != 10:
        return False

    provincia = int(cedula[0:2])

    if provincia < 1 or provincia > 24:
        return False

    tercer_digito = int(cedula[2])

    if tercer_digito >= 6:
        return False

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0

    for i in range(9):
        valor = int(cedula[i]) * coeficientes[i]

        if valor >= 10:
            valor -= 9

        suma += valor

    digito_verificador = int(cedula[9])
    digito_calculado = 10 - (suma % 10)

    if digito_calculado == 10:
        digito_calculado = 0

    return digito_calculado == digito_verificador


def validar_solo_letras(texto: str) -> bool:
    if texto is None:
        return False

    texto = texto.strip()

    if texto == "":
        return False

    patron = r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$"
    return re.match(patron, texto) is not None


def validar_periodo(periodo: str):
    if periodo is None or periodo.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="El periodo es obligatorio."
        )

    try:
        fecha_periodo = datetime.strptime(periodo, "%Y-%m")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="El periodo debe tener el formato AAAA-MM. Ejemplo: 2026-06."
        )

    hoy = date.today()
    periodo_actual = date(hoy.year, hoy.month, 1)
    periodo_solicitado = date(fecha_periodo.year, fecha_periodo.month, 1)

    if periodo_solicitado > periodo_actual:
        raise HTTPException(
            status_code=400,
            detail="No se permite generar roles de pago de periodos futuros."
        )


def validar_datos_empleado(empleado, sueldo_final: Optional[float] = None):
    campos_obligatorios = [
        empleado.identificacion,
        empleado.nombres,
        empleado.apellidos,
        empleado.telefono,
        empleado.direccion,
        empleado.cargo,
        empleado.estado_empleado
    ]

    for campo in campos_obligatorios:
        if campo is None or str(campo).strip() == "":
            raise HTTPException(
                status_code=400,
                detail="No se permiten campos obligatorios vacíos."
            )

    identificacion = limpiar_texto(empleado.identificacion)
    nombres = limpiar_texto(empleado.nombres)
    apellidos = limpiar_texto(empleado.apellidos)
    telefono = limpiar_texto(empleado.telefono)
    direccion = limpiar_texto(empleado.direccion)
    cargo = normalizar_cargo(empleado.cargo)
    estado_empleado = limpiar_texto(empleado.estado_empleado)

    configuracion_cargo = obtener_configuracion_cargo(cargo)

    if configuracion_cargo is None:
        raise HTTPException(
            status_code=400,
            detail="El cargo seleccionado no pertenece a la lista oficial de cargos de la empresa."
        )

    if not validar_cedula_ecuador(identificacion):
        raise HTTPException(
            status_code=400,
            detail="La cédula ingresada no es una cédula ecuatoriana válida."
        )

    if not validar_solo_letras(nombres):
        raise HTTPException(
            status_code=400,
            detail="Los nombres solo deben contener letras y espacios."
        )

    if not validar_solo_letras(apellidos):
        raise HTTPException(
            status_code=400,
            detail="Los apellidos solo deben contener letras y espacios."
        )

    if not telefono.isdigit():
        raise HTTPException(
            status_code=400,
            detail="El teléfono no debe contener letras."
        )

    if not re.match(r"^09\d{8}$", telefono):
        raise HTTPException(
            status_code=400,
            detail="El teléfono debe tener 10 dígitos y empezar con 09."
        )

    if len(direccion) < 5:
        raise HTTPException(
            status_code=400,
            detail="La dirección debe tener al menos 5 caracteres."
        )

    if empleado.fecha_ingreso < FECHA_MINIMA_EMPRESA:
        raise HTTPException(
            status_code=400,
            detail=f"No se permite registrar fecha de ingreso anterior a {FECHA_MINIMA_EMPRESA}."
        )

    if empleado.fecha_ingreso > date.today():
        raise HTTPException(
            status_code=400,
            detail="No se permite registrar fecha de ingreso futura."
        )

    if estado_empleado not in ["Activo", "Inactivo", "Suspendido"]:
        raise HTTPException(
            status_code=400,
            detail="Estado de empleado no válido. Use Activo, Inactivo o Suspendido."
        )

    if sueldo_final is None:
        sueldo_definitivo = float(configuracion_cargo["sueldo"])
    else:
        sueldo_definitivo = float(sueldo_final)

    if sueldo_definitivo <= 0:
        raise HTTPException(
            status_code=400,
            detail="El sueldo debe ser mayor a cero."
        )

    if sueldo_definitivo > 10000:
        raise HTTPException(
            status_code=400,
            detail="El sueldo ingresado es demasiado alto para este módulo."
        )

    return {
        "identificacion": identificacion,
        "nombres": nombres,
        "apellidos": apellidos,
        "telefono": telefono,
        "direccion": direccion,
        "cargo": cargo,
        "area": configuracion_cargo["area"],
        "sueldo": redondear(sueldo_definitivo),
        "fecha_ingreso": empleado.fecha_ingreso,
        "estado_empleado": estado_empleado
    }


def validar_empleado_activo(id_empleado: int, db: Session):
    empleado = db.execute(
        text("""
            SELECT id_empleado, nombres, apellidos, cargo, area, sueldo, estado_empleado
            FROM empleados
            WHERE id_empleado = :id_empleado
              AND estado = TRUE;
        """),
        {"id_empleado": id_empleado}
    ).mappings().first()

    if empleado is None:
        raise HTTPException(
            status_code=404,
            detail="El empleado no existe o fue eliminado."
        )

    if empleado["estado_empleado"] != "Activo":
        raise HTTPException(
            status_code=400,
            detail="Solo se puede usar empleados con estado Activo."
        )

    return empleado


def calcular_minutos_atraso(hora_entrada: time, hora_programada: time):
    entrada_minutos = hora_entrada.hour * 60 + hora_entrada.minute
    programada_minutos = hora_programada.hour * 60 + hora_programada.minute

    atraso = entrada_minutos - programada_minutos
    return atraso if atraso > 0 else 0


def calcular_horas_trabajadas(hora_entrada: time, hora_salida: time):
    entrada_minutos = hora_entrada.hour * 60 + hora_entrada.minute
    salida_minutos = hora_salida.hour * 60 + hora_salida.minute

    if salida_minutos <= entrada_minutos:
        raise HTTPException(
            status_code=400,
            detail="La hora de salida debe ser mayor que la hora de entrada."
        )

    minutos_trabajados = salida_minutos - entrada_minutos
    return round(minutos_trabajados / 60, 2)


def obtener_porcentaje_sancion(asistencia: MarcarEntradaCreate) -> float:
    if asistencia.sancion_porcentaje is not None:
        porcentaje = float(asistencia.sancion_porcentaje)
    elif asistencia.porcentaje_sancion is not None:
        porcentaje = float(asistencia.porcentaje_sancion)
    else:
        porcentaje = 0.00

    if porcentaje < 0:
        raise HTTPException(
            status_code=400,
            detail="El porcentaje de sanción no puede ser negativo."
        )

    if porcentaje > 100:
        raise HTTPException(
            status_code=400,
            detail="El porcentaje de sanción no puede ser mayor al 100%."
        )

    return redondear(porcentaje)


def calcular_valor_sancion(sueldo: float, porcentaje_sancion: float) -> float:
    if porcentaje_sancion <= 0:
        return 0.00

    return redondear((float(sueldo) * float(porcentaje_sancion)) / 100)


# ============================================================
# VALIDACIÓN DE AUTORIZACIÓN ADMINISTRATIVA
# ============================================================

def validar_autorizacion_admin(
    db: Session,
    usuario_autorizacion: str,
    clave_autorizacion: str
):
    usuario_autorizacion = limpiar_texto(usuario_autorizacion)
    clave_autorizacion = limpiar_texto(clave_autorizacion)

    if usuario_autorizacion == "" or clave_autorizacion == "":
        raise HTTPException(
            status_code=401,
            detail="Debe ingresar usuario y clave de autorización."
        )

    if not tabla_existe(db, "usuarios"):
        raise HTTPException(
            status_code=500,
            detail="No existe la tabla usuarios para validar la autorización."
        )

    columnas_usuarios = obtener_columnas_tabla(db, "usuarios")

    columna_usuario = primera_columna_existente(
        columnas_usuarios,
        ["usuario", "nombre_usuario", "username", "correo", "email"]
    )

    columna_clave = primera_columna_existente(
        columnas_usuarios,
        ["clave", "contrasena", "contraseña", "password", "clave_acceso"]
    )

    columna_perfil_directa = primera_columna_existente(
        columnas_usuarios,
        ["perfil", "rol", "tipo_usuario", "tipo_perfil"]
    )

    columna_id_perfil = primera_columna_existente(
        columnas_usuarios,
        ["id_perfil", "perfil_id"]
    )

    if columna_usuario is None or columna_clave is None:
        raise HTTPException(
            status_code=500,
            detail="No se pudo identificar las columnas de usuario y clave en la tabla usuarios."
        )

    perfil_usuario = None

    if columna_perfil_directa is not None:
        consulta = text(f"""
            SELECT {columna_usuario} AS usuario,
                   {columna_clave} AS clave,
                   {columna_perfil_directa} AS perfil
            FROM usuarios
            WHERE {columna_usuario} = :usuario
            LIMIT 1;
        """)

        fila = db.execute(
            consulta,
            {"usuario": usuario_autorizacion}
        ).mappings().first()

        if fila is None:
            raise HTTPException(
                status_code=401,
                detail="Usuario de autorización no encontrado."
            )

        clave_bd = str(fila["clave"])
        perfil_usuario = str(fila["perfil"] or "")

    elif columna_id_perfil is not None and tabla_existe(db, "perfiles"):
        columnas_perfiles = obtener_columnas_tabla(db, "perfiles")

        columna_nombre_perfil = primera_columna_existente(
            columnas_perfiles,
            ["nombre_perfil", "perfil", "nombre", "descripcion"]
        )

        columna_id_perfil_tabla = primera_columna_existente(
            columnas_perfiles,
            ["id_perfil", "perfil_id", "id"]
        )

        if columna_nombre_perfil is not None and columna_id_perfil_tabla is not None:
            consulta = text(f"""
                SELECT u.{columna_usuario} AS usuario,
                       u.{columna_clave} AS clave,
                       p.{columna_nombre_perfil} AS perfil
                FROM usuarios u
                LEFT JOIN perfiles p ON u.{columna_id_perfil} = p.{columna_id_perfil_tabla}
                WHERE u.{columna_usuario} = :usuario
                LIMIT 1;
            """)

            fila = db.execute(
                consulta,
                {"usuario": usuario_autorizacion}
            ).mappings().first()

            if fila is None:
                raise HTTPException(
                    status_code=401,
                    detail="Usuario de autorización no encontrado."
                )

            clave_bd = str(fila["clave"])
            perfil_usuario = str(fila["perfil"] or "")
        else:
            fila = db.execute(
                text(f"""
                    SELECT {columna_usuario} AS usuario,
                           {columna_clave} AS clave
                    FROM usuarios
                    WHERE {columna_usuario} = :usuario
                    LIMIT 1;
                """),
                {"usuario": usuario_autorizacion}
            ).mappings().first()

            if fila is None:
                raise HTTPException(
                    status_code=401,
                    detail="Usuario de autorización no encontrado."
                )

            clave_bd = str(fila["clave"])
            perfil_usuario = ""
    else:
        fila = db.execute(
            text(f"""
                SELECT {columna_usuario} AS usuario,
                       {columna_clave} AS clave
                FROM usuarios
                WHERE {columna_usuario} = :usuario
                LIMIT 1;
            """),
            {"usuario": usuario_autorizacion}
        ).mappings().first()

        if fila is None:
            raise HTTPException(
                status_code=401,
                detail="Usuario de autorización no encontrado."
            )

        clave_bd = str(fila["clave"])
        perfil_usuario = ""

    if clave_bd != clave_autorizacion:
        raise HTTPException(
            status_code=401,
            detail="Clave de autorización incorrecta."
        )

    perfil_normalizado = perfil_usuario.lower().strip()

    perfiles_autorizados = [
        "administrador",
        "admin",
        "gerente",
        "gerencia",
        "gerencial",
        "super administrador",
        "superadmin"
    ]

    if perfil_normalizado != "":
        es_autorizado = any(perfil in perfil_normalizado for perfil in perfiles_autorizados)

        if not es_autorizado:
            raise HTTPException(
                status_code=403,
                detail="Solo un usuario Administrador o Gerente puede autorizar esta acción."
            )

    return True


# ============================================================
# EMPLEADOS
# ============================================================

@router.get("/empleados")
def listar_empleados(db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    resultado = db.execute(
        text("""
            SELECT *
            FROM empleados
            WHERE estado = TRUE
            ORDER BY id_empleado ASC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


@router.get("/empleados/resumen")
def resumen_empleados(db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    resultado = db.execute(
        text("""
            SELECT
                COUNT(*) AS total_empleados,
                COUNT(*) FILTER (WHERE estado_empleado = 'Activo') AS empleados_activos,
                COUNT(*) FILTER (WHERE estado_empleado = 'Inactivo') AS empleados_inactivos,
                COUNT(*) FILTER (WHERE estado_empleado = 'Suspendido') AS empleados_suspendidos,
                COALESCE(SUM(sueldo) FILTER (WHERE estado_empleado = 'Activo'), 0) AS total_mensual_sueldos
            FROM empleados
            WHERE estado = TRUE;
        """)
    )

    fila = resultado.mappings().first()
    return dict(fila)


@router.get("/empleados/{id_empleado}")
def obtener_empleado(id_empleado: int, db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    resultado = db.execute(
        text("""
            SELECT *
            FROM empleados
            WHERE id_empleado = :id_empleado
              AND estado = TRUE;
        """),
        {"id_empleado": id_empleado}
    )

    fila = resultado.mappings().first()

    if fila is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado.")

    return dict(fila)


@router.post("/empleados")
def crear_empleado(empleado: EmpleadoCreate, db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    datos_empleado = validar_datos_empleado(empleado)

    cedula_existente = db.execute(
        text("""
            SELECT id_empleado
            FROM empleados
            WHERE identificacion = :identificacion
              AND estado = TRUE;
        """),
        {"identificacion": datos_empleado["identificacion"]}
    ).mappings().first()

    if cedula_existente is not None:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un empleado activo registrado con esa cédula."
        )

    consulta = text("""
        INSERT INTO empleados (
            identificacion,
            nombres,
            apellidos,
            telefono,
            direccion,
            cargo,
            area,
            sueldo,
            fecha_ingreso,
            estado_empleado
        )
        VALUES (
            :identificacion,
            :nombres,
            :apellidos,
            :telefono,
            :direccion,
            :cargo,
            :area,
            :sueldo,
            :fecha_ingreso,
            :estado_empleado
        )
        RETURNING
            id_empleado,
            identificacion,
            nombres,
            apellidos,
            cargo,
            area,
            sueldo,
            fecha_ingreso,
            estado_empleado;
    """)

    try:
        resultado = db.execute(consulta, datos_empleado)
        nuevo_empleado = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Empleado registrado correctamente.",
            "empleado": dict(nuevo_empleado)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar el empleado. Detalle: {str(error)}"
        )


@router.put("/empleados/{id_empleado}")
def actualizar_empleado(
    id_empleado: int,
    empleado: EmpleadoUpdate,
    db: Session = Depends(get_db)
):
    asegurar_columnas_talento_humano(db)

    empleado_actual = db.execute(
        text("""
            SELECT id_empleado, cargo, sueldo
            FROM empleados
            WHERE id_empleado = :id_empleado
              AND estado = TRUE;
        """),
        {"id_empleado": id_empleado}
    ).mappings().first()

    if empleado_actual is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado.")

    cargo_anterior = normalizar_cargo(empleado_actual["cargo"])
    cargo_nuevo = normalizar_cargo(empleado.cargo)
    configuracion_cargo_nuevo = obtener_configuracion_cargo(cargo_nuevo)

    if configuracion_cargo_nuevo is None:
        raise HTTPException(
            status_code=400,
            detail="El cargo seleccionado no pertenece a la lista oficial de cargos de la empresa."
        )

    if cargo_anterior == cargo_nuevo:
        sueldo_final = float(empleado_actual["sueldo"])
    else:
        sueldo_final = float(configuracion_cargo_nuevo["sueldo"])

    datos_empleado = validar_datos_empleado(empleado, sueldo_final=sueldo_final)

    cedula_duplicada = db.execute(
        text("""
            SELECT id_empleado
            FROM empleados
            WHERE identificacion = :identificacion
              AND id_empleado <> :id_empleado
              AND estado = TRUE;
        """),
        {
            "identificacion": datos_empleado["identificacion"],
            "id_empleado": id_empleado
        }
    ).mappings().first()

    if cedula_duplicada is not None:
        raise HTTPException(
            status_code=400,
            detail="Ya existe otro empleado registrado con esa cédula."
        )

    consulta = text("""
        UPDATE empleados
        SET
            identificacion = :identificacion,
            nombres = :nombres,
            apellidos = :apellidos,
            telefono = :telefono,
            direccion = :direccion,
            cargo = :cargo,
            area = :area,
            sueldo = :sueldo,
            fecha_ingreso = :fecha_ingreso,
            estado_empleado = :estado_empleado
        WHERE id_empleado = :id_empleado
          AND estado = TRUE
        RETURNING
            id_empleado,
            identificacion,
            nombres,
            apellidos,
            cargo,
            area,
            sueldo,
            fecha_ingreso,
            estado_empleado;
    """)

    try:
        resultado = db.execute(
            consulta,
            {
                **datos_empleado,
                "id_empleado": id_empleado
            }
        )

        empleado_actualizado = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Empleado actualizado correctamente.",
            "empleado": dict(empleado_actualizado)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo actualizar el empleado. Detalle: {str(error)}"
        )


@router.patch("/empleados/{id_empleado}/cambiar-sueldo")
def cambiar_sueldo_empleado(
    id_empleado: int,
    cambio: CambioSueldoCreate,
    db: Session = Depends(get_db)
):
    asegurar_columnas_talento_humano(db)

    validar_autorizacion_admin(
        db=db,
        usuario_autorizacion=cambio.usuario_autorizacion,
        clave_autorizacion=cambio.clave_autorizacion
    )

    motivo = limpiar_texto(cambio.motivo)

    if motivo == "" or len(motivo) < 5:
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar un motivo válido para el cambio de sueldo."
        )

    if cambio.nuevo_sueldo <= 0:
        raise HTTPException(
            status_code=400,
            detail="El nuevo sueldo debe ser mayor a cero."
        )

    if cambio.nuevo_sueldo > 10000:
        raise HTTPException(
            status_code=400,
            detail="El nuevo sueldo ingresado es demasiado alto para este módulo."
        )

    empleado_actual = db.execute(
        text("""
            SELECT id_empleado, nombres, apellidos, sueldo
            FROM empleados
            WHERE id_empleado = :id_empleado
              AND estado = TRUE;
        """),
        {"id_empleado": id_empleado}
    ).mappings().first()

    if empleado_actual is None:
        raise HTTPException(
            status_code=404,
            detail="Empleado no encontrado."
        )

    sueldo_anterior = redondear(float(empleado_actual["sueldo"]))
    sueldo_nuevo = redondear(float(cambio.nuevo_sueldo))

    if sueldo_anterior == sueldo_nuevo:
        raise HTTPException(
            status_code=400,
            detail="El nuevo sueldo no puede ser igual al sueldo actual."
        )

    try:
        resultado = db.execute(
            text("""
                UPDATE empleados
                SET sueldo = :sueldo_nuevo
                WHERE id_empleado = :id_empleado
                  AND estado = TRUE
                RETURNING id_empleado, nombres, apellidos, cargo, area, sueldo;
            """),
            {
                "id_empleado": id_empleado,
                "sueldo_nuevo": sueldo_nuevo
            }
        )

        empleado_actualizado = resultado.mappings().first()

        db.execute(
            text("""
                INSERT INTO historial_cambios_sueldos (
                    id_empleado,
                    sueldo_anterior,
                    sueldo_nuevo,
                    motivo,
                    usuario_autorizacion
                )
                VALUES (
                    :id_empleado,
                    :sueldo_anterior,
                    :sueldo_nuevo,
                    :motivo,
                    :usuario_autorizacion
                );
            """),
            {
                "id_empleado": id_empleado,
                "sueldo_anterior": sueldo_anterior,
                "sueldo_nuevo": sueldo_nuevo,
                "motivo": motivo,
                "usuario_autorizacion": limpiar_texto(cambio.usuario_autorizacion)
            }
        )

        db.commit()

        return {
            "mensaje": "Sueldo modificado correctamente con autorización administrativa.",
            "sueldo_anterior": sueldo_anterior,
            "sueldo_nuevo": sueldo_nuevo,
            "empleado": dict(empleado_actualizado)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo modificar el sueldo. Detalle: {str(error)}"
        )


@router.patch("/empleados/{id_empleado}/desactivar")
def desactivar_empleado(id_empleado: int, db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    try:
        resultado = db.execute(
            text("""
                UPDATE empleados
                SET estado_empleado = 'Inactivo'
                WHERE id_empleado = :id_empleado
                  AND estado = TRUE
                RETURNING id_empleado, nombres, apellidos, estado_empleado;
            """),
            {"id_empleado": id_empleado}
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(status_code=404, detail="Empleado no encontrado.")

        db.commit()

        return {
            "mensaje": "Empleado desactivado correctamente.",
            "empleado": dict(fila)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo desactivar el empleado. Detalle: {str(error)}"
        )


@router.patch("/empleados/{id_empleado}/suspender")
def suspender_empleado(id_empleado: int, db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    try:
        resultado = db.execute(
            text("""
                UPDATE empleados
                SET estado_empleado = 'Suspendido'
                WHERE id_empleado = :id_empleado
                  AND estado = TRUE
                RETURNING id_empleado, nombres, apellidos, estado_empleado;
            """),
            {"id_empleado": id_empleado}
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(status_code=404, detail="Empleado no encontrado.")

        db.commit()

        return {
            "mensaje": "Empleado suspendido correctamente.",
            "empleado": dict(fila)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo suspender el empleado. Detalle: {str(error)}"
        )


@router.patch("/empleados/{id_empleado}/activar")
def activar_empleado(id_empleado: int, db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    try:
        resultado = db.execute(
            text("""
                UPDATE empleados
                SET estado_empleado = 'Activo'
                WHERE id_empleado = :id_empleado
                  AND estado = TRUE
                RETURNING id_empleado, nombres, apellidos, estado_empleado;
            """),
            {"id_empleado": id_empleado}
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(status_code=404, detail="Empleado no encontrado.")

        db.commit()

        return {
            "mensaje": "Empleado activado correctamente.",
            "empleado": dict(fila)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo activar el empleado. Detalle: {str(error)}"
        )


@router.delete("/empleados/{id_empleado}")
def eliminar_logico_empleado(id_empleado: int, db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    try:
        resultado = db.execute(
            text("""
                UPDATE empleados
                SET estado = FALSE,
                    estado_empleado = 'Inactivo'
                WHERE id_empleado = :id_empleado
                  AND estado = TRUE
                RETURNING id_empleado, nombres, apellidos;
            """),
            {"id_empleado": id_empleado}
        )

        fila = resultado.mappings().first()

        if fila is None:
            raise HTTPException(status_code=404, detail="Empleado no encontrado.")

        db.commit()

        return {
            "mensaje": "Empleado eliminado lógicamente correctamente.",
            "empleado": dict(fila)
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo eliminar el empleado. Detalle: {str(error)}"
        )


@router.post("/empleados/corregir-cargos-areas")
def corregir_cargos_areas_empleados(db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    empleados = db.execute(
        text("""
            SELECT id_empleado, cargo, area
            FROM empleados
            WHERE estado = TRUE;
        """)
    ).mappings().all()

    corregidos = []

    try:
        for empleado in empleados:
            cargo_normalizado = normalizar_cargo(empleado["cargo"])
            configuracion = obtener_configuracion_cargo(cargo_normalizado)

            if configuracion is None:
                continue

            if empleado["cargo"] != cargo_normalizado or empleado["area"] != configuracion["area"]:
                db.execute(
                    text("""
                        UPDATE empleados
                        SET cargo = :cargo,
                            area = :area
                        WHERE id_empleado = :id_empleado
                          AND estado = TRUE;
                    """),
                    {
                        "id_empleado": empleado["id_empleado"],
                        "cargo": cargo_normalizado,
                        "area": configuracion["area"]
                    }
                )

                corregidos.append({
                    "id_empleado": empleado["id_empleado"],
                    "cargo_anterior": empleado["cargo"],
                    "area_anterior": empleado["area"],
                    "cargo_nuevo": cargo_normalizado,
                    "area_nueva": configuracion["area"]
                })

        db.commit()

        return {
            "mensaje": "Cargos y áreas corregidos correctamente.",
            "total_corregidos": len(corregidos),
            "corregidos": corregidos
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudieron corregir cargos y áreas. Detalle: {str(error)}"
        )


# ============================================================
# ASISTENCIA
# ============================================================

@router.post("/asistencia/marcar-entrada")
def marcar_entrada(asistencia: MarcarEntradaCreate, db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    empleado = validar_empleado_activo(asistencia.id_empleado, db)

    fecha_asistencia = asistencia.fecha or date.today()
    hora_entrada = asistencia.hora_entrada or datetime.now().time().replace(microsecond=0)

    if fecha_asistencia < FECHA_MINIMA_EMPRESA:
        raise HTTPException(
            status_code=400,
            detail=f"No se permite registrar asistencia anterior a {FECHA_MINIMA_EMPRESA}."
        )

    if fecha_asistencia > date.today():
        raise HTTPException(
            status_code=400,
            detail="No se permite registrar asistencia con fecha futura."
        )

    asistencia_existente = db.execute(
        text("""
            SELECT id_asistencia
            FROM asistencia_empleados
            WHERE id_empleado = :id_empleado
              AND fecha = :fecha;
        """),
        {
            "id_empleado": asistencia.id_empleado,
            "fecha": fecha_asistencia
        }
    ).mappings().first()

    if asistencia_existente is not None:
        raise HTTPException(
            status_code=400,
            detail="Este empleado ya tiene una entrada registrada para esta fecha."
        )

    porcentaje_sancion = obtener_porcentaje_sancion(asistencia)

    if porcentaje_sancion > 0 and limpiar_texto(asistencia.observacion) == "":
        raise HTTPException(
            status_code=400,
            detail="Cuando se aplica una sanción debe escribir la observación o motivo."
        )

    valor_sancion = calcular_valor_sancion(
        sueldo=float(empleado["sueldo"]),
        porcentaje_sancion=porcentaje_sancion
    )

    minutos_atraso = calcular_minutos_atraso(
        hora_entrada,
        asistencia.hora_programada_entrada
    )

    estado_asistencia = "Atraso" if minutos_atraso > 0 else "Presente"

    consulta = text("""
        INSERT INTO asistencia_empleados (
            id_empleado,
            fecha,
            hora_entrada,
            hora_programada_entrada,
            estado_asistencia,
            minutos_atraso,
            sancion,
            sancion_porcentaje,
            valor_sancion,
            observacion,
            horas_trabajadas,
            horas_extras
        )
        VALUES (
            :id_empleado,
            :fecha,
            :hora_entrada,
            :hora_programada_entrada,
            :estado_asistencia,
            :minutos_atraso,
            :sancion,
            :sancion_porcentaje,
            :valor_sancion,
            :observacion,
            0,
            0
        )
        RETURNING
            id_asistencia,
            id_empleado,
            fecha,
            hora_entrada,
            hora_programada_entrada,
            estado_asistencia,
            minutos_atraso,
            sancion,
            sancion_porcentaje,
            valor_sancion,
            horas_trabajadas,
            horas_extras,
            observacion;
    """)

    try:
        resultado = db.execute(
            consulta,
            {
                "id_empleado": asistencia.id_empleado,
                "fecha": fecha_asistencia,
                "hora_entrada": hora_entrada,
                "hora_programada_entrada": asistencia.hora_programada_entrada,
                "estado_asistencia": estado_asistencia,
                "minutos_atraso": minutos_atraso,
                "sancion": valor_sancion,
                "sancion_porcentaje": porcentaje_sancion,
                "valor_sancion": valor_sancion,
                "observacion": limpiar_texto(asistencia.observacion) or None
            }
        )

        nueva_asistencia = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Entrada marcada correctamente.",
            "asistencia": dict(nueva_asistencia)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo marcar la entrada. Detalle: {str(error)}"
        )


@router.patch("/asistencia/{id_asistencia}/marcar-salida")
def marcar_salida(
    id_asistencia: int,
    salida: MarcarSalidaUpdate,
    db: Session = Depends(get_db)
):
    asegurar_columnas_talento_humano(db)

    hora_salida = salida.hora_salida or datetime.now().time().replace(microsecond=0)

    if salida.horas_jornada_normal <= 0:
        raise HTTPException(
            status_code=400,
            detail="La jornada normal debe ser mayor a cero."
        )

    if salida.horas_jornada_normal > 24:
        raise HTTPException(
            status_code=400,
            detail="La jornada normal no puede ser mayor a 24 horas."
        )

    asistencia_actual = db.execute(
        text("""
            SELECT
                id_asistencia,
                hora_entrada,
                hora_salida
            FROM asistencia_empleados
            WHERE id_asistencia = :id_asistencia;
        """),
        {"id_asistencia": id_asistencia}
    ).mappings().first()

    if asistencia_actual is None:
        raise HTTPException(
            status_code=404,
            detail="Registro de asistencia no encontrado."
        )

    if asistencia_actual["hora_salida"] is not None:
        raise HTTPException(
            status_code=400,
            detail="Este registro ya tiene hora de salida marcada."
        )

    if asistencia_actual["hora_entrada"] is None:
        raise HTTPException(
            status_code=400,
            detail="No se puede marcar salida sin hora de entrada."
        )

    horas_trabajadas = calcular_horas_trabajadas(
        asistencia_actual["hora_entrada"],
        hora_salida
    )

    horas_extras = horas_trabajadas - salida.horas_jornada_normal

    if horas_extras < 0:
        horas_extras = 0

    horas_extras = redondear(horas_extras)

    consulta = text("""
        UPDATE asistencia_empleados
        SET
            hora_salida = :hora_salida,
            horas_trabajadas = :horas_trabajadas,
            horas_extras = :horas_extras,
            observacion = COALESCE(:observacion, observacion)
        WHERE id_asistencia = :id_asistencia
        RETURNING
            id_asistencia,
            id_empleado,
            fecha,
            hora_entrada,
            hora_salida,
            horas_trabajadas,
            horas_extras,
            estado_asistencia,
            minutos_atraso,
            sancion,
            sancion_porcentaje,
            valor_sancion,
            observacion;
    """)

    try:
        resultado = db.execute(
            consulta,
            {
                "id_asistencia": id_asistencia,
                "hora_salida": hora_salida,
                "horas_trabajadas": horas_trabajadas,
                "horas_extras": horas_extras,
                "observacion": limpiar_texto(salida.observacion) or None
            }
        )

        asistencia_actualizada = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Salida marcada correctamente.",
            "asistencia": dict(asistencia_actualizada)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo marcar la salida. Detalle: {str(error)}"
        )


@router.post("/asistencia")
def registrar_asistencia(asistencia: AsistenciaCreate, db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    if asistencia.estado_asistencia not in ["Presente", "Atraso", "Falta", "Justificado"]:
        raise HTTPException(
            status_code=400,
            detail="Estado de asistencia no válido. Use Presente, Atraso, Falta o Justificado."
        )

    if asistencia.fecha < FECHA_MINIMA_EMPRESA:
        raise HTTPException(
            status_code=400,
            detail=f"No se permite registrar asistencia anterior a {FECHA_MINIMA_EMPRESA}."
        )

    if asistencia.fecha > date.today():
        raise HTTPException(
            status_code=400,
            detail="No se permite registrar asistencia con fecha futura."
        )

    empleado = validar_empleado_activo(asistencia.id_empleado, db)

    porcentaje_sancion = redondear(asistencia.sancion_porcentaje)

    if porcentaje_sancion > 100:
        raise HTTPException(
            status_code=400,
            detail="La sanción no puede ser mayor al 100%."
        )

    valor_sancion = calcular_valor_sancion(
        sueldo=float(empleado["sueldo"]),
        porcentaje_sancion=porcentaje_sancion
    )

    consulta = text("""
        INSERT INTO asistencia_empleados (
            id_empleado,
            fecha,
            hora_entrada,
            hora_salida,
            estado_asistencia,
            minutos_atraso,
            sancion,
            sancion_porcentaje,
            valor_sancion,
            horas_trabajadas,
            horas_extras,
            observacion
        )
        VALUES (
            :id_empleado,
            :fecha,
            :hora_entrada,
            :hora_salida,
            :estado_asistencia,
            :minutos_atraso,
            :sancion,
            :sancion_porcentaje,
            :valor_sancion,
            :horas_trabajadas,
            :horas_extras,
            :observacion
        )
        RETURNING id_asistencia;
    """)

    try:
        resultado = db.execute(
            consulta,
            {
                "id_empleado": asistencia.id_empleado,
                "fecha": asistencia.fecha,
                "hora_entrada": asistencia.hora_entrada,
                "hora_salida": asistencia.hora_salida,
                "estado_asistencia": asistencia.estado_asistencia,
                "minutos_atraso": asistencia.minutos_atraso,
                "sancion": valor_sancion,
                "sancion_porcentaje": porcentaje_sancion,
                "valor_sancion": valor_sancion,
                "horas_trabajadas": asistencia.horas_trabajadas,
                "horas_extras": asistencia.horas_extras,
                "observacion": limpiar_texto(asistencia.observacion) or None
            }
        )

        nueva_asistencia = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Asistencia registrada correctamente.",
            "asistencia": dict(nueva_asistencia)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo registrar la asistencia. Detalle: {str(error)}"
        )


@router.get("/asistencia")
def listar_asistencia(db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    resultado = db.execute(
        text("""
            SELECT
                a.id_asistencia,
                a.id_empleado,
                e.identificacion,
                e.nombres || ' ' || e.apellidos AS empleado,
                e.cargo,
                e.area,
                a.fecha,
                a.hora_entrada,
                a.hora_salida,
                a.estado_asistencia,
                a.minutos_atraso,
                COALESCE(a.sancion_porcentaje, 0) AS sancion_porcentaje,
                COALESCE(a.sancion_porcentaje, 0) AS porcentaje_sancion,
                COALESCE(a.valor_sancion, a.sancion, 0) AS valor_sancion,
                COALESCE(a.valor_sancion, a.sancion, 0) AS sancion,
                a.horas_trabajadas,
                a.horas_extras,
                a.observacion
            FROM asistencia_empleados a
            INNER JOIN empleados e ON a.id_empleado = e.id_empleado
            WHERE e.estado = TRUE
            ORDER BY a.fecha DESC, a.id_asistencia DESC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]


# ============================================================
# CÁLCULO DE ROLES DE PAGO
# ============================================================

def calcular_rol_pago_mensual(
    id_empleado: int,
    periodo: str,
    valor_hora_extra: float,
    bonificaciones: float,
    otros_descuentos: float,
    db: Session
):
    validar_periodo(periodo)

    empleado = validar_empleado_activo(id_empleado, db)

    sueldo_base = redondear(float(empleado["sueldo"]))

    resumen_asistencia = db.execute(
        text("""
            SELECT
                COALESCE(SUM(horas_extras), 0) AS total_horas_extras,
                COALESCE(SUM(COALESCE(valor_sancion, sancion, 0)), 0) AS total_sanciones
            FROM asistencia_empleados
            WHERE id_empleado = :id_empleado
              AND fecha >= TO_DATE(:periodo || '-01', 'YYYY-MM-DD')
              AND fecha <  TO_DATE(:periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month';
        """),
        {
            "id_empleado": id_empleado,
            "periodo": periodo
        }
    ).mappings().first()

    total_horas_extras = redondear(float(resumen_asistencia["total_horas_extras"]))
    total_sanciones = redondear(float(resumen_asistencia["total_sanciones"]))

    valor_hora_extra = redondear(valor_hora_extra)

    if valor_hora_extra <= 0:
        raise HTTPException(
            status_code=400,
            detail="El valor de la hora extra debe ser mayor a cero."
        )

    bonificacion_horas_extras = redondear(total_horas_extras * valor_hora_extra)
    bonificaciones = redondear(bonificaciones)
    otros_descuentos = redondear(otros_descuentos)

    aporte_iess = redondear((sueldo_base * PORCENTAJE_IESS_EMPLEADO) / 100)

    total_ingresos = redondear(
        sueldo_base +
        bonificacion_horas_extras +
        bonificaciones
    )

    total_descuentos = redondear(
        total_sanciones +
        aporte_iess +
        otros_descuentos
    )

    neto_pagar = redondear(total_ingresos - total_descuentos)

    if neto_pagar < 0:
        raise HTTPException(
            status_code=400,
            detail="El neto a pagar no puede ser negativo. Revise sanciones y descuentos."
        )

    return {
        "empleado": empleado,
        "sueldo_base": sueldo_base,
        "total_horas_extras": total_horas_extras,
        "valor_hora_extra": valor_hora_extra,
        "bonificacion_horas_extras": bonificacion_horas_extras,
        "bonificaciones": bonificaciones,
        "sanciones": total_sanciones,
        "aporte_iess": aporte_iess,
        "porcentaje_iess": PORCENTAJE_IESS_EMPLEADO,
        "otros_descuentos": otros_descuentos,
        "descuentos_guardar": redondear(aporte_iess + otros_descuentos),
        "total_ingresos": total_ingresos,
        "total_descuentos": total_descuentos,
        "neto_pagar": neto_pagar
    }


@router.get("/roles-pago/calcular")
def calcular_rol_pago(
    id_empleado: int,
    periodo: str,
    valor_hora_extra: float = VALOR_HORA_EXTRA_DEFECTO,
    bonificaciones: float = 0,
    otros_descuentos: float = 0,
    db: Session = Depends(get_db)
):
    asegurar_columnas_talento_humano(db)

    calculo = calcular_rol_pago_mensual(
        id_empleado=id_empleado,
        periodo=periodo,
        valor_hora_extra=valor_hora_extra,
        bonificaciones=bonificaciones,
        otros_descuentos=otros_descuentos,
        db=db
    )

    empleado = calculo["empleado"]

    return {
        "id_empleado": id_empleado,
        "empleado": f"{empleado['nombres']} {empleado['apellidos']}",
        "cargo": empleado["cargo"],
        "area": empleado["area"],
        "periodo": periodo,
        "sueldo_base": calculo["sueldo_base"],
        "total_horas_extras": calculo["total_horas_extras"],
        "valor_hora_extra": calculo["valor_hora_extra"],
        "bonificacion_horas_extras": calculo["bonificacion_horas_extras"],
        "bonificaciones": calculo["bonificaciones"],
        "sanciones": calculo["sanciones"],
        "aporte_iess": calculo["aporte_iess"],
        "porcentaje_iess": calculo["porcentaje_iess"],
        "otros_descuentos": calculo["otros_descuentos"],
        "total_ingresos": calculo["total_ingresos"],
        "total_descuentos": calculo["total_descuentos"],
        "neto_pagar": calculo["neto_pagar"]
    }


@router.post("/roles-pago")
def crear_rol_pago(rol: RolPagoCreate, db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    validar_periodo(rol.periodo)

    valor_hora_extra = redondear(rol.valor_hora_extra or VALOR_HORA_EXTRA_DEFECTO)

    cambio_valor_hora_extra = valor_hora_extra != redondear(VALOR_HORA_EXTRA_DEFECTO)

    if cambio_valor_hora_extra:
        validar_autorizacion_admin(
            db=db,
            usuario_autorizacion=rol.usuario_autorizacion_hora_extra or "",
            clave_autorizacion=rol.clave_autorizacion_hora_extra or ""
        )

    rol_existente = db.execute(
        text("""
            SELECT id_rol_pago
            FROM roles_pago
            WHERE id_empleado = :id_empleado
              AND periodo = :periodo
              AND estado = TRUE;
        """),
        {
            "id_empleado": rol.id_empleado,
            "periodo": rol.periodo
        }
    ).mappings().first()

    if rol_existente is not None:
        raise HTTPException(
            status_code=400,
            detail="Este empleado ya tiene un rol de pago generado para ese periodo."
        )

    otros_descuentos = rol.otros_descuentos if rol.otros_descuentos > 0 else rol.descuentos

    calculo = calcular_rol_pago_mensual(
        id_empleado=rol.id_empleado,
        periodo=rol.periodo,
        valor_hora_extra=valor_hora_extra,
        bonificaciones=rol.bonificaciones,
        otros_descuentos=otros_descuentos,
        db=db
    )

    empleado = calculo["empleado"]

    consulta = text("""
        INSERT INTO roles_pago (
            id_empleado,
            periodo,
            sueldo_base,
            horas_extras,
            bonificaciones,
            sanciones,
            descuentos,
            observacion,
            total_horas_extras,
            valor_hora_extra,
            bonificacion_horas_extras,
            aporte_iess,
            porcentaje_iess,
            otros_descuentos,
            total_ingresos,
            total_descuentos,
            neto_pagar,
            usuario_autorizacion_hora_extra,
            hora_extra_autorizada
        )
        VALUES (
            :id_empleado,
            :periodo,
            :sueldo_base,
            :horas_extras,
            :bonificaciones,
            :sanciones,
            :descuentos,
            :observacion,
            :total_horas_extras,
            :valor_hora_extra,
            :bonificacion_horas_extras,
            :aporte_iess,
            :porcentaje_iess,
            :otros_descuentos,
            :total_ingresos,
            :total_descuentos,
            :neto_pagar,
            :usuario_autorizacion_hora_extra,
            :hora_extra_autorizada
        )
        RETURNING
            id_rol_pago,
            id_empleado,
            periodo,
            sueldo_base,
            horas_extras,
            bonificaciones,
            sanciones,
            descuentos,
            total_horas_extras,
            valor_hora_extra,
            bonificacion_horas_extras,
            aporte_iess,
            porcentaje_iess,
            otros_descuentos,
            total_ingresos,
            total_descuentos,
            neto_pagar,
            fecha_generacion;
    """)

    parametros = {
        "id_empleado": rol.id_empleado,
        "periodo": rol.periodo,
        "sueldo_base": calculo["sueldo_base"],
        "horas_extras": calculo["bonificacion_horas_extras"],
        "bonificaciones": calculo["bonificaciones"],
        "sanciones": calculo["sanciones"],
        "descuentos": calculo["descuentos_guardar"],
        "observacion": limpiar_texto(rol.observacion) or "Rol generado automáticamente desde Talento Humano.",
        "total_horas_extras": calculo["total_horas_extras"],
        "valor_hora_extra": calculo["valor_hora_extra"],
        "bonificacion_horas_extras": calculo["bonificacion_horas_extras"],
        "aporte_iess": calculo["aporte_iess"],
        "porcentaje_iess": calculo["porcentaje_iess"],
        "otros_descuentos": calculo["otros_descuentos"],
        "total_ingresos": calculo["total_ingresos"],
        "total_descuentos": calculo["total_descuentos"],
        "neto_pagar": calculo["neto_pagar"],
        "usuario_autorizacion_hora_extra": rol.usuario_autorizacion_hora_extra if cambio_valor_hora_extra else None,
        "hora_extra_autorizada": cambio_valor_hora_extra
    }

    try:
        resultado = db.execute(consulta, parametros)
        nuevo_rol = resultado.mappings().first()
        db.commit()

        return {
            "mensaje": "Rol de pago generado automáticamente correctamente.",
            "empleado": {
                "id_empleado": rol.id_empleado,
                "nombres": empleado["nombres"],
                "apellidos": empleado["apellidos"],
                "cargo": empleado["cargo"],
                "area": empleado["area"]
            },
            "calculo": {
                "sueldo_base": calculo["sueldo_base"],
                "total_horas_extras": calculo["total_horas_extras"],
                "valor_hora_extra": calculo["valor_hora_extra"],
                "bonificacion_horas_extras": calculo["bonificacion_horas_extras"],
                "bonificaciones": calculo["bonificaciones"],
                "sanciones": calculo["sanciones"],
                "aporte_iess": calculo["aporte_iess"],
                "porcentaje_iess": calculo["porcentaje_iess"],
                "otros_descuentos": calculo["otros_descuentos"],
                "total_ingresos": calculo["total_ingresos"],
                "total_descuentos": calculo["total_descuentos"],
                "neto_pagar": calculo["neto_pagar"]
            },
            "rol_pago": dict(nuevo_rol)
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo generar el rol de pago. Detalle: {str(error)}"
        )


@router.get("/roles-pago")
def listar_roles_pago(db: Session = Depends(get_db)):
    asegurar_columnas_talento_humano(db)

    resultado = db.execute(
        text("""
            SELECT
                rp.id_rol_pago,
                rp.id_empleado,
                e.identificacion,
                e.nombres || ' ' || e.apellidos AS empleado,
                e.nombres,
                e.apellidos,
                e.cargo,
                e.area,
                rp.periodo,
                rp.sueldo_base,
                COALESCE(rp.total_horas_extras, 0) AS total_horas_extras,
                COALESCE(rp.valor_hora_extra, 10) AS valor_hora_extra,
                COALESCE(rp.bonificacion_horas_extras, rp.horas_extras, 0) AS bonificacion_horas_extras,
                COALESCE(rp.horas_extras, 0) AS horas_extras,
                COALESCE(rp.bonificaciones, 0) AS bonificaciones,
                COALESCE(rp.sanciones, 0) AS sanciones,
                COALESCE(rp.aporte_iess, 0) AS aporte_iess,
                COALESCE(rp.porcentaje_iess, 9.45) AS porcentaje_iess,
                COALESCE(rp.otros_descuentos, 0) AS otros_descuentos,
                COALESCE(rp.descuentos, 0) AS descuentos,
                COALESCE(
                    rp.total_ingresos,
                    COALESCE(rp.sueldo_base, 0) + COALESCE(rp.horas_extras, 0) + COALESCE(rp.bonificaciones, 0)
                ) AS total_ingresos,
                COALESCE(
                    rp.total_descuentos,
                    COALESCE(rp.sanciones, 0) + COALESCE(rp.descuentos, 0)
                ) AS total_descuentos,
                COALESCE(rp.neto_pagar, rp.total_pagar, 0) AS neto_pagar,
                COALESCE(rp.total_pagar, rp.neto_pagar, 0) AS total_pagar,
                rp.observacion,
                rp.fecha_generacion
            FROM roles_pago rp
            INNER JOIN empleados e ON rp.id_empleado = e.id_empleado
            WHERE rp.estado = TRUE
            ORDER BY rp.fecha_generacion DESC, rp.id_rol_pago DESC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]