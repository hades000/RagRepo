"""
Standard response formatting utilities
"""
from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200
):
    """
    Create standardized success response.

    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code

    Returns:
        Dict for 200, JSONResponse for other status codes
    """
    response = {
        'success': True,
        'message': message
    }

    if data is not None:
        response['data'] = data

    if status_code == 200:
        return response
    return JSONResponse(content=response, status_code=status_code)


def error_response(
    message: str,
    status_code: int = 400,
    error_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    Create standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code
        error_type: Type of error
        details: Additional error details

    Returns:
        JSONResponse with error payload
    """
    response = {
        'success': False,
        'error': message
    }

    if error_type:
        response['error_type'] = error_type

    if details:
        response['details'] = details

    return JSONResponse(content=response, status_code=status_code)
