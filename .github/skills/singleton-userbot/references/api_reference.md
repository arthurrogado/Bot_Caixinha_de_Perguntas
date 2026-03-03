# API Reference — admin_runtime & Singleton

## admin_runtime.py

### Módulo

Arquivo na raiz do projeto. Gerencia o ciclo de vida do client Pyrogram em thread dedicada.

### Variáveis globais

| Variável | Tipo | Descrição |
|---|---|---|
| `admin_bot` | `Optional[Client]` | Instância do Pyrogram Client. `None` até `init_admin_bot()`. |

### Funções

#### `init_admin_bot(api_id: int, api_hash: str, bot_token: str, timeout: float = 60.0) → Client`

Inicializa a thread do admin_bot e retorna o `Client` conectado.

**Parâmetros**:
- `api_id` — ID da API Telegram (obtido de my.telegram.org)
- `api_hash` — Hash da API Telegram
- `bot_token` — Token do bot secundário (pode ser o mesmo ou diferente do TeleBot)
- `timeout` — Segundos para aguardar a inicialização (default: 60)

**Comportamento**:
- Idempotente: se já inicializou, retorna o client existente
- Thread-safe via `threading.Lock`
- Cria thread daemon (morre com o processo principal)
- Levanta `RuntimeError` se timeout ou falha na inicialização

**Retorno**: `pyrogram.Client` conectado e pronto para uso.

```python
from admin_runtime import init_admin_bot
from App.Config.secrets import API_ID, API_HASH, ADMIN_BOT_TOKEN

client = init_admin_bot(API_ID, API_HASH, ADMIN_BOT_TOKEN)
print(f"Admin bot: @{client.get_me().username}")  # NÃO - get_me é async
# Use submit_coro para chamar métodos do client
```

---

#### `submit_coro(coro) → concurrent.futures.Future`

Agenda uma coroutine no event loop da thread do admin_bot.

**Parâmetros**:
- `coro` — Coroutine object (resultado de chamar função async sem await)

**Retorno**: `concurrent.futures.Future` — permite `.result()`, `.cancel()`, `.add_done_callback()`

**Levanta**: `RuntimeError` se o loop não está disponível.

```python
from admin_runtime import submit_coro, admin_bot

# Enviar vídeo (async → sync bridge)
future = submit_coro(admin_bot.send_video(chat_id, "/path/video.mp4"))
message = future.result(timeout=300)

# Com callback (não-bloqueante)
future = submit_coro(admin_bot.send_document(chat_id, path))
future.add_done_callback(lambda f: print(f"Enviado: {f.result().id}"))

# Cancelar
future = submit_coro(admin_bot.download_media(msg))
future.cancel()
```

**Padrão de erro**:
```python
try:
    result = future.result(timeout=300)
except TimeoutError:
    print("Upload demorou demais")
except Exception as e:
    print(f"Erro no Pyrogram: {e}")
```

---

#### `shutdown(timeout: float = 5.0) → None`

Para o client Pyrogram e encerra o event loop.

**Parâmetros**:
- `timeout` — Segundos para aguardar o stop do client

**Comportamento**:
- Seguro para chamar mesmo se não inicializou
- Chama `admin_bot.stop()` e depois `loop.stop()`
- Suprime exceções (graceful shutdown)

---

### Internals

| Variável | Tipo | Propósito |
|---|---|---|
| `_lock` | `threading.Lock` | Protege init concorrente |
| `_loop` | `asyncio.AbstractEventLoop` | Loop privado da thread |
| `_thread` | `threading.Thread` | Thread daemon "AdminBotLoop" |
| `_ready` | `threading.Event` | Sinaliza que o client está pronto |

### Diagrama de sequência

```
init_admin_bot()
  │
  ├─ acquire _lock
  ├─ Thread("AdminBotLoop").start()
  ├─ release _lock
  ├─ _ready.wait(timeout) ◄── bloqueia
  │                            │
  │   [Thread AdminBotLoop]    │
  │   new_event_loop()         │
  │   set_event_loop()         │
  │   Client("admin_bot", ...) │
  │   await client.start()     │
  │   _ready.set() ───────────►│
  │   loop.run_forever()       │
  │                            │
  └─ return admin_bot ◄────────┘
```

