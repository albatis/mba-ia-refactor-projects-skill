import logging

from flask import jsonify, request

from src.config.constants import CATEGORIAS_VALIDAS
from src.middlewares.error_handler import AppError, NotFoundError
from src.models import produto_model

logger = logging.getLogger(__name__)


def _validar_produto(dados):
    erros = []

    if "nome" not in dados:
        erros.append("Nome é obrigatório")
    elif len(dados["nome"]) < 2:
        erros.append("Nome muito curto")
    elif len(dados["nome"]) > 200:
        erros.append("Nome muito longo")

    if "preco" not in dados:
        erros.append("Preço é obrigatório")
    elif dados["preco"] < 0:
        erros.append("Preço não pode ser negativo")

    if "estoque" not in dados:
        erros.append("Estoque é obrigatório")
    elif dados["estoque"] < 0:
        erros.append("Estoque não pode ser negativo")

    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        erros.append(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")

    if erros:
        raise AppError("; ".join(erros))


def listar():
    return jsonify({"dados": produto_model.get_todos(), "sucesso": True}), 200


def buscar_por_id(produto_id):
    produto = produto_model.get_por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return jsonify({"dados": produto, "sucesso": True}), 200


def buscar():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = request.args.get("preco_min", type=float)
    preco_max = request.args.get("preco_max", type=float)

    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar():
    dados = request.get_json(silent=True) or {}
    if not dados:
        raise AppError("Dados inválidos")
    _validar_produto(dados)

    novo_id = produto_model.criar(
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    logger.info("Produto criado com ID: %s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar(produto_id):
    dados = request.get_json(silent=True) or {}
    if not produto_model.get_por_id(produto_id):
        raise NotFoundError("Produto não encontrado")
    if not dados:
        raise AppError("Dados inválidos")
    _validar_produto(dados)

    produto_model.atualizar(
        produto_id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(produto_id):
    if not produto_model.get_por_id(produto_id):
        raise NotFoundError("Produto não encontrado")
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
