================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Dependencies:  flask-cors 4.0.0, marshmallow 3.20.1 (declarado, nunca importado), requests 2.31.0
               (declarado, não utilizado), python-dotenv 1.0.0 (declarado, não utilizado), pytest 8.3.5
Domain:        Task Manager (tasks, usuários, categorias, relatórios de produtividade)
Architecture:  Camadas nominais presentes (models/, routes/, services/, utils/), mas separação
               parcial: rotas acessam SQLAlchemy diretamente e reimplementam validação/regra de
               negócio já existente em models/utils; services/notification_service.py é uma
               camada completa nunca importada (código morto); utils/helpers.py define
               validadores e constantes nunca usados pelas rotas, que preferem literais inline.
Source files:  12 files analyzed (~1160 lines of code)
DB tables:     users, tasks, categories
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   12 analyzed | ~1160 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Hash de senha com MD5 sem salt
File: models/user.py:29,32
Description: `set_password`/`check_password` usam `hashlib.md5(pwd.encode()).hexdigest()`.
Impact: MD5 é criptograficamente quebrado para senha; sem salt, rainbow tables resolvem instantaneamente.
Recommendation: Trocar por `werkzeug.security.generate_password_hash`/`check_password_hash`.

### [CRITICAL] Hash da senha devolvido pela API
File: models/user.py:16-25 (`to_dict`); usado em routes/user_routes.py:33 (`get_user`), :85-86 (`create_user`), :129 (`update_user`), :207-210 (`login`)
Description: `to_dict()` inclui o campo `password`; todo endpoint que devolve um usuário via `to_dict()` expõe o hash.
Impact: Qualquer consumidor da API (inclusive não autenticado, no caso de `GET /users/<id>`) recebe o hash da senha.
Recommendation: Remover `password` de `to_dict()`.

### [CRITICAL] Chave secreta e credenciais SMTP hardcoded
File: app.py:13; services/notification_service.py:9-10
Description: `SECRET_KEY` fixa no código; `email_user`/`email_password` fixos em `NotificationService` (serviço atualmente morto, mas o segredo já está commitado).
Impact: Segredos versionados no Git; `SECRET_KEY` compromete a assinatura de qualquer token derivado dela.
Recommendation: Mover para variáveis de ambiente via módulo de config.

### [HIGH] Token de autenticação falso e previsível
File: routes/user_routes.py:210
Description: `'token': 'fake-jwt-token-' + str(user.id)` — não é assinado, é trivialmente forjável a partir de um ID sequencial.
Impact: Qualquer chamador pode se passar por qualquer usuário só adivinhando o ID.
Recommendation: Emitir um token assinado (ex.: `itsdangerous`, já é dependência do Flask) e validá-lo nas rotas que precisam de autenticação.

### [HIGH] Nenhum controle de autorização em operações administrativas
File: routes/report_routes.py:167-223 (criar/atualizar/deletar categoria); routes/user_routes.py:119-122 (troca de `role`/`active` dentro de `update_user`)
Description: Nenhuma dessas rotas verifica quem está chamando — qualquer requisição não autenticada pode criar/editar/apagar categorias ou promover um usuário a admin.
Impact: Qualquer cliente externo pode escalar privilégios ou corromper o catálogo de categorias.
Recommendation: Exigir um token válido de usuário com `role == 'admin'` nessas rotas.

### [HIGH] Lógica de negócio duplicada em vez de reusar o model
File: routes/task_routes.py:30-39,71-80; routes/user_routes.py:171-180; routes/report_routes.py:34-43,132-135
Description: O cálculo "task está atrasada" (due_date no passado + status não finalizado) é reescrito manualmente 5 vezes; `Task.is_overdue()` (models/task.py:50-60) já existe e nunca é chamado.
Impact: Qualquer mudança na regra de atraso precisa ser replicada em 5 lugares — já é uma fonte de drift.
Recommendation: Substituir as 5 cópias por chamadas a `task.is_overdue()`.

