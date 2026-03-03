#!/usr/bin/env python3
"""
Script de validação rápida de skills (versão mínima)
"""

import sys
import os
import re
import yaml
from pathlib import Path

def validate_skill(skill_path):
    """Validação básica de uma skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md não encontrado"

    # Read and validate frontmatter
    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith('---'):
        return False, "Frontmatter YAML não encontrado"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Formato de frontmatter inválido"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "O frontmatter deve ser um dicionário YAML"
    except yaml.YAMLError as e:
        return False, f"YAML inválido no frontmatter: {e}"

    # Define allowed properties
    ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Chave(s) inesperada(s) no frontmatter do SKILL.md: {', '.join(sorted(unexpected_keys))}. "
            f"Propriedades permitidas: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Campo obrigatório 'name' ausente no frontmatter"
    if 'description' not in frontmatter:
        return False, "Campo obrigatório 'description' ausente no frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"'name' deve ser string, recebido {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (kebab-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' deve ser kebab-case (apenas minúsculas, dígitos e hífens)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' não pode começar/terminar com hífen nem conter hífens consecutivos"
        # Check name length (max 64 characters per spec)
        if len(name) > 64:
            return False, f"Name é muito longo ({len(name)} caracteres). O máximo é 64 caracteres."

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"'description' deve ser string, recebido {type(description).__name__}"
    description = description.strip()
    if description:
        # Check for angle brackets
        if '<' in description or '>' in description:
            return False, "'description' não pode conter sinais de menor/maior (< ou >)"
        # Check description length (max 1024 characters per spec)
        if len(description) > 1024:
            return False, f"'description' é muito longa ({len(description)} caracteres). O máximo é 1024 caracteres."

    # Validate compatibility field if present (optional)
    compatibility = frontmatter.get('compatibility', '')
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"'compatibility' deve ser string, recebido {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"'compatibility' é muito longo ({len(compatibility)} caracteres). O máximo é 500 caracteres."

    return True, "Skill válida!"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)
    
    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)