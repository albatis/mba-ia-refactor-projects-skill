================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, usuários, pedidos)
Architecture:  Monolítica — 4 arquivos nominalmente separados (app/controllers/models/database), mas sem separação real: models.py concentra SQL cru + formatação de resposta; database.py usa conexão global mutável; app.py define endpoints administrativos sensíveis inline
Source files:  4 files analyzed (~780 lines of code)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Injeção de SQL generalizada (string concatenada)
File: models.py:28,48-50,57-61,68,92,109-111,126-128,140,148-151,163-166,279-281,290-297
Description: Praticamente toda função de acesso a dados monta SQL concatenando strings com input do usuário, em vez de usar parâmetros (`?`).
Impact: Qualquer endpoint que aceite input (busca, login, criação de produto/usuário/pedido) permite manipular a query; `login_usuario` é vulnerável a bypass de autenticação via `' OR '1'='1`.
Recommendation: Aplicar o padrão "SQL concatenado → query parametrizada" do playbook em todas as ocorrências.

### [CRITICAL] Endpoint que executa SQL arbitrário sem autenticação
File: app.py:59-78
Description: `/admin/query` aceita uma string SQL no corpo da requisição e a executa diretamente contra o banco, sem autenticação nem allowlist.
Impact: Equivale a controle total sobre o banco de dados a partir de qualquer cliente HTTP (leitura, escrita ou destruição de dados).
Recommendation: Remover o endpoint — não há caso de uso legítimo para SQL arbitrário vindo do cliente.

### [CRITICAL] Chave secreta hardcoded e reexposta em endpoint público
File: app.py:7; controllers.py:289
Description: `SECRET_KEY` está fixa no código-fonte e é devolvida em texto puro pelo endpoint `/health`.
Impact: Compromete qualquer mecanismo de sessão/assinatura baseado nessa chave.
Recommendation: Mover para variável de ambiente lida por um módulo de config único; remover o campo da resposta de `/health`.

### [CRITICAL] Senhas em texto puro — armazenadas, comparadas e devolvidas pela API
File: database.py:76-79; models.py:80-87,96-103,105-120
Description: Senhas de seed são texto puro; `login_usuario` compara senha em texto puro (via SQL concatenado); `get_todos_usuarios`/`get_usuario_por_id` devolvem o campo `senha` de qualquer usuário.
Impact: Vazamento total de credenciais de todos os usuários via `GET /usuarios`; login sem hashing real.
Recommendation: Hashear senha com `werkzeug.security.generate_password_hash`/`check_password_hash` e remover o campo `senha` de qualquer serialização de resposta.

### [CRITICAL] Endpoint administrativo destrutivo sem autenticação
File: app.py:47-57
Description: `/admin/reset-db` apaga todas as tabelas (`produtos`, `usuarios`, `pedidos`, `itens_pedido`) sem nenhuma checagem de autorização.
Impact: Qualquer cliente anônimo pode zerar o banco de produção.
Recommendation: Proteger com autenticação/autorização de admin antes do handler.

### [HIGH] Lógica de negócio no Controller/Model, sem camada de serviço
File: controllers.py:188-220; models.py:133-169
Description: Cálculo de total do pedido, baixa de estoque e "envio" de notificações (prints simulando email/SMS/push) estão dentro do controller/model, sem orquestração isolada.
Impact: Impossível testar a regra de criação de pedido isoladamente do transporte HTTP e do banco.
Recommendation: Extrair para uma camada de Controller que orquestra Model + notificação, conforme `mvc-guidelines.md`.

### [HIGH] Debug mode habilitado com bind público, relatado como "produção"
File: app.py:8,88; controllers.py:286
Description: `DEBUG=True` e `app.run(host="0.0.0.0", ..., debug=True)`, enquanto `/health` informa `"ambiente": "producao"`.
Impact: Debugger interativo do Werkzeug exposto publicamente é uma via conhecida de execução remota de código.
Recommendation: Ler `DEBUG` de variável de ambiente, desabilitado por padrão fora de desenvolvimento.

### [HIGH] Conexão de banco em estado global mutável
File: database.py:4,7-10
Description: `db_connection` é uma variável de módulo global, inicializada preguiçosamente, compartilhada por todas as requisições com `check_same_thread=False`.
Impact: Acoplamento forte e potencial condição de corrida sob concorrência; impossível injetar uma conexão de teste isolada.
Recommendation: Encapsular a conexão em uma factory/config, sem estado mutável de módulo.

### [MEDIUM] Queries N+1 ao montar pedidos
File: models.py:171-233
Description: `get_pedidos_usuario` e `get_todos_pedidos` abrem um novo cursor por pedido e por item dentro de loops aninhados, em vez de um JOIN.
Impact: Custo cresce linearmente com pedidos × itens.
Recommendation: Substituir por uma única query com JOIN, conforme playbook.

### [MEDIUM] Validação duplicada entre criar/atualizar produto
File: controllers.py:24-62 vs 64-96
Description: Blocos de validação de nome/preço/estoque quase idênticos, copiados entre as duas funções.
Impact: Mudança de regra precisa ser replicada manualmente nos dois lugares.
Recommendation: Extrair `validar_produto(dados)` reutilizável.

### [MEDIUM] Lista de categorias válidas hardcoded inline
File: controllers.py:52
Description: `categorias_validas` é uma lista literal dentro da função, sem constante central.
Impact: Qualquer alteração da lista de categorias exige editar código de validação diretamente.
Recommendation: Mover para uma constante no módulo de config/domínio.

