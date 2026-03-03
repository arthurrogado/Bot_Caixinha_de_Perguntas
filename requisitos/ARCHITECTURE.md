# Caixinha de Perguntas — Arquitetura

## Visão Geral

Bot Telegram para criar **caixinhas de perguntas** (question boxes) que podem ser compartilhadas via deep link. Qualquer pessoa pode enviar perguntas (opcionalmente anônimas) à caixinha de um usuário.

```
bot.py                          # Entry point — handlers, roteamento, start
singleton.py                    # Singleton thread-safe (Pyrogram opcional)
admin_runtime.py                # Runtime Pyrogram para operações pesadas
architecture.sql                # Schema do banco de dados
│
App/
├── custom_bot.py               # CustomBot — extensões do TeleBot
├── Config/
│   ├── __init__.py             # Re-exporta config + secrets
│   ├── config.py               # Configurações globais (DB, URLs, admin IDs)
│   └── secrets.py              # BOT_TOKEN, ADMINS_IDS (gitignored)
│
├── Core/
│   ├── Exceptions.py           # SilentException
│   ├── Messages.py             # Catálogo de traduções (pt/en/es) + função t()
│   ├── PermissionMiddleware.py # Guard de permissão (admin check)
│   └── RateLimit.py            # Rate limiting por usuário
│
├── Database/
│   ├── __init__.py             # Re-exporta Usuario, Caixinha, Pergunta
│   ├── DB.py                   # Camada base CRUD (SQLite + MariaDB)
│   ├── users.py                # DAO: Usuario
│   ├── caixinhas.py            # DAO: Caixinha
│   └── perguntas.py            # DAO: Pergunta
│
├── Components/                 # Feature modules (BaseComponent)
│   ├── BaseComponent.py        # Classe base com bot, userid, db, permission
│   ├── main_menu.py            # Menu principal com opções traduzidas
│   ├── CriarCaixinha.py        # Wizard: criar caixinha (com confirmação)
│   ├── MinhasCaixinhas.py      # Listar caixinhas ativas/concluídas
│   ├── VisualizarCaixinha.py   # Ver perguntas de uma caixinha (texto)
│   ├── GerenciarCaixinha.py    # Gerenciar: concluir/reativar/silenciar
│   ├── ResponderCaixinha.py    # Enviar pergunta a uma caixinha
│   ├── ResponderPergunta.py    # Toggle marcar/desmarcar respondida (15s delay)
│   ├── MudarIdioma.py          # Trocar idioma (pt/en/es)
│   ├── NuvemCaixinhas.py       # (legado — removido do menu)
│   ├── Comunicado.py           # Admin: broadcast para todos
│   ├── Queries.py              # Inline queries (prefixos: cx, mc, mc:c, p:)
│   ├── StoryShare.py           # Compartilhar story
│   └── get_user_info.py        # Info do usuário (webapp)
│
└── Utils/
    ├── __init__.py
    ├── Markup.py               # DSL para teclados inline/reply
    ├── ImageGenerator.py       # Geração de cartões PNG (pergunta, caixinha, story)
    └── utils.py                # Helpers genéricos
```

## Componentes (BaseComponent)

Cada componente herda `BaseComponent` e segue o padrão:

```python
class MeuComponente(BaseComponent):
    def __init__(self, bot, userid, call=None):
        super().__init__(bot, userid, call)
    
    def start(self):
        # Ponto de entrada via automatic_run
        pass
```

### Roteamento (automatic_run)

O `bot.py` roteia callbacks e deep links automaticamente:

```
Callback/Deep link:  CriarCaixinha__start
                     ↓
                     Importa App.Components.CriarCaixinha
                     Instancia CriarCaixinha(bot, userid, call)
                     Chama instance.start()

Com parâmetros:      GerenciarCaixinha__ver__<uid>
                     → instance.ver("<uid>")
```

**Convenção de nomes curtos para callbacks (≤ 64 bytes)**:
```
GerenciarCaixinha__c__<uid>    = concluir   (58 chars)
GerenciarCaixinha__r__<uid>    = reativar
GerenciarCaixinha__s__<uid>    = silenciar toggle
ResponderPergunta__m__<id>     = marcar respondida
ResponderPergunta__dm__<id>    = desmarcar respondida
ResponderPergunta__v__<id>     = visualizar pergunta
```

