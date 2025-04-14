"""
Test module for the root endpoint of the API.

This module contains tests for the root endpoint functionality.
"""

from fastapi import status

from scripts.api.routers.utils import APIResponse
from scripts.api.tests.conftest import SimpleTestClient


def test_root_endpoint(test_client: SimpleTestClient, api_version: str) -> None:
    """Test that the root endpoint returns expected status and data.

    Verifies:
    - Status code 200
    - Success flag is True
    - Message contains expected text
    - Version information is returned in details
    """
    # When: Making a GET request to the root endpoint
    response = test_client.get("/")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response body should match expected format and values
    data = response.json()

    # Check response structure matches APIResponse model
    assert "success" in data
    assert "message" in data
    assert "details" in data

    # Verify success is True
    assert data["success"] is True

    # Verify message contains expected text
    assert "API is running" in data["message"]

    # Verify details contains version information
    assert "details" in data and data["details"] is not None
    assert "version" in data["details"]
    assert data["details"]["version"] == api_version


def test_root_endpoint_model_validation(test_client: SimpleTestClient) -> None:
    """Test that the root endpoint response conforms to APIResponse model.

    Verifies the returned JSON can be parsed as an APIResponse object.
    """
    # When: Making a GET request to the root endpoint
    response = test_client.get("/")

    # Then: Response should be successful
    assert response.status_code == status.HTTP_200_OK

    # And: Response should validate against APIResponse model
    response_data = response.json()
    api_response = APIResponse(**response_data)

    # Verify model validation worked
    assert api_response.success is True
    assert "API is running" in api_response.message
    assert api_response.details is not None
    assert isinstance(api_response.details, dict)
    assert "version" in api_response.details.keys()
