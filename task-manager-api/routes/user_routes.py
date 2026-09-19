from flask import Blueprint

from controllers import user_controller
from middlewares.auth import require_admin

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    return user_controller.get_users()


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return user_controller.get_user(user_id)


@user_bp.route('/users', methods=['POST'])
def create_user():
    return user_controller.create_user()


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    return user_controller.update_user(user_id)


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    return user_controller.delete_user(user_id)


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    return user_controller.get_user_tasks(user_id)


@user_bp.route('/login', methods=['POST'])
def login():
    return user_controller.login()
