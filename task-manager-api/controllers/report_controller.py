import logging
from datetime import timedelta

from flask import jsonify, request
from sqlalchemy import func

from database import db
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import is_valid_color, utcnow

logger = logging.getLogger(__name__)

RECENT_ACTIVITY_WINDOW_DAYS = 7
DEFAULT_CATEGORY_COLOR = '#000000'


def _get_category_or_404(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        raise NotFoundError('Categoria não encontrada')
    return cat


def _validate_category(data):
    if 'name' in data and not data['name']:
        raise ValidationError('Nome é obrigatório')
    if 'color' in data and data['color'] is not None and not is_valid_color(data['color']):
        raise ValidationError('Cor inválida — use o formato #RRGGBB')


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    p1 = Task.query.filter_by(priority=1).count()
    p2 = Task.query.filter_by(priority=2).count()
    p3 = Task.query.filter_by(priority=3).count()
    p4 = Task.query.filter_by(priority=4).count()
    p5 = Task.query.filter_by(priority=5).count()

    overdue_list = []
    for t in Task.query.all():
        if t.is_overdue():
            overdue_list.append({
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (utcnow() - t.due_date).days
            })

    window_start = utcnow() - timedelta(days=RECENT_ACTIVITY_WINDOW_DAYS)
    recent_tasks = Task.query.filter(Task.created_at >= window_start).count()

    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= window_start
    ).count()

    # Uma única query agregada por usuário em vez de um SELECT de tasks por
    # usuário dentro do loop (N+1).
    per_user_totals = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .group_by(Task.user_id)
        .all()
    )
    per_user_done = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .filter(Task.status == 'done')
        .group_by(Task.user_id)
        .all()
    )

    user_stats = []
    for u in User.query.all():
        total = per_user_totals.get(u.id, 0)
        completed = per_user_done.get(u.id, 0)
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0
        })

    report = {
        'generated_at': str(utcnow()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': {
            'critical': p1,
            'high': p2,
            'medium': p3,
            'low': p4,
            'minimal': p5,
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }

    return jsonify(report), 200


def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    tasks = Task.query.filter_by(user_id=user_id).all()

    total = len(tasks)
    done = sum(1 for t in tasks if t.status == 'done')
    pending = sum(1 for t in tasks if t.status == 'pending')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    cancelled = sum(1 for t in tasks if t.status == 'cancelled')
    high_priority = sum(1 for t in tasks if t.priority <= 2)
    overdue = sum(1 for t in tasks if t.is_overdue())

    report = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': pending,
            'in_progress': in_progress,
            'cancelled': cancelled,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
        }
    }

    return jsonify(report), 200


def get_categories():
    # Contagem de tasks por categoria em uma única query agregada, em vez de
    # um COUNT(*) por categoria dentro do loop.
    counts = dict(
        db.session.query(Task.category_id, func.count(Task.id))
        .group_by(Task.category_id)
        .all()
    )

    result = []
    for c in Category.query.all():
        cat_data = c.to_dict()
        cat_data['task_count'] = counts.get(c.id, 0)
        result.append(cat_data)
    return jsonify(result), 200


def create_category():
    data = request.get_json()
    if not data:
        raise ValidationError('Dados inválidos')

    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')

    _validate_category(data)

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', DEFAULT_CATEGORY_COLOR)

    db.session.add(category)
    db.session.commit()

    logger.info("Categoria criada: %s - %s", category.id, category.name)
    return jsonify(category.to_dict()), 201


def update_category(cat_id):
    cat = _get_category_or_404(cat_id)

    data = request.get_json()
    if not data:
        raise ValidationError('Dados inválidos')

    _validate_category(data)

    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']

    db.session.commit()

    logger.info("Categoria atualizada: %s", cat.id)
    return jsonify(cat.to_dict()), 200


def delete_category(cat_id):
    cat = _get_category_or_404(cat_id)

    db.session.delete(cat)
    db.session.commit()

    logger.info("Categoria deletada: %s", cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
