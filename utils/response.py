"""
Standard response formatting utilities
"""
from flask import jsonify
from typing import Any, Dict, Optional


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200
) -> tuple:
    """
    Create standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Flask response tuple
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code


def error_response(
    message: str,
    status_code: int = 400,
    error_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> tuple:
    """
    Create standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_type: Type of error
        details: Additional error details
        
    Returns:
        Flask response tuple
    """
    response = {
        'success': False,
        'error': message
    }
    
    if error_type:
        response['error_type'] = error_type
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code