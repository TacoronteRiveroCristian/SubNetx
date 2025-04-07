"""
Servidor API de Gestión y Monitoreo de SubNetx VPN.

Este script inicia el servidor FastAPI que proporciona la API REST
para la gestión de OpenVPN y el acceso a datos de monitoreo.

El servidor gestiona dos tipos de endpoints:
1. Endpoints de métricas - Para monitoreo de rendimiento y estadísticas
2. Endpoints de gestión VPN - Para control del servidor OpenVPN y sus clientes

:module: vpn.metrics.api.api_server
:author: SubNetx Team
:version: 1.0.1
"""

import logging
import os
import sys

import uvicorn
from fastapi import FastAPI

from vpn.metrics.api.api_routes import metrics_router
from vpn.metrics.api.vpn_endpoints import router as vpn_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title="SubNetx VPN Management Platform",
    description="Plataforma completa para monitoreo y gestión de VPN",
    version="1.0.1",
    docs_url="/docs",  # Endpoint para Swagger UI
    redoc_url="/redoc",  # Endpoint para ReDoc
)

# Incluir routers para métricas y gestión de VPN
app.include_router(metrics_router)
app.include_router(vpn_router)

# Endpoint raíz
@app.get("/", include_in_schema=False)
async def root():
    """Endpoint raíz que redirige a la documentación."""
    return {
        "message": "Bienvenido a la API de SubNetx VPN",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

def start_api_server():
    """Iniciar el servidor API."""
    logger.info("Iniciando servidor API de SubNetx VPN")

    # Determinar host y puerto, permitiendo configuración por variables de entorno
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))

    # Iniciar servidor
    uvicorn.run(
        "vpn.metrics.api.api_server:app",
        host=host,
        port=port,
        reload=True  # Deshabilitar recarga en producción
    )

if __name__ == "__main__":
    start_api_server()
