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


class AsistenciaCreate(BaseModel):
    id_empleado: int
    fecha: date
    hora_entrada: Optional[time] = None
    hora_salida: Optional[time] = None
    estado_asistencia: str = "Presente"
    minutos_atraso: int = Field(default=0, ge=0)
    sancion: float = Field(default=0, ge=0)
    horas_trabajadas: float = Field(default=0, ge=0)
    horas_extras: float = Field(default=0, ge=0)
    observacion: Optional[str] = None


class MarcarEntradaCreate(BaseModel):
    id_empleado: int
    fecha: Optional[date] = None
    hora_entrada: Optional[time] = None
    hora_programada_entrada: time = time(8, 0)
    sancion: float = Field(default=0, ge=0)
    observacion: Optional[str] = None


class MarcarSalidaUpdate(BaseModel):
    hora_salida: Optional[time] = None
    horas_jornada_normal: float = Field(default=8, gt=0)
    observacion: Optional[str] = None


class RolPagoCreate(BaseModel):
    id_empleado: int
    periodo: str
    horas_extras: float = Field(default=0, ge=0)
    bonificaciones: float = Field(default=0, ge=0)
    sanciones: float = Field(default=0, ge=0)
    descuentos: float = Field(default=0, ge=0)
    observacion: Optional[str] = None


# ============================================================
# VALIDACIONES Y CÁLCULOS
# ============================================================

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
        datetime.strptime(periodo, "%Y-%m")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="El periodo debe tener el formato AAAA-MM. Ejemplo: 2026-06."
        )


def validar_datos_empleado(empleado):
    campos_obligatorios = [
        empleado.identificacion,
        empleado.nombres,
        empleado.apellidos,
        empleado.telefono,
        empleado.direccion,
        empleado.cargo,
        empleado.area,
        empleado.estado_empleado
    ]

    for campo in campos_obligatorios:
        if campo is None or str(campo).strip() == "":
            raise HTTPException(
                status_code=400,
                detail="No se permiten campos obligatorios vacíos."
            )

    if not validar_cedula_ecuador(empleado.identificacion):
        raise HTTPException(
            status_code=400,
            detail="La cédula ingresada no es una cédula ecuatoriana válida."
        )

    if not validar_solo_letras(empleado.nombres):
        raise HTTPException(
            status_code=400,
            detail="Los nombres solo deben contener letras y espacios."
        )

    if not validar_solo_letras(empleado.apellidos):
        raise HTTPException(
            status_code=400,
            detail="Los apellidos solo deben contener letras y espacios."
        )

    if not empleado.telefono.isdigit():
        raise HTTPException(
            status_code=400,
            detail="El teléfono no debe contener letras."
        )

    if len(empleado.telefono) < 7 or len(empleado.telefono) > 10:
        raise HTTPException(
            status_code=400,
            detail="El teléfono debe tener entre 7 y 10 dígitos."
        )

    if empleado.sueldo <= 0:
        raise HTTPException(
            status_code=400,
            detail="El sueldo debe ser mayor a cero."
        )

    if empleado.fecha_ingreso > date.today():
        raise HTTPException(
            status_code=400,
            detail="No se permite registrar fecha de ingreso futura."
        )

    if empleado.estado_empleado not in ["Activo", "Inactivo", "Suspendido"]:
        raise HTTPException(
            status_code=400,
            detail="Estado de empleado no válido. Use Activo, Inactivo o Suspendido."
        )


