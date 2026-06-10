import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# URL directa universal (Pooler) de tu base de datos en Supabase
URL_NUBE = "postgresql://postgres.zxtojfeqtrhgdpaxavll:Elvis2200209639@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

# En producción (Render) usará la variable de entorno, en local usará URL_NUBE
DATABASE_URL = os.getenv("DATABASE_URL", URL_NUBE)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def probar_conexion():
    try:
        with engine.connect() as conexion:
            resultado = conexion.execute(text("SELECT version();"))
            return {
                "estado": "conectado",
                "base_datos": "Supabase Nube (postgres)",
                "postgresql": resultado.scalar()
            }
    except Exception as error:
        return {
            "estado": "error",
            "detalle": str(error)
        }