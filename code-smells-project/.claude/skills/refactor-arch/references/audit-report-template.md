# Template do Relatório de Auditoria (saída da Fase 2)

Use exatamente este formato ao imprimir o relatório da Fase 2. `{{...}}` são placeholders a preencher com dados reais coletados na análise — nunca invente números.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: {{nome do projeto}}
Stack:   {{linguagem + framework}}
Files:   {{N}} analyzed | ~{{N}} lines of code

## Summary
CRITICAL: {{n}} | HIGH: {{n}} | MEDIUM: {{n}} | LOW: {{n}}

## Findings

### [{{SEVERIDADE}}] {{Nome do anti-pattern}}
File: {{arquivo}}:{{linha ou intervalo de linhas}}
Description: {{1-2 frases descrevendo o que foi encontrado}}
Impact: {{consequência concreta}}
Recommendation: {{ação objetiva, referenciando o padrão do playbook quando aplicável}}

### [{{SEVERIDADE}}] {{...}}
...

================================
Total: {{N}} findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de formatação

- **Ordene os findings por severidade** (CRITICAL → HIGH → MEDIUM → LOW); dentro da mesma severidade, ordene pela ordem em que aparecem no código-fonte (primeiro arquivo, depois linha).
- **Nunca omita `File:`** — todo finding precisa de arquivo e linha(s) exatos; se o problema for transversal (ex.: padrão repetido em vários arquivos), liste um finding por ocorrência, não um finding agregando vários locais.
- O `Summary` deve bater exatamente com a contagem de itens em `## Findings`.
- Sempre termine o relatório com a pergunta de confirmação (`Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`) e **pare a execução aqui** — a Fase 3 só começa após resposta afirmativa explícita do usuário na próxima mensagem. Nunca prossiga automaticamente para a Fase 3 na mesma resposta.
