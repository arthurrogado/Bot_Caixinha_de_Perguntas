"""Componente: Menu Principal.

Exibe opções principais do bot com tradução baseada no idioma do usuário.
Rota via automatic_run: MainMenu__start (ou chamada direta).
"""

from App.custom_bot import CustomBot
from telebot.types import CallbackQuery
from App.Components.BaseComponent import BaseComponent
from App.Database.users import Usuario
from App.Utils.Markup import Markup


class MainMenu(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None, startFrom=None) -> None:
        super().__init__(bot, userid, call, startFrom)

    def start(self):
        db = Usuario(self.bot)
        user = db.get(self.userid)

        # Registrar usuário se não existir
        if not user:
            info = self.bot.get_chat(self.userid)
            nome = info.first_name + (' ' + info.last_name if info.last_name else '')
            db.registrar(self.userid, nome, info.username)

        nome = self.bot.get_chat(self.userid).first_name

        buttons = [
            [[self.msg.CRIAR_CAIXINHA, 'CriarCaixinha__start'], [self.msg.MINHAS_CAIXINHAS, 'switch_inline_query_current_chat=mc ']],
            [[self.msg.PESQUISAR_CAIXINHAS, 'PesquisarCaixinhas__start']],
            [[self.msg.CAIXINHAS_CONCLUIDAS, 'switch_inline_query_current_chat=mc:c ']],
            [[self.msg.MUDAR_IDIOMA, 'MudarIdioma__start']],
        ]

        # Botão de admin panel se for admin
        if db.is_admin(self.userid):
            buttons.append([[self.msg.PAINEL_ADMIN, 'PainelAdmin__start']])

        markup = Markup.generate_inline(buttons)

        texto = self.msg.MENU_PRINCIPAL.format(nome)
        self.bot.send_message(self.userid, texto, reply_markup=markup)

    def ajuda(self):
        """Exibe mensagem de ajuda."""
        self.bot.send_message(self.userid, self.msg.MSG_AJUDA, parse_mode='HTML')
        self.start()

