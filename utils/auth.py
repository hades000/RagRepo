import jwt
import os
import inspect
from functools import wraps
from flask import request, g
from utils.response import error_response

JWT_SECRET = os.getenv('JWT_SECRET_KEY')

if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise ValueError('JWT_SECRET_KEY must be at least 32 characters long')

def _verify_token():
    """Helper to validate token and populate g.user_*"""
    auth_header = request.headers.get('Authorization')
    
    # print(f"🔍 Auth Debug:")
    # print(f"   Authorization header: {auth_header[:50] if auth_header else 'None'}...")
    
    if not auth_header or not auth_header.startswith('Bearer '):
        print(f"   ❌ Missing or invalid Authorization header")
        return error_response("Authentication required", 401)
    
    token = auth_header.split(' ')[1] if len(auth_header.split(' ')) > 1 else None
    
    if not token:
        print(f"   ❌ Token extraction failed")
        return error_response("Invalid token format", 401)
    
    # print(f"   Token extracted: {token[:20]}...")
    
    try:
        # Decode JWT token (uses HS256 algorithm like Next.js)
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        
        # Store user info in Flask's g object
        g.user_id = payload.get('id')
        g.user_email = payload.get('email')
        g.user_name = payload.get('name')
        g.user_role = payload.get('role')
        
        # print(f"   ✅ Token valid - User: {g.user_email}")
        
        if not g.user_id:
            return error_response("Invalid token: missing user ID", 401)
            
        return None  # Success
        
    except jwt.ExpiredSignatureError:
        print(f"   ❌ Token expired")
        return error_response("Token expired", 401)
    except jwt.InvalidTokenError as e:
        print(f"   ❌ JWT validation error: {e}")
        return error_response("Invalid token", 401)
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return error_response("Authentication failed", 500)

def require_auth(f):
    """
    Validate JWT token from Authorization header.
    Automatically detects if the wrapped function is async or sync.
    """
    if inspect.iscoroutinefunction(f):
        # Async wrapper for async routes (async def)
        @wraps(f)
        async def async_decorated_function(*args, **kwargs):
            error = _verify_token()
            if error: return error
            return await f(*args, **kwargs)
        return async_decorated_function
    else:
        # Sync wrapper for sync routes (def)
        @wraps(f)
        def sync_decorated_function(*args, **kwargs):
            error = _verify_token()
            if error: return error
            return f(*args, **kwargs)
        return sync_decorated_function

def get_current_user():
    """Get current authenticated user from request context"""
    return {
        'id': getattr(g, 'user_id', None),
        'email': getattr(g, 'user_email', None),
        'name': getattr(g, 'user_name', None),
        'role': getattr(g, 'user_role', None)
    }