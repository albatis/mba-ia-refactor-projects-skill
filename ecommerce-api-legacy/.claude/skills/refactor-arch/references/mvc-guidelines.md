# Guidelines de Arquitetura — Padrão MVC Alvo

Conhecimento usado na **Fase 3 (Refatoração)** para decidir a estrutura final, independentemente da linguagem/framework detectado na Fase 1.

## Camadas e responsabilidades

### Models (dados + regras invariantes da entidade)
- Representam uma entidade de domínio (ex.: `Produto`, `Usuario`, `Pedido`, `Task`).
- Contêm apenas: definição de schema/campos, validações intrínsecas do próprio dado (ex.: "status precisa ser um dos valores válidos"), e métodos que operam somente sobre os próprios dados (ex.: `is_overdue()`).
- **Não** contêm: acesso a `request`/`req`, chamadas HTTP, lógica de orquestração entre múltiplas entidades, formatação de resposta HTTP.
- Acesso a banco fica isolado aqui (ou em um Repository interno ao Model) — nunca com SQL concatenado; sempre com parâmetros/bind ou ORM.

### Views / Routes (transporte HTTP)
- Recebem a requisição, fazem parsing/validação de formato de entrada (tipos, campos obrigatórios), chamam o Controller correspondente, e traduzem o resultado para a resposta HTTP (status code + corpo).
- **Não** contêm regra de negócio nem acesso direto a banco — apenas delegação.
- Devem ter mapeamento 1:1 claro entre rota e método de Controller.

### Controllers (orquestração / regra de negócio de aplicação)
- Recebem dados já validados da Route, orquestram um ou mais Models/Services para executar o caso de uso (ex.: `criar_pedido`: valida estoque, calcula total, persiste, aciona notificação).
- Concentram as decisões de negócio que envolvem mais de uma entidade — é aqui que mora o "fluxo".
- Não devem formatar resposta HTTP diretamente nem acessar `request` bruto (isso é responsabilidade da Route, que já passou os dados prontos).

### Camadas de suporte (mantidas quando fizer sentido para o projeto)
- **Config:** centraliza leitura de variáveis de ambiente/segredos (nunca hardcoded). Um módulo único (`config/settings.*`) do qual todos os outros módulos leem.
- **Middlewares / Error handling:** tratamento de erro centralizado (um único ponto que decide o formato de erro da API), em vez de `try/except`/`try/catch` genérico repetido em cada handler.
- **Services** (opcional, quando a lógica de negócio for complexa o bastante para justificar): usados quando o Controller ficaria muito grande, ou quando a lógica precisa ser reutilizada fora do contexto HTTP. Se o projeto já tiver uma pasta `services/` mas ela não for usada, decida entre (a) conectá-la de fato ao fluxo ou (b) removê-la — nunca deixar código morto.

## Estrutura de diretórios alvo (adaptar aos nomes idiomáticos da linguagem)

```
src/
├── config/            # configuração, leitura de env vars, segredos
├── models/            # uma entidade por arquivo
├── views/ (ou routes/)# definição das rotas HTTP, validação de entrada
├── controllers/        # orquestração dos casos de uso
├── middlewares/        # error handling centralizado, auth, etc.
└── app.py|app.js       # composition root: monta app, registra rotas, sobe servidor
```

Adapte nomes de pastas à convenção idiomática da stack (`views/` para Flask-style, `routes/` quando o framework já usa esse termo, camelCase vs snake_case conforme a linguagem) — o que importa é a separação de responsabilidade, não o nome literal da pasta.

## Regras de decisão para a Fase 3

1. **Nunca misture camadas no mesmo arquivo** no resultado final — cada anti-pattern do tipo "God Class/God File" deve terminar dividido entre pelo menos Model + Controller + Route.
2. **Toda configuração/segredo vira variável de ambiente**, lida em um único módulo de config, nunca literal espalhado pelo código. Gere um `.env.example` (sem valores reais) documentando as chaves esperadas.
3. **Toda query SQL concatenada vira query parametrizada** (ou chamada de ORM, se o projeto já usar um).
4. **Toda regra de negócio encontrada em Controller/Route na auditoria migra para a camada correta** — mantendo o comportamento observável (mesmos endpoints, mesmos contratos de request/response) a menos que o comportamento seja o próprio bug de segurança (ex.: endpoint que executa SQL arbitrário deve ser removido ou protegido, não apenas "reorganizado").
5. **Tratamento de erro é centralizado** — um único handler/middleware traduz exceções em respostas HTTP consistentes; handlers individuais não devem mais ter `try/except` genérico devolvendo `str(e)` ao cliente.
6. **Preserve o contrato externo da API** (mesmas rotas, mesmos métodos HTTP, mesmo formato de payload de sucesso) sempre que a Fase 1/2 não tiver identificado o contrato atual como parte do problema — o objetivo é reestruturar internamente, não quebrar consumidores existentes.
7. **Projetos que já têm alguma separação de camadas** (ex.: já possuem `routes/`, `services/`, `models/`) não devem ser "refeitos do zero" — identifique especificamente onde a separação é apenas nominal (camada morta, lógica duplicada, rota chamando ORM direto) e corrija esses pontos, preservando o que já está correto.
