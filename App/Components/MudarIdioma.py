"""Componente: Mudar Idioma.

Exibe opções de idioma e salva preferência do usuário.

Rota: MudarIdioma__start
"""

from telebot.types import CallbackQuery

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Utils.Markup import Markup
from App.Core.Messages import get_msg, set_user_lang


class MudarIdioma(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)

    def start(self):
        """Exibe opções de idioma."""
        markup = Markup.generate_inline([
            [['🇧🇷🇵🇹 Português', '_lang_pt']],
            [['🇺🇸 English', '_lang_en']],
            [['🇲🇽🇪🇸 Español', '_lang_es']],
            [[self.msg.VOLTAR, 'MainMenu__start']],
        ])

        self.bot.send_message(self.userid, self.msg.SELECIONE_IDIOMA, reply_markup=markup)

        self.bot.add_callback_or_step_handler(
            self.userid, self._selecionar,
            respond_at_message=False,
            custom_filter=lambda call: call.data in ['_lang_pt', '_lang_en', '_lang_es']
        )

    def _selecionar(self, call: CallbackQuery):
        """Processa seleção de idioma."""
        idioma_map = {
            '_lang_pt': 'pt',
            '_lang_en': 'en',
            '_lang_es': 'es',
        }
        idioma = idioma_map.get(call.data, 'pt')

        set_user_lang(self.userid, idioma)  # salva no cache e no DB
        new_msg = get_msg(lang=idioma)
        self.bot.send_message(self.userid, new_msg.CONFIRMACAO_MUDANCA_IDIOMA)
        # Reabrir menu principal no novo idioma
        from App.Components.MainMenu import MainMenu
        MainMenu(self.bot, self.userid).start()
