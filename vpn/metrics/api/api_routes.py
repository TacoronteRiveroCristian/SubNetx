"""
SubNetx VPN Metrics API.

Este módulo principal de la API define las rutas y endpoints para el acceso a datos
de monitoreo y gestión de VPN, integrando tanto los endpoints de métricas como los
de gestión de la VPN.

Características principales:
- Acceso en tiempo real a datos de monitoreo de ping
- Recuperación de datos históricos con paginación
- Análisis de calidad de conexión y estadísticas
- Seguimiento de información de certificados TLS
- Gestión completa del servidor OpenVPN y sus clientes
- Análisis detallado de paquetes ICMP

La API está diseñada para ser:
- Asíncrona: Utiliza las capacidades async de FastAPI para mejor rendimiento
- RESTful: Sigue los principios REST con nomenclatura clara de endpoints
- Auto-documentada: Incluye documentación OpenAPI/Swagger
- Segura en tipos: Usa modelos Pydantic para validación de request/response

:module: vpn.metrics.api.api_routes
:author: SubNetx Team
:version: 1.0.1
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from vpn.metrics.api.db_adapter import DBAdapter as MetricsDBAdapter
from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
from vpn.metrics.conf import PING_DB_PATH

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router específico para métricas
metrics_router = APIRouter(
    prefix="/api/metrics",
    tags=["metrics-monitoring"],
    responses={404: {"description": "Not found"}},
)

# Initialize database connection
# Note: We use a single database instance for the entire application
# This is safe because FastAPI handles concurrent requests properly
db = PingDatabase(PING_DB_PATH)
db_adapter = MetricsDBAdapter(db)

# Pydantic Models for Request/Response Validation
# These models ensure type safety and automatic validation of API data


class Target(BaseModel):
    """Model for ping target information.

    Represents a host or IP address that is being monitored.
    Used for listing all available targets in the system.

    :ivar id: Unique identifier for the target
    :ivar target: Hostname or IP address being monitored
    :ivar description: Optional description of the target
    :ivar added_at: Timestamp when the target was added
    """

    id: int = Field(..., description="Unique identifier for the target")
    target: str = Field(
        ..., description="Hostname or IP address being monitored"
    )
    description: Optional[str] = Field(
        None, description="Optional description of the target"
    )
    added_at: str = Field(
        ..., description="Timestamp when the target was added"
    )


class RttStats(BaseModel):
    """Model for Round-Trip Time statistics.

    Contains statistical information about network latency measurements.
    Used to track the performance of network connections.

    :ivar min_rtt: Minimum RTT in milliseconds
    :ivar avg_rtt: Average RTT in milliseconds
    :ivar max_rtt: Maximum RTT in milliseconds
    :ivar mdev_rtt: Mean deviation of RTT in milliseconds
    """

    min_rtt: float = Field(..., description="Minimum RTT in milliseconds")
    avg_rtt: float = Field(..., description="Average RTT in milliseconds")
    max_rtt: float = Field(..., description="Maximum RTT in milliseconds")
    mdev_rtt: float = Field(
        ..., description="Mean deviation of RTT in milliseconds"
    )


class Packets(BaseModel):
    """Model for packet transmission statistics.

    Tracks the number of packets sent and received during ping tests.
    Used to calculate packet loss and connection reliability.

    :ivar transmitted: Number of packets transmitted
    :ivar received: Number of packets received
    """

    transmitted: int = Field(..., description="Number of packets transmitted")
    received: int = Field(..., description="Number of packets received")


class IcmpDetail(BaseModel):
    """Model for individual ICMP packet details.

    Represents a single ping response with its timing information.
    Used for detailed analysis of network performance.

    :ivar sequence: Sequence number of the ICMP packet
    :ivar response_time_ms: Response time in milliseconds
    """

    sequence: int = Field(..., description="Sequence number of the ICMP packet")
    response_time_ms: float = Field(
        ..., description="Response time in milliseconds"
    )


class TlsInfo(BaseModel):
    """Model for TLS certificate information.

    Contains details about SSL/TLS certificates for secure connections.
    Used for monitoring certificate validity and security status.

    :ivar cert_expiry: Certificate expiration date information
    :ivar issuer: Certificate issuer details
    :ivar subject: Certificate subject details
    :ivar version: TLS version used
    :ivar cipher: Cipher suite information
    """

    cert_expiry: Optional[Union[str, Dict[str, Any]]] = Field(
        None, description="Certificate expiration date information"
    )
    issuer: Optional[Union[str, Dict[str, str]]] = Field(
        None, description="Certificate issuer details"
    )
    subject: Optional[Union[str, Dict[str, str]]] = Field(
        None, description="Certificate subject details"
    )
    version: Optional[str] = Field(None, description="TLS version used")
    cipher: Optional[Union[str, Dict[str, Any]]] = Field(
        None, description="Cipher suite information"
    )


class PingMetric(BaseModel):
    """Model for complete ping metric data.

    Comprehensive model combining all aspects of a ping measurement:
    - Basic connection status
    - RTT statistics
    - Packet information
    - ICMP details
    - TLS information

    :ivar id: Unique identifier for the metric
    :ivar target_id: ID of the target being monitored
    :ivar timestamp: When the measurement was taken
    :ivar status: Connection status (online/offline/timeout)
    :ivar connection_quality: Quality rating of the connection
    :ivar packet_loss_percent: Percentage of lost packets
    :ivar min_rtt: Minimum RTT in milliseconds
    :ivar avg_rtt: Average RTT in milliseconds
    :ivar max_rtt: Maximum RTT in milliseconds
    :ivar mdev_rtt: Mean deviation of RTT in milliseconds
    :ivar packets_transmitted: Number of packets sent
    :ivar packets_received: Number of packets received
    :ivar icmp_details: Detailed ICMP packet information
    :ivar tls_info: TLS certificate information
    """

    id: int = Field(..., description="Unique identifier for the metric")
    target_id: int = Field(..., description="ID of the target being monitored")
    timestamp: str = Field(..., description="When the measurement was taken")
    status: str = Field(
        ..., description="Connection status (online/offline/timeout)"
    )
    connection_quality: str = Field(
        ..., description="Quality rating of the connection"
    )
    packet_loss_percent: float = Field(
        ..., description="Percentage of lost packets"
    )
    min_rtt: float = Field(..., description="Minimum RTT in milliseconds")
    avg_rtt: float = Field(..., description="Average RTT in milliseconds")
    max_rtt: float = Field(..., description="Maximum RTT in milliseconds")
    mdev_rtt: float = Field(
        ..., description="Mean deviation of RTT in milliseconds"
    )
    packets_transmitted: int = Field(..., description="Number of packets sent")
    packets_received: int = Field(..., description="Number of packets received")
    icmp_details: List[IcmpDetail] = Field(
        default_factory=list, description="Detailed ICMP packet information"
    )
    tls_info: Optional[TlsInfo] = Field(
        None, description="TLS certificate information"
    )


class ConnectionQualitySummary(BaseModel):
    """Model for connection quality analysis.

    Provides a summary of connection quality over a time period,
    including statistics and status distribution.

    :ivar target: Target being analyzed
    :ivar period_hours: Analysis period in hours
    :ivar quality_distribution: Distribution of quality ratings
    :ivar avg_rtt_ms: Average RTT in milliseconds
    :ivar avg_packet_loss_percent: Average packet loss percentage
    :ivar uptime_percent: Percentage of time the target was online
    :ivar status_counts: Count of different status types
    :ivar total_pings: Total number of ping attempts
    """

    target: str = Field(..., description="Target being analyzed")
    period_hours: int = Field(..., description="Analysis period in hours")
    quality_distribution: dict = Field(
        ..., description="Distribution of quality ratings"
    )
    avg_rtt_ms: float = Field(..., description="Average RTT in milliseconds")
    avg_packet_loss_percent: float = Field(
        ..., description="Average packet loss percentage"
    )
    uptime_percent: float = Field(
        ..., description="Percentage of time the target was online"
    )
    status_counts: dict = Field(..., description="Count of different status types")
    total_pings: int = Field(..., description="Total number of ping attempts")


class PaginatedResponse(BaseModel):
    """Model for paginated responses.

    Provides a standardized structure for paginated API responses,
    including metadata about the pagination state.

    :ivar items: The actual items being returned
    :ivar total: Total number of items
    :ivar page: Current page number
    :ivar size: Size of each page
    :ivar pages: Total number of pages
    """

    items: List[PingMetric] = Field(..., description="The actual items being returned")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Size of each page")
    pages: int = Field(..., description="Total number of pages")


# Función para formatear valores TLS en un formato más legible
def format_tls_value(value: Any) -> Any:
    """
    Formatear un valor TLS para mejor legibilidad.

    :param value: Valor TLS a formatear
    :type value: Any
    :return: Valor formateado
    :rtype: Any
    """
    if value is None:
        return None

    if not isinstance(value, str):
        return value

    # Primero intentamos parsear como representación de tuplas anidadas
    try:
        # Extraer todos los pares clave-valor usando regex
        pairs = []
        matches = re.finditer(r"'([^']+)', '([^']+)'", value)

        for match in matches:
            key, val = match.groups()
            # Mapear abreviaturas a nombres legibles
            key_map = {
                "C": "Country",
                "ST": "State",
                "L": "Locality",
                "O": "Organization",
                "OU": "Organizational Unit",
                "CN": "Common Name",
                "countryName": "Country",
                "stateOrProvinceName": "State",
                "localityName": "Locality",
                "organizationName": "Organization",
                "organizationalUnitName": "Organizational Unit",
                "commonName": "Common Name",
                "emailAddress": "Email",
            }
            readable_key = key_map.get(key, key)
            pairs.append(f"{readable_key}={val}")

        if pairs:
            return ", ".join(pairs)
    except Exception as e:
        logger.warning(f"Error formateando DN con regex: {e}")

    # Si es una cadena JSON, intentar parsearla
    if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
        try:
            # Intentar parsear como JSON
            import json
            parsed = json.loads(value)

            # Formatear arrays anidados de DN (Distinguished Name)
            if isinstance(parsed, list) and len(parsed) > 0:
                # Caso típico de issuer/subject: [[[key, value], ...], ...]
                parts = []

                # Intentar extraer partes de manera recursiva
                def extract_parts(data):
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, list):
                                extract_parts(item)
                            elif isinstance(item, list) and len(item) == 2:
                                key, val = item
                                readable_key = key_map.get(key, key)
                                parts.append(f"{readable_key}={val}")

                extract_parts(parsed)
                if parts:
                    return ", ".join(parts)

            # Formatear arrays de tipo cipher
            if isinstance(parsed, list) and len(parsed) >= 3:
                # Caso típico de cipher: ["CIPHER_NAME", "VERSION", bits]
                return f"{parsed[0]} ({parsed[1]}, {parsed[2]} bits)"

            # En otros casos, simplificar la representación JSON
            return json.dumps(parsed, ensure_ascii=False)

        except json.JSONDecodeError:
            # Si no es JSON válido, devolver el valor original
            return value

    # Para valores ya formateados o no son JSON, devolver como están
    return value


# Formatear los datos de TLS en la respuesta
def format_tls_info_response(metric: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formatear la información TLS en la respuesta para que sea más legible.

    :param metric: Métrica con información TLS
    :type metric: Dict[str, Any]
    :return: Métrica con información TLS formateada
    :rtype: Dict[str, Any]
    """
    # Crear una copia para no modificar el original
    result = dict(metric)

    # Formatear campos TLS si están presentes
    if "tls_info" in result and result["tls_info"]:
        tls_info = result["tls_info"]

        # Formatear el campo issuer como un diccionario
        if "issuer" in tls_info and tls_info["issuer"]:
            issuer_str = format_tls_value(tls_info["issuer"])
            # Convertir el string formateado a diccionario
            issuer_dict = {}
            for pair in issuer_str.split(", "):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    issuer_dict[key] = value
            tls_info["issuer"] = issuer_dict

        # Formatear el campo subject como un diccionario
        if "subject" in tls_info and tls_info["subject"]:
            subject_str = format_tls_value(tls_info["subject"])
            # Convertir el string formateado a diccionario
            subject_dict = {}
            for pair in subject_str.split(", "):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    subject_dict[key] = value
            tls_info["subject"] = subject_dict

        # Formatear cert_expiry como un diccionario con información de expiración
        if "cert_expiry" in tls_info and tls_info["cert_expiry"]:
            try:
                import datetime
                expiry_str = tls_info["cert_expiry"]
                expiry_date = datetime.datetime.fromisoformat(expiry_str)
                now = datetime.datetime.now()
                days_remaining = (expiry_date - now).days

                tls_info["cert_expiry"] = {
                    "date": expiry_str,
                    "days_remaining": days_remaining,
                    "expired": days_remaining < 0,
                    "status": "valid" if days_remaining > 30 else "expiring_soon" if days_remaining >= 0 else "expired"
                }
            except Exception as e:
                logger.warning(f"Error formateando fecha de expiración: {e}")
                # Mantener el formato original si hay error
                pass

        # Formatear cipher como un diccionario si contiene información estructurada
        if "cipher" in tls_info and tls_info["cipher"] and isinstance(tls_info["cipher"], str):
            cipher_str = tls_info["cipher"]
            # Detectar patrón "CIPHER (PROTOCOL, BITS bits)"
            import re
            cipher_match = re.match(r"([A-Z0-9_]+) \(([^,]+), (\d+) bits\)", cipher_str)
            if cipher_match:
                tls_info["cipher"] = {
                    "name": cipher_match.group(1),
                    "protocol": cipher_match.group(2),
                    "bits": int(cipher_match.group(3))
                }

    return result


