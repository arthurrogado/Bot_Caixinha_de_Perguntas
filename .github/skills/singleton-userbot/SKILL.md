---
name: singleton-userbot
description: Padrão singleton thread-safe e integração Pyrogram (userbot/admin_bot). Use quando precisar criar singleton com double-checked locking, integrar Pyrogram como client secundário lado a lado com pyTelegramBotAPI, executar operações async (upload de vídeos, bypass de limites da API oficial) a partir de handlers sync, ou manter uma instância global thread-safe de um manager/processor.
---

# Singleton & Pyrogram Userbot

## Problema

O pyTelegramBotAPI (TeleBot) é síncrono e executa handlers em worker threads. Algumas operações precisam de um segundo client Telegram (Pyrogram) que é assíncrono. Combinar os dois exige:

1. **Thread dedicada com event loop** — Python 3.12+ threads não têm loop por padrão; Pyrogram precisa de um no `__init__`.
2. **Ponte sync→async** — Handlers sync do TeleBot precisam chamar coroutines do Pyrogram.
3. **Instância única** — Apenas UM client Pyrogram ativo, evitando conflitos de sessão.

## Arquitetura

```
bot.py (TeleBot, sync)
  │
  ├── admin_runtime.py ─── Thread "AdminBotLoop"
  │     ├── asyncio event loop
  │     ├── Client Pyrogram (admin_bot)
  │     └── submit_coro() ← ponte sync→async
  │
  └── singleton.py ─── Singleton de qualquer manager
        ├── double-checked locking
        └── lazy import (evita circular)
```

## admin_runtime.py — Client Pyrogram em thread dedicada

### Configuração

Em `App/Config/secrets.py`:
```python
API_ID = 12345
API_HASH = "abc..."
ADMIN_BOT_TOKEN = "123:ABC..."
```

### Inicialização (em bot.py)

```python
from App.Config import config

if config.USE_PYROGRAM:
    from admin_runtime import init_admin_bot
    from App.Config.secrets import API_ID, API_HASH, ADMIN_BOT_TOKEN
    admin_client = init_admin_bot(API_ID, API_HASH, ADMIN_BOT_TOKEN)
```

`init_admin_bot()` é idempotente: se já inicializou, retorna o client existente.

### Uso em handlers sync

```python
from admin_runtime import submit_coro, admin_bot

def upload_video(self, chat_id, file_path):
    """Exemplo: upload de vídeo grande via Pyrogram (limite 2GB vs 50MB da Bot API)."""
    future = submit_coro(
        admin_bot.send_video(chat_id, file_path, supports_streaming=True)
    )
    result = future.result(timeout=300)  # bloqueia até completar
    return result.id
```

### API do admin_runtime

| Função | Descrição |
|---|---|
| `init_admin_bot(api_id, api_hash, bot_token)` | Cria thread + loop + Client. Retorna `Client`. |
| `submit_coro(coro)` | Agenda coroutine no loop. Retorna `concurrent.futures.Future`. |
| `shutdown(timeout=5.0)` | Para client e loop. |
| `admin_bot` | Variável global com a instância do `Client`. |

### Como funciona internamente

1. `init_admin_bot()` adquire lock, cria thread daemon `AdminBotLoop`
2. Dentro da thread: `asyncio.new_event_loop()` → `set_event_loop()` → instancia `Client` → `start()` → sinaliza `_ready`
3. Thread principal aguarda `_ready.wait(timeout)` e retorna o client
4. `submit_coro()` usa `asyncio.run_coroutine_threadsafe(coro, _loop)` para agendar no loop da thread

```python
def submit_coro(coro):
    if _loop is None:
        raise RuntimeError("Admin bot loop not available. Call init_admin_bot() first.")
    return asyncio.run_coroutine_threadsafe(coro, _loop)
```

O `Future` retornado pode ser:
- `.result(timeout=N)` — bloqueia até ter resultado
- `.add_done_callback(fn)` — callback quando completar
- `.cancel()` — tenta cancelar

### Injeção do admin_bot em componentes

O `automatic_run` em `bot.py` injeta `admin_bot` automaticamente via introspecção:

