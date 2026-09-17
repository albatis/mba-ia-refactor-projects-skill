import logging

from flask import jsonify, request

from src.middlewares.error_handler import AppError, NotFoundError
from src.models import usuario_model

logger = logging.getLogger(__name__)


def listar():
    return jsonify({"dados": usuario_model.get_todos(), "sucesso": True}), 200


def buscar_por_id(usuario_id):
    usuario = usuario_model.get_por_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar():
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise AppError("Nome, email e senha são obrigatórios")

    novo_id = usuario_model.criar(nome, email, senha)
    logger.info("Usuário criado: %s", email)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def login():
    dados = request.get_json(silent=True) or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        raise AppError("Email e senha são obrigatórios")

    usuario = usuario_model.autenticar(email, senha)
    if not usuario:
        logger.info("Login falhou: %s", email)
        raise AppError("Email ou senha inválidos", 401)

    logger.info("Login bem-sucedido: %s", email)
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
