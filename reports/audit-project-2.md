================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js, CommonJS)
Framework:     Express ^4.18.2
Dependencies:  sqlite3 ^5.1.6 (callback-based driver, banco em memória)
Domain:        LMS API com fluxo de checkout (cursos, matrículas, pagamentos)
Architecture:  Monolítica — toda a aplicação (conexão de banco, schema, seed e as 3 rotas) concentrada
               em uma única classe `AppManager`, que o próprio código nomeia como "Frankenstein"
               (src/app.js:13). Sem separação entre transporte, persistência e regra de negócio.
Source files:  3 files analyzed (~180 lines of code)
DB tables:     users, courses, enrollments, payments, audit_logs
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express ^4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] God Class concentrando banco, schema, seed e todas as rotas
File: src/AppManager.js:4-141
Description: `AppManager` é dona da conexão sqlite (`:7`), do schema/seed (`initDb`, `:10-23`) e de toda a lógica das 3 rotas (`setupRoutes`, `:25-138`).
Impact: Zero separação de responsabilidade — impossível testar checkout, relatório ou exclusão isoladamente.
Recommendation: Dividir em Models (uma entidade cada), Controllers (orquestração) e Routes (transporte), conforme mvc-guidelines.md.

### [CRITICAL] Segredos de produção hardcoded no código-fonte
File: src/utils.js:2-6
Description: `dbPass`, `paymentGatewayKey` (formato de chave "live" de gateway) e `smtpUser` estão literais no módulo `config`.
Impact: Credenciais versionadas no Git são consideradas comprometidas permanentemente.
Recommendation: Mover para variáveis de ambiente lidas por `config/settings.js`.

### [CRITICAL] Número de cartão de crédito e chave de gateway logados em texto puro
File: src/AppManager.js:45
Description: `console.log` imprime o PAN completo do cartão junto com a `paymentGatewayKey`.
Impact: Violação grave de PCI-DSS — dado de cartão e segredo de gateway expostos em qualquer coletor de logs.
Recommendation: Nunca logar PAN completo (mascarar) nem segredos; remover a chave do log.

### [CRITICAL] "Criptografia" de senha falsa e reversível
File: src/utils.js:17-23 (`badCrypto`), usada em src/AppManager.js:68
Description: Não é hashing — concatena substrings de Base64 10.000 vezes e trunca para 10 caracteres.
Impact: Trivialmente reversível/colidível; nenhuma proteção real da senha do usuário.
Recommendation: Usar um algoritmo de hash de senha real (bcrypt) com salt.

### [HIGH] "Processamento de pagamento" é apenas checar se o cartão começa com "4"
File: src/AppManager.js:46
Description: Não existe integração com gateway nenhum — aprovação/recusa depende só do primeiro dígito do PAN.
Impact: Lógica de negócio crítica (pagamento) trivialmente manipulável; também está inline no meio do fluxo de checkout, sem isolamento.
Recommendation: Isolar em um serviço de pagamento dedicado (mesmo que mock, deve ser explícito e testável isoladamente).

### [HIGH] Callback hell de até 5 níveis no checkout, sem transação
File: src/AppManager.js:37-77
Description: Curso → usuário → pagamento → matrícula → log de auditoria, tudo em callbacks aninhados, sem transação.
Impact: Falha parcial no meio do fluxo deixa o banco inconsistente (ex.: matrícula criada sem pagamento registrado).
Recommendation: Reescrever com async/await + transação explícita (BEGIN/COMMIT/ROLLBACK).

### [HIGH] Endpoints administrativos sem nenhuma autenticação
File: src/AppManager.js:80-129 (`/api/admin/financial-report`), src/AppManager.js:131-137 (`DELETE /api/users/:id`)
Description: Relatório financeiro completo e exclusão de usuário acessíveis por qualquer chamador, sem checagem alguma.
Impact: Vazamento de dados financeiros e exclusão destrutiva por qualquer cliente anônimo.
Recommendation: Proteger com middleware de autenticação/autorização de admin.

