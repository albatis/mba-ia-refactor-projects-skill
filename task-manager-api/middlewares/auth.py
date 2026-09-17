from functools import wraps

from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config.settings import TOKEN_MAX_AGE_SECONDS
from models.user import User


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='auth-token')


def generate_token(user_id):
    return _serializer().dumps({'user_id': user_id})


def _load_user_from_token(token):
    try:
        data = _serializer().loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return User.query.get(data.get('user_id'))


def get_current_user_from_request():
    """Retorna o usuário autenticado pelo header Authorization: Bearer <token>, ou None."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    user = _load_user_from_token(auth_header[len('Bearer '):])
    return user if user and user.active else None


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = get_current_user_from_request()
        if not user:
            return jsonify({'error': 'Token de autenticação ausente, inválido ou expirado'}), 401

        g.current_user = user
        return view(*args, **kwargs)

    return wrapper


def require_admin(view):
    @wraps(view)
    @require_auth
    def wrapper(*args, **kwargs):
        if not g.current_user.is_admin():
            return jsonify({'error': 'Requer privilégio de administrador'}), 403
        return view(*args, **kwargs)

    return wrapper
