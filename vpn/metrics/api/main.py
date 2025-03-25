"""FastAPI application for the SubNetx VPN metrics API."""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
from vpn.metrics.conf import PING_DB_PATH

# Initialize FastAPI app
app = FastAPI(
    title="SubNetx VPN Metrics API",
    description="API for accessing VPN monitoring metrics and statistics",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc",  # ReDoc endpoint
)

# Initialize database connection
db = PingDatabase(PING_DB_PATH)


class Target(BaseModel):
    """Pydantic model for ping target information."""

    id: int
    target: str
    description: Optional[str] = None
    added_at: datetime


class RttStats(BaseModel):
    """Pydantic model for RTT statistics."""

    min_ms: float
    avg_ms: float
    max_ms: float
    mdev_ms: float


class Packets(BaseModel):
    """Pydantic model for packet statistics."""

    transmitted: int
    received: int


class IcmpDetail(BaseModel):
    """Pydantic model for ICMP packet details."""

    sequence: int
    response_time_ms: float


class TlsInfo(BaseModel):
    """Pydantic model for TLS information."""

    cert_expiry: Optional[datetime] = None
    issuer: Optional[str] = None
    subject: Optional[str] = None
    version: Optional[str] = None
    cipher: Optional[str] = None


class PingMetric(BaseModel):
    """Pydantic model for ping metrics."""

    id: int
    target_id: int
    timestamp: datetime
    status: str
    connection_quality: str
    packet_loss_percent: float
    min_rtt: float
    avg_rtt: float
    max_rtt: float
    mdev_rtt: float
    packets_transmitted: int
    packets_received: int
    icmp_details: List[IcmpDetail]
    tls_info: Optional[TlsInfo] = None


class ConnectionQualitySummary(BaseModel):
    """Pydantic model for connection quality summary."""

    target: str
    period_hours: int
    quality_distribution: Dict[str, int]
    avg_rtt_ms: float
    avg_packet_loss_percent: float
    uptime_percent: float
    status_counts: Dict[str, int]
    total_pings: int


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root endpoint returning API information."""
    return {
        "name": "SubNetx VPN Metrics API",
        "version": "1.0.0",
        "description": "API for accessing VPN monitoring metrics and statistics",
    }


@app.get("/targets", response_model=List[Target], tags=["Targets"])
async def get_targets() -> List[Target]:
    """Get a list of all ping targets in the database."""
    targets = db.get_all_targets()
    return [Target(**target) for target in targets]


@app.get(
    "/targets/{target}/latest", response_model=PingMetric, tags=["Metrics"]
)
async def get_latest_ping(target: str) -> PingMetric:
    """Get the latest ping metrics for a specific target."""
    latest = db.get_latest_ping(target)
    if not latest:
        raise HTTPException(
            status_code=404, detail=f"No data found for target: {target}"
        )
    return PingMetric(**latest)


@app.get(
    "/targets/{target}/history",
    response_model=List[PingMetric],
    tags=["Metrics"],
)
async def get_ping_history(
    target: str, limit: int = 60, offset: int = 0
) -> List[PingMetric]:
    """Get ping history for a specific target with pagination."""
    history = db.get_ping_history(target, limit, offset)
    return [PingMetric(**metric) for metric in history]


@app.get(
    "/targets/{target}/summary",
    response_model=ConnectionQualitySummary,
    tags=["Metrics"],
)
async def get_connection_summary(
    target: str, hours: int = 24
) -> ConnectionQualitySummary:
    """Get connection quality summary for a specific target over a time period."""
    summary = db.get_connection_quality_summary(target, hours)
    return ConnectionQualitySummary(**summary)


@app.get(
    "/targets/latest", response_model=Dict[str, PingMetric], tags=["Metrics"]
)
async def get_all_latest_pings() -> Dict[str, PingMetric]:
    """Get the latest ping metrics for all targets."""
    targets = db.get_all_targets()
    result = {}
    for target in targets:
        latest = db.get_latest_ping(target["target"])
        if latest:
            result[target["target"]] = PingMetric(**latest)
    return result


@app.get(
    "/targets/summaries",
    response_model=Dict[str, ConnectionQualitySummary],
    tags=["Metrics"],
)
async def get_all_connection_summaries(
    hours: int = 24,
) -> Dict[str, ConnectionQualitySummary]:
    """Get connection quality summaries for all targets over a time period."""
    targets = db.get_all_targets()
    result = {}
    for target in targets:
        summary = db.get_connection_quality_summary(target["target"], hours)
        result[target["target"]] = ConnectionQualitySummary(**summary)
    return result
