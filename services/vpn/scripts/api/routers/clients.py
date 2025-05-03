"""
Client operations router.

This module provides endpoints to manage OpenVPN clients.
"""

import json
import re

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, field_validator

from scripts.api.routers.utils import APIResponse, ErrorResponse, run_command

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

    model_config = {
        "extra": "forbid"  # Reject additional fields not defined in the model
    }

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Validate that the IP field contains a valid IPv4 address."""
        ip_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
        if not ip_pattern.match(v):
            raise ValueError("Invalid IP address format")

        # Check that each octet is between 0 and 255
        octets = v.split(".")
        for octet in octets:
            num = int(octet)
            if num < 0 or num > 255:
                raise ValueError("IP address octets must be between 0 and 255")

        return v


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
      "details": {
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
            detail=ErrorResponse(
                success=False,
                message="Failed to list VPN clients",
                details={"error": result["error"]},
            ).dict(),
        )

    # Parse the JSON output from the script
    try:
        clients_data = json.loads(result["output"])
        return APIResponse(
            success=True,
            message="Retrieved client list successfully",
            details=clients_data,
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to parse client list",
                details={"error": str(e)},
            ).dict(),
        )


@router.post("/", response_model=APIResponse)
async def create_client(client: ClientConfig) -> APIResponse:
    """Create a new VPN client.

    :param client: Client configuration
    :type client: ClientConfig
    :return: Result of the operation
    :rtype: APIResponse
    """
    # First verify that PKI is properly initialized
    pki_verification = run_command(
        ["/app/scripts/openvpn/client/openvpn-client-verify-pki.sh"]
    )

    if not pki_verification["success"]:
        # Extract meaningful error message from output if possible
        error_message = "PKI verification failed. "
        if "Error: " in pki_verification["output"]:
            for line in pki_verification["output"].split("\n"):
                if line.startswith("Error:"):
                    error_message += line
                    break

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Changed to 400 to indicate client error
            detail=ErrorResponse(
                success=False,
                message="Server not properly configured for client creation",
                details={
                    "error": error_message,
                    "resolution": "Run server setup and start the server before creating clients",
                    "sequence": [
                        "1. POST /server/setup - Configure the server",
                        "2. POST /server/start - Start the server",
                        "3. POST /clients/ - Create clients"
                    ]
                },
            ).dict(),
        )

    # If PKI verification passed, proceed with client creation
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
            detail=ErrorResponse(
                success=False,
                message="Failed to create VPN client",
                details={"error": result["error"]},
            ).dict(),
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
        details={
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
            detail=ErrorResponse(
                success=False,
                message="Failed to delete VPN client",
                details={"error": result["error"]},
            ).dict(),
        )

    return APIResponse(
        success=True, message=f"Client {client_name} deleted successfully"
    )
