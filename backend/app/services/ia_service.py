import os
import json
import time as time_module
import socket
import urllib.request
import urllib.error
from datetime import date, datetime, time
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session
from openai import OpenAI

load_dotenv()

IA_PROVIDER = os.getenv("IA_PROVIDER", "gemini").lower().strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
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

GEMINI_TIMEOUT_SEGUNDOS = obtener_entero_env("GEMINI_TIMEOUT_SEGUNDOS", 45)
GEMINI_MAX_REINTENTOS = obtener_entero_env("GEMINI_MAX_REINTENTOS", 1)

MODELO_FALLBACK_GEMINI = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash").strip()


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


def extraer_mensaje_error_gemini(detalle_texto: str):
    try:
        detalle_json = json.loads(detalle_texto)
        error = detalle_json.get("error", {})

        codigo = error.get("code")
        estado = error.get("status", "")
        mensaje = error.get("message", "")

        return codigo, estado, mensaje

    except Exception:
        return None, "", detalle_texto


def mensaje_amigable_error_gemini(codigo, estado, mensaje_tecnico, modelo_usado):
    mensaje_tecnico = str(mensaje_tecnico or "")

    if codigo == 400:
        return (
            "La solicitud enviada a la IA no fue aceptada. "
            "Revise que la pregunta no esté vacía y que el modelo configurado sea válido."
        )

    if codigo == 401:
        return (
            "No se pudo autenticar con Gemini. "
            "La clave GEMINI_API_KEY no es válida, está mal copiada o no pertenece a Google AI Studio."
        )

    if codigo == 403:
        return (
            "La cuenta o proyecto de Google no tiene permiso para usar este modelo de IA. "
            "Revise la API key, el proyecto de Google AI Studio o cambie el modelo configurado."
        )

    if codigo == 404:
        return (
            f"El modelo de IA configurado no fue encontrado: {modelo_usado}. "
            "Revise el valor de GEMINI_MODEL en el archivo .env."
        )

    if codigo == 429:
        return (
            "Se alcanzó el límite de consultas de la IA. "
            "Espere unos minutos antes de volver a consultar."
        )

    if codigo == 500:
        return (
            "El proveedor de IA tuvo un error interno temporal. "
            "Intente nuevamente en unos minutos."
        )

    if codigo == 503:
        return (
            f"El modelo {modelo_usado} está temporalmente saturado por alta demanda. "
            "Intente nuevamente en unos minutos o use un modelo más estable como gemini-1.5-flash."
        )

    if "api key not valid" in mensaje_tecnico.lower():
        return (
            "La clave de Gemini no es válida. "
            "Genere una nueva API key desde Google AI Studio y colóquela en el archivo .env."
        )

    if "quota" in mensaje_tecnico.lower():
        return (
            "La cuenta alcanzó el límite o cuota disponible de Gemini. "
            "Espere unos minutos o revise el límite de uso en Google AI Studio."
        )

    return (
        "No se pudo consultar la IA en este momento. "
        "Revise la conexión, la API key o intente nuevamente más tarde."
    )


def construir_respuesta_error_ia(
    respuesta_usuario: str,
    codigo=None,
    estado_gemini: str = "",
    modelo_usado: str = "",
    detalle_tecnico: str = "",
):
    return {
        "estado": "error",
        "respuesta": respuesta_usuario,
        "codigo_error": codigo,
        "estado_gemini": estado_gemini,
        "modelo_usado": modelo_usado,
        "detalle_tecnico": detalle_tecnico,
    }


def construir_url_gemini(modelo: str):
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{modelo}:generateContent?key={GEMINI_API_KEY}"
    )