### [HIGH] Exclusão de usuário admite deixar dados órfãos, sem cascade
File: src/AppManager.js:131-137
Description: O próprio texto de resposta confirma: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`
Impact: Viola integridade referencial; expõe a falha de design diretamente ao cliente da API.
Recommendation: Implementar exclusão em cascata (matrículas + pagamentos) dentro de uma transação.

### [MEDIUM] Queries N+1 severas no relatório financeiro
File: src/AppManager.js:80-129
Description: Uma query por curso, depois uma por matrícula, depois duas mais por matrícula (usuário + pagamento) — sequencial, com contadores manuais (`coursesPending`/`enrPending`) em vez de `Promise.all`/JOIN.
Impact: Custo cresce com cursos × matrículas; código frágil e difícil de seguir.
Recommendation: Substituir por uma única query com LEFT JOIN.

### [MEDIUM] Estado mutável global usado como cache/contador
File: src/utils.js:9-15 (`globalCache`, `totalRevenue`), mutado em `logAndCache`
Description: Variáveis de módulo top-level, mutadas por múltiplos handlers concorrentes, sem nenhuma proteção.
Impact: Compartilhado entre requisições concorrentes, comportamento não determinístico.
Recommendation: Remover/encapsular; não usar estado de módulo mutável para dados por requisição.

### [LOW] Erros de banco silenciosamente ignorados em vários pontos
File: src/AppManager.js:92,104,106,133
Description: Callbacks de `db.all`/`db.get` recebem `err` mas não o tratam antes de seguir.
Impact: Falha de banco passa despercebida, produzindo resposta incompleta em vez de erro claro.
Recommendation: Propagar todo erro para um handler central.

### [LOW] Nomes de parâmetro ilegíveis para dados sensíveis
File: src/AppManager.js:29-33 (`u`, `e`, `p`, `cid`, `cc`)
Description: Abreviações de uma/duas letras para nome, email, senha, id do curso e número do cartão.
Impact: Dificulta revisão de segurança — não é óbvio que `cc` é um PAN de cartão.
Recommendation: Nomear por extenso (`name`, `email`, `password`, `courseId`, `cardNumber`).

## Deprecated API check
Checagem da seção 14 do catálogo executada contra o runtime do ambiente (Node 18+,
Express ^4.18.2, sqlite3 ^5.1.6): nenhuma API formalmente deprecated em uso — sem
`new Buffer()`, `util.isArray`, `url.parse()` ou `crypto.createCipher()`. O driver
`sqlite3` é callback-based (estilo legado, não deprecated): tratado no finding [HIGH]
de callback hell, resolvido na Fase 3 promisificando o driver. Nenhum finding próprio gerado.

================================
Total: 12 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
ecommerce-api-legacy/
├── src/
│   ├── app.js                          # composition root (createApp, entry point)
│   ├── config/
│   │   ├── settings.js                 # PORT/ADMIN_API_KEY/PAYMENT_GATEWAY_KEY via env
│   │   └── database.js                 # sqlite3 promisificado + withTransaction + schema/seed
│   ├── models/
│   │   ├── userModel.js
│   │   ├── courseModel.js              # inclui a query única (JOIN) do relatório financeiro
│   │   ├── enrollmentModel.js
│   │   ├── paymentModel.js
│   │   └── auditLogModel.js
│   ├── services/
│   │   └── paymentGatewayService.js    # mock de pagamento isolado, PAN mascarado no log
│   ├── controllers/
│   │   ├── checkoutController.js       # async/await + transação (matrícula+pagamento+auditoria)
│   │   ├── financialReportController.js
│   │   └── userController.js           # exclusão em cascata (matrículas+pagamentos) em transação
│   ├── routes/
│   │   └── index.js                    # só delega para os controllers
│   └── middlewares/
│       ├── errorHandler.js             # AppError + handler centralizado
│       └── requireAdminKey.js          # protege as 2 rotas administrativas
└── tests/test-endpoints.js             # atualizado para o novo contrato de segurança

## Validation
  ✓ Application boots without errors (node src/app.js — "LMS API rodando na porta 3000...")
  ✓ All endpoints respond correctly (7/7 em npm test + smoke test manual via curl)
  ✓ Zero anti-patterns remaining — dos 12 findings da Fase 2, todos foram corrigidos:
    - God Class AppManager → Models + Services + Controllers + Routes
    - Segredos hardcoded (utils.js) → config/settings.js via variáveis de ambiente
    - Cartão de crédito e chave de gateway logados em texto puro → PAN mascarado, chave nunca logada
    - "Criptografia" de senha falsa (badCrypto) → bcrypt com salt
    - Autorização de pagamento inline e trivial → isolada em paymentGatewayService (mock explícito)
    - Callback hell sem transação → async/await + withTransaction (BEGIN/COMMIT/ROLLBACK)
    - Endpoints admin sem autenticação → requireAdminKey (X-Admin-Key) em ambos
    - Exclusão de usuário deixando dados órfãos → cascade (matrículas+pagamentos) em transação
    - Queries N+1 no relatório financeiro → uma única query com LEFT JOIN
    - Estado global mutável (globalCache/totalRevenue) → removido (não referenciado em nenhum fluxo real)
    - Erros de banco silenciosamente ignorados → toda falha propaga para o errorHandler central
    - Nomes ilegíveis (u/e/p/cid/cc) → nomes por extenso em todos os controllers/models
================================

================================
RE-EXECUÇÃO — Fase 1+2+3 (skill atualizada com reconferência de sinal por finding)
================================
Motivo: a validação acima marcou "Zero anti-patterns remaining" só com base em a lógica de
pagamento ter sido isolada em `paymentGatewayService.js` — sem reconferir se o sinal de
aprovação em si (Impact original: "trivialmente manipulável") tinha mudado. Não tinha: o código
isolado continuava `cardNumber.startsWith('4')`, aprovando qualquer cartão real ou inventado
com esse prefixo. A skill (`SKILL.md`, `anti-patterns-catalog.md` item 7, `refactoring-playbook.md`
padrão 13) foi corrigida para exigir essa reconferência antes de marcar um finding como corrigido.

## Nova Auditoria (Fase 1+2, sobre o código já uma vez refatorado)
CRITICAL: 0 | HIGH: 1 | MEDIUM: 0 | LOW: 1

### [HIGH] Sinal de aprovação de pagamento continua previsível/manipulável (isolamento não resolveu o Impact original)
File: src/services/paymentGatewayService.js:10-14 (antes da correção)
Description: `authorize()` decidia por `cardNumber.startsWith('4')` — a Fase 3 anterior só moveu essa
função de `AppManager.js` para um service dedicado, sem trocar o sinal.
Impact: Idêntico ao finding original — qualquer atacante aprova o próprio pagamento usando um
cartão (real ou inventado) começando com "4".
Recommendation: Padrão 13 do playbook — allowlist de cartões de teste documentados, deny-by-default.

### [LOW] `console.log` direto usado como logging de evento de negócio
File: src/services/paymentGatewayService.js:11 (antes da correção)
Description: Chamada direta de `console.log` para registrar a autorização, sem logger configurável
(catálogo item 16) — nunca tinha sido reportado porque a auditoria original focou na exposição do
PAN, não na ausência de logger.
Impact: Sem níveis de log/estrutura, impossível desligar ou redirecionar em produção.
Recommendation: Logger mínimo centralizado.

Total: 2 findings

## Fase 3 — aplicada (confirmação do usuário em 2026-09-21)
- `src/services/paymentGatewayService.js`: sinal trocado para `APPROVED_TEST_CARDS` (Set fechado de
  cartões de teste), deny-by-default; `console.log` trocado por `src/utils/logger.js` (novo, sem
  dependência externa).
- `tests/test-endpoints.js` e `api.http`: cartão do teste de sucesso trocado para `4242424242424242`
  (allowlist); teste de recusa trocado para `4111222233334444` — mesmo começando com "4", agora é
  negado, provando que o bypass antigo foi fechado.

## Validation (reconferida no código, não só na estrutura)
  ✓ Application boots without errors (node src/app.js — "LMS API rodando na porta 3000...")
  ✓ All endpoints respond correctly (7/7 em npm test)
  ✓ Zero anti-patterns remaining — reconferido lendo `paymentGatewayService.js` após a mudança:
    nenhum `startsWith` remanescente; `grep -n "APPROVED_TEST_CARDS" src/services/paymentGatewayService.js`
    confirma o novo sinal; smoke test manual via curl confirma `4242424242424242` → PAID e
    `4999999999999999` (começa com "4", fora da allowlist) → DENIED.
================================
