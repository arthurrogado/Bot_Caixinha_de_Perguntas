"""Componente: Nuvem de Caixinhas.

Lista todas as caixinhas públicas e ativas (compartilhadas por todos os usuários).

Rota: NuvemCaixinhas__start
"""

from telebot.types import CallbackQuery
from telebot.formatting import escape_markdown

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.caixinhas import Caixinha
from App.Utils.Markup import Markup


class NuvemCaixinhas(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)

    def start(self):
        """Lista caixinhas públicas ativas."""
        db = Caixinha(self.bot)
        caixinhas = db.get_publicas()

        if not caixinhas:
            self.bot.send_message(self.userid, self.msg.SEM_CAIXINHAS)
            return

        bot_username = self.bot.get_me().username
        header = f"☁️ *{self.msg.NUVEM_CAIXINHAS}*\n\n"
        self.bot.send_message(self.userid, header, parse_mode='Markdown')

        for cx in caixinhas:
            titulo = cx['titulo']
            id_cx = cx.get('uid') or str(cx['id'])
            id_dono = cx['id_usuario']
            total = cx['total_perguntas']

            try:
                dono = self.bot.get_chat(id_dono)
                nome_dono = dono.first_name
            except Exception:
                nome_dono = '???'

            link = f"https://t.me/{bot_username}?start=cx-{id_cx}"

            markup = Markup.generate_inline([
                [[f"📝 {self.msg.RESPONDER_CAIXINHA}", f'ResponderCaixinha__iniciar__{id_cx}']],
            ])

            texto = (
                f"📦 <b>{titulo}</b>\n"
                f"👤 {nome_dono} | 📊 {total} perguntas\n"
                f"🔗 <code>{link}</code>"
            )

            self.bot.send_message(
                self.userid, texto,
                parse_mode='HTML',
                reply_markup=markup
            )