def construir_cuerpo_gemini(prompt_sistema: str, prompt_usuario: str):
    return {
        "systemInstruction": {
            "parts": [
                {
                    "text": prompt_sistema,
                }
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt_usuario,
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.8,
            "maxOutputTokens": 1200,
        },
    }


def llamar_gemini_una_vez(prompt_sistema: str, prompt_usuario: str, modelo: str):
    url = construir_url_gemini(modelo)
    cuerpo = construir_cuerpo_gemini(prompt_sistema, prompt_usuario)
    data = json.dumps(cuerpo).encode("utf-8")

    solicitud = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(solicitud, timeout=GEMINI_TIMEOUT_SEGUNDOS) as respuesta:
        contenido = respuesta.read().decode("utf-8")
        respuesta_json = json.loads(contenido)

    candidatos = respuesta_json.get("candidates", [])

    if not candidatos:
        return {
            "estado": "error",
            "respuesta": "La IA no devolvió una respuesta válida. Intente reformular la pregunta.",
            "modelo_usado": modelo,
        }

    partes = candidatos[0].get("content", {}).get("parts", [])
    textos = []

    for parte in partes:
        if "text" in parte:
            textos.append(parte["text"])

    texto_respuesta = "\n".join(textos).strip()

    if not texto_respuesta:
        texto_respuesta = "La IA respondió vacío. Intente reformular la pregunta."

    return {
        "estado": "ok",
        "respuesta": texto_respuesta,
        "modelo_usado": modelo,
    }


def consultar_gemini(prompt_sistema: str, prompt_usuario: str):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "PEGAR_AQUI_TU_CLAVE_REAL":
        return construir_respuesta_error_ia(
            "La IA real todavía no está configurada. Debe colocar una clave válida en GEMINI_API_KEY dentro del archivo .env.",
            codigo=401,
            estado_gemini="API_KEY_NO_CONFIGURADA",
            modelo_usado=GEMINI_MODEL,
        )

    modelos_a_probar = [GEMINI_MODEL]

    if (
        MODELO_FALLBACK_GEMINI
        and MODELO_FALLBACK_GEMINI not in modelos_a_probar
        and GEMINI_MODEL != MODELO_FALLBACK_GEMINI
    ):
        modelos_a_probar.append(MODELO_FALLBACK_GEMINI)

    ultimo_error = None

    for indice_modelo, modelo in enumerate(modelos_a_probar):
        intentos = 0

        while intentos <= GEMINI_MAX_REINTENTOS:
            try:
                return llamar_gemini_una_vez(prompt_sistema, prompt_usuario, modelo)

            except urllib.error.HTTPError as error:
                detalle = error.read().decode("utf-8", errors="replace")
                codigo, estado, mensaje_tecnico = extraer_mensaje_error_gemini(detalle)

                if codigo is None:
                    codigo = error.code

                respuesta_amigable = mensaje_amigable_error_gemini(
                    codigo,
                    estado,
                    mensaje_tecnico,
                    modelo,
                )

                ultimo_error = construir_respuesta_error_ia(
                    respuesta_amigable,
                    codigo=codigo,
                    estado_gemini=estado,
                    modelo_usado=modelo,
                    detalle_tecnico=detalle,
                )

                es_error_temporal = codigo in [429, 500, 503]

                if es_error_temporal and intentos < GEMINI_MAX_REINTENTOS:
                    intentos += 1
                    time_module.sleep(1)
                    continue

                if es_error_temporal and indice_modelo + 1 < len(modelos_a_probar):
                    break

                return ultimo_error

            except urllib.error.URLError as error:
                detalle = str(error)

                ultimo_error = construir_respuesta_error_ia(
                    "No se pudo conectar con Gemini. Revise la conexión a internet o la disponibilidad del servicio de IA.",
                    codigo="CONEXION",
                    estado_gemini="URL_ERROR",
                    modelo_usado=modelo,
                    detalle_tecnico=detalle,
                )

                if intentos < GEMINI_MAX_REINTENTOS:
                    intentos += 1
                    time_module.sleep(1)
                    continue

                if indice_modelo + 1 < len(modelos_a_probar):
                    break

                return ultimo_error

            except socket.timeout:
                ultimo_error = construir_respuesta_error_ia(
                    "La consulta a Gemini tardó demasiado tiempo. Intente nuevamente en unos minutos.",
                    codigo="TIMEOUT",
                    estado_gemini="TIMEOUT",
                    modelo_usado=modelo,
                    detalle_tecnico="Timeout al consultar Gemini.",
                )

                if intentos < GEMINI_MAX_REINTENTOS:
                    intentos += 1
                    time_module.sleep(1)
                    continue

                if indice_modelo + 1 < len(modelos_a_probar):
                    break

                return ultimo_error

            except Exception as error:
                return construir_respuesta_error_ia(
                    "Ocurrió un error inesperado al consultar la IA. Revise la configuración del backend.",
                    codigo="ERROR_INTERNO",
                    estado_gemini="EXCEPTION",
                    modelo_usado=modelo,
                    detalle_tecnico=str(error),
                )

    if ultimo_error:
        return ultimo_error

    return construir_respuesta_error_ia(
        "No se pudo consultar la IA en este momento.",
        codigo="SIN_RESPUESTA",
        estado_gemini="SIN_RESPUESTA",
        modelo_usado=GEMINI_MODEL,
    )

def consultar_openai(prompt_sistema: str, prompt_usuario: str):
    """
    Función de respaldo que llama a OpenAI si Gemini falla.
    """
    if not OPENAI_API_KEY:
        return construir_respuesta_error_ia(
            "API KEY de OpenAI no configurada en el entorno.",
            codigo=401,
            modelo_usado=OPENAI_MODEL
        )

    try:
        cliente_openai = OpenAI(api_key=OPENAI_API_KEY)
        respuesta = cliente_openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.2,
            max_tokens=1200
        )
        return {
            "estado": "ok",
            "respuesta": respuesta.choices[0].message.content,
            "modelo_usado": OPENAI_MODEL
        }
    except Exception as error:
        return construir_respuesta_error_ia(
            "El proveedor de respaldo (OpenAI) también falló.",
            codigo="ERROR_OPENAI",
            modelo_usado=OPENAI_MODEL,
            detalle_tecnico=str(error)
        )

