"""Entry point do bot Telegram — Caixinha de Perguntas.

Responsabilidades:
- Configura e inicia o CustomBot (pyTelegramBotAPI)
- Registra handlers (start, callbacks, inline, webapp)
- Roteamento dinâmico via automatic_run()
- Deep links para caixinhas: /start ResponderCaixinha__iniciar__<id>
- Rate limiting em todos os entry points
- (Opcional) Inicializa Pyrogram admin_bot via admin_runtime

Iniciar: python bot.py
"""

import importlib
import json
import math
import re
import signal
import time
import traceback
import requests

from telebot.types import (
    Message,
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    MenuButtonCommands,
    CallbackQuery,
    InlineQuery,
)
from telebot.apihelper import ApiTelegramException

from App.custom_bot import CustomBot
from App.Config.secrets import BOT_TOKEN
from App.Config.config import ADMINS_IDS
from App.Utils.Markup import Markup
from App.Core.Exceptions import SilentException
from App.Core.RateLimit import rate_limit
from App.Core.Messages import get_msg

# Import Components
from App.Components.MainMenu import MainMenu
from App.Components.Queries import Queries
from App.Components.Backup import Backup

# ─── (Opcional) Pyrogram admin_bot ───────────────────────────────────
# Descomente para habilitar o bot secundário (Pyrogram) para operações
# pesadas como upload de vídeos, backups, etc.
#
# from App.Config import USE_PYROGRAM
# if USE_PYROGRAM:
#     from admin_runtime import init_admin_bot, submit_coro
#     from App.Config.secrets import API_ID, API_HASH, ADMIN_BOT_TOKEN
#     admin_client = init_admin_bot(API_ID, API_HASH, ADMIN_BOT_TOKEN)
# else:
#     admin_client = None
admin_client = None


# ─── Bot principal ───────────────────────────────────────────────────

bot = CustomBot(BOT_TOKEN)

# Comandos para todos os usuários
basic_commands = [
    BotCommand("start", "🤖 Inicia o bot"),
    BotCommand("ajuda", "❓ Mostra a ajuda"),
    BotCommand("idioma", "🌐 Mudar idioma"),
]
bot.set_my_commands(basic_commands, scope=BotCommandScopeAllPrivateChats())
bot.set_chat_menu_button(menu_button=MenuButtonCommands(type="commands"))

# Comandos adicionais para admins
admin_commands = basic_commands + [
    BotCommand("comunicado", "📢 Enviar comunicado"),
    BotCommand("admin", "⚙️ Painel administrativo"),
]
for admin_id in ADMINS_IDS:
    try:
        bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(admin_id))
    except Exception:
        pass


# ─── Module cache para importação dinâmica ───────────────────────────
module_cache = {}
UUID_RE = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$')


# ─── WebApp ──────────────────────────────────────────────────────────

@bot.message_handler(content_types="web_app_data")
def answer_web_app_data(msg):
    userid = msg.from_user.id
    try:
        response = json.loads(msg.web_app_data.data)
        bot.send_message(userid, 'Success! Data received:\n\n' + str(response), reply_markup=Markup.clear_markup())

        action = response.get('action')
        if action == 'main_menu':
            MainMenu(bot=bot, userid=userid)

    except Exception as e:
        print("#Error", e)
        traceback.print_exc()
        response = msg.web_app_data.data
        bot.send_message(userid, 'Error, but data:\n\n' + response)


# ─── Roteador dinâmico ──────────────────────────────────────────────

def automatic_run(data_text: str, chat_id: int, call: CallbackQuery = None):
    """Roteador dinâmico de componentes.

    Convenção de callback/deep-link:
        Classe__metodo__arg1__arg2

    Callbacks com prefixo _ são privados (tratados localmente pelo componente).

    Features:
        - Rate limiting automático
        - Cache de módulos importados
        - Injeção de admin_bot quando o componente aceitar
        - Limpeza de handlers antes de cada execução
        - SilentException para guards (permission, etc.)
    """
    kind = "callback" if call else "command"
    tracker = rate_limit.begin(chat_id, kind, data_text)
    msg = get_msg(userid=chat_id)

    try:
        # Cancelamento genérico
        if data_text.lower() in ["cancel", "cancelar"]:
            if call:
                bot.answer_callback_query(call.id, msg.OP_CANCELLED, show_alert=False)
            else:
                bot.send_message(chat_id, msg.OP_CANCELLED + ".")
            return

        # Rate limit check (antes de importar/instanciar componentes)
        if not tracker.allowed:
            wait_s = int(max(1, math.ceil(tracker.retry_after_s)))
            msg_text = f"⏳ Muitas requisições. Aguarde {wait_s}s."
            if call:
                bot.answer_callback_query(call.id, msg_text, show_alert=True)
            else:
                bot.send_message(chat_id, msg_text)
            tracker.log_blocked()
            return

        class_path, method_name, *params = data_text.split("__")
        class_name = class_path.split("_")[-1] if "_" in class_path else class_path
        module_path_str = ".".join(class_path.split("_")) if "_" in class_path else class_path
        method_name = method_name or "start"

        # Cache de módulos
        module = module_cache.get(module_path_str)
        if not module:
            try:
                module = importlib.import_module(f"App.Components.{module_path_str}.{module_path_str}")
            except ModuleNotFoundError:
                module = importlib.import_module(f"App.Components.{module_path_str}")
            module_cache[module_path_str] = module

        class_ = getattr(module, class_name)

        # Injeção de admin_bot se o construtor aceitar
        try:
            from inspect import signature
            sig = signature(class_.__init__)
            if 'admin_bot' in sig.parameters and admin_client:
                instance = class_(bot, chat_id, call, admin_bot=admin_client)
            else:
                instance = class_(bot, chat_id, call)
        except Exception:
            instance = class_(bot, chat_id, call)

        # Limpar handlers antigos ANTES de executar
        bot.clear_registered_callback_handlers_by_chat_id(chat_id)
        bot.clear_step_handler_by_chat_id(chat_id)

        method = getattr(instance, method_name)
        method(*params)

        tracker.finish_ok()

    except SilentException:
        # Guard já enviou mensagem ao usuário — não exibir erro genérico
        tracker.finish_ok()

    except Exception as e:
        tracker.finish_error(e)
        text_erro = f"\n    *** Unexpected error: {e}\n File: {e.__traceback__.tb_frame.f_code.co_filename}\n Line: {e.__traceback__.tb_lineno}\n{traceback.format_exc()}"
        print(text_erro)
        if call:
            bot.answer_callback_query(call.id, msg.GENERIC_ERROR)
            return
        bot.send_message(chat_id, msg.GENERIC_ERROR)
        raise e


