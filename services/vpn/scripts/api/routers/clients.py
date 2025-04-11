"""
Client operations router.

This module provides endpoints to manage OpenVPN clients.
"""

import json

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from scripts.api.routers.utils import APIResponse, run_command

# Define router
router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    responses={404: {"description": "Not found"}},
)


class ClientConfig(BaseModel):
    """Client configuration for creating a new VPN client.

    :ivar name: Name of the client
    :ivar ip: IP address for the client
    """

    name: str
    ip: str


@router.get("/", response_model=APIResponse)
async def list_clients() -> APIResponse:
    """List all VPN clients with metadata.

    Returns a dictionary of clients where each key is the client name and the value
    is a dictionary containing metadata about the client:
    - ip_address: The fixed IP assigned to the client
    - creation_date: When the client certificate was created

    :return: Dictionary of VPN clients with metadata
    :rtype: APIResponse

    Example response:
    ```json
    {
      "success": true,
      "message": "Retrieved client list successfully",
      "data": {
        "clients": {
          "client1": {
            "ip_address": "10.10.10.10",
            "creation_date": "2023-04-11 23:36:54"
          },
          "client2": {
            "ip_address": "10.10.10.11",
            "creation_date": "2023-04-12 10:15:30"
          }
        }
      }
    }
    ```
    """
    # Use the new JSON script that provides client metadata
    result = run_command(
        ["/app/scripts/openvpn/client/openvpn-client-list-json.sh"]
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to list VPN clients",
                "details": result["error"],
            },
        )

    # Parse the JSON output from the script
    try:
        clients_data = json.loads(result["output"])
        return APIResponse(
            success=True,
            message="Retrieved client list successfully",
            data=clients_data,
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to parse client list",
                "details": str(e),
            },
        )


@router.post("/", response_model=APIResponse)
async def create_client(client: ClientConfig) -> APIResponse:
    """Create a new VPN client.

    :param client: Client configuration
    :type client: ClientConfig
    :return: Result of the operation
    :rtype: APIResponse
    """
    result = run_command(
        [
            "/app/scripts/openvpn/client/openvpn-client-new.sh",
            "--name",
            client.name,
            "--ip",
            client.ip,
        ]
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to create VPN client",
                "details": result["error"],
            },
        )

    # Get client configuration file
    config_file_path = (
        f"/etc/openvpn/certs/clients/{client.name}/{client.name}.ovpn"
    )
    config_result = run_command(["cat", config_file_path])

    client_config = (
        config_result["output"]
        if config_result["success"]
        else "Config file not found"
    )

    return APIResponse(
        success=True,
        message="Client created successfully",
        data={
            "client_name": client.name,
            "client_ip": client.ip,
            "client_config": client_config,
        },
    )


@router.delete("/{client_name}", response_model=APIResponse)
async def delete_client(client_name: str) -> APIResponse:
    """Delete a VPN client.

    :param client_name: Name of the client to delete
    :type client_name: str
    :return: Result of the operation
    :rtype: APIResponse
    """
    result = run_command(
        [
            "/app/scripts/openvpn/client/openvpn-client-delete.sh",
            client_name,
        ]
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to delete VPN client",
                "details": result["error"],
            },
        )

    return APIResponse(
        success=True, message=f"Client {client_name} deleted successfully"
    )
