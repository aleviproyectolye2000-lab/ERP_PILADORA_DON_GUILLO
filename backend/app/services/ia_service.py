import os
import json
import time as time_module
from datetime import date, datetime, time
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session
from openai import OpenAI

load_dotenv()

# =====================================================
# CONFIGURACIÓN OFICIAL DE IA
# =====================================================
# Este archivo queda configurado SOLO para OpenAI.
# Se deja OpenAI como proveedor único de inteligencia artificial.
#
# Variables recomendadas en el archivo .env:
# OPENAI_API_KEY=pega_aqui_tu_clave_real_de_openai
# OPENAI_MODEL=gpt-4o-mini
# IA_MAX_REGISTROS=20
# OPENAI_TIMEOUT_SEGUNDOS=45
# OPENAI_MAX_REINTENTOS=1
# OPENAI_MAX_TOKENS=1200
# =====================================================

IA_PROVIDER = "openai"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()


def obtener_entero_env(nombre_variable: str, valor_defecto: int) -> int:
    try:
        valor = int(os.getenv(nombre_variable, str(valor_defecto)))
        if valor <= 0:
            return valor_defecto
        return valor
    except Exception:
        return valor_defecto


IA_MAX_REGISTROS = obtener_entero_env("IA_MAX_REGISTROS", 20)
OPENAI_TIMEOUT_SEGUNDOS = obtener_entero_env("OPENAI_TIMEOUT_SEGUNDOS", 45)
OPENAI_MAX_REINTENTOS = obtener_entero_env("OPENAI_MAX_REINTENTOS", 1)
OPENAI_MAX_TOKENS = obtener_entero_env("OPENAI_MAX_TOKENS", 1200)


TEMAS_PERMITIDOS = [
    "compras",
    "bascula",
    "báscula",
    "peso de entrada",
    "peso de salida",
    "peso neto",
    "inventario",
    "bodega",
    "stock",
    "produccion",
    "producción",
    "pilado",
    "arroz",
    "arroz en cascara",
    "arroz en cáscara",
    "arroz pilado",
    "polvillo",
    "arrocillo",
    "cascarilla",
    "tamo",
    "ventas",
    "clientes",
    "proveedores",
    "talento humano",
    "empleados",
    "roles de pago",
    "asistencia",
    "auditoria",
    "auditoría",
    "usuarios",
    "perfiles",
    "reportes",
    "gerencia",
    "activos",
    "maquinaria",
    "mantenimiento",
    "transporte",
    "piladora",
    "erp",
    "don guillo",
]

TEMAS_PROHIBIDOS = [
    "receta",
    "cocinar",
    "comida",
    "medicina",
    "doctor",
    "enfermedad",
    "politica",
    "política",
    "elecciones",
    "religion",
    "religión",
    "futbol",
    "fútbol",
    "pelicula",
    "película",
    "musica",
    "música",
    "entretenimiento",
    "construccion",
    "construcción",
    "amor",
    "pareja",
    "chiste",
    "carro",
    "vehiculo personal",
    "vehículo personal",
    "moto",
    "casa",
    "terreno personal",
    "celular",
    "prestamo personal",
    "préstamo personal",
    "deuda personal",
    "inversion personal",
    "inversión personal",
    "viaje",
    "turismo",
    "ropa",
    "zapatos",
]


def convertir_json_seguro(valor):
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()

    if isinstance(valor, Decimal):
        return float(valor)

    return valor


def filas_a_lista(filas):
    datos = []

    for fila in filas:
        item = {}

        for clave, valor in dict(fila).items():
            item[clave] = convertir_json_seguro(valor)

        datos.append(item)

    return datos


def pregunta_es_valida(pregunta: str) -> bool:
    pregunta_normalizada = pregunta.lower().strip()

    for prohibido in TEMAS_PROHIBIDOS:
        if prohibido in pregunta_normalizada:
            return False

    for permitido in TEMAS_PERMITIDOS:
        if permitido in pregunta_normalizada:
            return True

    palabras_generales_validas = [
        "stock",
        "producto",
        "productos",
        "proveedor",
        "proveedores",
        "cliente",
        "clientes",
        "empleado",
        "empleados",
        "venta",
        "ventas",
        "compra",
        "compras",
        "produccion",
        "producción",
        "inventario",
        "reporte",
        "reportes",
        "recomendacion",
        "recomendación",
        "analiza",
        "analisis",
        "análisis",
        "riesgo",
        "rendimiento",
        "ingreso",
        "egreso",
        "arroz",
        "piladora",
        "gerencial",
        "utilidad",
        "ganancia",
        "perdida",
        "pérdida",
        "sueldo",
        "asistencia",
        "auditoria",
        "auditoría",
    ]

    for palabra in palabras_generales_validas:
        if palabra in pregunta_normalizada:
            return True

    return False


