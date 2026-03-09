"""
Authentication utilities.

The primary auth dependency is in api/deps.py (get_current_user).
This module re-exports it for backward compatibility.
"""
from api.deps import get_current_user

__all__ = ['get_current_user']
