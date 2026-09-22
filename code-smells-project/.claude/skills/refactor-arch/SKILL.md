---
name: refactor-arch
description: Analisa uma codebase de backend (qualquer linguagem/framework), audita anti-patterns de arquitetura/segurança/qualidade classificados por severidade (CRITICAL/HIGH/MEDIUM/LOW) com arquivo e linha exatos, gera um relatório estruturado e refatora o projeto para o padrão MVC, validando que a aplicação continua funcionando. Use quando o usuário pedir para analisar, auditar ou refatorar a arquitetura de um projeto para MVC, ou invocar "/refactor-arch".
---

# refactor-arch

Você é um especialista em arquitetura de software atuando como auditor e refatorador automatizado. Este projeto (o diretório de trabalho atual) é o alvo. Você **não sabe de antemão** qual linguagem/framework ele usa — descubra isso na Fase 1.

Esta skill é **agnóstica de tecnologia**: as heurísticas e o catálogo abaixo cobrem múltiplas linguagens/frameworks. Nunca assuma Python/Flask por padrão — sempre detecte.

O conhecimento de domínio necessário para cada fase está nos arquivos de referência desta skill (mesma pasta deste `SKILL.md`, em `references/`). Leia cada um **antes** de executar a fase correspondente:

| Fase | Arquivo de referência a ler primeiro |
|---|---|
| Fase 1 | `references/project-analysis.md` |
| Fase 2 | `references/anti-patterns-catalog.md` e `references/audit-report-template.md` |
| Fase 3 | `references/mvc-guidelines.md` e `references/refactoring-playbook.md` |

Execute as três fases **sequencialmente, em turnos separados quando houver um gate de confirmação** (ver Fase 2 → Fase 3 abaixo). Nunca pule uma fase nem produza a saída de uma fase sem antes ler o(s) arquivo(s) de referência correspondente(s).

## Fase 1 — Análise

1. Leia `references/project-analysis.md`.
2. Liste os arquivos do projeto (ignore `node_modules/`, `venv/`, `__pycache__/`, `.git/`, arquivos de banco `.db`, caches de teste) e leia os arquivos-fonte relevantes por completo — não infira conteúdo de código sem ler.
3. Aplique as heurísticas do arquivo de referência para detectar linguagem, framework (+ versão), dependências relevantes, banco de dados/tabelas, domínio de negócio e uma descrição curta da arquitetura atual.
4. Imprima o resumo exatamente no formato definido em `project-analysis.md` (bloco `PHASE 1: PROJECT ANALYSIS`).
5. Continue diretamente para a Fase 2 no mesmo turno (não é necessário parar aqui).

## Fase 2 — Auditoria

1. Leia `references/anti-patterns-catalog.md` e `references/audit-report-template.md`.
2. Cruze cada arquivo-fonte lido na Fase 1 contra o catálogo de anti-patterns. Para cada ocorrência real (não hipotética) encontrada, registre: anti-pattern, severidade, arquivo:linha(s) exatos, descrição, impacto e recomendação.
3. Inclua explicitamente uma checagem de **APIs deprecated** (seção 14 do catálogo) — confirme a versão de linguagem/runtime disponível no ambiente antes de classificar algo como deprecated.
4. Monte e imprima o relatório completo seguindo **exatamente** o formato de `audit-report-template.md`, incluindo o `Summary` com contagem por severidade e a lista de findings ordenada por severidade.
5. Termine a resposta com a pergunta de confirmação do template (`Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`) e **pare — não escreva nem edite nenhum arquivo do projeto nesta fase**. A Fase 3 só deve começar em uma mensagem/turno posterior, após o usuário responder afirmativamente (ex.: "y", "sim", "prossiga").

## Fase 3 — Refatoração

Só execute esta fase depois de uma confirmação explícita e afirmativa do usuário em resposta à pergunta da Fase 2. Se a resposta for negativa ou ambígua, não modifique nenhum arquivo e peça esclarecimento.

1. Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.
2. Para cada finding do relatório da Fase 2, aplique o padrão de transformação correspondente do playbook, seguindo as regras de decisão e a ordem de execução recomendada em `mvc-guidelines.md`.
3. Preserve o contrato externo da API (mesmas rotas, métodos e formato de payload) exceto quando o próprio contrato for o problema de segurança (ex.: endpoint que executa SQL arbitrário deve ser removido/protegido, não preservado).
4. Se o projeto já tiver alguma separação de camadas, não reescreva do zero — corrija especificamente os pontos identificados na auditoria (camadas mortas, duplicação, acesso direto a dados nas rotas), preservando o que já está correto.
5. **Reconfira cada finding no código, não apenas na estrutura.** Mover/isolar código para a camada certa não é, por si só, prova de que um finding foi corrigido. Para cada finding do relatório da Fase 2, depois de aplicar a transformação:
   - Releia o trecho de código que hoje implementa aquele comportamento no novo local (arquivo:linha reais, não a lembrança da Fase 2).
   - Compare esse código contra o `Description`/`Impact` original do finding — não contra a `Recommendation` isoladamente. Pergunte: "o comportamento problemático descrito no Impact ainda existe, só que em outro arquivo?" (ex.: uma regra de aprovação que continua sendo `input.startsWith(x)`, um segredo que ainda aparece como literal em algum módulo, uma query que ainda concatena string, mesmo que agora dentro de um Model).
   - Se o sinal/comportamento do Impact ainda estiver presente, o finding **não** está corrigido — corrija o comportamento de fato (use o padrão correspondente de `refactoring-playbook.md`; para decisões de negócio previsíveis/manipuláveis, ver padrão 13) antes de seguir.
   - Só é aceitável listar um finding como pendente (em vez de corrigido) quando a correção completa depender de uma decisão de produto fora do escopo da refatoração (ex.: credencial real de um gateway externo que não existe neste ambiente) — e nesse caso a saída da Fase 3 deve dizer isso explicitamente, nunca marcar `Zero anti-patterns remaining`.
6. Depois de mover e reconferir o código, **valide o resultado**:
   - Instale dependências e suba a aplicação (use o comando documentado no README do projeto, se existir) e confirme que ela inicia sem erro.
   - Rode a suíte de testes automatizada do projeto, se existir (`pytest`, `npm test`, etc.), e/ou faça chamadas manuais aos endpoints principais para confirmar que continuam respondendo como antes.
   - Se algo quebrar, corrija antes de concluir — não entregue uma refatoração que derrubou a aplicação.
7. Imprima o resultado final exatamente no formato abaixo, com a estrutura de diretórios **real** criada (não um template genérico) e o resultado real da validação. A linha `Zero anti-patterns remaining` só pode ser afirmativa se o passo 5 (reconferência por finding) confirmou isso para os 12/N findings — caso contrário, liste os que restaram e por quê, mesmo que a aplicação suba e os testes passem:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
{{árvore real de diretórios/arquivos criados}}

## Validation
  {{✓ ou ✗}} Application boots without errors
  {{✓ ou ✗}} All endpoints respond correctly
  {{✓ ou ✗}} Zero anti-patterns remaining (ou lista dos que restaram e por quê)
================================
```

8. Não faça commit — deixe as mudanças no working tree para o desenvolvedor revisar e commitar.
