from flask import Blueprint, jsonify

from src.controllers import (
    pedido_controller,
    produto_controller,
    relatorio_controller,
    sistema_controller,
    usuario_controller,
)
from src.middlewares.auth import require_admin_key

bp = Blueprint("api", __name__)


@bp.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


@bp.route("/health", methods=["GET"])
def health():
    return sistema_controller.health_check()


@bp.route("/admin/reset-db", methods=["POST"])
@require_admin_key
def reset_database():
    return sistema_controller.reset_database()


@bp.route("/produtos", methods=["GET"])
def listar_produtos():
    return produto_controller.listar()


@bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    return produto_controller.buscar()


@bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    return produto_controller.buscar_por_id(produto_id)


@bp.route("/produtos", methods=["POST"])
def criar_produto():
    return produto_controller.criar()


@bp.route("/produtos/<int:produto_id>", methods=["PUT"])
def atualizar_produto(produto_id):
    return produto_controller.atualizar(produto_id)


@bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
def deletar_produto(produto_id):
    return produto_controller.deletar(produto_id)


@bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    return usuario_controller.listar()


@bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    return usuario_controller.buscar_por_id(usuario_id)


@bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    return usuario_controller.criar()


@bp.route("/login", methods=["POST"])
def login():
    return usuario_controller.login()


@bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    return pedido_controller.criar()


@bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    return pedido_controller.listar_todos()


@bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    return pedido_controller.listar_por_usuario(usuario_id)


@bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    return pedido_controller.atualizar_status(pedido_id)


@bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    return relatorio_controller.vendas()
