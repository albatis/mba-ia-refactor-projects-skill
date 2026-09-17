import logging

from flask import jsonify

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message="Recurso não encontrado"):
        super().__init__(message, 404)


class UnauthorizedError(AppError):
    def __init__(self, message="Não autorizado"):
        super().__init__(message, 401)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(404)
    def handle_not_found(_err):
        return jsonify({"erro": "Rota não encontrada", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        logger.exception("Erro não tratado: %s", err)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
