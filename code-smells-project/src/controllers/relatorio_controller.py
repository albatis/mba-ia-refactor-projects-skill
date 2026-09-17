from flask import jsonify

from src.models import pedido_model


def vendas():
    return jsonify({"dados": pedido_model.relatorio_vendas(), "sucesso": True}), 200