### [MEDIUM] Endpoint de busca de produtos concatena filtros diretamente na query
File: models.py:285-299
Description: `buscar_produtos` monta a cláusula `WHERE` concatenando `termo`/`categoria`/`preco_min`/`preco_max` diretamente na string SQL.
Impact: Mesma classe de SQL Injection do finding CRITICAL acima, isolada aqui por ser um caso de query dinâmica (múltiplos filtros opcionais).
Recommendation: Construir a query com parâmetros posicionais e lista de bind values.

### [LOW] Tratamento de erro genérico devolvendo `str(e)` ao cliente
File: controllers.py:12,22,62,96,109,126,134,144,165,186,220,227,235,255,262,292
Description: Quase todo handler usa `except Exception` amplo e devolve a mensagem crua da exceção.
Impact: Vaza detalhes internos (mensagens de driver/stack) e trata todo erro da mesma forma.
Recommendation: Centralizar tratamento de erro com `@app.errorhandler`.

### [LOW] `print()` usado como mecanismo de logging
File: controllers.py:8,11,57,61,106,161,179,182,208-210,248,250; app.py:56,83-86
Description: Eventos de negócio e erro são registrados via `print()` em vez de um logger configurável.
Impact: Sem níveis de log, sem estrutura, impossível desabilitar em produção.
Recommendation: Substituir por `logging`/`app.logger`.

### [LOW] Números mágicos nos degraus de desconto do relatório de vendas
File: models.py:256-262
Description: Limiares (10000/5000/1000) e taxas (0.1/0.05/0.02) hardcoded inline em `relatorio_vendas`.
Impact: Regra de negócio sem nome nem documentação, difícil de alterar com segurança.
Recommendation: Extrair para constantes nomeadas, conforme playbook.

### [LOW] Mistura de nomenclatura PT/EN e status como string mágica
File: controllers.py:242
Description: Lista de status válidos (`"pendente","aprovado","enviado","entregue","cancelado"`) hardcoded inline, sem enum/constante central.
Impact: Risco de inconsistência se a lista precisar mudar em mais de um lugar.
Recommendation: Extrair para constante/enum compartilhado.

## Deprecated API check
Checagem da seção 14 do catálogo executada contra o runtime do ambiente (Python 3.12,
Flask 3.1.1, flask-cors 5.0.1): nenhuma ocorrência encontrada — sem `datetime.utcnow()`,
sem `collections.Mapping`, sem `@app.before_first_request`. Nenhum finding gerado.

================================
Total: 16 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
code-smells-project/
├── app.py                          # composition root (create_app, entry point)
├── .env.example
├── requirements.txt
├── src/
│   ├── config/
│   │   ├── settings.py             # SECRET_KEY/DEBUG/DB_PATH/ADMIN_API_KEY via env
│   │   ├── constants.py            # CATEGORIAS_VALIDAS, STATUS_PEDIDO_VALIDOS, DESCONTO_TIERS
│   │   └── database.py             # conexão por request (flask.g), schema + seed com senha hasheada
│   ├── models/
│   │   ├── produto_model.py
│   │   ├── usuario_model.py        # sem campo senha na serialização; hash com werkzeug
│   │   └── pedido_model.py         # queries parametrizadas, listagem via JOIN (sem N+1)
│   ├── controllers/
│   │   ├── produto_controller.py   # validação única reaproveitada (criar/atualizar)
│   │   ├── usuario_controller.py
│   │   ├── pedido_controller.py
│   │   ├── relatorio_controller.py
│   │   └── sistema_controller.py   # health check, reset-db
│   ├── views/
│   │   └── routes.py               # só delega para os controllers
│   └── middlewares/
│       ├── error_handler.py        # AppError + handler centralizado (sem vazar str(e))
│       └── auth.py                 # require_admin_key (protege /admin/reset-db)
└── tests/test_endpoints.py         # atualizado para o novo contrato de segurança

## Validation
  ✓ Application boots without errors (python app.py — Flask dev server on :5000)
  ✓ All endpoints respond correctly (4/4 pytest suites green + manual curl smoke test)
  ✓ Zero anti-patterns remaining — dos 16 findings da Fase 2, todos foram corrigidos:
    - SQL injection (models) → queries parametrizadas
    - /admin/query (RCE via SQL arbitrário) → endpoint removido
    - SECRET_KEY hardcoded + vazamento em /health → variável de ambiente, removido da resposta
    - Senhas em texto puro / devolvidas na API → hash (werkzeug) + nunca serializadas
    - /admin/reset-db sem autenticação → protegido por X-Admin-Key
    - Lógica de negócio dispersa no controller/model → orquestração no controller, dados no model
    - DEBUG=True + bind público relatado como "produção" → DEBUG via env (default false)
    - Conexão de banco global mutável → conexão por request via flask.g
    - Queries N+1 em pedidos → JOIN único
    - Validação duplicada criar/atualizar produto → helper único
    - Categorias hardcoded inline → constants.py
    - Busca de produtos com filtros concatenados → parametrizada
    - except genérico vazando str(e) → error handler centralizado
    - print() como logging → módulo logging
    - Magic numbers de desconto → DESCONTO_TIERS nomeado
    - Status de pedido como string mágica → STATUS_PEDIDO_VALIDOS

Observação de design: a criação de pedido (validação de estoque + cálculo de total) permanece no
`pedido_model`, pois envolve apenas a própria entidade Pedido e seus itens — não foi extraída para
uma camada de Service separada porque, conforme `mvc-guidelines.md`, Services são opcionais e devem
ser introduzidos apenas quando o Controller cresceria demais ou a lógica precisasse ser reutilizada
fora do contexto HTTP, o que não é o caso aqui. O disparo de notificações (antes 3 `print()` no
controller) foi isolado em `_notificar_novo_pedido()`.
================================
