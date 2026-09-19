import logging

from flask import jsonify, request

from database import db
from middlewares.auth import generate_token, get_current_user_from_request
from middlewares.error_handler import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from models.task import Task
from models.user import User
from utils.helpers import VALID_ROLES, validate_email

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 4


def _get_user_or_404(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def _validate_email_format(email):
    if not validate_email(email):
        raise ValidationError('Email inválido')


def _ensure_email_available(email, current_user_id=None):
    existing = User.query.filter_by(email=email).first()
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def get_users():
    result = []
    for u in User.query.all():
        user_data = u.to_dict()
        user_data['task_count'] = len(u.tasks)
        result.append(user_data)
    return jsonify(result), 200


def get_user(user_id):
    user = _get_user_or_404(user_id)

    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]

    return jsonify(data), 200


def create_user():
    data = request.get_json()
    if not data:
        raise ValidationError('Dados inválidos')

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')

    _validate_email_format(email)

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')

    _ensure_email_available(email)

    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    db.session.add(user)
    db.session.commit()

    logger.info("Usuário criado: %s - %s", user.id, user.name)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = _get_user_or_404(user_id)

    data = request.get_json()
    if not data:
        raise ValidationError('Dados inválidos')

    # Trocar role/active é uma ação administrativa: exige token de admin válido.
    if 'role' in data or 'active' in data:
        requester = get_current_user_from_request()
        if not requester or not requester.is_admin():
            raise ForbiddenError('Requer privilégio de administrador para alterar role/active')

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        _validate_email_format(data['email'])
        _ensure_email_available(data['email'], current_user_id=user_id)
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            raise ValidationError('Role inválido')
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    db.session.commit()

    logger.info("Usuário atualizado: %s", user.id)
    return jsonify(user.to_dict()), 200


def delete_user(user_id):
    user = _get_user_or_404(user_id)

    for t in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(t)

    db.session.delete(user)
    db.session.commit()

    logger.info("Usuário deletado: %s", user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    _get_user_or_404(user_id)

    result = []
    for t in Task.query.filter_by(user_id=user_id).all():
        result.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'created_at': str(t.created_at),
            'due_date': str(t.due_date) if t.due_date else None,
            'overdue': t.is_overdue(),
        })

    return jsonify(result), 200


def login():
    data = request.get_json()
    if not data:
        raise ValidationError('Dados inválidos')

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')

    if not user.active:
        raise ForbiddenError('Usuário inativo')

    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': generate_token(user.id)
    }), 200
