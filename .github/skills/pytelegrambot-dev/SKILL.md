---
name: pytelegrambot-dev
description: Guia completo de desenvolvimento de bots Telegram com pyTelegramBotAPI usando a arquitetura component-based deste projeto. Use quando precisar criar componentes, handlers, fluxos conversacionais, callbacks, inline queries, menus, rate limiting, permissões ou qualquer feature de bot Telegram. Cobre o padrão automatic_run, BaseComponent, CustomBot, Markup DSL, Database DAO, PermissionMiddleware e RateLimit.
---

# Desenvolvimento pyTelegramBotAPI

## Arquitetura geral

O projeto segue arquitetura **component-based** em 4 camadas:

| Camada | Diretório | Responsabilidade |
|---|---|---|
| Entry point | `bot.py` | Handlers, routing, startup |
| Components | `App/Components/` | Lógica de negócio (1 classe = 1 feature/tela) |
| Core | `App/Core/` | Cross-cutting: permissões, rate limit, exceptions, messages |
| Database | `App/Database/` | Acesso a dados: 1 classe por tabela, herda `DB` |
| Utils | `App/Utils/` | Markup builder, helpers |

## Roteamento dinâmico (`automatic_run`)

Todo o fluxo de navegação usa **um único roteador** que resolve `callback_data → class.method(*args)`.

### Convenção de callback data

```
Classe__metodo__arg1__arg2
Pasta_Classe__metodo__arg1
```

- `_` no caminho da classe = separador de diretório (`Pasta_Sub_Classe` → `App.Components.Pasta.Sub.Classe`)
- `__` separa classe, método e parâmetros
- O último segmento antes de `__` é o nome da classe

### 3 entry points alimentam `automatic_run`:

1. **Deep links**: `/start param` → `automatic_run(param, userid)`
2. **Callbacks**: botões → `automatic_run(call.data, userid, call)` (só callbacks SEM prefixo `_`)
3. **Comandos texto**: `/Algo__metodo` → `automatic_run(msg.text[1:], userid)`

### Callbacks privados (prefixo `_`)

Callbacks com `_` NÃO passam pelo roteador. São tratados localmente pelo componente via `bot.register_callback_query_handler()`. Usar para diálogos de confirmação, fluxos internos.

## Criar um componente

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
        self.bot.send_message(self.userid, "Ação 1 executada!")

    def acao2(self, param):
        self.bot.send_message(self.userid, f"Ação 2 com param: {param}")
```

### Componente com permissão de admin

```python
def painel_admin(self):
    self.permission.check_is_admin()  # levanta SilentException se não for admin
    # código admin-only segue aqui
```

### Fluxo conversacional (multi-step)

```python
def pedir_nome(self):
    msg = self.bot.send_message(self.userid, "Digite seu nome:")
    self.bot.register_next_step_handler(msg, self.receber_nome)

def receber_nome(self, message):
    nome = message.text
    markup = Markup.generate_inline([[['✅ Sim', '_confirmar'], ['❌ Não', '_cancelar']]])
    self.bot.send_message(self.userid, f"Nome: {nome}. Confirmar?", reply_markup=markup)
    self.bot.once_callback_query_handler(self.userid, self.confirmar_nome)
```

### Dual input (mensagem OU callback)

```python
def pedir_dados(self):
    msg = self.bot.send_message(self.userid, "Digite ou clique:", reply_markup=markup)
    self.bot.add_callback_or_step_handler(self.userid, self.processar,
        custom_filter=lambda call: call.data in ['_opt1', '_opt2'])

def processar(self, input):  # recebe Message ou CallbackQuery
    if isinstance(input, CallbackQuery):
        # tratou como clique
    else:
        # tratou como texto digitado
```

## Markup DSL

```python
from App.Utils import Markup

# Inline keyboard
Markup.generate_inline([
    [['Botão', 'callback_data']],                           # callback normal
    [['Link', 'url=https://example.com']],                  # URL button
    [['Buscar', 'switch_inline_query_current_chat=o: ']],   # inline switch
])

# Reply keyboard
Markup.generate_keyboard([['Btn1', 'Btn2'], ['Btn3']])

# Limpar reply keyboard
Markup.clear_markup()

