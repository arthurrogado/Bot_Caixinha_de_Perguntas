# Pipeline Técnico — Processamento em Fila

Padrão genérico para processar tarefas pesadas em background via fila assíncrona, usando Pyrogram como executor.

## Visão geral

```
TeleBot handler (sync, worker thread)
  → cria registro no DB (status: pendente)
  → submit_coro(manager.adicionar_a_fila(item))

Thread AdminBotLoop (async, loop dedicado)
  → asyncio.Queue recebe item
  → create_task(processar_fila)
     → download/processamento
     → await admin_bot.send_*(...)
     → atualiza DB (status: concluído)
     → limpa arquivos temporários
```

## Componentes

### 1. Singleton do Manager

Mantém UMA fila e UM processador por processo:

```python
# meu_manager_singleton.py
from __future__ import annotations
import threading

_instance = None
_lock = threading.Lock()

def get_meu_manager():
    global _instance
    if _instance is not None:
        return _instance
    with _lock:
        if _instance is None:
            from App.Components.MeuManager import MeuManager
            _instance = MeuManager(notify_bot=None, notify_chat_id=None)
    return _instance
```

### 2. O Manager (classe async)

```python
import asyncio

class MeuManager:
    def __init__(self, notify_bot=None, notify_chat_id=None):
        self.fila = None  # criada lazy no loop correto
        self.processando = False
        self.notify_bot = notify_bot
        self.notify_chat_id = notify_chat_id

    async def adicionar_a_fila(self, item: dict):
        """Chamado via submit_coro() a partir de handlers sync."""
        if self.fila is None:
            self.fila = asyncio.Queue()

        await self.fila.put(item)

        if not self.processando:
            self.processando = True
            asyncio.create_task(self.processar_fila())

    async def processar_fila(self):
        """Loop de processamento — roda como task no loop do admin_bot."""
        try:
            while not self.fila.empty():
                item = await self.fila.get()
                try:
                    await self._processar_item(item)
                except Exception as e:
                    print(f"Erro processando item: {e}")
                finally:
                    self.fila.task_done()
        finally:
            self.processando = False

    async def _processar_item(self, item: dict):
        """Lógica de processamento individual."""
        # 1. Download/preparação (sync em thread se necessário)
        # await asyncio.to_thread(download_pesado, item['url'])

        # 2. Upload via Pyrogram
        # from admin_runtime import admin_bot
        # await admin_bot.send_document(chat_id, file_path)

        # 3. Atualizar DB
        # MeuDAO().marcar_concluido(item['id'], file_id=msg.document.file_id)

        # 4. Limpar temporários
        # os.remove(file_path)
        pass
```

### 3. Enfileiramento a partir de handler sync

```python
# Em um componente (handler do TeleBot):
from admin_runtime import submit_coro
from meu_manager_singleton import get_meu_manager

class CriarEmMassa(BaseComponent):
    def processar(self, itens):
        manager = get_meu_manager()
        for item in itens:
            # 1. Criar registro no banco
            item_id = MeuDAO().criar(item)

            # 2. Enfileirar processamento async
            submit_coro(manager.adicionar_a_fila({
                'id': item_id,
                'url': item['url'],
            }))

        self.bot.send_message(self.userid, f"✅ {len(itens)} itens enfileirados")
```

## Regras da fila

1. `asyncio.Queue` deve ser criada **dentro do loop do admin_bot** (lazy no `.adicionar_a_fila()`)
2. `create_task` deve ser chamado **dentro do mesmo loop**
3. Nunca `await` de handlers sync — sempre `submit_coro()`
4. O singleton garante **uma fila única** por processo

## Retomada após reinício

O pipeline é volátil (fila em memória). Para retomar itens pendentes após reinício:

```python
# No startup (bot.py), após init_admin_bot():
def retomar_pendentes():
    pendentes = MeuDAO().get_pendentes()  # registros sem file_id/concluído
    if pendentes:
        manager = get_meu_manager()
        for item in pendentes:
            submit_coro(manager.adicionar_a_fila(item))
        print(f"📋 {len(pendentes)} itens pendentes retomados")
```

## Download síncrono no loop async

`requests.get()` bloqueia a thread. Como a arquitetura é "1 fila, 1 processador", é aceitável para volume baixo. Para paralelismo:

```python
# Mover download pesado para thread pool:
content = await asyncio.to_thread(requests.get, url)
```

## Glossário

| Termo | Definição |
|---|---|
| **Thread** | Linha de execução dentro do mesmo processo |
| **Worker thread** | Thread do pool do TeleBot que processa handlers |
| **Event loop** | Motor que executa coroutines async numa thread específica |
| **Coroutine** | Função `async def`, executável pelo event loop |
| **Task** | Coroutine agendada no loop via `asyncio.create_task()` |
| **Lock** | Exclusão mútua para evitar race conditions |
| **Singleton** | Padrão com apenas uma instância por processo |
| **submit_coro** | Agenda coroutine no loop do admin_bot de forma cross-thread |
| **asyncio.Queue** | Fila nativa do asyncio, segura dentro de um loop |
