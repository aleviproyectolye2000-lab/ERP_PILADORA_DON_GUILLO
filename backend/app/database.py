import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# =====================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =====================================================
# IMPORTANTE:
# - No escribir contraseñas reales dentro de este archivo.
# - No escribir la URL completa de Supabase quemada en el código.
# - Render debe tomar los datos desde Environment Variables.
# - En local debe tomar los datos desde backend/.env.
#
# Variables esperadas:
# DB_HOST
# DB_PORT
# DB_NAME
# DB_USER
# DB_PASSWORD
#
# Variable opcional:
# DATABASE_URL
# =====================================================


def obtener_variable_entorno(nombre: str, valor_defecto: str = "") -> str:
    valor = os.getenv(nombre, valor_defecto)

    if valor is None:
        return valor_defecto

    return str(valor).strip()


def es_host_local(host: str) -> bool:
    host_normalizado = str(host or "").strip().lower()

    return host_normalizado in [
        "localhost",
        "127.0.0.1",
        "::1",
    ]


def agregar_sslmode_si_corresponde(url: str, host: str) -> str:
    """
    Supabase normalmente requiere SSL.
    Si se está usando una base local, no se fuerza sslmode.
    Si se está usando una base en nube y la URL no trae sslmode,
    se agrega sslmode=require.
    """

    if not url:
        return url

    if es_host_local(host):
        return url

    if "sslmode=" in url.lower():
        return url

    separador = "&" if "?" in url else "?"
    return f"{url}{separador}sslmode=require"


def construir_database_url() -> str:
    """
    Construye la conexión a PostgreSQL usando variables de entorno.

    Prioridad:
    1. Si existe DATABASE_URL, se usa esa.
    2. Si no existe, se construye con DB_HOST, DB_PORT, DB_NAME, DB_USER y DB_PASSWORD.
    """

    database_url_env = obtener_variable_entorno("DATABASE_URL", "")

    db_host = obtener_variable_entorno("DB_HOST", "localhost")
    db_port = obtener_variable_entorno("DB_PORT", "5432")
    db_name = obtener_variable_entorno("DB_NAME", "erp_piladora_don_guillo")
    db_user = obtener_variable_entorno("DB_USER", "postgres")
    db_password = obtener_variable_entorno("DB_PASSWORD", "12345")

    if database_url_env:
        return agregar_sslmode_si_corresponde(database_url_env, db_host)

    usuario_seguro = quote_plus(db_user)
    password_seguro = quote_plus(db_password)
    nombre_base_seguro = quote_plus(db_name)

    database_url = (
        f"postgresql://{usuario_seguro}:{password_seguro}"
        f"@{db_host}:{db_port}/{nombre_base_seguro}"
    )

    return agregar_sslmode_si_corresponde(database_url, db_host)


DATABASE_URL = construir_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def obtener_nombre_base_datos():
    db_host = obtener_variable_entorno("DB_HOST", "localhost")
    db_name = obtener_variable_entorno("DB_NAME", "erp_piladora_don_guillo")

    if es_host_local(db_host):
        return f"PostgreSQL Local ({db_name})"

    if "supabase" in db_host.lower():
        return f"Supabase Nube ({db_name})"

    return f"PostgreSQL Nube ({db_name})"


def probar_conexion():
    try:
        with engine.connect() as conexion:
            resultado = conexion.execute(text("SELECT version();"))

            return {
                "estado": "conectado",
                "base_datos": obtener_nombre_base_datos(),
                "postgresql": resultado.scalar(),
            }

    except Exception as error:
        return {
            "estado": "error",
            "detalle": str(error),
        }