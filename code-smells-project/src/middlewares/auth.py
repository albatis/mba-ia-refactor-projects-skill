from functools import wraps

from flask import request

from src.config.settings import ADMIN_API_KEY
from src.middlewares.error_handler import UnauthorizedError


def require_admin_key(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-Admin-Key")
        if key != ADMIN_API_KEY:
            raise UnauthorizedError("Chave de administrador inválida ou ausente")
        return view(*args, **kwargs)

    return wrapper
