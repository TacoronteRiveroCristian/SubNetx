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
    Format TLS info in the metric response for better client-side processing.

    This function formats TLS certificate data to more human-readable formats,
    handling different representations of DN (Distinguished Name) fields.

    Args:
        metric: Metric data to format

    Returns:
        Dict[str, Any]: Formatted metric data
    """
    # Make a copy to avoid modifying the original
    formatted = metric.copy()

    # Check if we have the new format with primary_target
    primary_target = None
    tls_info = None

    if "primary_target" in formatted:
        primary_target = formatted["primary_target"]
        if primary_target and "tls_info" in primary_target:
            tls_info = primary_target["tls_info"]
    elif "tls_info" in formatted:
        tls_info = formatted["tls_info"]

    # Skip if no TLS info
    if not tls_info:
        return formatted

    # Format TLS fields for better display
    formatted_tls = {}

    # Process each field
    for field in ["cert_expiry", "expiry", "issuer", "subject", "version", "cipher"]:
        if field in tls_info and tls_info[field]:
            value = tls_info[field]
            formatted_value = format_tls_value(value)

            # Use standard field names in response
            if field == "expiry":  # Map expiry to cert_expiry
                formatted_tls["cert_expiry"] = formatted_value
            else:
                formatted_tls[field] = formatted_value

    # Ensure all expected fields exist in the response
    for field in ["cert_expiry", "issuer", "subject", "version", "cipher"]:
        if field not in formatted_tls:
            formatted_tls[field] = None

    # Update the TLS info in the formatted response
    if primary_target:
        formatted["primary_target"]["tls_info"] = formatted_tls
    else:
        formatted["tls_info"] = formatted_tls

    return formatted


# Endpoints de métricas

@metrics_router.get("/targets", response_model=List[Target], summary="List all monitoring targets")
async def get_targets():
    """
    Get all monitoring targets.

    Returns a list of targets that are currently being monitored,
    including their IDs, addresses, and descriptions.

    Returns:
        List[Target]: List of monitoring targets
    """
    try:
        # Get all targets from the database
        all_targets = db_adapter.get_targets()

        # Filter to only show the targets that are actively being monitored
        active_target_hostnames = get_active_target_hostnames()

        # Filter targets that are in the active list
        active_targets = [
            target for target in all_targets
            if target['target'] in active_target_hostnames
        ]

        return active_targets
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
        # Get only the actively monitored targets
        active_target_hostnames = get_active_target_hostnames()
        all_targets = db_adapter.get_targets()
        active_targets = [
            target for target in all_targets
            if target['target'] in active_target_hostnames
        ]

        result = []

        for target in active_targets:
            try:
                # Get the latest metric for the target
                metric = db_adapter.get_latest_metric(target['id'])

                if metric:
                    # Format TLS fields for better readability
                    formatted_metric = format_tls_info_response(metric)

                    # The metric should already be formatted by the db_adapter._format_metric method,
                    # but we need to extract it from the primary_target structure if present
                    if "primary_target" in formatted_metric:
                        # Keep only the metric fields needed by the API model
                        result.append({
                            'id': formatted_metric.get('id', 0),
                            'target_id': target['id'],
                            'timestamp': formatted_metric.get('primary_target', {}).get('timestamp', ''),
                            'status': formatted_metric.get('primary_target', {}).get('status', 'unknown'),
                            'connection_quality': formatted_metric.get('primary_target', {}).get('connection_quality', 'unknown'),
                            'packet_loss_percent': formatted_metric.get('primary_target', {}).get('packet_loss_percent', 0.0),
                            'min_rtt': formatted_metric.get('primary_target', {}).get('min_rtt', 0.0),
                            'avg_rtt': formatted_metric.get('primary_target', {}).get('avg_rtt', 0.0),
                            'max_rtt': formatted_metric.get('primary_target', {}).get('max_rtt', 0.0),
                            'mdev_rtt': formatted_metric.get('primary_target', {}).get('mdev_rtt', 0.0),
                            'packets_transmitted': formatted_metric.get('primary_target', {}).get('packets_transmitted', 0),
                            'packets_received': formatted_metric.get('primary_target', {}).get('packets_received', 0),
                            'icmp_details': formatted_metric.get('primary_target', {}).get('icmp_details', []),
                            'tls_info': formatted_metric.get('primary_target', {}).get('tls_info', {})
                        })
                    else:
                        # Use the metric directly as it's already in the right format
                        result.append(formatted_metric)
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
        # Get target info first
        target = db_adapter.get_target(target_id)
        if not target:
            raise HTTPException(
                status_code=404,
                detail=f"Target ID {target_id} not found"
            )

        # Check if this target is actively being monitored
        active_target_hostnames = get_active_target_hostnames()
        if target['target'] not in active_target_hostnames:
            raise HTTPException(
                status_code=404,
                detail=f"Target '{target['target']}' is not actively being monitored"
            )

        # Get the latest metric for the target
        metric = db_adapter.get_latest_metric(target_id)
        if not metric:
            raise HTTPException(
                status_code=404,
                detail=f"No metrics found for target ID {target_id}"
            )

        # Format TLS fields for better readability
        formatted_metric = format_tls_info_response(metric)

        # If the metric has a primary_target structure, extract the data from it
        if "primary_target" in formatted_metric:
            # Extract only the fields needed by the API model
            primary_data = formatted_metric.get('primary_target', {})
            return {
                'id': formatted_metric.get('id', 0),
                'target_id': target_id,
                'timestamp': primary_data.get('timestamp', ''),
                'status': primary_data.get('status', 'unknown'),
                'connection_quality': primary_data.get('connection_quality', 'unknown'),
                'packet_loss_percent': primary_data.get('packet_loss_percent', 0.0),
                'min_rtt': primary_data.get('min_rtt', 0.0),
                'avg_rtt': primary_data.get('avg_rtt', 0.0),
                'max_rtt': primary_data.get('max_rtt', 0.0),
                'mdev_rtt': primary_data.get('mdev_rtt', 0.0),
                'packets_transmitted': primary_data.get('packets_transmitted', 0),
                'packets_received': primary_data.get('packets_received', 0),
                'icmp_details': primary_data.get('icmp_details', []),
                'tls_info': primary_data.get('tls_info', {})
            }

        # Otherwise just return the formatted metric
        return formatted_metric

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

        # Check if this target is actively being monitored
        active_target_hostnames = get_active_target_hostnames()
        if target['target'] not in active_target_hostnames:
            raise HTTPException(
                status_code=404,
                detail=f"Target '{target['target']}' is not actively being monitored"
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

        # Check if this target is actively being monitored
        active_target_hostnames = get_active_target_hostnames()
        if target['target'] not in active_target_hostnames:
            raise HTTPException(
                status_code=404,
                detail=f"Target '{target['target']}' is not actively being monitored"
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


def get_active_target_hostnames() -> List[str]:
    """
    Get the list of hostnames that are actively being monitored.

    This centralizes the definition of which targets are considered "active"
    to ensure consistency across API endpoints.

    Returns:
        List[str]: List of active target hostnames
    """
    # These targets are hardcoded in the extract_and_save_ping.py script
    return ["google.com", "invalid.example.domain"]
