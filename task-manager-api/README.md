# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Como executar os testes

Com o ambiente virtual ativado e as dependências instaladas, execute:

```bash
pytest -q tests/test_endpoints.py
```

Ou use diretamente o executável do ambiente virtual:

```bash
venv/bin/pytest -q tests/test_endpoints.py
```

A suíte chama todos os endpoints da API usando o cliente de testes do Flask. Ela executa `seed_data()` antes dos testes para garantir os dados iniciais e registra cada chamada em `test-results.log`, informando método, endpoint, status esperado, status recebido e se houve sucesso ou falha.

Para conferir o log:

```bash
cat test-results.log
```
