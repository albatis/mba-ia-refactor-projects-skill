import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as application
import database


LOG_FILE = "test-results.log"


@pytest.fixture
def client(tmp_path):
    database.db_path = str(tmp_path / "test-loja.db")
    if database.db_connection is not None:
        database.db_connection.close()
    database.db_connection = None

    application.app.config.update(TESTING=True)
    with application.app.test_client() as test_client:
        database.get_db()
        yield test_client

    if database.db_connection is not None:
        database.db_connection.close()
    database.db_connection = None


@pytest.fixture(scope="session")
def request_log():
    logger = logging.getLogger("endpoint-tests")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)
    yield logger
    handler.close()
    logger.handlers.clear()


def call_and_log(client, logger, method, path, expected_status, **kwargs):
    response = getattr(client, method.lower())(path, **kwargs)
    success = response.status_code == expected_status
    logger.info(
        "TESTE %s %s | esperado=%s recebido=%s | %s",
        method.upper(),
        path,
        expected_status,
        response.status_code,
        "SUCESSO" if success else "FALHA",
    )
    assert success, response.get_json()
    return response


def test_root_health_and_admin_endpoints(client, request_log):
    call_and_log(client, request_log, "get", "/", 200)
    health = call_and_log(client, request_log, "get", "/health", 200)
    assert health.get_json()["status"] == "ok"

    query = call_and_log(
        client,
        request_log,
        "post",
        "/admin/query",
        200,
        json={"sql": "SELECT COUNT(*) AS total FROM produtos"},
    )
    assert query.get_json()["sucesso"] is True
    call_and_log(client, request_log, "post", "/admin/reset-db", 200)


def test_product_endpoints(client, request_log):
    products = call_and_log(client, request_log, "get", "/produtos", 200)
    product_id = products.get_json()["dados"][0]["id"]

    call_and_log(client, request_log, "get", f"/produtos/{product_id}", 200)
    call_and_log(client, request_log, "get", "/produtos/busca?q=Notebook", 200)
    call_and_log(
        client,
        request_log,
        "get",
        "/produtos/busca?categoria=informatica&preco_min=10&preco_max=6000",
        200,
    )

    created = call_and_log(
        client,
        request_log,
        "post",
        "/produtos",
        201,
        json={
            "nome": "Produto de teste",
            "descricao": "Criado pela suíte de endpoints",
            "preco": 10.5,
            "estoque": 4,
            "categoria": "geral",
        },
    )
    created_id = created.get_json()["dados"]["id"]
    call_and_log(
        client,
        request_log,
        "put",
        f"/produtos/{created_id}",
        200,
        json={
            "nome": "Produto atualizado",
            "descricao": "Atualizado",
            "preco": 12.5,
            "estoque": 3,
            "categoria": "geral",
        },
    )
    call_and_log(client, request_log, "delete", f"/produtos/{created_id}", 200)


def test_user_and_login_endpoints(client, request_log):
    users = call_and_log(client, request_log, "get", "/usuarios", 200)
    user_id = users.get_json()["dados"][0]["id"]
    call_and_log(client, request_log, "get", f"/usuarios/{user_id}", 200)

    email = "endpoint-test@example.com"
    created = call_and_log(
        client,
        request_log,
        "post",
        "/usuarios",
        201,
        json={"nome": "Endpoint Test", "email": email, "senha": "senha-teste"},
    )
    assert created.get_json()["sucesso"] is True
    call_and_log(
        client,
        request_log,
        "post",
        "/login",
        200,
        json={"email": email, "senha": "senha-teste"},
    )


def test_order_report_and_status_endpoints(client, request_log):
    products = call_and_log(client, request_log, "get", "/produtos", 200)
    users = call_and_log(client, request_log, "get", "/usuarios", 200)
    product_id = products.get_json()["dados"][0]["id"]
    user_id = users.get_json()["dados"][0]["id"]
    order = call_and_log(
        client,
        request_log,
        "post",
        "/pedidos",
        201,
        json={"usuario_id": user_id, "itens": [{"produto_id": product_id, "quantidade": 1}]},
    )
    order_id = order.get_json()["dados"]["pedido_id"]

    call_and_log(client, request_log, "get", "/pedidos", 200)
    call_and_log(client, request_log, "get", f"/pedidos/usuario/{user_id}", 200)
    call_and_log(
        client,
        request_log,
        "put",
        f"/pedidos/{order_id}/status",
        200,
        json={"status": "aprovado"},
    )
    call_and_log(client, request_log, "get", "/relatorios/vendas", 200)


def test_admin_query_error_endpoint(client, request_log):
    response = call_and_log(
        client,
        request_log,
        "post",
        "/admin/query",
        400,
        json={},
    )
    assert response.get_json()["erro"] == "Query não informada"