```python
import inspect
sig = inspect.signature(class_.__init__)
if 'admin_bot' in sig.parameters:
    instance = class_(bot, chat_id, call, admin_bot=admin_bot)
else:
    instance = class_(bot, chat_id, call)
```

Assim, componentes que precisam do Pyrogram declaram o parâmetro:

```python
class UploadVideo(BaseComponent):
    def __init__(self, bot, userid, call=None, admin_bot=None):
        super().__init__(bot, userid, call)
        self.admin_bot = admin_bot
```

## Regras de ouro

1. **Nunca** criar `pyrogram.Client(...)` fora de `admin_runtime.py`
2. **Nunca** `await admin_bot.send_*()` de handlers do TeleBot
3. **Sempre** `submit_coro(...)` para agendar no loop do Pyrogram
4. **Manter** singleton com `Lock` para managers/filas
5. `asyncio.Queue` e `create_task` somente no loop do admin_bot
6. Sessão Pyrogram precisa "conhecer" canais/peers antes de interagir

## Erros comuns

| Erro | Causa | Solução |
|---|---|---|
| `RuntimeError: no current event loop in thread 'WorkerThreadX'` | Client criado em worker thread do TeleBot | Instanciar apenas em `admin_runtime.py` |
| Upload trava em `send_video` | Loop/thread errado | Usar `submit_coro()` sempre |
| `PEER_ID_INVALID` | Sessão não conhece o peer | `get_chat(channel_id)` na inicialização |
| Duas instâncias de manager | Sem lock no singleton | Double-checked locking com `threading.Lock` |

## Singleton — Padrão genérico

### Quando usar

- Manager/processor que deve ter UMA instância global
- Classes que mantêm estado compartilhado entre handlers
- Filas de processamento, caches, pools de conexão

### Implementação

```python
# meu_singleton.py
from __future__ import annotations
import threading

_instance = None
_lock = threading.Lock()

def get_meu_manager():
    global _instance
    if _instance is not None:          # 1º check (sem lock, rápido)
        return _instance

    with _lock:                        # lock só na criação
        if _instance is None:          # 2º check (dentro do lock)
            from App.Components.MeuManager import MeuManager
            _instance = MeuManager()

    return _instance
```

### Double-checked locking

```
Thread A                    Thread B
────────                    ────────
_instance is None? → SIM
  acquire lock
    _instance is None? → SIM
      criar instância
      _instance = obj
  release lock
                            _instance is None? → NÃO
                            retorna _instance (sem lock!)
```

**Por que**: Evita contention. Após a criação, o lock NUNCA é adquirido — apenas a comparação rápida `is not None`.

### Import local

O `from ... import` está DENTRO do `with _lock`. Isso é intencional:

1. Evita importação circular (módulo A importa singleton que importa módulo A)
2. Adia o custo de importação até o primeiro uso
3. Se o import falhar, o singleton não fica "meio criado"

### Uso

```python
from meu_singleton import get_meu_manager

# Em qualquer handler, qualquer thread:
manager = get_meu_manager()
manager.processar(dados)
```

## Casos de uso concretos do Pyrogram

### Upload de arquivo grande (>50MB)
Bot API oficial limita uploads a 50MB. Pyrogram suporta até 2GB:

```python
future = submit_coro(admin_bot.send_document(chat_id, "/path/to/arquivo_grande.zip"))
msg = future.result(timeout=600)
```

### Download de mídia de canais
```python
future = submit_coro(admin_bot.download_media(message, file_name="video.mp4"))
path = future.result(timeout=300)
```

### Copiar mensagem entre canais/chats
```python
future = submit_coro(admin_bot.copy_message(
    chat_id=destino,
    from_chat_id=origem,
    message_id=msg_id
))
```

### Resolver peer de canal
Necessário antes de interagir com canais que o bot não "conhece" ainda:
```python
async def _start():
    await admin_bot.start()
    await admin_bot.get_chat(channel_id)  # resolve peer
```

## Referências detalhadas

- **API do admin_runtime e exemplos**: ver [references/api_reference.md](references/api_reference.md)
- **Pipeline de processamento em fila**: ver [references/pipeline-tecnico.md](references/pipeline-tecnico.md)
