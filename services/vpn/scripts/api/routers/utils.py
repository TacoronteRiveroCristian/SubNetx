"""
Utility functions for API routers.

This module provides common utility functions used across different routers.
"""

import subprocess
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class APIResponse(BaseModel):
    """API response model for operations.

    :ivar success: Indicates if the operation was successful
    :ivar message: Message describing the result of the operation
    :ivar data: Optional data returned by the operation
    """

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response model.

    :ivar success: Always False for error responses
    :ivar error: Error message
    :ivar details: Optional details about the error
    """

    success: bool = False
    error: str
    details: Optional[str] = None


def run_command(command: List[str]) -> Dict[str, Any]:
    """Run a shell command and return the result.

    :param command: The command to run as a list of strings
    :type command: List[str]
    :return: Dictionary containing the result of the command execution
    :rtype: Dict[str, Any]
    """
    try:
        result = subprocess.run(
            command, check=False, capture_output=True, text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "exit_code": result.returncode,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "exit_code": -1,
        }
