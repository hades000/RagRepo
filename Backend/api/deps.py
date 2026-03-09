"""
Shared FastAPI dependencies for authentication and service injection.
"""
import os
import jwt
from fastapi import HTTPException, Request

JWT_SECRET = os.getenv('JWT_SECRET_KEY')

if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise ValueError('JWT_SECRET_KEY must be at least 32 characters long')


async def get_current_user(request: Request) -> dict:
    """
    FastAPI dependency that extracts and validates JWT from Authorization header.
    Replaces Flask's @require_auth decorator + g object.

    Returns dict with keys: id, email, name, role
    Raises HTTPException(401) on failure.
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header.split(' ', 1)[1] if ' ' in auth_header else None

    if not token:
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

        user = {
            'id': payload.get('id'),
            'email': payload.get('email'),
            'name': payload.get('name'),
            'role': payload.get('role'),
        }

        if not user['id']:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Authentication failed")
