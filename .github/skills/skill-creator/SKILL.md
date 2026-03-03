---
name: skill-creator
description: Guia para criar skills eficazes. Use esta skill quando usuários quiserem criar uma nova skill (ou atualizar uma existente) para estender as capacidades do Claude com conhecimento especializado, fluxos de trabalho e/ou integrações com ferramentas.
license: Complete terms in LICENSE.txt
---

# Criador de Skills

Esta skill fornece orientações para criar skills eficazes.

## Sobre Skills

Skills são pacotes modulares e autocontidos que estendem as capacidades do Claude ao fornecer
conhecimento especializado, fluxos de trabalho e ferramentas. Pense nelas como "guias de onboarding"
para domínios ou tarefas específicas — elas transformam o Claude de um agente generalista em um
agente especializado, equipado com conhecimento procedimental que nenhum modelo consegue dominar
completamente.

### O que Skills oferecem

1. Fluxos de trabalho especializados — procedimentos em múltiplas etapas para domínios específicos
2. Integrações com ferramentas — instruções para trabalhar com formatos de arquivo ou APIs
3. Conhecimento de domínio — conhecimento específico da empresa, schemas e regras de negócio
4. Recursos embarcados — scripts, referências e assets para tarefas complexas e repetitivas

## Princípios fundamentais

### Ser conciso é essencial

A janela de contexto é um bem compartilhado. Skills dividem essa janela com tudo o que o Claude precisa: prompt de sistema, histórico da conversa, metadados de outras skills e o pedido real do usuário.

**Premissa padrão: o Claude já é muito inteligente.** Só adicione contexto que ele não teria. Questione cada pedaço de informação: "O Claude realmente precisa desta explicação?" e "Este parágrafo justifica seu custo em tokens?"

Prefira exemplos concisos a explicações longas.

### Defina graus de liberdade apropriados

Combine o nível de especificidade com a fragilidade e variabilidade da tarefa:

**Alta liberdade (instruções em texto)**: Use quando múltiplas abordagens são válidas, decisões dependem do contexto, ou heurísticas guiam a abordagem.

**Média liberdade (pseudocódigo ou scripts com parâmetros)**: Use quando existe um padrão preferido, alguma variação é aceitável, ou configuração afeta o comportamento.

**Baixa liberdade (scripts específicos, poucos parâmetros)**: Use quando operações são frágeis e sujeitas a erro, consistência é crítica, ou uma sequência específica deve ser seguida.

Pense no Claude explorando um caminho: uma ponte estreita com penhascos precisa de guardrails específicos (baixa liberdade), enquanto um campo aberto permite várias rotas (alta liberdade).

### Anatomia de uma skill

Toda skill consiste em um arquivo obrigatório SKILL.md e recursos opcionais embarcados:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   ├── description: (required)
│   │   └── compatibility: (optional, rarely needed)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

#### SKILL.md (obrigatório)

Todo SKILL.md consiste em:

- **Frontmatter** (YAML): Contém os campos `name` e `description` (obrigatórios), além de campos opcionais como `license`, `metadata` e `compatibility`. Apenas `name` e `description` são lidos pelo Claude para decidir quando a skill deve disparar; portanto, seja claro e completo sobre o que a skill faz e quando deve ser usada. O campo `compatibility` serve para registrar requisitos de ambiente (produto alvo, pacotes do sistema etc.), mas a maioria das skills não precisa dele.
- **Corpo** (Markdown): Instruções e orientações para usar a skill. Só é carregado DEPOIS que a skill dispara (se disparar).

#### Recursos embarcados (opcional)

##### Scripts (`scripts/`)

Código executável (Python/Bash/etc.) para tarefas que exigem confiabilidade determinística ou que são reescritas com frequência.

- **Quando incluir**: quando o mesmo código está sendo reescrito repetidamente ou quando é necessária confiabilidade determinística
- **Exemplo**: `scripts/rotate_pdf.py` para tarefas de rotação de PDF
- **Benefícios**: eficiente em tokens, determinístico, pode ser executado sem ser carregado para a janela de contexto
- **Observação**: scripts ainda podem precisar ser lidos pelo Claude para correções (patches) ou ajustes específicos do ambiente

##### Referências (`references/`)

Documentação e material de referência destinados a serem carregados sob demanda no contexto para orientar o processo e o raciocínio do Claude.

