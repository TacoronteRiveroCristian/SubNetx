"""
Test module for the server operations endpoints.

This module contains tests for the server endpoints following the correct
operational sequence: cleanup -> setup -> start -> stop/reset.
"""

import pytest
from fastapi import status

from scripts.api.tests.conftest import SimpleTestClient


@pytest.fixture(scope="module")
def server_test_sequence() -> list:
    """Define the test execution sequence to ensure proper server lifecycle."""
    return ["cleanup", "setup", "start", "status", "reset", "stop", "cleanup"]


def test_cleanup_before_setup(test_client: SimpleTestClient) -> None:
    """Test cleanup endpoint to ensure a clean state before setup.

    This should be run first to ensure we start from a clean state.
    """
    # When: Making a POST request to cleanup endpoint
    response = test_client.post("/server/cleanup")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response body should indicate success
    data = response.json()
    assert data["success"] is True
    assert "cleaned up" in data["message"].lower()

    # The server should be in stopped state
    assert data["details"]["current_status"] == "stopped"


def test_server_setup(test_client: SimpleTestClient) -> None:
    """Test server setup with default configuration."""
    # Setup default configuration
    config = {
        "red": "10.10.10.0",
        "mask": "255.255.255.0",
        "port": "1194",
        "proto": "udp",
        "tun": "tun0",
        "ip": "localhost",
    }

    # When: Making a POST request to setup endpoint with config
    response = test_client.post("/server/setup", json=config)

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should indicate success
    data = response.json()
    assert data["success"] is True
    assert "set up successfully" in data["message"].lower()

    # Should have setup output
    assert "setup_output" in data["details"]


def test_server_start(test_client: SimpleTestClient) -> None:
    """Test starting the server after setup."""
    # When: Making a POST request to start endpoint
    response = test_client.post("/server/start")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should indicate success
    data = response.json()
    assert data["success"] is True
    assert "started successfully" in data["message"].lower()


def test_server_status_after_start(test_client: SimpleTestClient) -> None:
    """Test server status endpoint after starting the server."""
    # When: Making a GET request to status endpoint
    response = test_client.get("/server/status")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should indicate the server is running
    data = response.json()
    assert data["success"] is True
    assert "status retrieved successfully" in data["message"].lower()

    # The server should be in running state
    assert data["details"]["status"]["state"] == "running"
    assert data["details"]["status"]["is_active"] is True


def test_server_reset(test_client: SimpleTestClient) -> None:
    """Test resetting the server while it's running."""
    # When: Making a POST request to reset endpoint
    response = test_client.post("/server/reset")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should indicate success
    data = response.json()
    assert data["success"] is True
    assert "restarted" in data["message"].lower()

    # Should have been running before
    assert data["details"]["previous_status"] == "running"

    # Should still be running after reset
    assert data["details"]["current_status"] == "running"


def test_server_stop(test_client: SimpleTestClient) -> None:
    """Test stopping the server."""
    # When: Making a POST request to stop endpoint
    response = test_client.post("/server/stop")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should indicate success
    data = response.json()
    assert data["success"] is True
    assert "stopped successfully" in data["message"].lower()

    # Should indicate the server was running and now stopped
    assert data["details"]["status"] == "stopped"
    assert data["details"]["was_running"] is True


def test_server_status_after_stop(test_client: SimpleTestClient) -> None:
    """Test server status after stopping it."""
    # When: Making a GET request to status endpoint
    response = test_client.get("/server/status")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should indicate the server is stopped
    data = response.json()
    assert data["success"] is True

    # The server should be in stopped state
    assert data["details"]["status"]["state"] == "stopped"
    assert data["details"]["status"]["is_active"] is False


def test_stop_already_stopped_server(test_client: SimpleTestClient) -> None:
    """Test stopping a server that's already stopped."""
    # When: Making a POST request to stop endpoint when server is already stopped
    response = test_client.post("/server/stop")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should indicate the server was already stopped
    data = response.json()
    assert data["success"] is True
    assert "already stopped" in data["message"].lower()
    assert data["details"]["was_running"] is False


def test_final_cleanup(test_client: SimpleTestClient) -> None:
    """Test final cleanup to return to a clean state."""
    # When: Making a POST request to cleanup endpoint
    response = test_client.post("/server/cleanup")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response body should indicate success
    data = response.json()
    assert data["success"] is True
    assert "cleaned up" in data["message"].lower()

    # The server should be in stopped state
    assert data["details"]["current_status"] == "stopped"
    # The server should NOT have been running before (we stopped it)
    assert data["details"]["was_running"] is False
