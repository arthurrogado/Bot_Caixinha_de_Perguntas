#!/usr/bin/env python3
"""
Inicializador de Skill - Cria uma nova skill a partir de um template

Usage:
    init_skill.py <skill-name> --path <path>

Examples:
    init_skill.py my-new-skill --path skills/public
    init_skill.py my-api-helper --path skills/private
    init_skill.py custom-skill --path /custom/location
"""

import sys
from pathlib import Path


SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: Explicação completa e informativa do que a skill faz e quando usar. Inclua QUANDO usar esta skill — cenários específicos, tipos de arquivo ou tarefas que a disparam.]
---

# {skill_title}

## Visão geral

[TODO: 1-2 frases explicando o que esta skill possibilita]

## Estrutura desta skill

[TODO: Escolha a estrutura que melhor se encaixa no propósito desta skill. Padrões comuns:

**1. Baseada em workflow** (melhor para processos sequenciais)
- Funciona bem quando há procedimentos claros passo a passo
- Exemplo: skill de DOCX com "Árvore de decisão do workflow" → "Leitura" → "Criação" → "Edição"
- Estrutura: ## Visão geral → ## Árvore de decisão do workflow → ## Passo 1 → ## Passo 2...

**2. Baseada em tarefas** (melhor para coleções de ferramentas)
- Funciona bem quando a skill oferece diferentes operações/capacidades
- Exemplo: skill de PDF com "Início rápido" → "Unir PDFs" → "Separar PDFs" → "Extrair texto"
- Estrutura: ## Visão geral → ## Início rápido → ## Categoria de tarefa 1 → ## Categoria de tarefa 2...

**3. Referência/diretrizes** (melhor para padrões ou especificações)
- Funciona bem para guidelines de marca, padrões de código ou requisitos
- Exemplo: estilo de marca com "Diretrizes de marca" → "Cores" → "Tipografia" → "Funcionalidades"
- Estrutura: ## Visão geral → ## Diretrizes → ## Especificações → ## Uso...

**4. Baseada em capacidades** (melhor para sistemas integrados)
- Funciona bem quando a skill fornece múltiplas funcionalidades inter-relacionadas
- Exemplo: Gestão de produto com "Capacidades principais" → lista numerada de capacidades
- Estrutura: ## Visão geral → ## Capacidades principais → ### 1. Funcionalidade → ### 2. Funcionalidade...

Os padrões podem ser combinados conforme necessário. A maioria das skills combina padrões (por exemplo, começar por tarefas e adicionar workflow para operações complexas).

Apague toda esta seção "Estrutura desta skill" quando terminar — ela é apenas orientação.]

## [TODO: Substitua pela primeira seção principal com base na estrutura escolhida]

[TODO: Adicione conteúdo aqui. Veja exemplos em skills existentes:
- Amostras de código para skills técnicas
- Árvores de decisão para workflows complexos
- Exemplos concretos com pedidos realistas de usuários
- Referências a scripts/templates/referências conforme necessário]

## Recursos

Esta skill inclui diretórios de recursos de exemplo que demonstram como organizar diferentes tipos de recursos embarcados:

### scripts/
Código executável (Python/Bash/etc.) que pode ser executado diretamente para realizar operações específicas.

**Exemplos de outras skills:**
- Skill de PDF: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilitários para manipulação de PDF
- Skill de DOCX: `document.py`, `utilities.py` - módulos Python para processamento de documentos

**Adequado para:** scripts Python, scripts de shell ou qualquer código executável que faça automação, processamento de dados ou operações específicas.

**Observação:** scripts podem ser executados sem carregar no contexto, mas ainda podem ser lidos pelo Claude para patches ou ajustes de ambiente.

### references/
Documentação e material de referência destinados a serem carregados no contexto para orientar o processo e o raciocínio do Claude.

**Exemplos de outras skills:**
- Gestão de produto: `communication.md`, `context_building.md` - guias detalhados de workflow
- BigQuery: documentação de referência de API e exemplos de queries
- Finanças: documentação de schemas, políticas da empresa

**Adequado para:** documentação aprofundada, referências de API, schemas de banco de dados, guias completos ou qualquer informação detalhada que o Claude deva consultar durante o trabalho.

### assets/
Arquivos que não devem ser carregados no contexto, mas sim usados no output produzido pelo Claude.

**Exemplos de outras skills:**
- Estilo de marca: templates de PowerPoint (.pptx), arquivos de logo
- Frontend builder: diretórios de projeto boilerplate HTML/React
- Tipografia: arquivos de fonte (.ttf, .woff2)

**Adequado para:** templates, boilerplate de código, templates de documentos, imagens, ícones, fontes ou quaisquer arquivos destinados a serem copiados ou usados no output final.

---

**Quaisquer diretórios desnecessários podem ser apagados.** Nem toda skill precisa dos três tipos de recursos.
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""
Script helper de exemplo para {skill_name}

Este é um script placeholder que pode ser executado diretamente.
Substitua por uma implementação real ou apague se não for necessário.

