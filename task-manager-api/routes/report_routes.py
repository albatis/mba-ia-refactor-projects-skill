import logging
from datetime import timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from database import db
from middlewares.auth import require_admin
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import is_valid_color, utcnow

report_bp = Blueprint('reports', __name__)
logger = logging.getLogger(__name__)


@report_bp.route('/reports/summary', methods=['GET'])
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

    seven_days_ago = utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()

    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago
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


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

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


@report_bp.route('/categories', methods=['GET'])
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


def _validate_category(data):
    if 'name' in data and not data['name']:
        return 'Nome é obrigatório'
    if 'color' in data and data['color'] is not None and not is_valid_color(data['color']):
        return 'Cor inválida — use o formato #RRGGBB'
    return None


@report_bp.route('/categories', methods=['POST'])
@require_admin
def create_category():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    name = data.get('name')
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    error = _validate_category(data)
    if error:
        return jsonify({'error': error}), 400

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', '#000000')

    try:
        db.session.add(category)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Erro ao criar categoria")
        return jsonify({'error': 'Erro ao criar categoria'}), 500

    return jsonify(category.to_dict()), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@require_admin
def update_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    error = _validate_category(data)
    if error:
        return jsonify({'error': error}), 400

    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Erro ao atualizar categoria %s", cat_id)
        return jsonify({'error': 'Erro ao atualizar'}), 500

    return jsonify(cat.to_dict()), 200


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@require_admin
def delete_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    try:
        db.session.delete(cat)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Erro ao deletar categoria %s", cat_id)
        return jsonify({'error': 'Erro ao deletar'}), 500

    return jsonify({'message': 'Categoria deletada'}), 200