### [HIGH] Camada de serviço e helpers de validação existentes e nunca conectados
File: services/notification_service.py (77 linhas, nunca importado); utils/helpers.py:57-108 (`process_task_data`, nunca importado), :19-23 (`validate_email`, duplicado inline em routes/user_routes.py:61,106 em vez de reusado), :110-116 (constantes `VALID_STATUSES`/`VALID_ROLES`/`MAX_TITLE_LENGTH` nunca importadas)
Description: Três peças de infraestrutura já prontas (notificação, validação de task, constantes) existem no repositório mas nenhuma rota as usa.
Impact: Código morto ocupando espaço mental, e duplicação de lógica (validação de task reimplementada inline em vez de reusar `process_task_data`).
Recommendation: Conectar `NotificationService` ao fluxo de criação de task (notificar usuário atribuído), e trocar validação/constantes inline pelas versões de `utils/helpers.py`.

### [MEDIUM] Queries N+1 em múltiplos endpoints
File: routes/task_routes.py:41-57 (`get_tasks` — `User.query.get`/`Category.query.get` por task, em loop); routes/report_routes.py:55-68 (`summary_report` — `Task.query.filter_by(user_id=u.id).all()` por usuário, em loop); routes/report_routes.py:161-164 (`get_categories` — `Task.query.filter_by(category_id=c.id).count()` por categoria, em loop)
Description: Busca registros relacionados um a um dentro de loops em vez de eager loading/agregação.
Impact: Custo cresce com o volume de tasks/usuários/categorias.
Recommendation: Usar `joinedload`/`selectinload` do SQLAlchemy (relação `task.user`/`task.category` já existe via `backref`) ou uma query agregada.

### [MEDIUM] `except` genérico mascarando qualquer erro
File: routes/task_routes.py:62,236; routes/user_routes.py:130,149; routes/report_routes.py:186,207,221
Description: `except:` (sem tipo) trata bug de programação e erro de integridade da mesma forma, sempre devolvendo 500 genérico.
Impact: Dificulta diagnóstico; esconde a causa real do erro nos logs.
Recommendation: Capturar exceções específicas e logar a exceção original.

### [MEDIUM] Validação inconsistente entre endpoints quase idênticos de categoria
File: routes/report_routes.py:167-209
Description: `create_category` valida `name` mas não o formato de `color` (embora `utils/helpers.is_valid_color()` já exista); `update_category` não valida nenhum campo antes de commitar.
Impact: Permite salvar `color` em formato inválido, principalmente via update.
Recommendation: Validar `name` e `color` (via `is_valid_color`) em ambos os endpoints.

### [LOW] Uso de `datetime.utcnow()`, deprecated desde Python 3.12
File: models/task.py:15-16,52; routes/task_routes.py (múltiplos); routes/report_routes.py (múltiplos); seed.py (múltiplos)
Description: `datetime.utcnow()` está deprecated desde Python 3.12 em favor de `datetime.now(timezone.utc)`.
Impact: Gera `DeprecationWarning` no ambiente atual (Python 3.12.3, confirmado via `python3 --version`).
Recommendation: Trocar por `datetime.now(timezone.utc)` (ajustando comparações que hoje assumem datetime naive).

### [LOW] Idiomas booleanos verbosos (`if x: return True else: return False`)
File: models/task.py:38-43 (`validate_status`), :45-48 (`validate_priority`), :50-60 (`is_overdue`); models/user.py:34-38 (`is_admin`)
Description: Métodos que poderiam ser uma única expressão booleana usam if/else aninhado.
Impact: Legibilidade; mais linhas para o mesmo resultado.
Recommendation: Simplificar para `return <expressão booleana>`.

### [LOW] Imports não utilizados
File: routes/task_routes.py:7 (`json, os, sys, time`); app.py:7 (`os, sys, json`); routes/report_routes.py:8 (`json`)
Description: Módulos importados e nunca referenciados no arquivo.
Impact: Ruído; sugere código copiado/colado sem limpeza.
Recommendation: Remover imports não utilizados.

### [LOW] Mesma forma de dado serializada de 3 formas diferentes
File: models/task.py:23-36 (`to_dict`) vs. dict manual em routes/task_routes.py:17-28 e routes/user_routes.py:162-169
Description: `get_tasks` e `get_user_tasks` reconstroem manualmente o mesmo shape que `Task.to_dict()` já produz, em vez de reusá-lo.
Impact: Risco de divergência entre as três versões (já visível: apenas a versão do model inclui `tags` normalizado).
Recommendation: Reusar `task.to_dict()` e apenas acrescentar os campos extras (`overdue`, `user_name`, `category_name`).