# Endpoints de métricas

@metrics_router.get("/targets", response_model=List[Target], summary="List monitoring targets")
async def get_targets():
    """
    List all monitoring targets in the system.

    Returns a list of targets that are currently being monitored,
    including their IDs, addresses, and descriptions.

    Returns:
        List[Target]: List of monitoring targets
    """
    try:
        return db_adapter.get_targets()
    except Exception as e:
        logger.error(f"Error fetching targets: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}"
        )


@metrics_router.get("/status", response_model=List[PingMetric], summary="Get latest status for all targets")
async def get_all_latest_status():
    """
    Get the most recent ping metrics for all targets.

    Returns a list of the latest monitoring data for all targets,
    including connection status, RTT statistics, and quality ratings.

    Returns:
        List[PingMetric]: List of latest ping metric data for all targets
    """
    try:
        targets = db_adapter.get_targets()
        result = []

        for target in targets:
            try:
                metric = db_adapter.get_latest_metric(target['id'])
                if metric:
                    # Formatear campos TLS
                    metric = format_tls_info_response(metric)
                    result.append(metric)
            except Exception as e:
                logger.warning(f"Error fetching metric for target {target['id']}: {str(e)}")
                # Continue with next target if one fails
                continue

        return result
    except Exception as e:
        logger.error(f"Error fetching all latest metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}"
        )


