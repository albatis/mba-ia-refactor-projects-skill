# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

## Como executar os testes

Na pasta `code-smells-project`, crie e ative o ambiente virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

Execute a suíte de testes dos endpoints:

```bash
pytest -q tests/test_endpoints.py
```

Os testes usam um banco SQLite temporário e cobrem todos os endpoints da API. O resultado detalhado de cada chamada, com status esperado, status recebido e indicação de sucesso ou falha, é gravado em `test-results.log`.

Para executar os testes e gerar o log novamente:

```bash
rm -f test-results.log
pytest -q tests/test_endpoints.py
cat test-results.log
```