- **Quando incluir**: quando houver documentação que o Claude deve consultar durante o trabalho
- **Exemplos**: `references/finance.md` para schemas financeiros, `references/mnda.md` para template de NDA da empresa, `references/policies.md` para políticas internas, `references/api_docs.md` para especificações de API
- **Casos de uso**: schemas de banco de dados, documentação de API, conhecimento de domínio, políticas da empresa, guias detalhados de workflow
- **Benefícios**: mantém o SKILL.md enxuto; é carregado apenas quando o Claude determina que é necessário
- **Boa prática**: se arquivos forem grandes (>10k palavras), inclua padrões de busca (grep) no SKILL.md
- **Evite duplicação**: a informação deve viver no SKILL.md ou nos arquivos de referências, não nos dois. Prefira referências para detalhes, a menos que seja realmente central para a skill — isso mantém o SKILL.md enxuto e ainda deixa a informação descoberta sob demanda sem consumir a janela de contexto. Mantenha no SKILL.md apenas instruções procedimentais essenciais e orientação de workflow; mova material de referência detalhado, schemas e exemplos para `references/`.

##### Assets (`assets/`)

Arquivos que não devem ser carregados no contexto, mas sim usados dentro do output produzido pelo Claude.

- **Quando incluir**: quando a skill precisa de arquivos que serão usados no output final
- **Exemplos**: `assets/logo.png` para assets de marca, `assets/slides.pptx` para templates de PowerPoint, `assets/frontend-template/` para boilerplate HTML/React, `assets/font.ttf` para tipografia
- **Casos de uso**: templates, imagens, ícones, boilerplate de código, fontes, documentos de exemplo que serão copiados ou modificados
- **Benefícios**: separa recursos de output da documentação; permite que o Claude use arquivos sem carregá-los na janela de contexto

#### O que não incluir em uma skill

Uma skill deve conter apenas arquivos essenciais que suportem diretamente sua funcionalidade. NÃO crie documentação extra ou arquivos auxiliares, incluindo:

- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- etc.

A skill deve conter apenas a informação necessária para um agente de IA executar o trabalho. Ela não deve conter contexto auxiliar sobre como foi criada, procedimentos de setup e teste, documentação voltada a usuários finais etc. Criar arquivos adicionais de documentação só adiciona ruído e confusão.

### Princípio de design: divulgação progressiva

Skills usam um sistema de carregamento em três níveis para gerenciar contexto de forma eficiente:

1. **Metadados (name + description)** — sempre no contexto (~100 palavras)
2. **Corpo do SKILL.md** — quando a skill dispara (<5k palavras)
3. **Recursos embarcados** — conforme necessário (potencialmente “ilimitado”, pois scripts podem ser executados sem serem carregados na janela de contexto)

#### Padrões de divulgação progressiva

Mantenha o corpo do SKILL.md apenas com o essencial e abaixo de 500 linhas para minimizar inchaço de contexto. Divida o conteúdo em arquivos separados ao se aproximar desse limite. Ao separar conteúdo em outros arquivos, é muito importante referenciá-los a partir do SKILL.md e descrever claramente quando eles devem ser lidos, para garantir que o leitor da skill saiba que existem e quando usar.

**Princípio-chave:** quando uma skill suporta múltiplas variações, frameworks ou opções, mantenha no SKILL.md apenas o workflow principal e a orientação de seleção. Mova detalhes específicos de variações (padrões, exemplos, configuração) para arquivos de referência separados.

**Pattern 1: High-level guide with references**

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber:
[code example]

## Advanced features

