"""Configurações globais do bot Caixinha de Perguntas.

Variáveis como BOT_TOKEN vêm de secrets.py (gitignored).
Aqui ficam configurações de comportamento, DB, e constantes.
"""

# ─── Bot Info ────────────────────────────────────────────────
BOT_NAME = "Caixinha de Perguntas"

# ─── Database ────────────────────────────────────────────────
# "sqlite" ou "mariadb"
DB_BACKEND = "sqlite"

# SQLite
DB_NAME = "App/Database/database.db"

# ─── Cloud / Nuvem ──────────────────────────────────────────
CLOUD_ID = -1001667850537  # Chat ID para backups (override em secrets.py)

# ─── Admins ──────────────────────────────────────────────────
ADMINS_IDS = [850446631]  # Override em secrets.py

# ─── Canal obrigatório ──────────────────────────────────────
# Usuários devem estar neste canal para criar caixinhas.
# Deixe None para desativar a verificação.
CANAL_ID = -1001834199290

# ─── URLs ────────────────────────────────────────────────────
URL_HOME = ""  # WebApp URL se houver

# ─── Pyrogram (opcional) ────────────────────────────────────
USE_PYROGRAM = False

# ─── Fuso horário padrão ─────────────────────────────────────
DEFAULT_TIMEZONE = "America/Sao_Paulo"

# ─── Backup automático ──────────────────────────────────────
BACKUP_ENABLED = True
BACKUP_INTERVAL_HOURS = 24

# ─── Gerador de imagens ──────────────────────────────────────
# 'pillow'      -> usa as imagens base (assets) com Pillow (leve, recomendado)
# 'playwright'  -> renderiza HTML/CSS com Chromium headless (pesado, alta qualidade)
IMAGE_ENGINE = 'pillow'