def validar_empleado_activo(id_empleado: int, db: Session):
    empleado = db.execute(
        text("""
            SELECT id_empleado, nombres, apellidos, sueldo, estado_empleado
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

    if salida_minutos < entrada_minutos:
        raise HTTPException(
            status_code=400,
            detail="La hora de salida no puede ser menor que la hora de entrada."
        )

    minutos_trabajados = salida_minutos - entrada_minutos
    return round(minutos_trabajados / 60, 2)


# ============================================================
# EMPLEADOS
# ============================================================

@router.get("/empleados")
def listar_empleados(db: Session = Depends(get_db)):
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
    validar_datos_empleado(empleado)

    cedula_existente = db.execute(
        text("""
            SELECT id_empleado
            FROM empleados
            WHERE identificacion = :identificacion
              AND estado = TRUE;
        """),
        {"identificacion": empleado.identificacion}
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
        resultado = db.execute(consulta, empleado.model_dump())
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
    validar_datos_empleado(empleado)

    existe_empleado = db.execute(
        text("""
            SELECT id_empleado
            FROM empleados
            WHERE id_empleado = :id_empleado
              AND estado = TRUE;
        """),
        {"id_empleado": id_empleado}
    ).mappings().first()

    if existe_empleado is None:
        raise HTTPException(status_code=404, detail="Empleado no encontrado.")

    cedula_duplicada = db.execute(
        text("""
            SELECT id_empleado
            FROM empleados
            WHERE identificacion = :identificacion
              AND id_empleado <> :id_empleado
              AND estado = TRUE;
        """),
        {
            "identificacion": empleado.identificacion,
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
                **empleado.model_dump(),
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


@router.patch("/empleados/{id_empleado}/desactivar")
def desactivar_empleado(id_empleado: int, db: Session = Depends(get_db)):
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


# ============================================================
# ASISTENCIA
# ============================================================

@router.post("/asistencia/marcar-entrada")
def marcar_entrada(asistencia: MarcarEntradaCreate, db: Session = Depends(get_db)):
    validar_empleado_activo(asistencia.id_empleado, db)

    fecha_asistencia = asistencia.fecha or date.today()
    hora_entrada = asistencia.hora_entrada or datetime.now().time().replace(microsecond=0)

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
            estado_asistencia,
            minutos_atraso,
            sancion,
            observacion,
            horas_trabajadas,
            horas_extras
        )
        VALUES (
            :id_empleado,
            :fecha,
            :hora_entrada,
            :estado_asistencia,
            :minutos_atraso,
            :sancion,
            :observacion,
            0,
            0
        )
        RETURNING
            id_asistencia,
            id_empleado,
            fecha,
            hora_entrada,
            estado_asistencia,
            minutos_atraso,
            sancion,
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
                "estado_asistencia": estado_asistencia,
                "minutos_atraso": minutos_atraso,
                "sancion": asistencia.sancion,
                "observacion": asistencia.observacion
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
    hora_salida = salida.hora_salida or datetime.now().time().replace(microsecond=0)

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
                "observacion": salida.observacion
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
    if asistencia.estado_asistencia not in ["Presente", "Atraso", "Falta", "Justificado"]:
        raise HTTPException(
            status_code=400,
            detail="Estado de asistencia no válido. Use Presente, Atraso, Falta o Justificado."
        )

    if asistencia.fecha > date.today():
        raise HTTPException(
            status_code=400,
            detail="No se permite registrar asistencia con fecha futura."
        )

    validar_empleado_activo(asistencia.id_empleado, db)

    consulta = text("""
        INSERT INTO asistencia_empleados (
            id_empleado,
            fecha,
            hora_entrada,
            hora_salida,
            estado_asistencia,
            minutos_atraso,
            sancion,
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
            :horas_trabajadas,
            :horas_extras,
            :observacion
        )
        RETURNING id_asistencia;
    """)

    try:
        resultado = db.execute(consulta, asistencia.model_dump())
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
    resultado = db.execute(
        text("""
            SELECT
                a.id_asistencia,
                e.identificacion,
                e.nombres || ' ' || e.apellidos AS empleado,
                e.cargo,
                e.area,
                a.fecha,
                a.hora_entrada,
                a.hora_salida,
                a.estado_asistencia,
                a.minutos_atraso,
                a.sancion,
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
# ROLES DE PAGO
# ============================================================

@router.post("/roles-pago")
def crear_rol_pago(rol: RolPagoCreate, db: Session = Depends(get_db)):
    validar_periodo(rol.periodo)

    empleado = validar_empleado_activo(rol.id_empleado, db)

    sueldo_base = float(empleado["sueldo"])

    resumen_asistencia = db.execute(
        text("""
            SELECT
                COALESCE(SUM(horas_extras), 0) AS horas_extras_asistencia,
                COALESCE(SUM(sancion), 0) AS sanciones_asistencia
            FROM asistencia_empleados
            WHERE id_empleado = :id_empleado
              AND fecha >= TO_DATE(:periodo || '-01', 'YYYY-MM-DD')
              AND fecha <  TO_DATE(:periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month';
        """),
        {
            "id_empleado": rol.id_empleado,
            "periodo": rol.periodo
        }
    ).mappings().first()

    horas_extras_asistencia = float(resumen_asistencia["horas_extras_asistencia"])
    sanciones_asistencia = float(resumen_asistencia["sanciones_asistencia"])

    horas_extras_total = horas_extras_asistencia + float(rol.horas_extras)
    sanciones_total = sanciones_asistencia + float(rol.sanciones)

    total_estimado = (
        sueldo_base +
        horas_extras_total +
        rol.bonificaciones -
        sanciones_total -
        rol.descuentos
    )

    if total_estimado < 0:
        raise HTTPException(
            status_code=400,
            detail="El total a pagar no puede ser negativo."
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

    consulta = text("""
        INSERT INTO roles_pago (
            id_empleado,
            periodo,
            sueldo_base,
            horas_extras,
            bonificaciones,
            sanciones,
            descuentos,
            observacion
        )
        VALUES (
            :id_empleado,
            :periodo,
            :sueldo_base,
            :horas_extras,
            :bonificaciones,
            :sanciones,
            :descuentos,
            :observacion
        )
        RETURNING id_rol_pago, total_pagar;
    """)

    parametros = {
        "id_empleado": rol.id_empleado,
        "periodo": rol.periodo,
        "sueldo_base": sueldo_base,
        "horas_extras": horas_extras_total,
        "bonificaciones": rol.bonificaciones,
        "sanciones": sanciones_total,
        "descuentos": rol.descuentos,
        "observacion": rol.observacion
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
                "apellidos": empleado["apellidos"]
            },
            "calculo": {
                "sueldo_base": sueldo_base,
                "horas_extras_asistencia": horas_extras_asistencia,
                "horas_extras_manual": rol.horas_extras,
                "horas_extras_total": horas_extras_total,
                "sanciones_asistencia": sanciones_asistencia,
                "sanciones_manual": rol.sanciones,
                "sanciones_total": sanciones_total,
                "bonificaciones": rol.bonificaciones,
                "descuentos": rol.descuentos,
                "total_estimado": total_estimado
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
    resultado = db.execute(
        text("""
            SELECT *
            FROM vista_talento_humano_roles
            ORDER BY fecha_generacion DESC;
        """)
    )

    filas = resultado.mappings().all()
    return [dict(fila) for fila in filas]