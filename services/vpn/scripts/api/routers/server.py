"""
Server operations router.

This module provides endpoints to manage the OpenVPN server.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from scripts.api.routers.utils import APIResponse, ErrorResponse, run_command

# Define router
router = APIRouter(
    prefix="/server",
    tags=["server"],
    responses={404: {"description": "Not found"}},
)


class SetupConfig(BaseModel):
    """Configuration for setting up OpenVPN server.

    :ivar red: Network address
    :ivar mask: Network mask
    :ivar port: Server port
    :ivar proto: Network protocol
    :ivar tun: TUN device name
    :ivar ip: Server IP address
    """

    red: str = "10.10.10.0"
    mask: str = "255.255.255.0"
    port: str = "1194"
    proto: str = "udp"
    tun: str = "tun0"
    ip: str


@router.get("/status", response_model=APIResponse)
async def get_status() -> APIResponse:
    """Get the current status of the OpenVPN server.

    :return: Status of the OpenVPN server
    :rtype: APIResponse
    """
    result = run_command(["/app/scripts/openvpn/core/openvpn-status.sh"])

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to get VPN status",
                details={"error": result["error"]},
            ).dict(),
        )

    # Process the output to ensure it is in English and properly formatted
    raw_output = result["output"].lower()

    # Determine server status
    status_info: Dict[str, Any] = {}
    if "status: running" in raw_output or "active" in raw_output:
        status_info["state"] = "running"
        status_info["is_active"] = True
    else:
        status_info["state"] = "stopped"
        status_info["is_active"] = False

    # Extract additional information if available
    if "pid" in raw_output:
        try:
            # Try to extract PID if present
            pid_match = raw_output.split("pid ", 1)[1].split()[0].strip()
            status_info["pid"] = pid_match
        except (IndexError, ValueError):
            pass

    # Return standardized response
    return APIResponse(
        success=True,
        message="VPN server status retrieved successfully",
        details={"status": status_info},
    )


@router.post("/start", response_model=APIResponse)
async def start_server() -> APIResponse:
    """Start the OpenVPN server.

    :return: Result of the operation
    :rtype: APIResponse
    """
    result = run_command(["/app/scripts/openvpn/core/openvpn-start.sh"])

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to start VPN server",
                details={"error": result["error"]},
            ).dict(),
        )

    return APIResponse(success=True, message="VPN server started successfully")


@router.post("/stop", response_model=APIResponse)
async def stop_server() -> APIResponse:
    """Stop the OpenVPN server.

    :return: Result of the operation
    :rtype: APIResponse
    """
    # Verificar primero si la VPN está activa
    status_result = run_command(["/app/scripts/openvpn/core/openvpn-status.sh"])

    # Procesamos la salida para determinar el estado
    is_running = False
    if status_result["success"]:
        status_output = status_result["output"].lower()
        is_running = (
            "status: running" in status_output or "active" in status_output
        )

    # Si la VPN no está en ejecución, devolver directamente
    if not is_running:
        return APIResponse(
            success=True,
            message="VPN server is already stopped",
            details={"status": "stopped", "was_running": False},
        )

    # Si está en ejecución, intentar detenerla
    result = run_command(["/app/scripts/openvpn/core/openvpn-stop.sh"])

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to stop VPN server",
                details={"error": result["error"]},
            ).dict(),
        )

    return APIResponse(
        success=True,
        message="VPN server stopped successfully",
        details={"status": "stopped", "was_running": True},
    )


@router.post("/setup", response_model=APIResponse)
async def setup_server(config: SetupConfig) -> APIResponse:
    """Set up the OpenVPN server with the specified configuration.

    :param config: Server configuration parameters
    :type config: SetupConfig
    :return: Result of the operation
    :rtype: APIResponse
    """
    result = run_command(
        [
            "/app/scripts/openvpn/core/openvpn-setup.sh",
            "--red",
            config.red,
            "--mask",
            config.mask,
            "--port",
            config.port,
            "--proto",
            config.proto,
            "--tun",
            config.tun,
            "--ip",
            config.ip,
        ]
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to set up VPN server",
                details={"error": result["error"]},
            ).dict(),
        )

    return APIResponse(
        success=True,
        message="VPN server set up successfully",
        details={"setup_output": result["output"]},
    )


@router.post("/reset", response_model=APIResponse)
async def reset_server() -> APIResponse:
    """Reset the OpenVPN server (restart the service if it's running).

    :return: Result of the operation
    :rtype: APIResponse
    """
    # Primero verificamos el estado de la VPN
    status_result = run_command(["/app/scripts/openvpn/core/openvpn-status.sh"])
    status_output = (
        status_result["output"] if status_result["success"] else "Unknown"
    )

    # Verificamos si la VPN está corriendo
    is_running = False
    if status_result["success"]:
        status_output_lower = status_output.lower()
        is_running = (
            "status: running" in status_output_lower
            or "active" in status_output_lower
        )

    # Ejecutamos el reset
    result = run_command(["/app/scripts/openvpn/core/openvpn-reset.sh"])

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to reset VPN server",
                details={"error": result["error"]},
            ).dict(),
        )

    # Determinamos el mensaje adecuado
    if is_running:
        message = "VPN server has been successfully restarted"
    else:
        message = "VPN server was not running, no restart was necessary"

    return APIResponse(
        success=True,
        message=message,
        details={
            "previous_status": "running" if is_running else "stopped",
            "current_status": "running" if is_running else "stopped",
            "reset_output": result["output"],
        },
    )


@router.post("/cleanup", response_model=APIResponse)
async def cleanup_server() -> APIResponse:
    """Clean up the OpenVPN server configuration.

    This operation stops the server if it's running and removes all certificates,
    keys, clients, and configuration files.

    :return: Result of the operation
    :rtype: APIResponse
    """
    # Primero verificamos el estado de la VPN
    status_result = run_command(["/app/scripts/openvpn/core/openvpn-status.sh"])
    status_output = (
        status_result["output"] if status_result["success"] else "Unknown"
    )

    # Verificamos si la VPN estaba corriendo
    was_running = False
    if status_result["success"]:
        status_output_lower = status_output.lower()
        was_running = (
            "status: running" in status_output_lower
            or "active" in status_output_lower
        )

    # Ejecutamos la limpieza
    result = run_command(["/app/scripts/openvpn/core/openvpn-cleanup.sh"])

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to clean up VPN server",
                details={"error": result["error"]},
            ).dict(),
        )

    return APIResponse(
        success=True,
        message="VPN server has been completely cleaned up",
        details={
            "was_running": was_running,
            "current_status": "stopped",
            "cleanup_output": result["output"],
        },
    )
