"""Componente: StoryShare.

Tenta postar nos stories quando houver suporte Business API; caso contrário,
envia arte pronta para compartilhamento manual.
"""

import io
import os

from telebot.types import CallbackQuery

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.perguntas import Pergunta
from App.Database.caixinhas import Caixinha


class StoryShare(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)

    def start(self, id_pergunta: str):
        try:
            id_pergunta_int = int(id_pergunta)
        except Exception:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.PERGUNTA_NAO_ENCONTRADA, show_alert=True)
            return

        db_pg = Pergunta(self.bot)
        pergunta = db_pg.get(id_pergunta_int)
        if not pergunta:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.PERGUNTA_NAO_ENCONTRADA, show_alert=True)
            return

        db_cx = Caixinha(self.bot)
        if not db_cx.is_owner(pergunta['id_caixinha'], self.userid):
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.VOCE_NAO_AUTOR, show_alert=True)
            return

        caixinha = db_cx.get(pergunta['id_caixinha'])
        titulo = (caixinha or {}).get('titulo', 'Caixinha')
        resposta = (pergunta.get('resposta') or '').strip() or (pergunta.get('pergunta') or '').strip()

        buffer = io.BytesIO()
        from App.Utils.ImageGenerator import criar_story_card
        img = criar_story_card(titulo, resposta)
        img.save(buffer, format='PNG')
        buffer.name = 'story.png'
        buffer.seek(0)

        business_connection_id = os.getenv('TELEGRAM_BUSINESS_CONNECTION_ID', '').strip()

        posted = False
        if business_connection_id and hasattr(self.bot, 'post_story'):
            try:
                self.bot.post_story(
                    business_connection_id=business_connection_id,
                    content={
                        'type': 'photo',
                        'photo': 'attach://story',
                    },
                    active_period=86400,
                    caption=f"📦 {titulo}\n\n{resposta[:700]}",
                    files={'story': buffer.getvalue()},
                )
                posted = True
            except Exception:
                posted = False

        if posted:
            self.bot.send_message(self.userid, '✅ Story postado automaticamente.')
            return

        self.bot.send_document(
            self.userid,
            buffer,
            caption=self.msg.STORY_INDISPONIVEL_BOT,
            reply_markup=None,
        )

        if self.call:
            self.bot.answer_callback_query(self.call.id, self.msg.STORY_INDISPONIVEL_BOT, show_alert=False)