---

## singleton.py — Template

### Arquivo

Arquivo na raiz do projeto. Template genérico para criar singletons.

### Uso

1. Copiar `singleton.py` para `meu_singleton.py`
2. Ajustar import e instanciação dentro do `with _lock`
3. Renomear `get_instance` para algo descritivo

### Exemplo concreto

```python
# upload_manager_singleton.py

from __future__ import annotations
import threading

_instance = None
_lock = threading.Lock()

def get_upload_manager():
    global _instance
    if _instance is not None:
        return _instance
    with _lock:
        if _instance is None:
            from App.Components.Upload.UploadManager import UploadManager
            _instance = UploadManager(chunk_size=1024*1024)
    return _instance
```

### Propriedades do padrão

| Propriedade | Garantia |
|---|---|
| Thread-safe | `_lock` protege criação concorrente |
| Lazy | Instância criada no primeiro uso |
| Lock-free após criação | Double-checked locking evita contention |
| Anti-circular import | Import local dentro do lock |
| Determinístico | Se `__init__` falha, `_instance` permanece `None` |

### Anti-patterns a evitar

```python
# ❌ ERRADO: import no topo cria dependência circular
from App.Components.MeuManager import MeuManager
_instance = MeuManager()  # executa na importação!

# ❌ ERRADO: sem double-checked locking
def get_instance():
    global _instance
    with _lock:  # lock em TODA chamada, mesmo após criação
        if _instance is None:
            _instance = MeuManager()
    return _instance

# ❌ ERRADO: sem lock
def get_instance():
    global _instance
    if _instance is None:
        _instance = MeuManager()  # race condition!
    return _instance
```

## Integração TeleBot + Pyrogram

### bot.py — Startup

```python
from App.Config import config

admin_bot = None
if config.USE_PYROGRAM:
    from admin_runtime import init_admin_bot
    from App.Config.secrets import API_ID, API_HASH, ADMIN_BOT_TOKEN
    admin_bot = init_admin_bot(API_ID, API_HASH, ADMIN_BOT_TOKEN)
    print("✅ Admin bot (Pyrogram) iniciado")
```

### automatic_run — Injeção

```python
import inspect

sig = inspect.signature(class_.__init__)
if admin_bot and 'admin_bot' in sig.parameters:
    instance = class_(bot, chat_id, call, admin_bot=admin_bot)
else:
    instance = class_(bot, chat_id, call)
```

### Componente que usa Pyrogram

```python
class MeuUploader(BaseComponent):
    def __init__(self, bot, userid, call=None, admin_bot=None):
        super().__init__(bot, userid, call)
        self.admin_bot = admin_bot

    def upload(self, file_path):
        if not self.admin_bot:
            self.bot.send_message(self.userid, "Upload via Pyrogram não disponível.")
            return

        from admin_runtime import submit_coro
        self.bot.send_message(self.userid, "⏳ Enviando...")
        future = submit_coro(
            self.admin_bot.send_video(self.userid, file_path, supports_streaming=True)
        )
        try:
            msg = future.result(timeout=300)
            self.bot.send_message(self.userid, f"✅ Enviado! ID: {msg.id}")
        except Exception as e:
            self.bot.send_message(self.userid, f"❌ Erro: {e}")
```

### Quando usar Pyrogram vs Bot API

| Cenário | Usar |
|---|---|
| Upload > 50MB | Pyrogram |
| Download de mídia de canais | Pyrogram |
| Enviar mensagem simples | Bot API (TeleBot) |
| Editar mensagem | Bot API (TeleBot) |
| Inline queries | Bot API (TeleBot) |
| Interações com teclado | Bot API (TeleBot) |
| Operações batch em canais | Pyrogram |
| Forward/copy entre chats privados | Pyrogram (mais confiável para lotes) |
