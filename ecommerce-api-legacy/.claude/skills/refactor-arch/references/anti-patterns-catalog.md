# Catálogo de Anti-Patterns

Conhecimento usado na **Fase 2 (Auditoria)**. Para cada anti-pattern: sinais de detecção (agnósticos de linguagem, com exemplos por stack), severidade e o porquê. Cruze o código contra esta lista arquivo por arquivo; todo finding deve citar **arquivo e linha(s) exatas**.

Regra de severidade (mesma do desafio): **CRITICAL** = falha grave de arquitetura/segurança ou exposição de dados sensíveis; **HIGH** = violação forte de MVC/SOLID que dificulta muito manutenção/teste; **MEDIUM** = padronização/duplicação/performance moderada; **LOW** = legibilidade/nomenclatura/magic numbers.

---

### 1. God Class / God File (CRITICAL)
**Sinal:** um único arquivo/classe concentra roteamento + acesso a dados + regra de negócio + configuração. Heurística prática: arquivo com mais de ~150 linhas cobrindo mais de uma responsabilidade, ou uma classe cujos métodos tocam banco de dados diretamente e também formatam a resposta HTTP.
**Exemplos observados:** `models.py` fazendo o papel de model+DAO com SQL cru; `AppManager.js` concentrando conexão, schema, seed e todas as rotas.
**Por quê:** impossível testar em isolamento; qualquer mudança tem raio de impacto total.

