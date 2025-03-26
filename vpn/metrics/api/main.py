"""
SubNetx VPN Metrics API.

This FastAPI application provides a RESTful API interface for accessing VPN metrics data.
It exposes endpoints to retrieve ping monitoring data, connection quality statistics,
and historical metrics from the SQLite database.

Key Features:
- Real-time access to ping monitoring data
- Historical data retrieval with pagination
- Connection quality analysis and statistics
- TLS certificate information tracking
- Detailed ICMP packet analysis

The API is designed to be:
- Asynchronous: Uses FastAPI's async capabilities for better performance
- RESTful: Follows REST principles with clear endpoint naming
- Self-documenting: Includes OpenAPI/Swagger documentation
- Type-safe: Uses Pydantic models for request/response validation

Dependencies:
- FastAPI: Modern web framework for building APIs
- Pydantic: Data validation using Python type annotations
- SQLite: Local database for metrics storage

:module: vpn.metrics.api.main
:author: SubNetx Team
:version: 1.0.0
"""

import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
from vpn.metrics.conf import PING_DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with metadata
app = FastAPI(
    title="SubNetx VPN Metrics API",
    description="API for accessing VPN metrics and monitoring data",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc",  # ReDoc endpoint
)

# Initialize database connection
# Note: We use a single database instance for the entire application
# This is safe because FastAPI handles concurrent requests properly
db = PingDatabase(PING_DB_PATH)

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

    :ivar cert_expiry: Certificate expiration date
    :ivar issuer: Certificate issuer
    :ivar subject: Certificate subject
    :ivar version: TLS version used
    :ivar cipher: Cipher suite used
    """

    cert_expiry: Optional[str] = Field(
        None, description="Certificate expiration date"
    )
    issuer: Optional[str] = Field(None, description="Certificate issuer")
    subject: Optional[str] = Field(None, description="Certificate subject")
    version: Optional[str] = Field(None, description="TLS version used")
    cipher: Optional[str] = Field(None, description="Cipher suite used")


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
    status_counts: dict = Field(
        ..., description="Count of different status types"
    )
    total_pings: int = Field(..., description="Total number of ping attempts")


# API Endpoints


@app.get("/", response_model=dict)
async def root() -> dict:
    """Root endpoint providing basic API information.

    This endpoint serves as a health check and provides basic information
    about the API version and available endpoints.

    :return: Basic API information including version and endpoints
    :rtype: dict
    """
    return {
        "message": "Welcome to SubNetx VPN Metrics API",
        "version": "1.0.0",
        "endpoints": {
            "targets": "/targets",
            "target_latest": "/targets/{target}/latest",
            "target_history": "/targets/{target}/history",
            "target_summary": "/targets/{target}/summary",
            "all_latest": "/targets/latest",
            "all_summaries": "/targets/summaries",
        },
    }


@app.get("/targets", response_model=List[Target])
async def get_targets() -> List[Target]:
    """Get a list of all ping targets.

    Returns a list of all targets currently being monitored,
    including their IDs, descriptions, and when they were added.

    :return: List of all ping targets
    :rtype: List[Target]
    :raises HTTPException: If database error occurs
    """
    try:
        targets = db.get_all_targets()
        return [Target(**target) for target in targets]
    except Exception as e:
        logger.error(f"Error getting targets: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/targets/{target}/latest", response_model=PingMetric)
async def get_target_latest(target: str) -> PingMetric:
    """Get the latest ping metrics for a specific target.

    Retrieves the most recent ping measurement data for the specified target,
    including detailed ICMP and TLS information if available.

    :param target: Target hostname or IP address
    :type target: str
    :return: Latest ping metrics for the target
    :rtype: PingMetric
    :raises HTTPException: If target is not found or database error occurs
    """
    try:
        latest = db.get_latest_ping(target)
        if not latest:
            raise HTTPException(
                status_code=404, detail=f"Target {target} not found"
            )
        return PingMetric(**latest)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest ping for {target}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/targets/{target}/history", response_model=List[PingMetric])
async def get_target_history(
    target: str, limit: int = 60, offset: int = 0
) -> List[PingMetric]:
    """Get historical ping data for a target.

    Retrieves a paginated list of historical ping measurements for the specified target.
    Results are ordered by timestamp in descending order (newest first).

    :param target: Target hostname or IP address
    :type target: str
    :param limit: Maximum number of records to return
    :type limit: int
    :param offset: Number of records to skip
    :type offset: int
    :return: List of historical ping metrics
    :rtype: List[PingMetric]
    :raises HTTPException: If target is not found or database error occurs
    """
    try:
        history = db.get_ping_history(target, limit, offset)
        if not history:
            raise HTTPException(
                status_code=404, detail=f"Target {target} not found"
            )
        return [PingMetric(**metric) for metric in history]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history for {target}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/targets/{target}/summary", response_model=ConnectionQualitySummary)
async def get_target_summary(
    target: str, hours: int = 24
) -> ConnectionQualitySummary:
    """Get connection quality summary for a target.

    Provides a comprehensive summary of connection quality over a specified time period,
    including statistics, status distribution, and uptime percentage.

    :param target: Target hostname or IP address
    :type target: str
    :param hours: Number of hours to analyze
    :type hours: int
    :return: Summary of connection quality metrics
    :rtype: ConnectionQualitySummary
    :raises HTTPException: If target is not found or database error occurs
    """
    try:
        summary = db.get_connection_quality_summary(target, hours)
        if not summary:
            raise HTTPException(
                status_code=404, detail=f"Target {target} not found"
            )
        return ConnectionQualitySummary(**summary)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary for {target}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/targets/latest", response_model=List[PingMetric])
async def get_all_latest() -> List[PingMetric]:
    """Get the latest ping metrics for all targets.

    Retrieves the most recent ping measurement for each target in the system.
    Useful for getting a quick overview of all monitored targets.

    :return: List of latest ping metrics for all targets
    :rtype: List[PingMetric]
    :raises HTTPException: If database error occurs
    """
    try:
        targets = db.get_all_targets()
        latest_metrics = []
        for target in targets:
            latest = db.get_latest_ping(target["target"])
            if latest:
                latest_metrics.append(PingMetric(**latest))
        return latest_metrics
    except Exception as e:
        logger.error(f"Error getting all latest pings: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/targets/summaries", response_model=List[ConnectionQualitySummary])
async def get_all_summaries(hours: int = 24) -> List[ConnectionQualitySummary]:
    """Get connection quality summaries for all targets.

    Provides connection quality summaries for all monitored targets over a specified time period.
    Useful for comparing performance across different targets.

    :param hours: Number of hours to analyze
    :type hours: int
    :return: List of connection quality summaries for all targets
    :rtype: List[ConnectionQualitySummary]
    :raises HTTPException: If database error occurs
    """
    try:
        targets = db.get_all_targets()
        summaries = []
        for target in targets:
            summary = db.get_connection_quality_summary(target["target"], hours)
            if summary:
                summaries.append(ConnectionQualitySummary(**summary))
        return summaries
    except Exception as e:
        logger.error(f"Error getting all summaries: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
