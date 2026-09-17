import logging

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services.notification_service import NotificationService
from utils.helpers import process_task_data, utcnow

task_bp = Blueprint('tasks', __name__)
logger = logging.getLogger(__name__)
notification_service = NotificationService()


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
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
    except SQLAlchemyError:
        logger.exception("Erro ao listar tasks")
        return jsonify({'error': 'Erro interno'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(task.to_dict()), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    if not data.get('title'):
        return jsonify({'error': 'Título é obrigatório'}), 400

    validated, error = process_task_data(data)
    if error:
        return jsonify({'error': error}), 400

    user_id = data.get('user_id')
    category_id = data.get('category_id')

    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

    if category_id:
        cat = Category.query.get(category_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

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

    try:
        db.session.add(task)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Erro ao criar task")
        return jsonify({'error': 'Erro ao criar task'}), 500

    logger.info("Task criada: %s - %s", task.id, task.title)

    if task.user:
        notification_service.notify_task_assigned(task.user, task)

    return jsonify(task.to_dict()), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    validated, error = process_task_data(data, existing_task=task)
    if error:
        return jsonify({'error': error}), 400

    if 'user_id' in data:
        if data['user_id']:
            user = User.query.get(data['user_id'])
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id']:
            cat = Category.query.get(data['category_id'])
            if not cat:
                return jsonify({'error': 'Categoria não encontrada'}), 404
        task.category_id = data['category_id']

    for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
        if field in validated:
            setattr(task, field, validated[field])

    task.updated_at = utcnow()

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Erro ao atualizar task %s", task_id)
        return jsonify({'error': 'Erro ao atualizar'}), 500

    logger.info("Task atualizada: %s", task.id)
    return jsonify(task.to_dict()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    try:
        db.session.delete(task)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Erro ao deletar task %s", task_id)
        return jsonify({'error': 'Erro ao deletar'}), 500

    logger.info("Task deletada: %s", task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

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

    if priority:
        tasks = tasks.filter(Task.priority == int(priority))

    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    results = tasks.all()
    return jsonify([t.to_dict() for t in results]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
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
