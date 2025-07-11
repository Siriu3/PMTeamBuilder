from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def admin_required(fn):
    """
    JWT decorator that verifies a JWT is present and the user is an admin.
    The JWT must contain the 'is_admin: True' claim.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('is_admin', False) is True:
            return fn(*args, **kwargs)
        else:
            return jsonify({"msg": "Admins only!"}), 403
    return wrapper

# Add other decorators here if needed 