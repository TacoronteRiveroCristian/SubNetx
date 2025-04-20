"""
Test module for API error handling.

This module contains tests to verify proper handling of HTTP error conditions.
"""

from fastapi import status

from scripts.api.tests.conftest import SimpleTestClient


def test_nonexistent_endpoint(test_client: SimpleTestClient) -> None:
    """Test that a request to a non-existent endpoint returns 404.

    This verifies that the API correctly handles invalid routes.
    """
    # When: Making a GET request to a non-existent endpoint
    response = test_client.get("/nonexistent-endpoint")

    # Then: Response should be 404 Not Found
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # And: Response body should follow the standard error format
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["message"].lower()


def test_wrong_http_method(test_client: SimpleTestClient) -> None:
    """Test using an invalid HTTP method on an existing endpoint.

    This verifies that the API responds appropriately when the wrong HTTP method is used.
    """
    # When: Making a POST request to an endpoint that only accepts GET
    response = test_client.post("/server/status")

    # Then: Response should be 405 Method Not Allowed
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # And: Response body should follow the standard error format
    data = response.json()
    assert data["success"] is False
    assert "method not allowed" in data["message"].lower()


def test_invalid_json_format(test_client: SimpleTestClient) -> None:
    """Test sending JSON with extra fields to an endpoint.

    Tests that the API rejects requests with fields not defined in the model.
    """
    # When: Making a POST request with extra fields to the clients endpoint
    response = test_client.post(
        "/clients/",
        json={
            "name": "test",
            "ip": "10.10.10.10",
            "invalid_field": "test",  # Extra field that should be rejected
        },
    )

    # Then: Response should indicate validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # And: Response should indicate failure
    data = response.json()
    assert data["success"] is False
    assert "validation error" in data["message"].lower()

    # Should contain information about the validation error
    assert "details" in data
    assert "errors" in data["details"]

    # Check if there are validation errors related to unexpected fields
    # This can be mentioned in different ways depending on the Pydantic version
    errors = data["details"]["errors"]
    unexpected_field_found = False
    for error in errors:
        error_str = str(error).lower()
        if any(
            term in error_str
            for term in [
                "extra",
                "additional",
                "unexpected",
                "invalid_json",
                "forbidden",
            ]
        ):
            unexpected_field_found = True
            break

    assert unexpected_field_found, "No error about unexpected fields found"
