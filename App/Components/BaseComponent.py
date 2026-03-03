"""Classe base para todos os componentes do bot.

Todo componente de feature deve herdar BaseComponent. Fornece:
- Referência ao bot e userid
- ``self.msg`` — wrapper localizado (``Msg``) com o idioma do usuário
- Auto-envio de "typing" action
- PermissionMiddleware auto-instanciado
- cancel() com cleanup de handlers
- set_callback_query_handler() helper
"""

from App.custom_bot import CustomBot
from telebot.types import CallbackQuery

from App.Utils.Markup import Markup
from App.Database.DB import DB
from App.Core.PermissionMiddleware import PermissionMiddleware
from App.Core.Messages import get_msg, CANCEL_TRIGGERS


class BaseComponent():
    markup_cancel = Markup.generate_inline([[['❌ Cancel', '*cancel']]])

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None, startFrom = None) -> None:
        self.bot = bot
        self.userid = userid
        self.call = call
        self.db = DB(self.bot)
        self.msg = get_msg(userid=userid)
        self.bot.send_chat_action(self.userid, 'typing')
        self.permission = PermissionMiddleware(self.bot, self.userid, self.call)

        if startFrom:
            startFrom(self)

    def _is_cancel(self, text: str | None) -> bool:
        """Verifica se o texto é um trigger de cancelamento."""
        return (text or '').strip().lower() in CANCEL_TRIGGERS

    def cancel(self, call=None):
        """Cancela operação atual e limpa todos os handlers do chat."""
        if call:
            self.bot.answer_callback_query(call.id, self.msg.OP_CANCELLED)
            self.bot.delete_message(call.message.chat.id, call.message.message_id)
            chat_id = call.message.chat.id
        else:
            chat_id = self.userid
        self.bot.clear_step_handler_by_chat_id(chat_id)
        self.bot.clear_registered_callback_handlers_by_chat_id(chat_id)

    def set_callback_query_handler(self, handler_function, call_data):
        """Registra handler de callback privado (prefixo _ no call_data).
        
        Usa once_callback_query_handler para escopo por chat_id e auto-remoção."""
        self.bot.once_callback_query_handler(
            self.userid,
            handler_function,
            filter=lambda call: call.data == call_data
        )