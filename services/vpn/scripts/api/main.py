#!/usr/bin/env python3
"""
VPN Operations API.

This API provides endpoints to manage OpenVPN operations.
"""

import os
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI

from scripts.api.routers import clients, server

# Initialize FastAPI application
app = FastAPI(
    title="VPN Operations API",
    description="API for OpenVPN management operations",
    version="1.0.0",
)

# Include routers
app.include_router(server.router)
app.include_router(clients.router)


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint to check API status."""
    return {
        "status": "online",
        "message": "VPN Operations API is running",
        "version": app.version,
    }


if __name__ == "__main__":
    uvicorn.run(
        "scripts.api.main:app",
        host=os.getenv("VPN_API_HOST", "0.0.0.0"),
        port=int(os.getenv("VPN_API_PORT", "9000")),
        reload=True,
    )