# WebApp button
Markup.webapp_button("Abrir App", "https://app.example.com")
```

## Database

Padrão: 1 classe DAO por tabela, herda `DB`. Instâncias são **short-lived**.

```python
from App.Database.DB import DB

class Produto(DB):
    def __init__(self, bot=None):
        super().__init__(bot)

    def criar(self, nome, preco):
        return self.insert('produtos', {'nome': nome, 'preco': preco})

    def buscar(self, id):
        return self.select_one('produtos', ['*'], 'id = ?', params=[id])

    def listar(self):
        return self.select('produtos', ['*'], final='ORDER BY nome')

    def atualizar_preco(self, id, preco):
        return self.update('produtos', {'preco': preco}, 'id = ?', params=[id])

    def remover(self, id):
        return self.delete('produtos', 'id = ?', params=[id])
```

Tabelas com coluna `deleted_at` têm soft-delete automático no `select`.

## CustomBot — métodos essenciais

| Método | Uso |
|---|---|
| `edit_message(chat_id, text, message_id, ...)` | Edita ou envia como fallback |
| `try_edit_message_text(text, call=call, ...)` | Edita via callback com fallback |
| `edit_message_from_callback(chat_id, text, call)` | Extrai message_id do call |
| `try_copy_message(chat_id, from_chat_id, message_id)` | Copy com fallback |
| `register_next_step_or_callback_handler(chat_id, cb)` | Dual: msg ou callback |
| `once_callback_query_handler(chat_id, cb)` | Single-use callback |
| `add_callback_or_step_handler(chat_id, cb, ...)` | Combinado com filtros |
| `clear_registered_callback_handlers_by_chat_id(id)` | Limpa handlers do chat |

## Rate Limiting

Token-bucket por usuário e tipo (`command`, `callback`, `inline`). Configurado em `App/Core/RateLimit.py`. O `automatic_run` e o `inline_handler` aplicam rate limit automaticamente.

## Modularização de componentes

Quebrar features grandes em múltiplos arquivos:

```
App/Components/
  MeuRecurso/
    GerenciarRecurso.py    # Menu + CRUD read/delete
    CriarRecurso.py        # Wizard de criação
    EditarRecurso.py       # Menu de edição
    Editar/
      EditarCampoX.py      # Edição de campo específico
```

Callbacks com subpastas usam `_` como separador de diretório:

```python
'MeuRecurso_CriarRecurso__start'
# → App.Components.MeuRecurso.CriarRecurso.CriarRecurso.start()

'MeuRecurso_Editar_EditarCampoX__iniciar__42'
# → App.Components.MeuRecurso.Editar.EditarCampoX.EditarCampoX.iniciar(42)
```

### Regras de separação

1. Separar **gerenciamento** (menu/CRUD) de **criação** (wizards)
2. Um arquivo por wizard complexo (>200 linhas)
3. Edições de campos individuais em subpasta `Editar/`
4. Manter componente principal "fino" — delegar para sub-componentes
5. Último segmento do `_path` = nome da classe

## Boas práticas gerais

1. Preferir editar mensagens (`try_edit_...`) a enviar novas
2. Sempre `self.permission.check_is_admin()` em métodos administrativos
3. Blocos `try-except` com feedback amigável ao usuário
4. `automatic_run` limpa handlers antigos nas transições — confiar nele
5. Validar e converter IDs para `int` cedo
6. Sempre botão Voltar/Cancelar em fluxos multi-etapas
7. Após completar ação, retornar ao menu de origem (nunca deixar o usuário "solto")
8. Cache de módulos importados em `module_cache` (dict global) para evitar re-imports
9. Não fazer imports relativos entre componentes — usar import absoluto (Exemplo: `from App.Database.user import User`, isto é, não importar User direto de Database e sim de Database.user)


## Referências detalhadas

- **Inline queries, deep links e callbacks**: ver [references/patterns.md](references/patterns.md)
- **Frontend, navegação, wizards e picklist**: ver [references/frontend-navegacao.md](references/frontend-navegacao.md)
- **API do CustomBot, BaseComponent e RateLimit**: ver [references/api_reference.md](references/api_reference.md)