**Callbacks privados** (prefixo `_`): tratados localmente pelo componente via `add_callback_or_step_handler`. Não passam pelo roteador.

**Callback `cancelar`**: edita a mensagem original adicionando "❌ Cancelado" e remove os botões inline.

### Fluxos Conversacionais

Usam `register_next_step_handler` para ReplyKeyboard e `add_callback_or_step_handler` para InlineKeyboard:

```
CriarCaixinha:
  start → receber_titulo → _pedir_confirmacao → _processar_confirmacao → salvar_caixinha, /cancel aborta

ResponderCaixinha:
  iniciar → _confirmar → _receber_pergunta → _salvar → _notificar_dono
  Se dono clica no próprio link → redirecionado para GerenciarCaixinha.ver()
  /cancel aborta o fluxo em qualquer etapa

ResponderPergunta (toggle):
  m(id) → marcar respondida + timer 15s → notifica autor
  dm(id) → desmarcar + cancela timer
  v(id) → visualizar cartão da pergunta

Queries (inline):
  cx <termo> → caixinhas públicas
  mc <termo> → minhas caixinhas ativas
  mc:c <termo> → minhas concluídas
  p:<uid> <termo> → perguntas de uma caixinha
```

## Banco de Dados

### Dual Backend (SQLite / MariaDB)

- Backend selecionado via `App.Config.DB_BACKEND` (`"sqlite"` ou `"mariadb"`)
- `DB.py` adapta placeholders automaticamente (`?` → `%s`)
- Schema definido em `architecture.sql`
- Soft-delete automático via coluna `deleted_at`

### Tabelas

| Tabela      | Descrição                       | PK         |
|-------------|----------------------------------|------------|
| `usuarios`  | Contas de usuário + idioma       | `id` (BIGINT, Telegram ID) |
| `caixinhas` | Caixinhas de perguntas           | `id` (autoincrement)       |
| `perguntas` | Perguntas/mensagens nas caixinhas| `id` (autoincrement)       |

### DAOs

Cada tabela tem um DAO que herda `DB`:

- `Usuario` → registrar, get, get_idioma, set_idioma, check_exists
- `Caixinha` → criar, get_by_usuario, get_concluidas, get_publicas, concluir, reativar, silenciar, ativar_notificacoes, search_by_usuario
- `Pergunta` → criar, get_by_caixinha, marcar_respondida, desmarcar_respondida, search_all_by_caixinha

## Traduções (i18n)

Sistema de tradução em `App/Core/Messages.py`:

```python
from App.Core.Messages import t

texto = t('menu_principal', 'pt', 'João')  # → "👋😀 Olá João, escolha..."
texto = t('criar_caixinha', 'en')          # → "📚 Create question box"
```

3 idiomas: 🇧🇷 Português, 🇺🇸 English, 🇪🇸 Español

## Geração de Imagens

`App/Utils/ImageGenerator.py` gera cartões PNG via PIL (escala 2x + LANCZOS):

- `criar_cartao(titulo, mensagem)` → 500×dinâmico, header gradiente + corpo claro
- `criar_cartao_caixinha(titulo)` → 500×dinâmico, cartão de convite
- `criar_cartao_resposta(titulo, resp)` → 500×dinâmico, cartão de resposta
- `criar_story_card(titulo, mensagem)` → 1080×dinâmico, formato story

Visual: header com gradiente azul (escuro → claro), avatar com anel gradiente estilo Instagram Stories, ícone de enviar, cantos arredondados com anti-aliasing.

## Deep Links

```
https://t.me/BOT_USERNAME?start=cx-<uid>
```

Formato legado bloqueado (retorna aviso):
```
https://t.me/BOT_USERNAME?start=id_caixinha_42
```

Formato de callback para inline results (HTML text_link):
```html
<a href="https://t.me/BOT_USERNAME?start=GerenciarCaixinha__ver__<uid>">texto</a>
```

## Segurança

- **Rate Limiting**: por usuário, por tipo de ação (command/callback/inline)
- **PermissionMiddleware**: admin check automático nos componentes
- **SilentException**: guards que enviam msg ao usuário sem erro genérico
- **Soft-delete**: dados nunca são apagados fisicamente
