"""Tratamento de erro centralizado da API.

Um único ponto decide o formato de erro ({'error': <mensagem>}) e o status HTTP.
Controllers sinalizam falhas de negócio levantando as exceções abaixo, em vez de
repetir `try/except` e montar resposta de erro em cada handler.
"""

import logging

from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from database import db

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Erro de aplicação esperado, traduzido para uma resposta HTTP."""

    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(err):
        db.session.rollback()
        logger.exception("Erro de banco de dados")
        return jsonify({'error': 'Erro interno'}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        # Erros do próprio framework (404 de rota inexistente, 405, ...) também
        # saem no formato JSON padrão da API.
        return jsonify({'error': err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        db.session.rollback()
        logger.exception("Erro não tratado")
        return jsonify({'error': 'Erro interno'}), 500
