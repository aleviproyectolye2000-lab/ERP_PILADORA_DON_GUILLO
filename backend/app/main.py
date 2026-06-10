from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import probar_conexion

from app.routers import (
    reportes,
    ia,
    compras,
    inventario,
    produccion,
    ventas,
    talento_humano,
    activos,
    auditoria,
    seguridad
)

# =====================================================
# APLICACIÓN PRINCIPAL - ERP PILADORA DON GUILLO
# =====================================================

app = FastAPI(
    title="ERP Piladora Don Guillo",
    description=(
        "Sistema ERP para compras, producción, inventario, ventas, "
        "talento humano, activos, seguridad, auditoría, reportes e inteligencia artificial."
    ),
    version="1.0.0"
)

# =====================================================
# CONFIGURACIÓN CORS
# Permite que el frontend local se conecte con FastAPI.
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # El asterisco significa "permitir desde cualquier página de internet"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# REGISTRO DE ROUTERS DEL SISTEMA
# No cambiar el orden si los módulos ya están funcionando.
# =====================================================

app.include_router(reportes.router)
app.include_router(ia.router)
app.include_router(compras.router)
app.include_router(inventario.router)
app.include_router(produccion.router)
app.include_router(ventas.router)
app.include_router(talento_humano.router)
app.include_router(activos.router)
app.include_router(auditoria.router)
app.include_router(seguridad.router)

# =====================================================
# ENDPOINT PRINCIPAL
# =====================================================

@app.get("/")
def inicio():
    return {
        "mensaje": "ERP Piladora Don Guillo funcionando correctamente",
        "estado": "activo",
        "version": "1.0.0",
        "modulos": [
            "Seguridad y auditoría",
            "Compras, recepción y báscula",
            "Inventario y bodega",
            "Producción y pilado",
            "Ventas y comercialización",
            "Talento humano",
            "Activos y mantenimientos",
            "Reportes gerenciales",
            "Inteligencia artificial"
        ]
    }


# =====================================================
# VERIFICACIÓN DEL BACKEND
# =====================================================

@app.get("/salud")
def verificar_salud():
    return {
        "sistema": "ERP Piladora Don Guillo",
        "backend": "FastAPI",
        "estado": "funcionando",
        "ambiente": "desarrollo"
    }


# =====================================================
# PRUEBA DE CONEXIÓN A POSTGRESQL
# =====================================================

@app.get("/db-test")
def verificar_base_datos():
    return probar_conexion()