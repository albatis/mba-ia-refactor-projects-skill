import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app
from models.category import Category
from models.task import Task
from models.user import User
from seed import seed_data


LOG_FILE = "test-results.log"


@pytest.fixture(scope="module")
def client():
    seed_data()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(scope="module")
def request_log():
    logger = logging.getLogger("task-manager-endpoint-tests")
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
    passed = response.status_code == expected_status
    logger.info(
        "TESTE %s %s | esperado=%s recebido=%s | %s",
        method.upper(),
        path,
        expected_status,
        response.status_code,
        "SUCESSO" if passed else "FALHA",
    )
    assert passed, response.get_json()
    return response


def test_root_and_health_endpoints(client, request_log):
    root = call_and_log(client, request_log, "get", "/", 200)
    assert root.get_json()["message"] == "Task Manager API"

    health = call_and_log(client, request_log, "get", "/health", 200)
    assert health.get_json()["status"] == "ok"


def test_task_endpoints(client, request_log):
    tasks = call_and_log(client, request_log, "get", "/tasks", 200)
    task_id = tasks.get_json()[0]["id"]
    call_and_log(client, request_log, "get", f"/tasks/{task_id}", 200)
    call_and_log(client, request_log, "get", "/tasks/search?q=autenticação", 200)
    call_and_log(client, request_log, "get", "/tasks/search?status=pending&priority=1", 200)

    stats = call_and_log(client, request_log, "get", "/tasks/stats", 200)
    assert stats.get_json()["total"] == 10

    created = call_and_log(
        client,
        request_log,
        "post",
        "/tasks",
        201,
        json={
            "title": "Testar endpoint de task",
            "description": "Task criada pela suíte",
            "status": "pending",
            "priority": 3,
            "user_id": 1,
            "category_id": 1,
            "due_date": "2030-01-01",
            "tags": ["teste", "api"],
        },
    )
    created_id = created.get_json()["id"]
    call_and_log(
        client,
        request_log,
        "put",
        f"/tasks/{created_id}",
        200,
        json={"title": "Task atualizada", "status": "done", "priority": 2},
    )
    call_and_log(client, request_log, "delete", f"/tasks/{created_id}", 200)


def test_user_and_login_endpoints(client, request_log):
    users = call_and_log(client, request_log, "get", "/users", 200)
    user_id = users.get_json()[0]["id"]
    call_and_log(client, request_log, "get", f"/users/{user_id}", 200)
    call_and_log(client, request_log, "get", f"/users/{user_id}/tasks", 200)

    login = call_and_log(
        client,
        request_log,
        "post",
        "/login",
        200,
        json={"email": "joao@email.com", "password": "1234"},
    )
    assert login.get_json()["token"] == f"fake-jwt-token-{user_id}"

    created = call_and_log(
        client,
        request_log,
        "post",
        "/users",
        201,
        json={"name": "Usuário de teste", "email": "teste@endpoints.com", "password": "1234"},
    )
    created_id = created.get_json()["id"]
    call_and_log(
        client,
        request_log,
        "put",
        f"/users/{created_id}",
        200,
        json={"name": "Usuário atualizado", "role": "manager"},
    )
    call_and_log(client, request_log, "delete", f"/users/{created_id}", 200)


def test_report_and_category_endpoints(client, request_log):
    summary = call_and_log(client, request_log, "get", "/reports/summary", 200)
    assert summary.get_json()["overview"]["total_tasks"] == 10

    user_report = call_and_log(client, request_log, "get", "/reports/user/1", 200)
    assert user_report.get_json()["user"]["id"] == 1

    categories = call_and_log(client, request_log, "get", "/categories", 200)
    assert len(categories.get_json()) == 4

    created = call_and_log(
        client,
        request_log,
        "post",
        "/categories",
        201,
        json={"name": "Testes", "description": "Categoria de teste", "color": "#123456"},
    )
    created_id = created.get_json()["id"]
    call_and_log(
        client,
        request_log,
        "put",
        f"/categories/{created_id}",
        200,
        json={"name": "Testes atualizados"},
    )
    call_and_log(client, request_log, "delete", f"/categories/{created_id}", 200)


def test_seed_created_expected_records(client):
    assert User.query.count() == 3
    assert Category.query.count() == 4
    assert Task.query.count() == 10