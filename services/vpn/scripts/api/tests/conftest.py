"""
Configuration for pytest test suite.

This module contains fixtures and configurations used across test modules.
"""

import os
import threading
import time
from typing import Any, Dict, Generator, Optional

import pytest
import requests  # type: ignore
import uvicorn

from scripts.api.main import app

# Default test configuration
TEST_PORT = int(os.getenv("VPN_API_PORT", "9000")) + 1
TEST_HOST = os.getenv("VPN_API_HOST", "0.0.0.0")

# Timeout for requests
TIMEOUT = 120.0


class SimpleTestClient:
    """A simple test client that sends real HTTP requests to a running server."""

    def __init__(self, base_url: str) -> None:
        """Initialize the test client with a base URL."""
        self.base_url = base_url

    def get(self, path: str) -> requests.Response:
        """Send a GET request to the specified path."""
        response = requests.get(f"{self.base_url}{path}", timeout=TIMEOUT)
        return response

    def post(
        self, path: str, json: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Send a POST request to the specified path."""
        response = requests.post(
            f"{self.base_url}{path}", json=json, timeout=TIMEOUT
        )
        return response


@pytest.fixture(scope="session")
def api_version() -> str:
    """Return the expected API version."""
    return str(app.version)


@pytest.fixture(scope="session")
def test_server() -> Generator[str, None, None]:
    """Start a test server in a separate thread."""
    # Override environment for test
    os.environ["VPN_API_PORT"] = str(TEST_PORT)
    os.environ["VPN_API_HOST"] = TEST_HOST

    # Create and start the server in a separate thread
    server_thread = threading.Thread(
        target=uvicorn.run,
        args=("scripts.api.main:app",),
        kwargs={
            "host": TEST_HOST,
            "port": TEST_PORT,
            "log_level": "error",
        },
        daemon=True,
    )
    server_thread.start()

    # Wait for the server to start
    time.sleep(1)

    # Return the base URL for the test server
    yield f"http://{TEST_HOST}:{TEST_PORT}"


@pytest.fixture(scope="session")
def test_client(test_server: str) -> SimpleTestClient:
    """Return a test client for the application."""
    return SimpleTestClient(test_server)


@pytest.fixture(scope="session")
def test_base_url() -> str:
    """Return the base URL for API tests."""
    return f"http://{TEST_HOST}:{TEST_PORT}"
