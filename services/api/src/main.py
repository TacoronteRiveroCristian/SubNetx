"""
Main FastAPI application for the VPN management API.

This module serves as the entry point for the API service, providing:
- API routing and middleware
- Database connection management
- Authentication and authorization
- API documentation
- Health checks and monitoring
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from sqlalchemy.ext.asyncio import AsyncSession

from .api.router import api_router
from .db.session import async_session
from .models.base import Base

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan manager for FastAPI application.

    Handles startup and shutdown events:
    - Database initialization
    - Cache setup
    - Background tasks
    """
    # Startup
    logger.info("starting_application")

    # Initialize database
    async with async_session() as session:
        await session.execute("SELECT 1")

    yield

    # Shutdown
    logger.info("shutting_down_application")

# Initialize FastAPI app
app = FastAPI(
    title="VPN Management API",
    description="API for managing VPN services and metrics",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(
        "incoming_request",
        method=request.method,
        url=str(request.url),
        client_host=request.client.host if request.client else None
    )

    response = await call_next(request)

    logger.info(
        "request_completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code
    )

    return response

# Add error handling middleware
@app.middleware("http")
async def error_handling(request: Request, call_next):
    """Handle and log all errors."""
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(
            "request_failed",
            error=str(e),
            method=request.method,
            url=str(request.url)
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