# ─── Helpers ─────────────────────────────────────────────────────────

def _ensure_user(msg: Message):
    """Garante que o usuário está registrado no banco."""
    from App.Database.users import Usuario
    userid = msg.from_user.id
    db = Usuario()
    if not db.check_exists(userid):
        nome = msg.from_user.first_name + (' ' + msg.from_user.last_name if msg.from_user.last_name else '')
        db.registrar(userid, nome, msg.from_user.username)
    db.close()


def _run_start_payload(param: str, userid: int):
    """Resolve payload do /start mantendo compatibilidade legada."""
    if param.startswith('cx-'):
        caixinha_uid = param[3:]
        automatic_run(f'ResponderCaixinha__iniciar__{caixinha_uid}', userid)
        return

    # Bloqueia formato legado incremental para evitar enumeração
    if param.startswith('id_caixinha_'):
        bot.send_message(userid, '🔒 Esse link é antigo. Gere um novo link da caixinha.')
        return

    automatic_run(param, userid)


# ─── Handlers ────────────────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def start_parameter(msg: Message):
    userid = msg.from_user.id
    _ensure_user(msg)

    param = msg.text.split(" ")[1] if len(msg.text.split(" ")) > 1 else None

    if param:
        _run_start_payload(param, userid)
    else:
        MainMenu(bot, userid).start()


@bot.message_handler(commands=['ajuda'])
def cmd_ajuda(msg: Message):
    userid = msg.from_user.id
    _ensure_user(msg)
    MainMenu(bot, userid).ajuda()


@bot.message_handler(commands=['idioma'])
def cmd_idioma(msg: Message):
    userid = msg.from_user.id
    _ensure_user(msg)
    automatic_run('MudarIdioma__start', userid)


@bot.message_handler(commands=['comunicado'])
def cmd_comunicado(msg: Message):
    userid = msg.from_user.id
    _ensure_user(msg)
    automatic_run('Comunicado__start', userid)


@bot.message_handler(commands=['admin'])
def cmd_admin(msg: Message):
    userid = msg.from_user.id
    _ensure_user(msg)
    automatic_run('PainelAdmin__start', userid)


@bot.message_handler(commands=['caixinhas_concluidas'])
def cmd_concluidas(msg: Message):
    userid = msg.from_user.id
    _ensure_user(msg)
    automatic_run('MinhasCaixinhas__concluidas', userid)


@bot.message_handler(commands=['cancel'])
def cmd_cancel(msg: Message):
    userid = msg.from_user.id
    bot.clear_step_handler_by_chat_id(userid)
    bot.clear_registered_callback_handlers_by_chat_id(userid)
    lang_msg = get_msg(userid=userid)
    bot.send_message(userid, '❌ ' + lang_msg.OP_CANCELLED)


@bot.message_handler(func=lambda m: True)
def receber(msg: Message):
    userid = msg.from_user.id
    _ensure_user(msg)

    entities = msg.entities if msg.entities else []
    for entity in entities:
        if entity.type == "url":
            if f"t.me/{bot.get_me().username}?start=" in msg.text:
                _run_start_payload(msg.text.split("start=")[1], userid)
                return
        elif entity.type == "text_link":
            if f"t.me/{bot.get_me().username}?start=" in entity.url:
                _run_start_payload(entity.url.split("start=")[1], userid)
                return

    if msg.text == "/id":
        bot.send_message(userid, f"*Seu ID:* `{userid}`", parse_mode="Markdown")
        return

    # Permitir digitar UUID da caixinha manualmente
    if msg.text and UUID_RE.fullmatch(msg.text.strip()):
        automatic_run(f'ResponderCaixinha__iniciar__{msg.text.strip()}', userid)
        return

    if msg.text and msg.text.strip().startswith('cx-'):
        _run_start_payload(msg.text.strip(), userid)
        return

    if msg.text and msg.text.startswith("/") and not msg.text.startswith("/start"):
        automatic_run(msg.text[1:], userid)
        return

    try:
        MainMenu(bot, userid).start()
    except ApiTelegramException as e:
        if e.result_json['description'] == "Forbidden: bot was blocked by the user":
            print(f"User {userid} blocked the bot.")
        else:
            print(f"Error starting menu for user {userid}: {e}")


