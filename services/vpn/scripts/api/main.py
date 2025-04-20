#!/usr/bin/env python3
"""
VPN Operations API.

This API provides endpoints to manage OpenVPN operations.
"""

import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from scripts.api.routers import clients, server
from scripts.api.routers.utils import APIResponse, ErrorResponse

# Initialize FastAPI application
app = FastAPI(
    title="VPN Operations API",
    description="API for OpenVPN management operations",
    version="1.0.0",
)

# Include routers
app.include_router(server.router)
app.include_router(clients.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    _request: Request, exc: HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions with standardized format.

    Ensures all error responses follow the standardized format.
    """
    status_code = exc.status_code

    # If detail is already a dict with our format, use it
    if isinstance(exc.detail, dict) and "success" in exc.detail:
        return JSONResponse(status_code=status_code, content=exc.detail)

    # Otherwise, create a properly formatted error response
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            success=False, message=str(exc.detail), details=None
        ).model_dump(exclude_none=True),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with standardized format."""
    # Ensure all error information is JSON serializable
    errors = []
    for error in exc.errors():
        # Create a serializable version of the error
        error_dict = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        errors.append(error_dict)

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            success=False,
            message="Validation error",
            details={"errors": errors},
        ).model_dump(),
    )


@app.get("/", response_model=APIResponse)
async def root() -> APIResponse:
    """Root endpoint to check API status."""
    return APIResponse(
        success=True,
        message="VPN Operations API is running",
        details={"version": app.version},
    )


if __name__ == "__main__":
    uvicorn.run(
        "scripts.api.main:app",
        host=os.getenv("VPN_API_HOST", "0.0.0.0"),
        port=int(os.getenv("VPN_API_PORT", "9000")),
        reload=True,
    )
