"""CustomBot — extensão do TeleBot com funcionalidades essenciais.

Adiciona:
- edit_message com fallback para send_message
- try_edit_message_text / try_edit_message_caption
- edit_message_from_callback
- try_copy_message com fallback
- Gerenciamento de handlers por chat_id (register/unregister/clear)
- register_next_step_or_callback_handler (dual input)
- once_callback_query_handler (single-use)
- add_callback_or_step_handler (com filtros)
"""

from telebot import TeleBot, types
from telebot.types import Message, MessageEntity, CallbackQuery
from telebot import REPLY_MARKUP_TYPES
from typing import List, Optional, Union, Callable


class CustomBot(TeleBot):
    def __init__(self, token, **kwargs):
        super().__init__(token, **kwargs)
        # Rastreia handlers registrados manualmente por chat_id
        # {chat_id: [handler_func1, handler_func2, ...]}
        self._registered_callback_handlers = {}

    # ─── Message Editing (try → fallback) ────────────────────────────

    def edit_message(
        self,
        chat_id: int | str,
        text: str,
        message_id: int | None = None,
        parse_mode: str | None = None,
        entities: List[MessageEntity] | None = None,
        disable_web_page_preview: bool | None = None,
        disable_notification: bool | None = None,
        protect_content: bool | None = None,
        reply_to_message_id: int | None = None,
        allow_sending_without_reply: bool | None = None,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
        timeout: int | None = None,
        message_thread_id: int | None = None,
    ) -> Message:
        """Tenta editar mensagem; se falhar, envia nova."""
        try:
            return self.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=text,
                parse_mode=parse_mode, entities=entities,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=reply_markup,
            )
        except Exception:
            return self.send_message(
                chat_id=chat_id, text=text, parse_mode=parse_mode,
                entities=entities, disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                allow_sending_without_reply=allow_sending_without_reply,
                reply_markup=reply_markup, timeout=timeout,
                message_thread_id=message_thread_id,
            )

    def try_edit_message_text(
        self, text: str,
        chat_id: Optional[Union[int, str]] = None,
        call: CallbackQuery = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        entities: Optional[List[types.MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[types.InlineKeyboardMarkup] = None,
        timeout: Optional[int] = None,
    ) -> Union[types.Message, bool]:
        """Tenta edit_message_text; fallback para edit_message_from_callback."""
        effective_chat_id = chat_id or (call.message.chat.id if call and call.message else None)
        try:
            return self.edit_message_text(
                text=text, chat_id=effective_chat_id,
                message_id=call.message.id if call and call.message else message_id,
                inline_message_id=inline_message_id,
                parse_mode=parse_mode, entities=entities,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=reply_markup, timeout=timeout,
            )
        except Exception:
            return self.edit_message_from_callback(
                chat_id=effective_chat_id, text=text, call=call,
                parse_mode=parse_mode, entities=entities,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=reply_markup, timeout=timeout,
            )

    def try_edit_message_caption(
        self, caption: str,
        chat_id: Optional[Union[int, str]] = None,
        callback_query: CallbackQuery = None,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[List[types.MessageEntity]] = None,
        reply_markup: Optional[types.InlineKeyboardMarkup] = None,
        show_caption_above_media: Optional[bool] = None,
        business_connection_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Union[types.Message, bool]:
        """Tenta editar caption; fallback para edit_message_from_callback."""
        try:
            return self.edit_message_caption(
                chat_id=chat_id, message_id=callback_query.message.id,
                inline_message_id=inline_message_id, caption=caption,
                parse_mode=parse_mode, caption_entities=caption_entities,
                reply_markup=reply_markup,
                show_caption_above_media=show_caption_above_media,
                business_connection_id=business_connection_id,
                timeout=timeout,
            )
        except Exception:
            return self.edit_message_from_callback(
                chat_id=chat_id, text=caption, call=callback_query,
                parse_mode=parse_mode, entities=caption_entities,
                reply_markup=reply_markup, timeout=timeout,
            )

    def try_copy_message(
        self, *,
        chat_id: int | str,
        from_chat_id: int | str,
        message_id: int,
        caption: str | None = None,
        parse_mode: str | None = None,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
        fallback_text: str | None = None,
        fallback_parse_mode: str | None = None,
        fallback_reply_markup: REPLY_MARKUP_TYPES | None = None,
        **kwargs,
    ) -> Union[types.Message, bool]:
        """Tenta copy_message; fallback para send_message."""
        try:
            return self.copy_message(
                chat_id=chat_id, from_chat_id=from_chat_id,
                message_id=message_id, caption=caption,
                parse_mode=parse_mode, reply_markup=reply_markup, **kwargs,
            )
        except Exception:
            fb_text = fallback_text or caption
            fb_markup = fallback_reply_markup or reply_markup
            fb_parse = fallback_parse_mode or parse_mode
            if fb_text is None:
                return False
            try:
                return self.send_message(
                    chat_id=chat_id, text=fb_text,
                    parse_mode=fb_parse, reply_markup=fb_markup,
                )
            except Exception:
                return False

    def edit_message_from_callback(
        self,
        chat_id: int | str,
        text: str,
        call: CallbackQuery,
        parse_mode: str | None = None,
        entities: List[MessageEntity] | None = None,
        disable_web_page_preview: bool | None = None,
        disable_notification: bool | None = None,
        protect_content: bool | None = None,
        reply_to_message_id: int | None = None,
        allow_sending_without_reply: bool | None = None,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
        timeout: int | None = None,
        message_thread_id: int | None = None,
    ) -> Message:
        """Edita mensagem extraindo message_id do CallbackQuery."""
        if call and call.message:
            message_id = call.message.id
        else:
            message_id = None
        return self.edit_message(
            chat_id=chat_id, message_id=message_id, text=text,
            parse_mode=parse_mode, entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup, timeout=timeout,
            message_thread_id=message_thread_id,
        )

    # ─── Handler Tracking ────────────────────────────────────────────

    def _add_registered_handler(self, chat_id: int, handler_func: Callable):
        """Registra um handler no dicionário de tracking."""
        if chat_id not in self._registered_callback_handlers:
            self._registered_callback_handlers[chat_id] = []
        if handler_func not in self._registered_callback_handlers[chat_id]:
            self._registered_callback_handlers[chat_id].append(handler_func)

    def _remove_registered_handler(self, chat_id: int, handler_func: Callable):
        """Remove um handler do dicionário de tracking."""
        if chat_id in self._registered_callback_handlers:
            try:
                self._registered_callback_handlers[chat_id].remove(handler_func)
                if not self._registered_callback_handlers[chat_id]:
                    del self._registered_callback_handlers[chat_id]
            except ValueError:
                pass

    def unregister_callback_query_handler(self, callback: Callable):
        """Remove um handler de callback específico por identidade de objeto."""
        new_handlers = []
        found = False
        chat_id_to_clean = None

        for handler in self.callback_query_handlers:
            try:
                if handler.get('function') is callback:
                    found = True
                    for cid, funcs in self._registered_callback_handlers.items():
                        if callback in funcs:
                            chat_id_to_clean = cid
                            break
                    continue
                new_handlers.append(handler)
            except Exception:
                new_handlers.append(handler)

        if found:
            self.callback_query_handlers = new_handlers
            if chat_id_to_clean is not None:
                self._remove_registered_handler(chat_id_to_clean, callback)

    def clear_registered_callback_handlers_by_chat_id(self, chat_id: int):
        """Remove todos os handlers de callback registrados para um chat_id.
        
        Chamado automaticamente no automatic_run() antes de executar cada componente,
        prevenindo handlers obsoletos de interações anteriores.
        """
        if chat_id in self._registered_callback_handlers:
            handlers_to_remove = list(self._registered_callback_handlers[chat_id])
            for handler_func in handlers_to_remove:
                self.unregister_callback_query_handler(handler_func)
            if chat_id in self._registered_callback_handlers and not self._registered_callback_handlers[chat_id]:
                del self._registered_callback_handlers[chat_id]

    # ─── Dual Input Handlers ─────────────────────────────────────────

    def register_next_step_or_callback_handler(self, chat_id: int, callback: Callable, filter: Callable = None, **kwargs):
        """Registra handler que aguarda mensagem OU callback. Limpa o outro ao acionar.

        Útil para formulários que aceitam tanto texto digitado quanto botões de opção.
        """
        internal_callback_query_handler_func = None

        def internal_callback_query_handler(call: CallbackQuery):
            nonlocal internal_callback_query_handler_func
            if call.message.chat.id == chat_id:
                self.clear_step_handler_by_chat_id(chat_id)
                if internal_callback_query_handler_func:
                    self.unregister_callback_query_handler(internal_callback_query_handler_func)
                callback(call)

        def internal_message_handler(message: Message):
            nonlocal internal_callback_query_handler_func
            if message.chat.id == chat_id:
                if internal_callback_query_handler_func:
                    self.unregister_callback_query_handler(internal_callback_query_handler_func)
                callback(message)

        internal_callback_query_handler_func = internal_callback_query_handler

        self.register_next_step_handler_by_chat_id(chat_id, internal_message_handler, **kwargs)

        def combined_filter(call: CallbackQuery) -> bool:
            if call.message.chat.id != chat_id:
                return False
            if filter:
                return filter(call)
            return True

        self._add_registered_handler(chat_id, internal_callback_query_handler_func)
        self.add_callback_query_handler({
            'function': internal_callback_query_handler_func,
            'filters': {'func': combined_filter}
        })

    def once_callback_query_handler(self, chat_id: int, callback: Callable, filter: Callable = None):
        """Registra handler de callback que se auto-desregistra após primeiro uso."""
        internal_handler_func = None

        def internal_callback_query_handler(call: CallbackQuery):
            nonlocal internal_handler_func
            callback(call)
            if internal_handler_func:
                self.unregister_callback_query_handler(internal_handler_func)

        internal_handler_func = internal_callback_query_handler

        def combined_filter(call: CallbackQuery) -> bool:
            if call.message.chat.id != chat_id:
                return False
            if filter is not None and not filter(call):
                return False
            return True

        self._add_registered_handler(chat_id, internal_handler_func)
        self.register_callback_query_handler(internal_handler_func, func=combined_filter)

    def add_callback_or_step_handler(self, chat_id: int, callback: Callable, respond_at_message: bool = True, send_alert: bool = False, **kwargs):
        """Handler combinado: prioriza callback, mas aceita mensagem como fallback.

        Args:
            chat_id: ID do chat
            callback: Função que recebe Message ou CallbackQuery
            respond_at_message: Se True, chama callback com a mensagem recebida
            send_alert: Se True, avisa o usuário que era esperado um clique
            **kwargs: Filtros adicionais (custom_filter=lambda call: ...)
        """
        def callback_query_handler(call: CallbackQuery):
            callback(call)
            self.unregister_callback_query_handler(callback_query_handler)

        filters: List[Callable] = []
        filters.append(lambda call: call.message.chat.id == chat_id)
        for key, custom_filter in kwargs.items():
            if callable(custom_filter):
                filters.append(custom_filter)

        self._add_registered_handler(chat_id, callback_query_handler)
        self.register_callback_query_handler(
            callback_query_handler,
            func=lambda call: all([f(call) for f in filters])
        )

        def message_handler(message: Message):
            self.unregister_callback_query_handler(callback_query_handler)
            if respond_at_message:
                callback(message)
            else:
                if send_alert:
                    self.send_message(chat_id, "Expected a button click, not a message. Resetting handler.")
                    return
                self.add_callback_or_step_handler(chat_id, callback, respond_at_message=False, send_alert=False, **kwargs)

        self.register_next_step_handler_by_chat_id(chat_id, message_handler)