def ejecutar_consulta_lectura(db: Session, nombre: str, consulta_sql: str):
    try:
        resultado = db.execute(text(consulta_sql))
        filas = resultado.mappings().all()

        return {
            "estado": "ok",
            "datos": filas_a_lista(filas),
        }

    except Exception as error:
        return {
            "estado": "error",
            "detalle": f"No se pudo consultar {nombre}: {str(error)}",
            "datos": [],
        }


def obtener_contexto_erp(db: Session, modulo: str = "general"):
    limite = IA_MAX_REGISTROS
    contexto = {}
    modulo = modulo.strip().lower()

    if modulo in ["general", "gerencial", "reportes", "dashboard", "index"]:
        contexto["resumen_gerencial"] = ejecutar_consulta_lectura(
            db,
            "resumen gerencial",
            "SELECT * FROM fn_resumen_gerencial();",
        )

        contexto["stock_bajo"] = ejecutar_consulta_lectura(
            db,
            "stock bajo",
            f"SELECT * FROM fn_stock_bajo() LIMIT {limite};",
        )

        contexto["ventas_por_producto"] = ejecutar_consulta_lectura(
            db,
            "ventas por producto",
            f"SELECT * FROM fn_ventas_por_producto() LIMIT {limite};",
        )

        contexto["compras_recientes"] = ejecutar_consulta_lectura(
            db,
            "compras recientes",
            f"""
            SELECT *
            FROM vista_compras_completas
            ORDER BY fecha_compra DESC
            LIMIT {limite};
            """,
        )

        contexto["ventas_recientes"] = ejecutar_consulta_lectura(
            db,
            "ventas recientes",
            f"""
            SELECT *
            FROM vista_ventas_completas
            ORDER BY fecha_venta DESC
            LIMIT {limite};
            """,
        )

        contexto["inventario_actual"] = ejecutar_consulta_lectura(
            db,
            "inventario actual",
            f"""
            SELECT *
            FROM vista_inventario_actual
            LIMIT {limite};
            """,
        )

        contexto["produccion_reciente"] = ejecutar_consulta_lectura(
            db,
            "producción reciente",
            f"""
            SELECT *
            FROM vista_produccion_rendimiento
            ORDER BY fecha_pilado DESC
            LIMIT {limite};
            """,
        )

        contexto["talento_humano"] = ejecutar_consulta_lectura(
            db,
            "talento humano",
            f"""
            SELECT *
            FROM vista_talento_humano_roles
            LIMIT {limite};
            """,
        )

        contexto["activos_mantenimientos"] = ejecutar_consulta_lectura(
            db,
            "activos y mantenimientos",
            f"""
            SELECT *
            FROM vista_activos_mantenimientos
            LIMIT {limite};
            """,
        )

        contexto["auditoria_reciente"] = ejecutar_consulta_lectura(
            db,
            "auditoría reciente",
            f"""
            SELECT *
            FROM vista_auditoria_general
            ORDER BY fecha_accion DESC, hora_accion DESC
            LIMIT {limite};
            """,
        )

    elif modulo == "compras":
        contexto["compras_recientes"] = ejecutar_consulta_lectura(
            db,
            "compras recientes",
            f"""
            SELECT *
            FROM vista_compras_completas
            ORDER BY fecha_compra DESC
            LIMIT {limite};
            """,
        )
        contexto["inventario_actual"] = ejecutar_consulta_lectura(
            db,
            "inventario actual",
            f"""
            SELECT *
            FROM vista_inventario_actual
            LIMIT {limite};
            """,
        )

    elif modulo == "ventas":
        contexto["ventas_recientes"] = ejecutar_consulta_lectura(
            db,
            "ventas recientes",
            f"""
            SELECT *
            FROM vista_ventas_completas
            ORDER BY fecha_venta DESC
            LIMIT {limite};
            """,
        )
        contexto["ventas_por_producto"] = ejecutar_consulta_lectura(
            db,
            "ventas por producto",
            f"SELECT * FROM fn_ventas_por_producto() LIMIT {limite};",
        )
        contexto["inventario_actual"] = ejecutar_consulta_lectura(
            db,
            "inventario actual",
            f"""
            SELECT *
            FROM vista_inventario_actual
            LIMIT {limite};
            """,
        )

    elif modulo == "inventario" or modulo == "bodega":
        contexto["inventario_actual"] = ejecutar_consulta_lectura(
            db,
            "inventario actual",
            f"""
            SELECT *
            FROM vista_inventario_actual
            LIMIT {limite};
            """,
        )
        contexto["stock_bajo"] = ejecutar_consulta_lectura(
            db,
            "stock bajo",
            f"SELECT * FROM fn_stock_bajo() LIMIT {limite};",
        )

    elif modulo == "produccion" or modulo == "pilado":
        contexto["produccion_reciente"] = ejecutar_consulta_lectura(
            db,
            "producción reciente",
            f"""
            SELECT *
            FROM vista_produccion_rendimiento
            ORDER BY fecha_pilado DESC
            LIMIT {limite};
            """,
        )
        contexto["inventario_actual"] = ejecutar_consulta_lectura(
            db,
            "inventario actual",
            f"""
            SELECT *
            FROM vista_inventario_actual
            LIMIT {limite};
            """,
        )

    elif modulo == "talento_humano":
        contexto["talento_humano"] = ejecutar_consulta_lectura(
            db,
            "talento humano",
            f"""
            SELECT *
            FROM vista_talento_humano_roles
            LIMIT {limite};
            """,
        )

    elif modulo == "activos":
        contexto["activos_mantenimientos"] = ejecutar_consulta_lectura(
            db,
            "activos y mantenimientos",
            f"""
            SELECT *
            FROM vista_activos_mantenimientos
            LIMIT {limite};
            """,
        )

    elif modulo == "auditoria":
        contexto["auditoria_reciente"] = ejecutar_consulta_lectura(
            db,
            "auditoría reciente",
            f"""
            SELECT *
            FROM vista_auditoria_general
            ORDER BY fecha_accion DESC, hora_accion DESC
            LIMIT {limite};
            """,
        )

    return contexto


