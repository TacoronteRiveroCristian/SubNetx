"""
SubNetx VPN API Package.

Este paquete incluye los módulos para la API de gestión y monitoreo de SubNetx VPN.

Módulos principales:
- api_server: Script para iniciar el servidor API con todos los endpoints
- api_routes: Definición de rutas y endpoints para métricas
- vpn_endpoints: Endpoints para la gestión del servidor OpenVPN
- db_adapter: Adaptador entre la API y la base de datos

:author: SubNetx Team
:version: 1.0.1
"""

from vpn.metrics.api.api_routes import metrics_router

# Importaciones para facilitar el acceso a los componentes principales
from vpn.metrics.api.api_server import app, start_api_server
from vpn.metrics.api.vpn_endpoints import router as vpn_router
