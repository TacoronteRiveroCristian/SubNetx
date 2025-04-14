"""
Test module for server setup endpoint with incremental configurations.

This module tests how the server API handles configurations with progressive
amounts of parameters, from empty to complete.
"""

from typing import Any, Generator

import pytest
from fastapi import status

from scripts.api.tests.conftest import SimpleTestClient


@pytest.fixture
def incremental_configs() -> list:
    """Return a list of configurations with progressively more parameters."""
    return [
        # Empty configuration
        {},
        # Only IP
        {"ip": "localhost"},
        # IP and Mask
        {"ip": "localhost", "mask": "255.255.255.0"},
        # IP, Mask, and Port
        {"ip": "localhost", "mask": "255.255.255.0", "port": "1194"},
        # IP, Mask, Port, and Protocol
        {
            "ip": "localhost",
            "mask": "255.255.255.0",
            "port": "1194",
            "proto": "udp",
        },
        # IP, Mask, Port, Protocol, and TUN
        {
            "ip": "localhost",
            "mask": "255.255.255.0",
            "port": "1194",
            "proto": "udp",
            "tun": "tun0",
        },
        # Complete configuration
        {
            "ip": "localhost",
            "mask": "255.255.255.0",
            "port": "1194",
            "proto": "udp",
            "tun": "tun0",
            "red": "10.10.10.0",
        },
    ]


@pytest.fixture(scope="module", autouse=True)
def cleanup_before_and_after() -> Generator[None, Any, None]:
    """Ensure the server is in a clean state before and after the tests."""
    # Create a test client locally
    client = SimpleTestClient(f"http://0.0.0.0:{9001}")

    # Clean up before running tests
    client.post("/server/cleanup")

    # Allow tests to run
    yield

    # Clean up after running tests
    client.post("/server/cleanup")


@pytest.mark.parametrize("config_index", range(7))
def test_setup_with_incremental_config(
    test_client: SimpleTestClient, incremental_configs: list, config_index: int
) -> None:
    """Test server setup with progressively more parameters.

    This test checks how the API handles configurations with different amounts
    of parameters, from an empty dict to a complete configuration.

    Args:
        test_client: The test client to use
        incremental_configs: List of configs with progressively more parameters
        config_index: Index of the configuration to test
    """
    # Get the configuration for this test
    config = incremental_configs[config_index]

    # When: Making a POST request to setup endpoint with this config
    response = test_client.post("/server/setup", json=config)

    # Then: Check response and log result
    data = response.json()

    # Log details for analysis
    params_provided = len(config)
    params_names = ", ".join(config.keys()) if config else "none"
    status_code = response.status_code

    # For analysis purposes, we check both success and failure cases
    if data["success"]:
        print(
            f"Config {config_index} with {params_provided} params ({params_names}) "
            f"succeeded with status {status_code}"
        )
        assert "set up successfully" in data["message"].lower()
    else:
        print(
            f"Config {config_index} with {params_provided} params ({params_names}) "
            f"failed with status {status_code}"
        )
        assert "failed" in data["message"].lower()

    # Always verify a valid response was received (either success or proper error)
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ]


def test_complete_server_lifecycle_after_tests(
    test_client: SimpleTestClient,
) -> None:
    """Run a quick server lifecycle test to ensure everything works after the tests."""
    # Setup with a complete configuration
    complete_config = {
        "ip": "localhost",
        "mask": "255.255.255.0",
        "port": "1194",
        "proto": "udp",
        "tun": "tun0",
        "red": "10.10.10.0",
    }

    # Setup
    response = test_client.post("/server/setup", json=complete_config)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True

    # Start
    response = test_client.post("/server/start")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True

    # Status (ensure it's running)
    response = test_client.get("/server/status")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["details"]["status"]["is_active"] is True

    # Clean up after ourselves
    response = test_client.post("/server/cleanup")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True