Exemplos de scripts reais de outras skills:
- pdf/scripts/fill_fillable_fields.py - Fills PDF form fields
- pdf/scripts/convert_pdf_to_images.py - Converts PDF pages to images
"""

def main():
    print("Este é um script de exemplo para {skill_name}")
    # TODO: Add actual script logic here
    # This could be data processing, file conversion, API calls, etc.

if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Documentação de referência para {skill_title}

Este é um placeholder para documentação de referência detalhada.
Substitua por conteúdo real ou apague se não for necessário.

Exemplos reais de docs de referência de outras skills:
- product-management/references/communication.md - Guia completo para status updates
- product-management/references/context_building.md - Deep-dive em coleta de contexto
- bigquery/references/ - Referências de API e exemplos de queries

## Quando docs de referência são úteis

Docs de referência são ideais para:
- Documentação completa de API
- Guias detalhados de workflow
- Processos complexos em múltiplas etapas
- Informação longa demais para o SKILL.md principal
- Conteúdo necessário apenas em casos de uso específicos

## Sugestões de estrutura

### API Reference Example
- Overview
- Authentication
- Endpoints with examples
- Error codes
- Rate limits

### Workflow Guide Example
- Prerequisites
- Step-by-step instructions
- Common patterns
- Troubleshooting
- Best practices
"""

EXAMPLE_ASSET = """# Arquivo de asset de exemplo

Este placeholder representa onde arquivos de asset seriam armazenados.
Substitua por assets reais (templates, imagens, fontes etc.) ou apague se não for necessário.

Arquivos de asset NÃO devem ser carregados no contexto; eles devem ser usados
no output produzido pelo Claude.

Exemplos de assets de outras skills:
- Brand guidelines: logo.png, slides_template.pptx
- Frontend builder: hello-world/ directory with HTML/React boilerplate
- Typography: custom-font.ttf, font-family.woff2
- Data: sample_data.csv, test_dataset.json

## Tipos comuns de asset

- Templates: .pptx, .docx, boilerplate directories
- Images: .png, .jpg, .svg, .gif
- Fonts: .ttf, .otf, .woff, .woff2
- Boilerplate code: Project directories, starter files
- Icons: .ico, .svg
- Data files: .csv, .json, .xml, .yaml

Observação: isto é um placeholder em texto. Assets reais podem ser qualquer tipo de arquivo.
"""


def title_case_skill_name(skill_name):
    """Converte nome de skill com hífens para Title Case (para exibição)."""
    return ' '.join(word.capitalize() for word in skill_name.split('-'))


def init_skill(skill_name, path):
    """
    Inicializa um novo diretório de skill com um SKILL.md de template.

    Args:
        skill_name: Nome da skill
        path: Caminho onde o diretório da skill deve ser criado

    Returns:
        Path do diretório criado, ou None em caso de erro
    """
    # Determine skill directory path
    skill_dir = Path(path).resolve() / skill_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"❌ Erro: diretório da skill já existe: {skill_dir}")
        return None

    # Create skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ Diretório da skill criado: {skill_dir}")
    except Exception as e:
        print(f"❌ Erro ao criar diretório: {e}")
        return None

    # Create SKILL.md from template
    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title
    )

    skill_md_path = skill_dir / 'SKILL.md'
    try:
        skill_md_path.write_text(skill_content, encoding="utf-8")
        print("✅ SKILL.md criado")
    except Exception as e:
        print(f"❌ Erro ao criar SKILL.md: {e}")
        return None

    # Create resource directories with example files
    try:
        # Create scripts/ directory with example script
        scripts_dir = skill_dir / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        example_script = scripts_dir / 'example.py'
        example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name), encoding="utf-8")
        example_script.chmod(0o755)
        print("✅ scripts/example.py criado")

        # Create references/ directory with example reference doc
        references_dir = skill_dir / 'references'
        references_dir.mkdir(exist_ok=True)
        example_reference = references_dir / 'api_reference.md'
        example_reference.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title), encoding="utf-8")
        print("✅ references/api_reference.md criado")

        # Create assets/ directory with example asset placeholder
        assets_dir = skill_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)
        example_asset = assets_dir / 'example_asset.txt'
        example_asset.write_text(EXAMPLE_ASSET, encoding="utf-8")
        print("✅ assets/example_asset.txt criado")
    except Exception as e:
        print(f"❌ Erro ao criar diretórios de recursos: {e}")
        return None

    # Print next steps
    print(f"\n✅ Skill '{skill_name}' inicializada com sucesso em {skill_dir}")
    print("\nPróximos passos:")
    print("1. Edite o SKILL.md para completar os TODOs e atualizar a descrição")
    print("2. Customize ou apague os arquivos de exemplo em scripts/, references/ e assets/")
    print("3. Rode o validador quando estiver pronto para checar a estrutura")

    return skill_dir


def main():
    if len(sys.argv) < 4 or sys.argv[2] != '--path':
        print("Usage: init_skill.py <skill-name> --path <path>")
        print("\nRequisitos do nome da skill:")
        print("  - Identificador em kebab-case (ex.: 'my-data-analyzer')")
        print("  - Apenas letras minúsculas, dígitos e hífens")
        print("  - Máximo de 64 caracteres")
        print("  - Deve corresponder exatamente ao nome do diretório")
        print("\nExamples:")
        print("  init_skill.py my-new-skill --path skills/public")
        print("  init_skill.py my-api-helper --path skills/private")
        print("  init_skill.py custom-skill --path /custom/location")
        sys.exit(1)

    skill_name = sys.argv[1]
    path = sys.argv[3]

    print(f"🚀 Inicializando skill: {skill_name}")
    print(f"   Local: {path}")
    print()

    result = init_skill(skill_name, path)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
