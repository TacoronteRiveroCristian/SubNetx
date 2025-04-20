"""
Test module for the client operations endpoints.

This module contains tests for the client-related endpoints following the correct
operational sequence: list -> create -> list -> delete -> list.
"""

import pytest
from fastapi import status

from scripts.api.tests.conftest import SimpleTestClient


@pytest.fixture(scope="module")
def client_test_sequence() -> list:
    """Define the test execution sequence to ensure proper client lifecycle."""
    return [
        "list",
        "create",
        "list_after_create",
        "delete",
        "list_after_delete",
    ]


@pytest.fixture(scope="module")
def test_client_config() -> dict:
    """Return a test client configuration."""
    return {"name": "test_client", "ip": "10.10.10.50"}


def test_initial_client_list(test_client: SimpleTestClient) -> None:
    """Test listing clients when none have been created yet (or after cleanup).

    This should return an empty list or existing clients if any.
    """
    # When: Making a GET request to list clients endpoint
    response = test_client.get("/clients/")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response body should indicate success
    data = response.json()
    assert data["success"] is True
    assert "retrieved client list" in data["message"].lower()

    # Details should contain a clients dictionary (which might be empty)
    assert "details" in data
    assert isinstance(data["details"], dict)


def test_create_client(
    test_client: SimpleTestClient, test_client_config: dict
) -> None:
    """Test creating a new VPN client."""
    # When: Making a POST request to create a client
    response = test_client.post("/clients/", json=test_client_config)

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should indicate success
    data = response.json()
    assert data["success"] is True
    assert "created successfully" in data["message"].lower()

    # Should contain client details
    assert data["details"]["client_name"] == test_client_config["name"]
    assert data["details"]["client_ip"] == test_client_config["ip"]
    assert "client_config" in data["details"]

    # Client config should be a non-empty string containing OpenVPN configuration
    assert isinstance(data["details"]["client_config"], str)
    assert len(data["details"]["client_config"]) > 0
    assert "openvpn" in data["details"]["client_config"].lower()


def test_client_list_after_create(
    test_client: SimpleTestClient, test_client_config: dict
) -> None:
    """Test listing clients after creating one.

    The newly created client should be present in the list.
    """
    # When: Making a GET request to list clients endpoint
    response = test_client.get("/clients/")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response body should indicate success
    data = response.json()
    assert data["success"] is True
    assert "retrieved client list" in data["message"].lower()

    # The client we created should be in the list
    assert "details" in data
    assert "clients" in data["details"]

    # Find our test client
    clients = data["details"]["clients"]
    assert test_client_config["name"] in clients

    # Check client properties
    client_data = clients[test_client_config["name"]]
    assert "ip_address" in client_data
    assert client_data["ip_address"] == test_client_config["ip"]
    assert "creation_date" in client_data


def test_delete_client(
    test_client: SimpleTestClient, test_client_config: dict
) -> None:
    """Test deleting a client."""
    # When: Making a POST request to delete the client
    response = test_client.post(f"/clients/{test_client_config['name']}")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should indicate success
    data = response.json()
    assert data["success"] is True
    assert "deleted successfully" in data["message"].lower()
    assert test_client_config["name"] in data["message"]


def test_client_list_after_delete(
    test_client: SimpleTestClient, test_client_config: dict
) -> None:
    """Test listing clients after deleting one.

    The deleted client should no longer be present in the list.
    """
    # When: Making a GET request to list clients endpoint
    response = test_client.get("/clients/")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response body should indicate success
    data = response.json()
    assert data["success"] is True

    # Our deleted client should not be in the list
    clients = data["details"].get("clients", {})
    assert test_client_config["name"] not in clients


def test_delete_nonexistent_client(test_client: SimpleTestClient) -> None:
    """Test deleting a client that doesn't exist.

    This should return an error.
    """
    # When: Making a POST request to delete a non-existent client
    response = test_client.post("/clients/nonexistent_client")

    # Then: Response should indicate an error
    # It could be a 404 or 500 depending on implementation
    assert response.status_code in (
        status.HTTP_404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    # And: Response should indicate failure
    data = response.json()
    assert data["success"] is False
    assert (
        "failed" in data["message"].lower()
        or "not found" in data["message"].lower()
    )
