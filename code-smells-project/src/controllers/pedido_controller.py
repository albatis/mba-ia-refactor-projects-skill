import logging

from flask import jsonify, request

from src.config.constants import STATUS_PEDIDO_VALIDOS
from src.middlewares.error_handler import AppError
from src.models import pedido_model

logger = logging.getLogger(__name__)


def _notificar_novo_pedido(pedido_id, usuario_id):
    # Simula o disparo de notificações (email/SMS/push) para o usuário.
    # Em produção isso seria delegado a um serviço de mensageria real.
    logger.info("Notificações de novo pedido enviadas: pedido=%s usuario=%s", pedido_id, usuario_id)


def criar():
    dados = request.get_json(silent=True) or {}
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise AppError("Usuario ID é obrigatório")
    if not itens:
        raise AppError("Pedido deve ter pelo menos 1 item")

    resultado = pedido_model.criar(usuario_id, itens)
    if "erro" in resultado:
        raise AppError(resultado["erro"])

    _notificar_novo_pedido(resultado["pedido_id"], usuario_id)

    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_por_usuario(usuario_id):
    return jsonify({"dados": pedido_model.listar_por_usuario(usuario_id), "sucesso": True}), 200


def listar_todos():
    return jsonify({"dados": pedido_model.listar_todos(), "sucesso": True}), 200


def atualizar_status(pedido_id):
    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status", "")

    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise AppError("Status inválido")

    pedido_model.atualizar_status(pedido_id, novo_status)

    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado — preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Pedido %s cancelado — devolver estoque", pedido_id)

    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
