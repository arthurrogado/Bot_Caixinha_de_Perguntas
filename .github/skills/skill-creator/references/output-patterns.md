# Padrões de Output

Use estes padrões quando skills precisarem produzir outputs consistentes e de alta qualidade.

## Padrão de template

Forneça templates para o formato do output. Ajuste o nível de rigidez conforme sua necessidade.

**Para requisitos rígidos (como respostas de API ou formatos de dados):**

```markdown
## Estrutura do relatório

SEMPRE use exatamente esta estrutura de template:

# [Título da análise]

## Resumo executivo
[Visão geral em um parágrafo dos principais achados]

## Principais achados
- Achado 1 com dados de suporte
- Achado 2 com dados de suporte
- Achado 3 com dados de suporte

## Recomendações
1. Recomendação específica e acionável
2. Recomendação específica e acionável
```

**Para orientação flexível (quando adaptação é útil):**

```markdown
## Estrutura do relatório

Aqui está um formato padrão sensato, mas use seu bom senso:

# [Título da análise]

## Resumo executivo
[Visão geral]

## Principais achados
[Adapte as seções com base no que você encontrar]

## Recomendações
[Ajuste ao contexto específico]

Ajuste as seções conforme o tipo específico de análise.
```

## Padrão de exemplos

Para skills em que a qualidade do output depende de ver exemplos, forneça pares de input/output:

```markdown
## Formato de mensagem de commit

Gere mensagens de commit seguindo estes exemplos:

**Exemplo 1:**
Input: Added user authentication with JWT tokens
Output:
```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**Exemplo 2:**
Input: Fixed bug where dates displayed incorrectly in reports
Output:
```
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation
```

Siga este estilo: type(scope): descrição curta, depois explicação detalhada.
```

Exemplos ajudam o Claude a entender o estilo e o nível de detalhe desejados com mais clareza do que descrições sozinhas.
