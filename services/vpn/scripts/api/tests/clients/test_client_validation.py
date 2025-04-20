"""
Test module for client validation in the API.

This module contains tests to verify proper validation of client creation parameters.
"""

from fastapi import status

from scripts.api.tests.conftest import SimpleTestClient


def test_create_client_missing_name(test_client: SimpleTestClient) -> None:
    """Test creating a client without a name parameter.

    This should return a validation error.
    """
    # When: Making a POST request with missing name
    response = test_client.post("/clients/", json={"ip": "10.10.10.60"})

    # Then: Response should indicate validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # And: Response should indicate failure
    data = response.json()
    assert data["success"] is False
    assert "validation error" in data["message"].lower()

    # Should have details with error information
    assert "details" in data
    assert "errors" in data["details"]

    # Find the error about the missing name field
    errors = data["details"]["errors"]
    assert any("name" in str(error).lower() for error in errors)


def test_create_client_missing_ip(test_client: SimpleTestClient) -> None:
    """Test creating a client without an IP parameter.

    This should return a validation error.
    """
    # When: Making a POST request with missing IP
    response = test_client.post("/clients/", json={"name": "test_missing_ip"})

    # Then: Response should indicate validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # And: Response should indicate failure
    data = response.json()
    assert data["success"] is False
    assert "validation error" in data["message"].lower()

    # Should have details with error information
    assert "details" in data
    assert "errors" in data["details"]

    # Find the error about the missing IP field
    errors = data["details"]["errors"]
    assert any("ip" in str(error).lower() for error in errors)


def test_create_client_invalid_ip(test_client: SimpleTestClient) -> None:
    """Test creating a client with an invalid IP address format.

    This should return a validation error.
    """
    # When: Making a POST request with an invalid IP
    response = test_client.post(
        "/clients/", json={"name": "test_invalid_ip", "ip": "invalid-ip"}
    )

    # Then: Expect a validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # And: Response should indicate failure with a proper JSON response
    try:
        data = response.json()
        assert data["success"] is False
        assert "validation error" in data["message"].lower()

        # Should have details with error information
        assert "details" in data
        assert "errors" in data["details"]

        # Verify that the error mentions the IP field
        errors = data["details"]["errors"]
        ip_error_found = False
        for error in errors:
            if "ip" in str(error).lower():
                ip_error_found = True
                break

        assert ip_error_found, "No error about invalid IP found"

    except Exception as e:
        # If there's a problem parsing the JSON response, fail the test
        assert False, f"Invalid JSON response: {e}"


def test_create_client_empty_name(test_client: SimpleTestClient) -> None:
    """Test creating a client with an empty name.

    This should return a validation error or a server error.
    """
    # When: Making a POST request with an empty name
    response = test_client.post(
        "/clients/", json={"name": "", "ip": "10.10.10.70"}
    )

    # Then: Expect either a validation error or a server error
    assert response.status_code in (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    # And: Response should indicate failure
    data = response.json()
    assert data["success"] is False


def test_create_client_extra_fields(test_client: SimpleTestClient) -> None:
    """Test creating a client with additional unexpected fields.

    This should return a validation error as we've configured the model to forbid extra fields.
    """
    # When: Making a POST request with additional field
    response = test_client.post(
        "/clients/",
        json={
            "name": "test_extra_fields",
            "ip": "10.10.10.80",
            "invalid_field": "test",
        },
    )

    # Then: Response should indicate validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # And: Response should indicate failure
    data = response.json()
    assert data["success"] is False
    assert "validation error" in data["message"].lower()

    # Should have details with error information
    assert "details" in data
    assert "errors" in data["details"]

    # Check if there are validation errors related to unexpected fields
    # This can be mentioned in different ways depending on the Pydantic version
    errors = data["details"]["errors"]
    unexpected_field_found = False
    for error in errors:
        error_str = str(error).lower()
        if any(term in error_str for term in ["extra", "additional", "unexpected", "invalid_field", "forbidden"]):
            unexpected_field_found = True
            break

    assert unexpected_field_found, "No error about unexpected fields found"