@metrics_router.get(
    "/targets/{target_id}/latest",
    response_model=PingMetric,
    summary="Get latest metric for a target"
)
async def get_latest_metric(target_id: int):
    """
    Get the most recent ping metric for a target.

    Retrieves the latest monitoring data for the specified target,
    including connection status, RTT statistics, and quality rating.

    Args:
        target_id: ID of the target to retrieve data for

    Returns:
        PingMetric: Latest ping metric data
    """
    try:
        metric = db_adapter.get_latest_metric(target_id)
        if not metric:
            raise HTTPException(
                status_code=404,
                detail=f"No metrics found for target ID {target_id}"
            )

        # Formatear campos TLS para mejor legibilidad
        metric = format_tls_info_response(metric)

        return metric
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest metric: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}"
        )


@metrics_router.get(
    "/targets/{target_id}/metrics",
    response_model=PaginatedResponse,
    summary="Get paginated metrics for a target"
)
async def get_metrics_for_target(
    target_id: int, page: int = 1, size: int = 20, hours: Optional[int] = None
):
    """
    Get paginated ping metrics for a target.

    Retrieves a paginated list of ping measurements for the specified target.
    Can be filtered to include only data from the past X hours.

    Args:
        target_id: ID of the target to retrieve data for
        page: Page number to retrieve (starting from 1)
        size: Number of items per page
        hours: Optional filter to include only data from past X hours

    Returns:
        PaginatedResponse: Paginated metrics with metadata
    """
    try:
        # Validate target exists
        target = db_adapter.get_target(target_id)
        if not target:
            raise HTTPException(
                status_code=404, detail=f"Target ID {target_id} not found"
            )

        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=400, detail="Page must be >= 1"
            )
        if size < 1 or size > 100:
            raise HTTPException(
                status_code=400, detail="Size must be between 1 and 100"
            )

        # Get paginated metrics
        metrics, total = db_adapter.get_metrics_paginated(
            target_id, page, size, hours
        )

        # Formatear TLS info en cada métrica
        formatted_metrics = [format_tls_info_response(m) for m in metrics]

        # Calculate total pages
        total_pages = (total + size - 1) // size if total > 0 else 1

        # Return paginated response
        return {
            "items": formatted_metrics,
            "total": total,
            "page": page,
            "size": size,
            "pages": total_pages,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}"
        )


@metrics_router.get(
    "/targets/{target_id}/quality",
    response_model=ConnectionQualitySummary,
    summary="Get connection quality analysis"
)
async def get_connection_quality(target_id: int, hours: int = 24):
    """
    Get connection quality analysis for a target.

    Analyzes ping data over the specified time period to provide
    a summary of connection quality and reliability statistics.

    Args:
        target_id: ID of the target to analyze
        hours: Time period for analysis in hours

    Returns:
        ConnectionQualitySummary: Summary of connection quality
    """
    try:
        # Validate target exists
        target = db_adapter.get_target(target_id)
        if not target:
            raise HTTPException(
                status_code=404, detail=f"Target ID {target_id} not found"
            )

        # Validate hours parameter
        if hours < 1 or hours > 720:  # Max 30 days
            raise HTTPException(
                status_code=400,
                detail="Hours must be between 1 and 720 (30 days)"
            )

        # Get connection quality summary
        summary = db_adapter.get_connection_quality(target_id, hours)

        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing connection quality: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Analysis error: {str(e)}"
        )
