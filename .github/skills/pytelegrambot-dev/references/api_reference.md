# API Reference — CustomBot & BaseComponent

## CustomBot (App/custom_bot.py)

Herda `TeleBot`. Adiciona gerenciamento de handlers e métodos utilitários.

### Handler management

| Método | Assinatura | Descrição |
|---|---|---|
| `once_callback_query_handler` | `(chat_id, callback, custom_filter=None)` | Registra handler de uso único para callbacks. Remove-se após primeira execução. |
| `register_next_step_or_callback_handler` | `(chat_id, callback, filter_fn=None)` | Dual input: aceita próxima mensagem texto OU callback. O que chegar primeiro cancela o outro. |
| `add_callback_or_step_handler` | `(chat_id, callback, custom_filter=None)` | Alias com filtro customizado para callback. |
| `clear_registered_callback_handlers_by_chat_id` | `(chat_id)` | Remove todos os handlers de callback registrados manualmente para o chat_id. Chamado automaticamente no `automatic_run`. |
| `unregister_callback_query_handler` | `(handler)` | Remove um handler específico por identidade de objeto. |

### Message utilities

| Método | Assinatura | Descrição |
|---|---|---|
| `edit_message` | `(chat_id, text, message_id, **kwargs)` | Edita mensagem. Se falhar (`MessageNotModified`, `MessageToEditNotFound`), envia nova. |
| `try_edit_message_text` | `(text, call=None, message_id=None, chat_id=None, **kwargs)` | Edita via callback ou IDs explícitos, com fallback. |
| `edit_message_from_callback` | `(chat_id, text, call, **kwargs)` | Extrai `message_id` do `call.message` e edita. |
| `try_copy_message` | `(chat_id, from_chat_id, message_id)` | `copy_message` com `try/except` silencioso. |

### Handler tracking internals

Handlers registrados manualmente são armazenados em `_registered_callback_handlers: dict[int, list]` (chat_id → lista de handler objects). O `automatic_run` chama `clear_registered_callback_handlers_by_chat_id` antes de cada execução para evitar handlers "fantasma".

---

## BaseComponent (App/Components/BaseComponent.py)

Classe base para todos os componentes.

### Construtor

```python
def __init__(self, bot: CustomBot, userid: int, call=None, startFrom=None):
```

| Parâmetro | Descrição |
|---|---|
| `bot` | Instância de `CustomBot` |
| `userid` | ID do chat/usuário |
| `call` | `CallbackQuery` opcional (se veio de callback) |
| `startFrom` | Método a executar imediatamente após `__init__` |

### Atributos disponíveis

| Atributo | Tipo | Descrição |
|---|---|---|
| `self.bot` | `CustomBot` | Instância do bot |
| `self.userid` | `int` | ID do usuário/chat |
| `self.call` | `CallbackQuery \| None` | Callback que originou (se houver) |
| `self.permission` | `PermissionMiddleware` | Verificação de permissões |

### Métodos

| Método | Descrição |
|---|---|
| `cancel()` | Limpa handlers registrados e envia mensagem de cancelamento |

### Comportamentos automáticos

1. **send_chat_action('typing')** — Enviado no `__init__` para feedback visual
2. **PermissionMiddleware** — Instanciado automaticamente
3. **startFrom** — Se passado, executado ao final do `__init__`

---

## PermissionMiddleware (App/Core/PermissionMiddleware.py)

### Métodos

| Método | Descrição |
|---|---|
| `check_is_admin()` | Levanta `SilentException` se `userid` não está em `ADMINS_IDS` |
| `check_is_admin_callback()` | Idem, mas responde o callback com alert antes |

### Uso

```python
self.permission.check_is_admin()
# código admin-only continua aqui (só alcançado se for admin)
```

---

## RateLimitManager (App/Core/RateLimit.py)

### API

| Método | Descrição |
|---|---|
| `begin(user_id, kind, label)` | Inicia tracking. Retorna `RequestTracker`. |

### RequestTracker

| Atributo/método | Descrição |
|---|---|
| `.allowed` | `bool` — Se a request foi permitida |
| `.retry_after_s` | `float` — Segundos para retry (se bloqueado) |
| `.finish_ok()` | Marca request como concluída com sucesso |
| `.finish_error(exc)` | Marca request como falha |
| `.log_blocked()` | Registra no log que foi bloqueada |

### Configuração default

| Kind | Rate | Burst |
|---|---|---|
| `command` | 1/s | 5 |
| `callback` | 2/s | 8 |
| `inline` | 1/s | 3 |
