"""Componente: Pesquisar Caixinhas Públicas (submenu).

Exibe submenu com opções de busca por caixinhas públicas:
    - Mais recentes (inline cx)
    - Mais perguntados (inline cxp)
    - Em alta 24h (inline cxt)
    - Responder por código (abre ResponderCaixinha.iniciar)

Rota: PesquisarCaixinhas__start
"""

from telebot.types import CallbackQuery

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Utils.Markup import Markup


class PesquisarCaixinhas(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)

    def start(self):
        """Exibe submenu de pesquisa de caixinhas públicas."""
        markup = Markup.generate_inline([
            [[self.msg.MAIS_RECENTES, 'switch_inline_query_current_chat=cx ']],
            [[self.msg.MAIS_PERGUNTADOS, 'switch_inline_query_current_chat=cxp ']],
            [[self.msg.EM_ALTA, 'switch_inline_query_current_chat=cxt ']],
            [[self.msg.RESPONDER_POR_CODIGO, 'ResponderCaixinha__iniciar']],
            [[self.msg.VOLTAR, 'MainMenu__start']],
        ])

        if self.call:
            self.bot.try_edit_message_text(
                self.msg.MENU_PESQUISAR,
                chat_id=self.userid, call=self.call,
                parse_mode='HTML', reply_markup=markup,
            )
        else:
            self.bot.send_message(
                self.userid,
                self.msg.MENU_PESQUISAR,
                parse_mode='HTML',
                reply_markup=markup,
            )