def construir_prompt_sistema(modulo: str = "general"):
    modulo_seguro = modulo.strip().lower()

    instruccion_aislamiento = ""
    if modulo_seguro not in ["general", "gerencial", "reportes", "dashboard", "index"]:
        instruccion_aislamiento = (
            f"\n\nATENCIÓN - POLÍTICA ESTRICTA DE AISLAMIENTO:\n"
            f"El usuario te está consultando desde el submódulo operativo de '{modulo_seguro.upper()}'. "
            f"Tienes PROHIBIDO dar información, analizar o responder preguntas sobre otros módulos de la empresa (ej. si estás en compras, no hables de ventas o empleados). "
            f"Si el usuario pregunta algo ajeno a '{modulo_seguro.upper()}', debes responder exactamente: 'Lo siento, por políticas de seguridad, en este chat solo tengo acceso a la información operativa del módulo de {modulo_seguro.upper()}. Diríjase al módulo correspondiente para esa consulta.'\n"
        )

    return f"""
Eres el asistente gerencial de inteligencia artificial del ERP Piladora Don Guillo.{instruccion_aislamiento}

Contexto obligatorio:
El sistema pertenece a una piladora de arroz llamada Piladora Don Guillo ubicada en Babahoyo, Los Ríos, Ecuador.
Fecha actual y percepción del tiempo: Estamos en Junio de 2026. Este es tu presente absoluto. Si se te solicita información, proyecciones o cálculos sobre años como el 2025, debes saber que es el pasado y ofrecer proyecciones hacia el cierre del año actual (2026) o años venideros.
El ERP maneja compras de arroz en cáscara, báscula, inventario, producción/pilado, ventas, talento humano, auditoría, reportes, activos, maquinaria, transporte y mantenimiento.

Reglas obligatorias:
1. Responde únicamente sobre operaciones reales del ERP Piladora Don Guillo.
2. Puedes analizar compras, báscula, inventario, producción, ventas, talento humano, auditoría, reportes, activos, transporte y maquinaria.
3. Trabajas solamente con los datos enviados por el backend desde PostgreSQL.
4. No inventes datos que no estén en el contexto.
5. No debes modificar, insertar, actualizar ni eliminar datos.
6. No debes dar instrucciones SQL de escritura como INSERT, UPDATE, DELETE, DROP, ALTER o TRUNCATE.
7. No respondas sobre comida, medicina, política, entretenimiento, construcción, deportes, religión, compras personales, carros, viajes, celulares, ropa ni temas ajenos al ERP.
8. No hagas recomendaciones financieras personales del usuario.
9. No hagas simulaciones personales como comprar carro, comprar casa, préstamos personales o gastos ajenos al negocio.
10. Si la pregunta está fuera del ERP, responde de forma breve: "Solo puedo ayudar con información relacionada al ERP Piladora Don Guillo."
11. Si la pregunta es ambigua, pide que la relacione con un módulo del ERP.
12. Si no existe suficiente información en los datos reales, dilo claramente.
13. No exageres. Responde de forma concreta, gerencial y profesional.
14. No uses respuestas demasiado largas salvo que el usuario pida un análisis detallado.
15. Cuando detectes riesgos, menciona el área afectada y la acción recomendada.
16. Si haces cálculos, deben basarse en datos reales del contexto enviado por PostgreSQL.
17. No conviertas preguntas personales en análisis del ERP si no tienen relación directa con compras, ventas, inventario, producción o gestión de la piladora.

Formato de respuesta:
- Resumen ejecutivo.
- Análisis según datos disponibles.
- Recomendaciones.
- Advertencias o limitaciones de datos, si aplica.

Estilo:
Responde en español claro, directo y profesional.
Evita inventar, exagerar o asumir información que no aparece en los datos reales.
"""