### 2. Injeção de SQL / concatenação de query (CRITICAL)
**Sinal:** strings de SQL montadas com `+`, f-string ou template literal usando dado vindo de `request`/`req.body`/`req.params`, em vez de placeholders (`?`, `%s`, bind parameters do ORM).
**Detecção:** grep por `"SELECT" +`, `f"...{`, `` `...${ `` próximos de `.execute(`/`db.run(`/`db.get(`/`db.all(`.
**Por quê:** permite manipulação/exfiltração/bypass de autenticação via input do usuário.

### 3. Segredos hardcoded no código-fonte (CRITICAL)
**Sinal:** valores literais para `SECRET_KEY`, senhas de banco, API keys, credenciais SMTP, atribuídos diretamente em código (`= "..."`), em vez de lidos de variável de ambiente/`.env`/secret manager.
**Detecção:** grep por `secret`, `password`, `senha`, `api_key`, `token` seguidos de `=` e uma string literal.
**Por quê:** credencial versionada no Git é considerada comprometida permanentemente.

### 4. Autenticação/hash de senha quebrados (CRITICAL)
**Sinal:** senha comparada em texto puro; hashing com algoritmo não seguro para senha (MD5, SHA1 sem salt) ou "criptografia" caseira reversível; token de sessão/JWT falso (string concatenada manualmente, ex. `"fake-jwt-" + id`).
**Por quê:** compromete toda a camada de autenticação da aplicação.

### 5. Endpoint administrativo sem autorização (CRITICAL)
**Sinal:** rota que executa ações destrutivas ou sensíveis (reset de banco, execução de SQL arbitrário, exclusão de usuário, relatório financeiro) sem nenhuma checagem de autenticação/autorização antes de executar.
**Por quê:** qualquer chamador anônimo pode executar a ação.

### 6. Exposição de dados sensíveis na resposta da API (CRITICAL/HIGH conforme o dado)
**Sinal:** serialização (`to_dict`, `JSON.stringify`, resposta manual) que inclui campos como senha/hash, chave secreta, dados de cartão.
**Por quê:** vaza segredo mesmo quando o armazenamento está correto.

### 7. Lógica de negócio dentro do Controller/Route (HIGH)
**Sinal:** cálculos, regras de aprovação/estoque/pagamento, ou orquestração multi-etapas escritos diretamente dentro da função de rota, sem uma camada de serviço/domínio intermediária.
**Por quê:** viola a separação Model-View-Controller — o Controller deveria orquestrar, não conter a regra.

### 8. Acoplamento forte / ausência de injeção de dependência (HIGH)
**Sinal:** módulo que cria sua própria conexão de banco, cliente HTTP ou dependência externa diretamente dentro da função de negócio, em vez de recebê-la como parâmetro/serviço injetado.
**Por quê:** impossível testar com mocks/stubs; qualquer troca de infraestrutura exige editar lógica de negócio.

### 9. Estado global mutável (HIGH)
**Sinal:** variável de módulo (`global`, `let cache = {}` no top-level, singleton mutável) alterada por múltiplos handlers concorrentes, sem nenhuma proteção.
**Por quê:** condição de corrida e comportamento não determinístico sob concorrência.

### 10. Fluxo assíncrono sem transação / "callback hell" (HIGH)
**Sinal:** múltiplos callbacks aninhados (≥3 níveis) ou múltiplas operações de escrita sequenciais sem transação, onde uma falha no meio do fluxo deixa o banco em estado inconsistente.
**Por quê:** viola atomicidade; bugs de estado parcial são difíceis de reproduzir.

### 11. Queries N+1 (MEDIUM)
**Sinal:** loop `for`/`.map`/`.forEach` que executa uma nova query de banco a cada iteração, quando um único JOIN/`IN (...)`/eager load resolveria.
**Por quê:** degrada performance linearmente com o volume de dados.

### 12. Duplicação de lógica / validação (MEDIUM)
**Sinal:** o mesmo bloco de validação, cálculo ou serialização copiado em 2+ lugares, ou uma função utilitária pronta que existe mas nunca é importada (código morto por duplicação).
**Por quê:** correções e mudanças de regra precisam ser replicadas manualmente — fonte comum de bugs de "esqueci de atualizar aqui também".

### 13. Tratamento de erro genérico demais (MEDIUM/LOW conforme exposição)
**Sinal:** `except Exception`/`catch (e)` amplo que devolve `str(e)`/`e.message` cru ao cliente, tratando toda falha (validação, bug, infra) da mesma forma.
**Por quê:** vaza detalhes internos e impede tratamento diferenciado por tipo de erro.

### 14. Uso de API deprecated (MEDIUM — reclassificar conforme o caso)
**Sinal e exemplos concretos a checar:**
- Python: `datetime.utcnow()`/`datetime.utcfromtimestamp()` → deprecated desde Python 3.12, substituir por `datetime.now(timezone.utc)`.
- Python: `flask.Markup` movido para `markupsafe.Markup`.
- Node/Express: middlewares embutidos removidos (`express.bodyParser()`, `express.json()` ausente quando necessário), `new Buffer()` deprecated em favor de `Buffer.from()`.
- Dependência declarada no manifesto mas nunca importada em lugar nenhum (ex.: `marshmallow` em `requirements.txt` sem nenhum `import marshmallow`) — não é bem "deprecated" mas indica dependência morta/abandonada; reportar como MEDIUM/LOW.
**Como validar:** confirme a versão da linguagem/runtime disponível no ambiente (`python --version`, `node --version`) antes de classificar como deprecated, pois o corte de versão importa.

### 15. Magic numbers / strings e nomenclatura ruim (LOW)
**Sinal:** literais numéricos ou strings de domínio (status, limiares, taxas) espalhados pelo código sem constante/enum nomeado; nomes de variável de uma letra para dados sensíveis (`cc`, `u`, `p`).
**Por quê:** dificulta leitura e alteração segura da regra.

### 16. `print()`/`console.log()` como logging (LOW)
**Sinal:** chamadas diretas de print/console.log para registrar eventos de negócio, em vez de um logger configurável.
**Por quê:** sem níveis de log, sem estrutura, impossível desligar em produção.

---

## Como reportar cada finding

Para cada ocorrência encontrada, produza um item com: título do anti-pattern, severidade, arquivo:linha(s) exatos, descrição de 1-2 frases, impacto, e recomendação objetiva (o que fazer — referencie o playbook de refatoração quando aplicável). Nunca agrupe achados de arquivos/linhas diferentes em um único item "genérico" — cada ocorrência distinta é um finding separado, mesmo que sejam do mesmo anti-pattern.
