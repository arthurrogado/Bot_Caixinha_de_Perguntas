#!/usr/bin/env bash
# =============================================================
#  setup.sh — Instalação do Bot Caixinha de Perguntas
# =============================================================
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERRO]${NC} $*"; exit 1; }
section() { echo -e "\n${BOLD}── $* ──${NC}"; }

# ─── Python ──────────────────────────────────────────────────
section "Verificando Python"
PYTHON=$(command -v python3 || command -v python || true)
[ -z "$PYTHON" ] && error "Python não encontrado. Instale Python 3.10+ e tente novamente."
PY_VERSION=$($PYTHON -c "import sys; print('%d.%d' % sys.version_info[:2])")
info "Python $PY_VERSION em: $PYTHON"

# ─── Virtualenv ──────────────────────────────────────────────
section "Ambiente virtual"
if [ ! -d "venv" ]; then
    info "Criando venv..."
    $PYTHON -m venv venv
else
    info "venv já existe, pulando criação."
fi

# Ativa o venv
if [ -f "venv/bin/activate" ]; then
    # Linux / macOS
    source venv/bin/activate
    PIP="venv/bin/pip"
    PYTHON="venv/bin/python"
elif [ -f "venv/Scripts/activate" ]; then
    # Windows (Git Bash / WSL)
    source venv/Scripts/activate
    PIP="venv/Scripts/pip"
    PYTHON="venv/Scripts/python"
else
    error "Não foi possível ativar o venv."
fi

# ─── Dependências principais ─────────────────────────────────
section "Instalando dependências (requirements.txt)"
$PIP install --upgrade pip -q
$PIP install -r requirements.txt
info "Dependências principais instaladas."

# ─── Playwright (Chromium) ───────────────────────────────────
section "Playwright"
echo -n "Instalar o navegador Chromium para engine 'playwright'? (recomendado para imagens mais bonitas) [s/N]: "
read -r INSTALL_PW
if [[ "$INSTALL_PW" =~ ^[sS]$ ]]; then
    info "Instalando Chromium via Playwright..."
    $PYTHON -m playwright install chromium
    info "Chromium instalado."
else
    warn "Playwright Chromium não instalado. Engine 'pillow' será usado."
fi

# ─── Extras opcionais: MariaDB ───────────────────────────────
section "Banco de dados"
echo -n "Usar MariaDB em vez de SQLite? [s/N]: "
read -r USE_MARIADB
if [[ "$USE_MARIADB" =~ ^[sS]$ ]]; then
    info "Instalando mysql-connector-python..."
    $PIP install mysql-connector-python
    warn "Lembre-se de ajustar DB_BACKEND = 'mariadb' e as credenciais em App/Config/config.py"
else
    info "SQLite selecionado (padrão, sem dependências extras)."
fi

# ─── Extras opcionais: Pyrogram ──────────────────────────────
section "Pyrogram (opcional)"
echo -n "Usar Pyrogram para operações pesadas (upload de vídeos, bypass de limites)? [s/N]: "
read -r USE_PYROGRAM
if [[ "$USE_PYROGRAM" =~ ^[sS]$ ]]; then
    info "Instalando Pyrogram + TgCrypto..."
    $PIP install Pyrogram TgCrypto
    warn "Lembre-se de definir USE_PYROGRAM = True e API_ID / API_HASH em App/Config/secrets.py"
else
    info "Pyrogram não instalado."
fi

# ─── secrets.py ──────────────────────────────────────────────
section "Configuração de secrets"
SECRETS_SRC="App/Config/secrets.py.example"
SECRETS_DST="App/Config/secrets.py"
if [ ! -f "$SECRETS_DST" ]; then
    cp "$SECRETS_SRC" "$SECRETS_DST"
    warn "Arquivo '$SECRETS_DST' criado a partir do exemplo."
    warn "Edite-o e insira seu BOT_TOKEN antes de iniciar o bot."
else
    info "'$SECRETS_DST' já existe, não foi alterado."
fi

# ─── Banco de dados SQLite ───────────────────────────────────
section "Inicializando banco de dados"
$PYTHON - <<'PYEOF'
import sys, os
sys.path.insert(0, '.')
try:
    from App.Database.DB import DB
    db = DB()
    db.close()
    print("[INFO] Banco de dados inicializado com sucesso.")
except Exception as e:
    print(f"[WARN] Não foi possível inicializar o banco agora: {e}")
    print("[WARN] Verifique as credenciais em App/Config/secrets.py e tente novamente.")
PYEOF

# ─── Concluído ───────────────────────────────────────────────
section "Pronto!"
echo -e "${GREEN}Instalação concluída.${NC}"
echo ""
echo "  Próximos passos:"
echo "  1. Edite ${BOLD}App/Config/secrets.py${NC} e defina seu BOT_TOKEN"
echo "  2. Ajuste ${BOLD}App/Config/config.py${NC} conforme necessário"
echo "  3. Inicie o bot:"
echo "       source venv/bin/activate   # Linux/macOS"
echo "       python bot.py"
echo ""
