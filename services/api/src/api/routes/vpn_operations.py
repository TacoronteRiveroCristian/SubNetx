from typing import Dict, Optional, Any

import os
import requests
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# Models for request bodies
class ClientCreate(BaseModel):
    name: str
    ip: str

# Initialize router
router = APIRouter(tags=["vpn"])

# Get VPN API URL from environment variables or use default
VPN_API_HOST = os.getenv("VPN_API_HOST", "subnetx_vpn")
VPN_API_PORT = os.getenv("VPN_API_PORT", "9000")
VPN_API_URL = f"http://{VPN_API_HOST}:{VPN_API_PORT}"

def call_vpn_api(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """Call the VPN API and return the response"""
    try:
        url = f"{VPN_API_URL}{endpoint}"

        if method.lower() == "get":
            response = requests.get(url, timeout=10)
        elif method.lower() == "post":
            response = requests.post(url, json=data, timeout=10)
        elif method.lower() == "delete":
            response = requests.delete(url, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")

        # Raise exception for HTTP errors
        response.raise_for_status()

        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error communicating with VPN API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling VPN API: {str(e)}"
        )

@router.get("/vpn/status")
async def vpn_status() -> Dict:
    """
    Get the status of the OpenVPN server

    Returns:
        Dict: Status information of the OpenVPN server
    """
    result = call_vpn_api("get", "/status")

    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get VPN status: {result.get('error', 'Unknown error')}"
        )

    return {
        "status": "Running",
        "details": result.get("data", {}).get("status_output", "No status available")
    }

@router.post("/vpn/start")
async def start_vpn() -> Dict:
    """
    Start the OpenVPN server

    Returns:
        Dict: Result of the operation
    """
    result = call_vpn_api("post", "/start")

    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start VPN server: {result.get('error', 'Unknown error')}"
        )

    return {"message": "VPN server started successfully"}

@router.post("/vpn/stop")
async def stop_vpn() -> Dict:
    """
    Stop the OpenVPN server

    Returns:
        Dict: Result of the operation
    """
    result = call_vpn_api("post", "/stop")

    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop VPN server: {result.get('error', 'Unknown error')}"
        )

    return {"message": "VPN server stopped successfully"}

@router.get("/vpn/clients")
async def list_clients() -> Dict:
    """
    List all VPN clients

    Returns:
        Dict: List of clients
    """
    result = call_vpn_api("get", "/clients")

    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list clients: {result.get('error', 'Unknown error')}"
        )

    return {"clients": result.get("data", {}).get("clients", [])}

@router.post("/vpn/clients")
async def create_client(client: ClientCreate) -> Dict:
    """
    Create a new VPN client

    Args:
        client: Client information

    Returns:
        Dict: Result of the operation
    """
    result = call_vpn_api("post", "/clients", data={"name": client.name, "ip": client.ip})

    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {result.get('error', 'Unknown error')}"
        )

    return {
        "message": "Client created successfully",
        "client_config": result.get("data", {}).get("client_config", "Config not available")
    }

@router.delete("/vpn/clients/{client_name}")
async def delete_client(client_name: str) -> Dict:
    """
    Delete a VPN client

    Args:
        client_name: Name of the client to delete

    Returns:
        Dict: Result of the operation
    """
    result = call_vpn_api("delete", f"/clients/{client_name}")

    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete client: {result.get('error', 'Unknown error')}"
        )

    return {"message": f"Client {client_name} deleted successfully"}
