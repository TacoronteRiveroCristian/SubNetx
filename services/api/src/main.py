#!/usr/bin/env python3
"""
Flexible API for Dynamic Database Operations

This API is designed to be reusable across multiple projects,
allowing dynamic operations on any database compatible
with SQLAlchemy.
"""

import os
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from src.api.routes import db_operations_router

# Initialize FastAPI application
app = FastAPI(
    title="Flexible Database API",
    description="Dynamic API for database operations",
    version="1.0.0",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, limit to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    db_operations_router,
    prefix="/api/db",
    # Remove the duplicated "database" tag to prevent duplicated sections in Swagger UI
    # The tags are already defined in each sub-router
)


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint that confirms the API is working correctly

    Returns:
        Dict: API status

    Example:
        Response:
        ```json
        {
            "status": "online",
            "message": "API working correctly",
            "version": "1.0.0"
        }
        ```
    """
    return {
        "status": "online",
        "message": "API working correctly",
        "version": app.version,
    }


# Run the API server
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
    )
