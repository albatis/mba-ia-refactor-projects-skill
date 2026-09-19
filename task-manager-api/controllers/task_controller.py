import logging

from flask import jsonify, request
from sqlalchemy.orm import joinedload

from database import db
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User
from services.notification_service import NotificationService
from utils.helpers import process_task_data, utcnow

logger = logging.getLogger(__name__)
notification_service = NotificationService()


def _get_task_or_404(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def get_tasks():
    # joinedload evita N+1: antes buscava usuário/categoria com uma query
    # por task, dentro do loop.
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    result = []
    for t in tasks:
        data = t.to_dict()
        data['user_name'] = t.user.name if t.user else None
        data['category_name'] = t.category.name if t.category else None
        result.append(data)
    return jsonify(result), 200


def get_task(task_id):
    return jsonify(_get_task_or_404(task_id).to_dict()), 200


def create_task():
    data = request.get_json()
    if not data:
        raise ValidationError('Dados inválidos')
    if not data.get('title'):
        raise ValidationError('Título é obrigatório')

    validated, error = process_task_data(data)
    if error:
        raise ValidationError(error)

    user_id = data.get('user_id')
    category_id = data.get('category_id')

    if user_id and not User.query.get(user_id):
        raise NotFoundError('Usuário não encontrado')

    if category_id and not Category.query.get(category_id):
        raise NotFoundError('Categoria não encontrada')

    task = Task(
        title=validated['title'],
        description=validated.get('description', ''),
        status=validated.get('status', 'pending'),
        priority=validated.get('priority', 3),
        user_id=user_id,
        category_id=category_id,
        due_date=validated.get('due_date'),
        tags=validated.get('tags'),
    )

    db.session.add(task)
    db.session.commit()

    logger.info("Task criada: %s - %s", task.id, task.title)

    if task.user:
        notification_service.notify_task_assigned(task.user, task)

    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = _get_task_or_404(task_id)

    data = request.get_json()
    if not data:
        raise ValidationError('Dados inválidos')

    validated, error = process_task_data(data, existing_task=task)
    if error:
        raise ValidationError(error)

    if 'user_id' in data:
        if data['user_id'] and not User.query.get(data['user_id']):
            raise NotFoundError('Usuário não encontrado')
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not Category.query.get(data['category_id']):
            raise NotFoundError('Categoria não encontrada')
        task.category_id = data['category_id']

    for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
        if field in validated:
            setattr(task, field, validated[field])

    task.updated_at = utcnow()
    db.session.commit()

    logger.info("Task atualizada: %s", task.id)
    return jsonify(task.to_dict()), 200


def delete_task(task_id):
    task = _get_task_or_404(task_id)

    db.session.delete(task)
    db.session.commit()

    logger.info("Task deletada: %s", task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def _int_arg(name):
    """Lê um filtro numérico da query string; ausente vira None, inválido vira 400."""
    raw = request.args.get(name, '')
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as err:
        raise ValidationError(f'Parâmetro "{name}" deve ser um número inteiro') from err


def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = _int_arg('priority')
    user_id = _int_arg('user_id')

    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority is not None:
        tasks = tasks.filter(Task.priority == priority)

    if user_id is not None:
        tasks = tasks.filter(Task.user_id == user_id)

    return jsonify([t.to_dict() for t in tasks.all()]), 200


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

    stats = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }

    return jsonify(stats), 200
