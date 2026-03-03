# MiniApp MiniFramework — Telegram Bot

Template/miniframework para bots Telegram com **pyTelegramBotAPI**, arquitetura component-based e suporte opcional a **Pyrogram** para operações pesadas.

Inclui também um mini-framework client-side (vanilla JS SPA) para Telegram Mini Apps.

## Stack

| Camada | Tecnologia | Descrição |
|---|---|---|
| Bot principal | pyTelegramBotAPI (TeleBot) | Handlers, menus, callbacks, inline queries |
| Bot secundário | Pyrogram (opcional) | Upload de arquivos grandes, operações async |
| Database | SQLite | Persistência via classes DAO |
| Frontend | Vanilla JS | SPA para Telegram Mini Apps (WebApps) |

## Estrutura do projeto

```
├── bot.py                  # Entry point — handlers, automatic_run, startup
├── admin_runtime.py        # Thread dedicada Pyrogram (opcional)
├── singleton.py            # Template singleton thread-safe
├── App/
│   ├── custom_bot.py       # CustomBot (extends TeleBot) — handler tracking, message editing
│   ├── Components/
│   │   ├── BaseComponent.py    # Classe base para todos os componentes
│   │   ├── main_menu.py        # Menu principal
│   │   ├── Queries.py          # Inline queries (dispatch por prefixo)
│   │   └── ...                 # Seus componentes
│   ├── Core/
│   │   ├── Exceptions.py       # SilentException
│   │   ├── Messages.py         # Mensagens padrão
│   │   ├── PermissionMiddleware.py  # Guard de admin
│   │   └── RateLimit.py        # Token-bucket por usuário/tipo
│   ├── Config/
│   │   ├── config.py           # Configurações gerais
│   │   └── secrets.py          # Tokens e chaves (gitignored)
│   ├── Database/
│   │   ├── DB.py               # Base DAO (SQLite)
│   │   └── users.py            # DAO de usuários
│   └── Utils/
│       ├── Markup.py           # Builder de teclados inline/reply
│       └── utils.py            # Helpers (deep links, admin check, etc.)
└── webapp/
    ├── app.js              # Router SPA
    ├── index.html          # Shell
    └── pages/              # Páginas (html + css + js)
```

## Setup

### 1. Bot

```bash
# Criar e ativar venv
python -m venv venv
source venv/bin/activate  # Linux/WSL
# ou: .\venv\Scripts\Activate.ps1  # Windows

# Instalar dependências
pip install pyTelegramBotAPI
# Opcional (para Pyrogram):
pip install pyrogram tgcrypto
```

### 2. Configuração

1. Criar bot via [BotFather](https://t.me/botfather) e copiar o token
2. Copiar `App/Config/secrets.py.example` para `App/Config/secrets.py`
3. Preencher `BOT_TOKEN` em `secrets.py`
4. (Opcional) Preencher `API_ID`, `API_HASH`, `ADMIN_BOT_TOKEN` para Pyrogram
5. Configurar `ADMINS_IDS` em `App/Config/config.py`

### 3. WebApp (Mini App)

A webapp precisa estar acessível via HTTPS:

- **Local**: `python -m http.server 8080` + `ngrok http 8080`
- **Deploy**: Qualquer hosting estático (Netlify, Vercel, GitHub Pages)

Configurar a URL da webapp em `App/Config/config.py`.

### 4. Executar

```bash
python bot.py
```

## Arquitetura

### Roteamento dinâmico (`automatic_run`)

Todo o fluxo de navegação usa um roteador que resolve `callback_data → classe.método(*args)`:

```
Classe__metodo__arg1__arg2
Pasta_Classe__metodo__arg1
```

- `__` separa classe, método e parâmetros
- `_` no caminho = separador de diretório
- 3 entry points: deep links (`/start param`), callbacks e comandos texto

### Componentes

Cada feature/tela é uma classe que herda `BaseComponent`:

```python
from App.Components.BaseComponent import BaseComponent
from App.Utils import Markup

class MeuComponente(BaseComponent):
    def __init__(self, bot, userid, call=None):
        super().__init__(bot, userid, call)

    def start(self):
        markup = Markup.generate_inline([
            [['Opção 1', 'MeuComponente__acao1']],
            [['Opção 2', 'MeuComponente__acao2__param']],
        ])
        self.bot.send_message(self.userid, "Escolha:", reply_markup=markup)

    def acao1(self):
        self.bot.send_message(self.userid, "Ação 1!")
```

### Core

- **SilentException** — Interrompe fluxo sem mostrar erro genérico
- **PermissionMiddleware** — `self.permission.check_is_admin()` em métodos admin-only
- **RateLimit** — Token-bucket por usuário e tipo (command/callback/inline)
- **Messages** — Constantes de mensagem padronizadas

### Database

1 classe DAO por tabela, herda `DB`:

```python
from App.Database.DB import DB

class Produto(DB):
    def criar(self, nome, preco):
        return self.insert('produtos', {'nome': nome, 'preco': preco})

    def buscar(self, id):
        return self.select_one('produtos', ['*'], 'id = ?', params=[id])
```

### Pyrogram (opcional)

Para operações que excedem os limites da Bot API (upload >50MB, etc.):

1. Configurar `USE_PYROGRAM = True` em `config.py`
2. Preencher credenciais em `secrets.py`
3. O `admin_runtime.py` cria thread dedicada com event loop próprio
4. Usar `submit_coro()` para agendar coroutines do Pyrogram a partir de handlers sync

### WebApp (Mini App)

SPA em vanilla JS com router baseado em `history.pushState`:

- `navigateTo(route)` — Push route + fetch HTML/CSS/JS da página
- Páginas em `webapp/pages/<nome>/<nome>.{html,css,js}`
- Comunicação: Bot → WebApp via query string na URL; WebApp → Bot via `sendData()`

## Skills

O projeto inclui skills para Claude/Copilot em `.github/skills/`:

- **pytelegrambot-dev** — Guia completo de componentes, routing, Markup, DB, inline queries, wizards, picklist, frontend
- **singleton-userbot** — Singleton thread-safe, integração Pyrogram, pipeline de processamento async

## License

MIT — ver [LICENCE](LICENCE).