def construir_prompt_usuario(pregunta: str, contexto: dict):
    contexto_json = json.dumps(
        contexto,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
Pregunta del usuario:
{pregunta}

Datos reales consultados desde PostgreSQL:
{contexto_json}

Responde usando solamente estos datos y las reglas del ERP Piladora Don Guillo.
"""


def api_key_openai_configurada() -> bool:
    if not OPENAI_API_KEY:
        return False

    claves_invalidas = [
        "PEGAR_AQUI_TU_CLAVE_REAL",
        "PEGAR_AQUI_TU_OPENAI_API_KEY",
        "TU_OPENAI_API_KEY",
        "TU_API_KEY",
        "OPENAI_API_KEY",
        "sk-...",
    ]

    return OPENAI_API_KEY not in claves_invalidas


def extraer_mensaje_error_openai(error):
    codigo = getattr(error, "status_code", None)
    estado = error.__class__.__name__
    mensaje = str(error)

    try:
        cuerpo = getattr(error, "body", None)

        if isinstance(cuerpo, dict):
            error_body = cuerpo.get("error", cuerpo)
            mensaje = error_body.get("message", mensaje)
            estado = error_body.get("type", estado) or estado
            codigo = error_body.get("code", codigo) or codigo

    except Exception:
        pass

    return codigo, estado, mensaje


def mensaje_amigable_error_openai(codigo, estado, mensaje_tecnico, modelo_usado):
    mensaje_tecnico = str(mensaje_tecnico or "")
    mensaje_minuscula = mensaje_tecnico.lower()

    if codigo == 400:
        return (
            "La solicitud enviada a OpenAI no fue aceptada. "
            "Revise que la pregunta no esté vacía, que el modelo configurado sea válido "
            "y que los parámetros enviados sean compatibles con el modelo."
        )

    if codigo == 401:
        return (
            "No se pudo autenticar con OpenAI. "
            "Revise que OPENAI_API_KEY exista en el archivo .env, que esté bien copiada "
            "y que pertenezca a una cuenta activa."
        )

    if codigo == 403:
        return (
            "La cuenta de OpenAI no tiene permiso para usar este modelo o este proyecto. "
            "Revise permisos, facturación, proyecto y organización de OpenAI."
        )

    if codigo == 404:
        return (
            f"El modelo de OpenAI configurado no fue encontrado: {modelo_usado}. "
            "Revise el valor de OPENAI_MODEL en el archivo .env."
        )

    if codigo == 408:
        return (
            "La consulta a OpenAI tardó demasiado tiempo. "
            "Intente nuevamente en unos minutos."
        )

    if codigo == 429:
        if "quota" in mensaje_minuscula or "billing" in mensaje_minuscula or "insufficient" in mensaje_minuscula:
            return (
                "OpenAI rechazó la consulta por límite de cuota, crédito insuficiente o facturación no disponible. "
                "Revise el saldo, el método de pago y los límites de uso de la cuenta."
            )

        return (
            "Se alcanzó el límite temporal de consultas de OpenAI. "
            "Espere unos minutos antes de volver a consultar."
        )

    if codigo in [500, 502, 503, 504]:
        return (
            "OpenAI tuvo un error temporal o alta demanda en este momento. "
            "Intente nuevamente en unos minutos."
        )

    if "api key" in mensaje_minuscula and ("invalid" in mensaje_minuscula or "incorrect" in mensaje_minuscula):
        return (
            "La API key de OpenAI no es válida. "
            "Genere o copie nuevamente la clave y colóquela en OPENAI_API_KEY dentro del archivo .env."
        )

    if "model" in mensaje_minuscula and ("not found" in mensaje_minuscula or "does not exist" in mensaje_minuscula):
        return (
            f"El modelo configurado no existe o no está disponible para la cuenta: {modelo_usado}. "
            "Revise OPENAI_MODEL en el archivo .env."
        )

    if "billing" in mensaje_minuscula or "quota" in mensaje_minuscula:
        return (
            "La cuenta de OpenAI tiene un problema de facturación, saldo o cuota. "
            "Revise la sección de billing/usage de OpenAI."
        )

    if "timeout" in mensaje_minuscula or "timed out" in mensaje_minuscula:
        return (
            "La consulta a OpenAI excedió el tiempo de espera. "
            "Revise la conexión o vuelva a intentar."
        )

    if "connection" in mensaje_minuscula or "network" in mensaje_minuscula:
        return (
            "No se pudo conectar con OpenAI. "
            "Revise la conexión a internet del servidor donde está corriendo FastAPI."
        )

    return (
        "No se pudo consultar OpenAI en este momento. "
        "Revise la API key, el modelo, la facturación, la conexión o intente nuevamente más tarde."
    )


def construir_respuesta_error_ia(
    respuesta_usuario: str,
    codigo=None,
    estado_openai: str = "",
    modelo_usado: str = "",
    detalle_tecnico: str = "",
):
    return {
        "estado": "error",
        "respuesta": respuesta_usuario,
        "codigo_error": codigo,
        "estado_openai": estado_openai,
        "modelo_usado": modelo_usado,
        "detalle_tecnico": detalle_tecnico,
    }


def llamar_openai_una_vez(prompt_sistema: str, prompt_usuario: str):
    cliente_openai = OpenAI(
        api_key=OPENAI_API_KEY,
        timeout=OPENAI_TIMEOUT_SEGUNDOS,
        max_retries=0,
    )

    respuesta = cliente_openai.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": prompt_sistema,
            },
            {
                "role": "user",
                "content": prompt_usuario,
            },
        ],
        temperature=0.2,
        max_tokens=OPENAI_MAX_TOKENS,
    )

    if not respuesta.choices:
        return {
            "estado": "error",
            "respuesta": "OpenAI no devolvió una respuesta válida. Intente reformular la pregunta.",
            "modelo_usado": OPENAI_MODEL,
        }

    texto_respuesta = respuesta.choices[0].message.content

    if texto_respuesta is None:
        texto_respuesta = ""

    texto_respuesta = texto_respuesta.strip()

    if not texto_respuesta:
        texto_respuesta = "OpenAI respondió vacío. Intente reformular la pregunta."

    return {
        "estado": "ok",
        "respuesta": texto_respuesta,
        "modelo_usado": OPENAI_MODEL,
    }


def consultar_openai(prompt_sistema: str, prompt_usuario: str):
    if not api_key_openai_configurada():
        return construir_respuesta_error_ia(
            "La IA real todavía no está configurada. Debe colocar una clave válida en OPENAI_API_KEY dentro del archivo .env.",
            codigo=401,
            estado_openai="API_KEY_NO_CONFIGURADA",
            modelo_usado=OPENAI_MODEL,
        )

    intentos = 0
    ultimo_error = None

    while intentos <= OPENAI_MAX_REINTENTOS:
        try:
            return llamar_openai_una_vez(prompt_sistema, prompt_usuario)

        except Exception as error:
            codigo, estado, mensaje_tecnico = extraer_mensaje_error_openai(error)

            respuesta_amigable = mensaje_amigable_error_openai(
                codigo,
                estado,
                mensaje_tecnico,
                OPENAI_MODEL,
            )

            ultimo_error = construir_respuesta_error_ia(
                respuesta_amigable,
                codigo=codigo,
                estado_openai=estado,
                modelo_usado=OPENAI_MODEL,
                detalle_tecnico=mensaje_tecnico,
            )

            error_temporal = codigo in [408, 429, 500, 502, 503, 504]

            if error_temporal and intentos < OPENAI_MAX_REINTENTOS:
                intentos += 1
                time_module.sleep(1)
                continue

            return ultimo_error

    if ultimo_error:
        return ultimo_error

    return construir_respuesta_error_ia(
        "No se pudo consultar OpenAI en este momento.",
        codigo="SIN_RESPUESTA",
        estado_openai="SIN_RESPUESTA",
        modelo_usado=OPENAI_MODEL,
    )


def consultar_ia_erp(db: Session, pregunta: str, contexto_modulo: str = "general"):
    pregunta_limpia = pregunta.strip()

    if not pregunta_limpia:
        return {
            "estado": "error",
            "proveedor": IA_PROVIDER,
            "modelo": OPENAI_MODEL,
            "respuesta": "Debe escribir una pregunta para la IA.",
        }

    if len(pregunta_limpia) > 1000:
        return {
            "estado": "error",
            "proveedor": IA_PROVIDER,
            "modelo": OPENAI_MODEL,
            "respuesta": "La pregunta es demasiado larga. Redúzcala y vuelva a intentar.",
        }

    if not pregunta_es_valida(pregunta_limpia):
        return {
            "estado": "bloqueado",
            "proveedor": IA_PROVIDER,
            "modelo": OPENAI_MODEL,
            "respuesta": (
                "Solo puedo responder preguntas relacionadas con el ERP Piladora Don Guillo: "
                "compras, báscula, inventario, producción, ventas, talento humano, auditoría, "
                "reportes, activos, transporte y maquinaria."
            ),
        }

    contexto = obtener_contexto_erp(db, contexto_modulo)

    prompt_sistema = construir_prompt_sistema(contexto_modulo)
    prompt_usuario = construir_prompt_usuario(pregunta_limpia, contexto)

    respuesta = consultar_openai(prompt_sistema, prompt_usuario)

    if respuesta.get("estado") == "ok":
        return {
            "estado": "exito",
            "proveedor": IA_PROVIDER,
            "modelo": respuesta.get("modelo_usado", OPENAI_MODEL),
            "respuesta": respuesta.get("respuesta", "No se obtuvo respuesta de OpenAI."),
            "codigo_error": respuesta.get("codigo_error"),
            "estado_openai": respuesta.get("estado_openai"),
        }

    return {
        "estado": "error",
        "proveedor": IA_PROVIDER,
        "modelo": respuesta.get("modelo_usado", OPENAI_MODEL),
        "respuesta": respuesta.get("respuesta", "No se pudo obtener respuesta de OpenAI."),
        "codigo_error": respuesta.get("codigo_error"),
        "estado_openai": respuesta.get("estado_openai"),
        "detalle_tecnico": respuesta.get("detalle_tecnico"),
    }


def estado_ia():
    return {
        "proveedor": IA_PROVIDER,
        "modelo": OPENAI_MODEL,
        "openai_configurada": api_key_openai_configurada(),
        "configurada": api_key_openai_configurada(),
        "modo": "solo lectura",
        "backend": "FastAPI",
        "base_datos": "PostgreSQL",
        "max_registros": IA_MAX_REGISTROS,
        "timeout_segundos": OPENAI_TIMEOUT_SEGUNDOS,
        "max_reintentos": OPENAI_MAX_REINTENTOS,
        "max_tokens": OPENAI_MAX_TOKENS,
    }