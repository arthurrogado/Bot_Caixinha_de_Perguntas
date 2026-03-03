"""Runtime do admin_bot (Pyrogram) em thread dedicada.

Resolve o problema de misturar sync (TeleBot worker threads) com async (Pyrogram):
- Python 3.12+ threads não possuem event loop por padrão.
- O Client do Pyrogram precisa de um event loop no __init__.
- TeleBot handlers rodam em worker threads sem loop.

Solução: thread dedicada com seu próprio event loop, criada ANTES de instanciar o Client.

Configuração:
    Em App/Config/secrets.py, definir:
        ADMIN_BOT_TOKEN = "..."
        API_ID = 12345
        API_HASH = "abc..."

Uso:
    from admin_runtime import init_admin_bot, submit_coro

    # No startup (bot.py):
    admin_client = init_admin_bot()

    # Em qualquer handler sync:
    future = submit_coro(admin_client.send_video(chat_id, file))
    result = future.result(timeout=300)  # bloqueia se necessário
"""

from __future__ import annotations

import asyncio
import contextlib
import threading
from typing import Optional

from pyrogram import Client


admin_bot: Optional[Client] = None

_lock = threading.Lock()
_loop: Optional[asyncio.AbstractEventLoop] = None
_thread: Optional[threading.Thread] = None
_ready = threading.Event()


def _thread_main(api_id: int, api_hash: str, bot_token: str) -> None:
    global _loop, admin_bot
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)

    # Instanciar o Client DENTRO da thread com loop setado.
    admin_bot = Client(
        "admin_bot",
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token,
    )

    async def _start() -> None:
        await admin_bot.start()

    _loop.run_until_complete(_start())
    _ready.set()

    try:
        _loop.run_forever()
    finally:
        with contextlib.suppress(Exception):
            if admin_bot and admin_bot.is_connected:
                _loop.run_until_complete(admin_bot.stop())
        with contextlib.suppress(Exception):
            _loop.close()


def init_admin_bot(api_id: int, api_hash: str, bot_token: str, timeout: float = 60.0) -> Client:
    """Inicializa o admin_bot e retorna o Client.

    Pode ser chamado de qualquer thread (inclusive worker threads do TeleBot).
    Chamadas subsequentes retornam o client existente se já estiver ativo.
    """
    global _thread
    with _lock:
        if _thread and _thread.is_alive() and _ready.is_set() and admin_bot is not None:
            return admin_bot

        _ready.clear()
        _thread = threading.Thread(
            target=_thread_main,
            args=(api_id, api_hash, bot_token),
            name="AdminBotLoop",
            daemon=True,
        )
        _thread.start()

    if not _ready.wait(timeout=timeout):
        raise RuntimeError("admin_bot did not start in time (timeout)")
    if admin_bot is None:
        raise RuntimeError("admin_bot was not initialized")
    return admin_bot


def submit_coro(coro):
    """Agenda uma coroutine no loop do admin_bot e retorna Future (concurrent.futures).
    
    Uso:
        future = submit_coro(admin_bot.send_video(...))
        result = future.result(timeout=300)
    """
    if _loop is None:
        raise RuntimeError("Admin bot loop not available. Call init_admin_bot() first.")
    return asyncio.run_coroutine_threadsafe(coro, _loop)


def shutdown(timeout: float = 5.0) -> None:
    """Tenta parar o client e encerrar o loop de forma limpa."""
    global _loop
    if _loop is None:
        return

    async def _stop() -> None:
        if admin_bot and admin_bot.is_connected:
            await admin_bot.stop()

    with contextlib.suppress(Exception):
        asyncio.run_coroutine_threadsafe(_stop(), _loop).result(timeout=timeout)
    with contextlib.suppress(Exception):
        _loop.call_soon_threadsafe(_loop.stop)


__all__ = ["admin_bot", "init_admin_bot", "submit_coro", "shutdown"]
