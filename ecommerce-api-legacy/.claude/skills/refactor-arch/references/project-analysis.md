# Análise de Projeto — Heurísticas de Detecção

Conhecimento usado na **Fase 1 (Análise)**. Objetivo: identificar linguagem, framework, dependências, domínio e arquitetura atual **sem assumir nenhuma stack específica** — as heurísticas abaixo são baseadas em arquivos-marcadores (manifest files) e padrões de import, não em uma linguagem fixa.

## 1. Detecção de linguagem e gerenciador de pacotes

Procure, na raiz do projeto, por arquivos de manifesto (`ls -a` na raiz e um nível abaixo):

| Arquivo encontrado | Linguagem | Gerenciador |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | pip / poetry / pipenv |
| `package.json` | JavaScript/TypeScript (Node.js) | npm / yarn / pnpm |
| `go.mod` | Go | go modules |
| `pom.xml`, `build.gradle` | Java/Kotlin | Maven / Gradle |
| `Gemfile` | Ruby | Bundler |
| `composer.json` | PHP | Composer |

Se houver `tsconfig.json` junto de `package.json`, classifique como TypeScript; caso contrário, JavaScript puro.

## 2. Detecção de framework

Leia o arquivo de manifesto encontrado e cruze as dependências declaradas com padrões conhecidos:

- **Python:** `flask` → Flask · `django` → Django · `fastapi` → FastAPI · `sqlalchemy`/`flask-sqlalchemy` → indica uso de ORM.
- **Node.js:** `express` → Express · `fastify` → Fastify · `@nestjs/core` → NestJS · `koa` → Koa.
- Extraia também a **versão declarada** (ex.: `Flask==3.1.1`, `"express": "^4.18.2"`) para reportar no resumo da Fase 1.

Se nenhum framework for reconhecido, procure o ponto de entrada (`app.py`, `main.py`, `index.js`, `server.js`) e infira pelo padrão de código (ex.: `app.listen(...)` sugere um servidor HTTP manual; `app.add_url_rule` ou `@app.route` confirma Flask mesmo sem checar a versão).

## 3. Detecção de banco de dados

- Procure strings de conexão, imports de drivers (`sqlite3`, `psycopg2`, `pg`, `mysql2`, `mongoose`) e arquivos `.db`/`.sqlite` na raiz.
- Se houver um ORM (SQLAlchemy, Sequelize, Prisma, Mongoose), liste as **entidades/tabelas** a partir das classes de model ou dos `CREATE TABLE` embutidos em código (comum em projetos legados que criam o schema manualmente, sem migrations).
- Reporte o nome de cada tabela/coleção encontrada.

## 4. Mapeamento da arquitetura atual

Não assuma que a presença de pastas como `models/`, `routes/`, `controllers/` significa que a arquitetura está correta — **organização física de arquivos não é o mesmo que separação real de responsabilidades**. Para cada arquivo-fonte relevante, verifique:

- Ele mistura definição de rotas **e** acesso a banco **e** regra de negócio no mesmo arquivo/função? → indício de God File/God Class.
- Existe uma pasta de camada (ex.: `services/`) que nunca é importada por nenhuma rota? → camada morta, não conta como separação real.
- Handlers de rota chamam o ORM/driver diretamente, sem passar por nenhuma função intermediária? → ausência de camada de Model real.

Classifique a arquitetura observada em uma frase curta, por exemplo:
- "Monolítica — tudo em N arquivos, sem separação de camadas"
- "Camadas nominais presentes (models/routes/services), mas regra de negócio duplicada nas rotas e serviço não utilizado"

## 5. Domínio da aplicação

Infira o domínio de negócio a partir dos nomes de tabelas/entidades e das rotas (ex.: tabelas `produtos`, `pedidos`, `usuarios` → e-commerce; `courses`, `enrollments`, `payments` → LMS com checkout; `tasks`, `categories`, `users` → gestão de tarefas). Descreva em uma linha curta.

## 6. Resumo a imprimir ao final da Fase 1

Sempre reporte, no formato do template abaixo, preenchido com os dados reais coletados (não invente números — conte os arquivos-fonte de fato analisados):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <libs relevantes>
Domain:        <domínio inferido>
Architecture:  <frase curta sobre a arquitetura atual>
Source files:  <N> files analyzed
DB tables:     <lista de tabelas/coleções>
================================
```