- **Form filling**: See [FORMS.md](FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
- **Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

O Claude carrega FORMS.md, REFERENCE.md ou EXAMPLES.md somente quando necessário.

**Pattern 2: Domain-specific organization**

Para skills com múltiplos domínios, organize o conteúdo por domínio para evitar carregar contexto irrelevante:

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

Quando um usuário pergunta sobre métricas de vendas, o Claude lê apenas sales.md.

Da mesma forma, para skills que suportam múltiplos frameworks ou variações, organize por variação:

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md (AWS deployment patterns)
    ├── gcp.md (GCP deployment patterns)
    └── azure.md (Azure deployment patterns)
```

Quando o usuário escolhe AWS, o Claude lê apenas aws.md.

**Pattern 3: Conditional details**

Show basic content, link to advanced content:

```markdown
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents

For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

Claude reads REDLINING.md or OOXML.md only when the user needs those features.

**Diretrizes importantes:**

- **Evite referências profundamente aninhadas** — mantenha referências a um nível de profundidade a partir do SKILL.md. Todos os arquivos de referência devem estar linkados diretamente no SKILL.md.
- **Estruture arquivos de referência longos** — para arquivos com mais de 100 linhas, inclua um sumário no topo para que o Claude consiga ver o escopo completo ao pré-visualizar.

## Processo de criação de skills

A criação de uma skill envolve estas etapas:

1. Entender a skill com exemplos concretos
2. Planejar conteúdos reutilizáveis (scripts, referências, assets)
3. Inicializar a skill (executar init_skill.py)
4. Editar a skill (implementar recursos e escrever o SKILL.md)
5. Empacotar a skill (executar package_skill.py)
6. Iterar com base no uso real

Siga estas etapas nesta ordem, pulando apenas quando houver um motivo claro para não se aplicarem.

### Etapa 1: Entender a skill com exemplos concretos

Pule esta etapa apenas quando os padrões de uso da skill já estiverem claramente entendidos. Ela continua valiosa mesmo ao trabalhar em uma skill existente.

Para criar uma skill eficaz, entenda bem exemplos concretos de como ela será usada. Esse entendimento pode vir de exemplos reais fornecidos pelo usuário ou de exemplos gerados que você valida com feedback.

Por exemplo, ao criar uma skill de edição de imagens, perguntas relevantes incluem:

- "Que funcionalidades a skill de edição de imagens deve suportar? Editar, rotacionar, mais alguma coisa?"
- "Você pode dar alguns exemplos de como essa skill seria usada?"
- "Eu consigo imaginar usuários pedindo coisas como 'Remova o olho vermelho desta imagem' ou 'Gire esta imagem'. Existem outros pedidos que você imagina?"
- "O que um usuário diria que deveria disparar esta skill?"

Para não sobrecarregar usuários, evite fazer muitas perguntas em uma única mensagem. Comece pelas perguntas mais importantes e aprofunde conforme necessário.

Conclua esta etapa quando houver clareza sobre as funcionalidades que a skill deve suportar.

### Etapa 2: Planejar conteúdos reutilizáveis

Para transformar exemplos concretos em uma skill eficaz, analise cada exemplo:

1. Considerando como executar o exemplo do zero
2. Identificando quais scripts, referências e assets seriam úteis ao repetir esses workflows

Exemplo: ao criar uma skill `pdf-editor` para lidar com pedidos como "Me ajude a rotacionar este PDF", a análise mostra:

1. Rotacionar um PDF exige reescrever o mesmo código sempre
2. Um script `scripts/rotate_pdf.py` seria útil para guardar dentro da skill

Exemplo: ao desenhar uma skill `frontend-webapp-builder` para pedidos como "Crie um app de tarefas" ou "Crie um dashboard para acompanhar meus passos", a análise mostra:

1. Criar um webapp frontend exige o mesmo boilerplate HTML/React sempre
2. Um template `assets/hello-world/` contendo os arquivos de projeto boilerplate seria útil para armazenar na skill

Exemplo: ao criar uma skill `big-query` para pedidos como "Quantos usuários fizeram login hoje?", a análise mostra:

1. Consultar o BigQuery exige redescobrir schemas e relacionamentos toda vez
2. Um arquivo `references/schema.md` documentando os schemas seria útil para guardar na skill

Para estabelecer o conteúdo da skill, analise cada exemplo concreto e crie uma lista dos recursos reutilizáveis a incluir: scripts, referências e assets.

### Etapa 3: Inicializar a skill

Neste ponto, é hora de criar a skill.

Pule esta etapa apenas se a skill já existir e você estiver apenas iterando ou empacotando. Nesse caso, siga para a próxima etapa.

Ao criar uma nova skill do zero, sempre execute o script `init_skill.py`. Ele gera um diretório de skill a partir de um template que já inclui tudo o que uma skill precisa, tornando o processo mais eficiente e confiável.

Usage:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

O script:

- Cria o diretório da skill no caminho especificado
- Gera um template de SKILL.md com frontmatter correto e placeholders TODO
- Cria diretórios de recursos de exemplo: `scripts/`, `references/` e `assets/`
- Adiciona arquivos de exemplo em cada diretório, que podem ser customizados ou removidos

Depois de inicializar, customize ou remova o SKILL.md gerado e os arquivos de exemplo conforme necessário.

### Etapa 4: Editar a skill

Ao editar a skill (recém-gerada ou existente), lembre que ela está sendo criada para ser usada por outra instância do Claude. Inclua informações que seriam úteis e não óbvias para o Claude. Pense em qual conhecimento procedimental, detalhes de domínio ou assets reutilizáveis ajudariam outra instância a executar essas tarefas de forma mais eficaz.

#### Aprenda padrões de design comprovados

Consulte estes guias conforme a necessidade da sua skill:

- **Processos em múltiplas etapas**: veja references/workflows.md para workflows sequenciais e lógica condicional
- **Formatos específicos de output ou padrões de qualidade**: veja references/output-patterns.md para templates e padrões com exemplos

Esses arquivos contêm boas práticas consolidadas para um design de skill efetivo.

#### Comece pelos conteúdos reutilizáveis

Para iniciar a implementação, comece pelos recursos reutilizáveis identificados acima: arquivos em `scripts/`, `references/` e `assets/`. Note que esta etapa pode exigir input do usuário. Por exemplo, ao implementar uma skill `brand-guidelines`, o usuário pode precisar fornecer assets de marca ou templates para armazenar em `assets/`, ou documentação para armazenar em `references/`.

Scripts adicionados devem ser testados executando-os de fato para garantir que não há bugs e que o output é o esperado. Se houver muitos scripts semelhantes, basta testar uma amostra representativa para ganhar confiança de que todos funcionam, balanceando tempo de execução.

Quaisquer arquivos e diretórios de exemplo que não sejam necessários devem ser removidos. O script de inicialização cria exemplos em `scripts/`, `references/` e `assets/` para demonstrar estrutura, mas a maioria das skills não vai precisar de todos.

#### Atualize o SKILL.md

**Diretriz de escrita:** sempre use forma imperativa/infinitiva.

##### Frontmatter

Escreva o frontmatter YAML com `name` e `description`:

- `name`: o nome da skill
- `description`: este é o principal mecanismo de disparo da skill e ajuda o Claude a entender quando usá-la.
    - Inclua tanto o que a skill faz quanto gatilhos/contexts específicos de quando usá-la.
    - Inclua aqui toda a informação de “quando usar” — não no corpo. O corpo só é carregado após o disparo; então seções do tipo “Quando usar esta skill” no corpo não ajudam o Claude.
    - Exemplo de `description` para uma skill `docx`: "Criação, edição e análise completas de documentos com suporte a tracked changes, comentários, preservação de formatação e extração de texto. Use quando o Claude precisar trabalhar com documentos profissionais (.docx) para: (1) Criar documentos, (2) Modificar/editar conteúdo, (3) Trabalhar com tracked changes, (4) Adicionar comentários, ou outras tarefas com documentos"

Não inclua outros campos no frontmatter YAML.

##### Body

Escreva instruções para usar a skill e seus recursos embarcados.

### Etapa 5: Empacotar a skill

Quando o desenvolvimento da skill estiver concluído, ela deve ser empacotada em um arquivo distribuível `.skill` para ser compartilhado. O processo de empacotamento valida a skill automaticamente antes, para garantir que atende aos requisitos:

```bash
scripts/package_skill.py <path/to/skill-folder>
```

Optional output directory specification:

```bash
scripts/package_skill.py <path/to/skill-folder> ./dist
```

O script de empacotamento vai:

1. **Validar** a skill automaticamente, checando:

    - Formato do frontmatter YAML e campos obrigatórios
    - Convenções de nome e estrutura de diretórios da skill
    - Completude e qualidade da descrição
    - Organização de arquivos e referências a recursos

2. **Empacotar** a skill se a validação passar, criando um arquivo `.skill` com o nome da skill (por exemplo, `my-skill.skill`) que inclui todos os arquivos e mantém a estrutura correta de diretórios para distribuição. O arquivo `.skill` é um zip com extensão `.skill`.

Se a validação falhar, o script reporta os erros e sai sem criar o pacote. Corrija os erros de validação e rode o comando novamente.

### Etapa 6: Iterar

Após testar a skill, usuários podem pedir melhorias. Muitas vezes isso acontece logo depois de usar a skill, com contexto fresco de como ela se comportou.

**Workflow de iteração:**

1. Use a skill em tarefas reais
2. Note dificuldades ou ineficiências
3. Identifique como o SKILL.md ou recursos embarcados devem ser atualizados
4. Implemente mudanças e teste novamente
