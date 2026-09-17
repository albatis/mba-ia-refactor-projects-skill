# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Como executar os testes

Instale as dependências do projeto:

```bash
npm install
```

Execute a suíte de integração:

```bash
npm test
```

Os testes iniciam a aplicação automaticamente, executam as quatro chamadas de `api.http` e encerram o servidor ao final. Cada chamada é registrada em `test-results.log` com método, endpoint, status esperado, status recebido e indicação de sucesso ou falha.

Para visualizar o log:

```bash
cat test-results.log
```