# ─── Callbacks ───────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda call: not call.data.startswith('_'))
def callback(call):
    """Callback global: encaminha callbacks públicos para automatic_run.

    Callbacks com prefixo _ são privados (tratados localmente por componentes).
    """
    userid = call.from_user.id
    data = call.data
    msg = get_msg(userid=userid)

    if data == "cancelar":
        try:
            # Editar a mensagem: append "❌ Cancelado" e remover botões
            original = call.message
            if original and original.text:
                bot.edit_message_text(
                    original.text + "\n\n❌ " + msg.OP_CANCELLED,
                    chat_id=userid,
                    message_id=original.message_id,
                    reply_markup=None,
                )
            elif original and original.caption:
                bot.edit_message_caption(
                    original.caption + "\n\n❌ " + msg.OP_CANCELLED,
                    chat_id=userid,
                    message_id=original.message_id,
                    reply_markup=None,
                )
            else:
                bot.edit_message_reply_markup(
                    chat_id=userid,
                    message_id=original.message_id,
                    reply_markup=None,
                )
                bot.send_message(userid, "❌ " + msg.OP_CANCELLED)
        except Exception:
            bot.send_message(userid, "❌ " + msg.OP_CANCELLED)
        bot.answer_callback_query(call.id)
        return

    automatic_run(data, userid, call)


# ─── Inline Queries ──────────────────────────────────────────────────

@bot.inline_handler(lambda query: True)
def inline_handler(query: InlineQuery):
    try:
        userid = query.from_user.id
        query_text = query.query or ""

        tracker = rate_limit.begin(userid, "inline", query_text)

        if not tracker.allowed:
            wait_s = int(max(1, math.ceil(tracker.retry_after_s)))
            try:
                bot.answer_inline_query(
                    query.id, [], cache_time=1, is_personal=True,
                    switch_pm_text=f"⏳ Aguarde {wait_s}s.",
                    switch_pm_parameter="rate_limit",
                )
            except Exception:
                pass
            tracker.log_blocked()
            return

        offset = int(query.offset) if query.offset else 0
        limit = 50

        db = Queries(bot, userid, query_text, query.chat_type)
        results = db.get_results(offset, limit)

        next_offset = str(offset + limit) if len(results) == limit else ''
        bot.answer_inline_query(query.id, results, next_offset=next_offset, cache_time=1)

        tracker.finish_ok()

    except ApiTelegramException as e:
        if "query is too old" in str(e.description):
            print(f"Timeout: inline query expired for user {userid}")
        else:
            print(f"API error in inline_handler: {e}")

    except Exception as e:
        traceback.print_exc()
        try:
            bot.answer_inline_query(query.id, [], cache_time=1, switch_pm_text="Erro ao processar query.", switch_pm_parameter="error")
        except Exception:
            pass
        try:
            tracker.finish_error(e)
        except Exception:
            pass


# ─── Start ───────────────────────────────────────────────────────────

# Iniciar agendamento de backup automático
try:
    backup_manager = Backup(bot)
    backup_manager.iniciar_agendamento()
except Exception as e:
    print(f'[Backup] Falha ao iniciar agendamento: {e}')


def run_polling_forever():
    """Loop resiliente para quedas transitórias de conexão no long polling."""
    def _shutdown(signum, frame):
        print('\n[Bot] Sinal de encerramento recebido. Parando polling...')
        bot.stop_polling()

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    backoff_s = 2
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=5)
            # infinity_polling retornou normalmente → stop foi pedido
            break
        except ApiTelegramException as e:
            desc = str(getattr(e, 'description', '') or e)
            if 'terminated by other getUpdates request' in desc:
                print('⚠️ Outra instância do bot detectada (409). Tentando novamente em 3s...')
                time.sleep(3)
                continue
            print(f'ApiTelegramException no polling: {e}')
            time.sleep(backoff_s)
            backoff_s = min(backoff_s * 2, 30)
        except (requests.exceptions.ConnectionError, ConnectionResetError, OSError) as e:
            print(f'Conexão interrompida no polling ({e}). Retry em {backoff_s}s...')
            time.sleep(backoff_s)
            backoff_s = min(backoff_s * 2, 30)
        except Exception as e:
            print(f'Erro inesperado no polling: {e}')
            traceback.print_exc()
            time.sleep(backoff_s)
            backoff_s = min(backoff_s * 2, 30)


run_polling_forever()