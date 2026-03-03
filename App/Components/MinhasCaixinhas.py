"""Componente: Minhas Caixinhas.

Lista caixinhas ativas e concluídas do usuário.

Rotas:
    MinhasCaixinhas__start       - Caixinhas ativas
    MinhasCaixinhas__concluidas  - Caixinhas concluídas
"""

import io

from telebot.types import CallbackQuery
from telebot.formatting import escape_markdown

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.caixinhas import Caixinha
from App.Utils.Markup import Markup


class MinhasCaixinhas(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)

    def start(self):
        """Lista caixinhas ativas."""
        db = Caixinha(self.bot)
        caixinhas = db.get_by_usuario(self.userid, concluida=0)

        if not caixinhas:
            self.bot.send_message(self.userid, self.msg.SEM_CAIXINHAS)
            return

        self.bot.send_message(
            self.userid,
            self.msg.SUAS_CAIXINHAS,
            parse_mode='Markdown'
        )

        self._enviar_lista(caixinhas, concluida=False)

    def concluidas(self):
        """Lista caixinhas concluídas."""
        db = Caixinha(self.bot)
        caixinhas = db.get_concluidas(self.userid)

        if not caixinhas:
            self.bot.send_message(self.userid, self.msg.SEM_CAIXINHAS)
            return

        self.bot.send_message(
            self.userid,
            self.msg.SUAS_CAIXINHAS_CONCLUIDAS,
            parse_mode='Markdown'
        )

        self._enviar_lista(caixinhas, concluida=True)

    def _enviar_lista(self, caixinhas: list, concluida: bool = False):
        """Envia cada caixinha com imagem + markup."""
        bot_username = self.bot.get_me().username

        for cx in caixinhas:
            titulo = cx['titulo']
            id_cx = cx.get('uid') or str(cx['id'])
            link = f"https://t.me/{bot_username}?start=cx-{id_cx}"

            if concluida:
                markup = Markup.generate_inline([
                    [[self.msg.VER_PERGUNTAS, f'switch_inline_query_current_chat=p:{id_cx} ']],
                    [[self.msg.REATIVAR_CAIXINHA, f'GerenciarCaixinha__r__{id_cx}']],
                    [[self.msg.VOLTAR, 'MainMenu__start']],
                ])
            else:
                markup = Markup.generate_inline([
                    [[self.msg.VER_PERGUNTAS, f'switch_inline_query_current_chat=p:{id_cx} ']],
                    [[self.msg.MARCAR_CONCLUIDA, f'GerenciarCaixinha__c__{id_cx}']],
                    [[self.msg.VOLTAR, 'MainMenu__start']],
                ])

            # Tentar gerar imagem
            try:
                from App.Utils.ImageGenerator import criar_cartao_caixinha
                img = criar_cartao_caixinha(titulo)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.name = 'caixinha.png'
                buffer.seek(0)

                caption = f"📦 <b>{titulo}</b>\n\n🔗 <code>{link}</code>"
                self.bot.send_photo(
                    self.userid, buffer,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except Exception:
                caption = f"📦 <b>{titulo}</b>\n\n🔗 <code>{link}</code>"
                self.bot.send_message(
                    self.userid, caption,
                    parse_mode='HTML',
                    reply_markup=markup
                )
