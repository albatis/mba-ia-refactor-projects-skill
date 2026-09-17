# Playbook de Refatoração

Conhecimento usado na **Fase 3 (Refatoração)**. Cada padrão abaixo mapeia para um ou mais anti-patterns do catálogo e mostra a transformação concreta. Adapte a sintaxe ao idioma da stack detectada — o princípio é o mesmo.

---

### 1. SQL concatenado → query parametrizada
Mapeia: *Injeção de SQL*.

```python
# Antes
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

# Depois
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```
```javascript
// Antes
db.get(`SELECT * FROM users WHERE email = '${email}'`)

// Depois
db.get("SELECT * FROM users WHERE email = ?", [email])
```

### 2. Segredo hardcoded → variável de ambiente + módulo de config
Mapeia: *Segredos hardcoded*.

```python
# Antes
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"

# Depois — config/settings.py
import os
SECRET_KEY = os.environ["SECRET_KEY"]  # falha explícita se não configurado

# app.py
from config.settings import SECRET_KEY
app.config["SECRET_KEY"] = SECRET_KEY
```
Gerar `.env.example` com `SECRET_KEY=changeme` (sem o valor real) documentando a chave esperada.

### 3. Senha em texto puro / hash fraco → hash seguro com salt
Mapeia: *Autenticação/hash de senha quebrados*.

```python
# Antes
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

# Depois
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password_hash = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password_hash, pwd)
```
E remover o campo de senha/hash de qualquer `to_dict()`/serialização de resposta.

### 4. God Class/God File → separação em Model + Controller + Route
Mapeia: *God Class*, *lógica de negócio no Controller*.

```
# Antes: um arquivo único
models.py  →  SQL cru + validação + formatação de resposta

# Depois
models/produto_model.py     → acesso a dados da entidade Produto (queries parametrizadas)
controllers/produto_controller.py → orquestra caso de uso (ex.: criar_produto: valida regra de negócio, chama o model)
views/routes.py                    → define a rota HTTP, chama o controller, traduz para JSON
```
Regra prática: se uma função faz `cursor.execute(...)` **e** monta a resposta JSON **e** decide uma regra de negócio, ela deve ser dividida em três funções, uma por camada.

### 5. Endpoint administrativo sem autorização → proteger ou remover
Mapeia: *Endpoint administrativo sem autorização*.

```python
# Antes
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)  # SQL arbitrário do cliente

# Depois: remover o endpoint (não existe caso de uso legítimo para
# executar SQL arbitrário vindo do cliente) e, para os demais endpoints
# administrativos legítimos (ex.: reset de dados em ambiente de teste),
# adicionar um middleware de autenticação/autorização antes do handler:

@app.route("/admin/reset-db", methods=["POST"])
@require_admin_auth
def reset_database():
    ...
```

### 6. Queries N+1 → query única com JOIN/eager load
Mapeia: *Queries N+1*.

```python
# Antes
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))

# Depois
cursor.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total,
           ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    JOIN itens_pedido ip ON ip.pedido_id = p.id
    JOIN produtos pr ON pr.id = ip.produto_id
""")
# agrupar as linhas por pedido_id em memória, uma única ida ao banco
```

### 7. Validação/lógica duplicada → função/helper único reutilizado
Mapeia: *Duplicação de lógica*.

```python
# Antes: bloco de validação repetido em criar_produto() e atualizar_produto()

# Depois
def validar_produto(dados):
    erros = []
    if "nome" not in dados: erros.append("Nome é obrigatório")
    if dados.get("preco", -1) < 0: erros.append("Preço não pode ser negativo")
    ...
    return erros

def criar_produto():
    erros = validar_produto(dados)
    ...

def atualizar_produto(id):
    erros = validar_produto(dados)
    ...
```
Se o projeto já possui um helper pronto e não usado (ex.: `utils/helpers.py:process_task_data`), a refatoração é **conectar** o helper existente às rotas, em vez de escrever um novo.

### 8. Tratamento de erro disperso → error handler centralizado
Mapeia: *Tratamento de erro genérico demais*.

```python
# Antes: try/except Exception em cada handler, retornando str(e)

# Depois — middlewares/error_handler.py
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"erro": str(e)}), 400

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    app.logger.exception(e)
    return jsonify({"erro": "Erro interno"}), 500
```
```javascript
// Node/Express — middleware de erro no final da cadeia
app.use((err, req, res, next) => {
  logger.error(err);
  res.status(err.status || 500).json({ error: err.publicMessage || "Erro interno" });
});
```

### 9. Callback hell / falta de transação → async/await + transação
Mapeia: *Fluxo assíncrono sem transação*.

```javascript
// Antes: 5 callbacks aninhados, sem transação

// Depois
async function checkout(courseId, userId, cardNumber) {
  return db.transaction(async (trx) => {
    const course = await trx.get("SELECT * FROM courses WHERE id = ?", [courseId]);
    const payment = await processPayment(cardNumber, course.price); // serviço isolado, mockável em teste
    await trx.run("INSERT INTO enrollments ...");
    await trx.run("INSERT INTO payments ...");
    return { status: "PAID", enrollmentId: ... };
  });
}
```

### 10. Estado global mutável → escopo local / serviço com estado encapsulado
Mapeia: *Estado global mutável*.

```javascript
// Antes
let globalCache = {};
let totalRevenue = 0;

// Depois — encapsulado numa classe/serviço injetado, sem mutação de módulo top-level
class RevenueTracker {
  constructor() { this._total = 0; }
  add(value) { this._total += value; }
  get total() { return this._total; }
}
```

### 11. Magic numbers/strings → constantes nomeadas
Mapeia: *Magic numbers*.

```python
# Antes
if faturamento > 10000:
    desconto = faturamento * 0.1

# Depois
DESCONTO_TIER_1 = (10000, 0.10)
DESCONTO_TIER_2 = (5000, 0.05)
DESCONTO_TIER_3 = (1000, 0.02)

def calcular_desconto(faturamento):
    for limite, taxa in (DESCONTO_TIER_1, DESCONTO_TIER_2, DESCONTO_TIER_3):
        if faturamento > limite:
            return faturamento * taxa
    return 0
```

### 12. API deprecated → equivalente moderno
Mapeia: *Uso de API deprecated*.

```python
# Antes
criado_em = datetime.utcnow()

# Depois
from datetime import datetime, timezone
criado_em = datetime.now(timezone.utc)
```

---

## Ordem de execução recomendada na Fase 3

1. Criar a nova estrutura de diretórios (vazia).
2. Mover/criar Models (dados + queries parametrizadas).
3. Extrair Services quando necessário (regra de negócio complexa/reutilizável).
4. Criar Controllers chamando Models/Services.
5. Reescrever Routes/Views para apenas delegar ao Controller.
6. Extrair configuração/segredos para o módulo de config + `.env.example`.
7. Centralizar tratamento de erro.
8. Atualizar o entry point (composition root) para montar tudo.
9. Rodar a suíte de testes/validação (ver próxima seção) antes de considerar a fase concluída.
10. Remover arquivos antigos que ficaram órfãos após a migração.