def consultar_ia_erp(db: Session, pregunta: str, contexto_modulo: str = "general"):
    pregunta_limpia = pregunta.strip()

    if not pregunta_limpia:
        return {
            "estado": "error",
            "proveedor": IA_PROVIDER,
            "modelo": GEMINI_MODEL,
            "respuesta": "Debe escribir una pregunta para la IA.",
        }

    if len(pregunta_limpia) > 1000:
        return {
            "estado": "error",
            "proveedor": IA_PROVIDER,
            "modelo": GEMINI_MODEL,
            "respuesta": "La pregunta es demasiado larga. Redúzcala y vuelva a intentar.",
        }

    if not pregunta_es_valida(pregunta_limpia):
        return {
            "estado": "bloqueado",
            "proveedor": IA_PROVIDER,
            "modelo": GEMINI_MODEL,
            "respuesta": (
                "Solo puedo responder preguntas relacionadas con el ERP Piladora Don Guillo: "
                "compras, báscula, inventario, producción, ventas, talento humano, auditoría, "
                "reportes, activos, transporte y maquinaria."
            ),
        }

    contexto = obtener_contexto_erp(db, contexto_modulo)

    prompt_sistema = construir_prompt_sistema(contexto_modulo)
    prompt_usuario = construir_prompt_usuario(pregunta_limpia, contexto)

    if IA_PROVIDER == "gemini":
        respuesta = consultar_gemini(prompt_sistema, prompt_usuario)

        if respuesta.get("estado") == "ok":
            return {
                "estado": "exito",
                "proveedor": "gemini",
                "modelo": respuesta.get("modelo_usado", GEMINI_MODEL),
                "respuesta": respuesta.get("respuesta", "No se obtuvo respuesta de la IA."),
                "codigo_error": respuesta.get("codigo_error"),
                "estado_gemini": respuesta.get("estado_gemini"),
            }
        else:
            print(f"Alerta: Gemini falló ({respuesta.get('detalle_tecnico')}). Activando respaldo OpenAI...")
            respuesta_openai = consultar_openai(prompt_sistema, prompt_usuario)
            
            if respuesta_openai.get("estado") == "ok":
                return {
                    "estado": "exito",
                    "proveedor": "openai (respaldo)",
                    "modelo": respuesta_openai.get("modelo_usado", OPENAI_MODEL),
                    "respuesta": respuesta_openai.get("respuesta", "No se obtuvo respuesta de OpenAI."),
                }
            else:
                return {
                    "estado": "error",
                    "proveedor": "ambos_fallaron",
                    "modelo": "N/A",
                    "respuesta": "Ambos proveedores de Inteligencia Artificial están temporalmente saturados. Por favor, intente nuevamente en unos minutos.",
                    "detalle_tecnico": respuesta_openai.get("detalle_tecnico")
                }

    return {
        "estado": "error",
        "proveedor": IA_PROVIDER,
        "modelo": GEMINI_MODEL,
        "respuesta": "Proveedor de IA no soportado. Configure IA_PROVIDER=gemini en el archivo .env.",
    }


def estado_ia():
    return {
        "proveedor": IA_PROVIDER,
        "modelo": GEMINI_MODEL,
        "modelo_fallback": MODELO_FALLBACK_GEMINI,
        "openai_configurada": bool(OPENAI_API_KEY),
        "configurada": bool(GEMINI_API_KEY and GEMINI_API_KEY != "AQ.Ab8RN6JCkSL9eHYJdc7zLUmNAemxEJDtYM7uit7LypG5jEQAqw"),
        "modo": "solo lectura",
        "backend": "FastAPI",
        "base_datos": "PostgreSQL",
        "max_registros": IA_MAX_REGISTROS,
        "timeout_segundos": GEMINI_TIMEOUT_SEGUNDOS,
    }