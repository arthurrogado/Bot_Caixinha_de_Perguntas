# Padrões de workflow

## Workflows sequenciais

Para tarefas complexas, quebre as operações em etapas claras e sequenciais. Muitas vezes ajuda dar ao Claude uma visão geral do processo logo no começo do SKILL.md:

```markdown
Preencher um formulário PDF envolve estas etapas:

1. Analisar o formulário (executar analyze_form.py)
2. Criar o mapeamento de campos (editar fields.json)
3. Validar o mapeamento (executar validate_fields.py)
4. Preencher o formulário (executar fill_form.py)
5. Verificar o output (executar verify_output.py)
```

## Workflows condicionais

Para tarefas com ramificações, guie o Claude pelos pontos de decisão:

```markdown
1. Determine o tipo de modificação:
   **Criando conteúdo novo?** → Siga o "workflow de criação" abaixo
   **Editando conteúdo existente?** → Siga o "workflow de edição" abaixo

2. Workflow de criação: [etapas]
3. Workflow de edição: [etapas]
```