================================
Total: 15 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
task-manager-api/                   (estrutura de camadas já existia; corrigidos os pontos da auditoria)
├── app.py                          # composition root — agora lê config/settings.py
├── database.py                     # inalterado (já era só `db = SQLAlchemy()`)
├── .env.example
├── requirements.txt                # marshmallow/requests removidos (não usados); itsdangerous explícito
├── config/
│   └── settings.py                 # SECRET_KEY/DEBUG/DATABASE_URL/SMTP/TOKEN_MAX_AGE via env
├── middlewares/
│   └── auth.py                     # gera/valida token assinado (itsdangerous); require_auth/require_admin
├── models/
│   ├── user.py                     # hash com werkzeug; to_dict() sem password; is_admin() simplificado
│   ├── task.py                     # is_overdue()/validate_* simplificados; to_dict() já inclui "overdue"
│   └── category.py                 # utcnow() em vez de datetime.utcnow()
├── routes/
│   ├── task_routes.py              # process_task_data + constantes reaproveitados; joinedload (sem N+1);
│   │                                # is_overdue() reaproveitado; except específico; logging
│   ├── user_routes.py              # validate_email reaproveitado; token assinado; require_admin em
│   │                                # role/active e DELETE; except específico; logging
│   └── report_routes.py            # queries agregadas (GROUP BY) em vez de loop; is_valid_color
│                                    # reaproveitado; require_admin no CRUD de categorias
├── services/
│   └── notification_service.py     # credenciais via config; conectado a create_task (não é mais morto)
├── utils/
│   └── helpers.py                  # utcnow() adicionado; process_task_data/validate_email/is_valid_color
│                                    # /constantes agora efetivamente usados pelas rotas
├── seed.py                         # utcnow() em vez de datetime.utcnow()
└── tests/test_endpoints.py         # atualizado para o novo contrato (token real, gates de admin)

## Validation
  ✓ Application boots without errors (python app.py — Flask dev server on :5000)
  ✓ All endpoints respond correctly (5/5 pytest suites green + smoke test manual via curl)
  ✓ Zero anti-patterns remaining — dos 15 findings da Fase 2, todos foram corrigidos:
    - Hash MD5 sem salt → werkzeug generate_password_hash/check_password_hash
    - Senha devolvida pela API → removida de User.to_dict()
    - SECRET_KEY e credenciais SMTP hardcoded → config/settings.py via variáveis de ambiente
    - Token de autenticação falso e previsível → token assinado (itsdangerous), com expiração
    - Autorização ausente em rotas administrativas → require_admin (categorias, DELETE /users,
      troca de role/active em PUT /users)
    - Lógica de "task atrasada" duplicada 5x → todas as ocorrências chamam Task.is_overdue()
    - NotificationService e helpers de validação mortos → conectados ao fluxo real (create_task
      notifica o usuário atribuído; process_task_data/validate_email/is_valid_color/constantes
      agora são a fonte única de validação)
    - Queries N+1 (tasks, resumo por usuário, contagem por categoria) → joinedload/queries agregadas
    - except genérico → exceções específicas (SQLAlchemyError) com log da causa real
    - Validação inconsistente de categoria → name e color validados em create e update
    - datetime.utcnow() deprecated → utils.helpers.utcnow() em todos os arquivos afetados
    - Idiomas booleanos verbosos → simplificados para expressão booleana direta
    - Imports não utilizados → removidos
    - Mesmo shape serializado 3 formas diferentes → Task.to_dict() reaproveitado onde o contrato
      permitia (get_tasks passou a incluir os mesmos campos que já expunha, agora via to_dict());
      em /users/<id>/tasks o shape reduzido original foi mantido de propósito (contrato mais
      enxuto pré-existente), só a checagem de atraso passou a reaproveitar is_overdue()

Observação de design: como este projeto já tinha camadas físicas (models/routes/services/utils),
a Fase 3 não recriou a estrutura — conectou o que já existia e estava correto (helpers, service de
notificação) e adicionou apenas o necessário para fechar os achados de segurança (config/, middlewares/).
================================
