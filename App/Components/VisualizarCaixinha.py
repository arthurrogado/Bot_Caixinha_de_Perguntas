"""Componente: Visualizar Caixinha.

Lista todas as perguntas de uma caixinha, com cartão de imagem.

Rota: VisualizarCaixinha__start__<id_caixinha>
"""

import io

from telebot.types import CallbackQuery
from telebot.formatting import escape_markdown

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.caixinhas import Caixinha
from App.Database.perguntas import Pergunta
from App.Utils.Markup import Markup


class VisualizarCaixinha(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)

    def start(self, id_caixinha: str):
        """Lista perguntas da caixinha."""
        db_cx = Caixinha(self.bot)
        caixinha = db_cx.get(id_caixinha)
        if not caixinha:
            self.bot.send_message(self.userid, self.msg.CAIXINHA_NAO_ENCONTRADA.format(id_caixinha))
            return

        id_cx_db = caixinha['id']
        id_cx_publico = caixinha.get('uid') or str(caixinha['id'])
        titulo = caixinha['titulo']
        db_pg = Pergunta(self.bot)
        perguntas = db_pg.get_by_caixinha(id_cx_db)

        markup = Markup.generate_inline([
            [[self.msg.VER_PERGUNTAS, f'switch_inline_query_current_chat=p:{id_cx_publico} ']],
            [[self.msg.VOLTAR, 'MinhasCaixinhas__start']],
        ])

        if not perguntas:
            self.bot.send_message(
                self.userid,
                f"📦 *{escape_markdown(titulo)}*\n\n📭 _Nenhuma pergunta ainda_",
                parse_mode='MarkdownV2',
                reply_markup=markup
            )
            return

        # Construir texto das perguntas (com limite de 3900 chars)
        message = f"📦 Perguntas caixinha:\n\nTítulo: *_{escape_markdown(titulo)}_*\n\nMENSAGENS DA CAIXINHA:\n\n"

        for pg in perguntas:
            id_pg = pg['id']
            texto_pg = pg['pergunta']
            id_autor = pg['id_usuario_autor']
            anonima = pg['anonima'] == 1

            if anonima:
                autor_texto = self.msg.AUTOR_ANONIMO
            else:
                autor_texto = self._get_user_link(id_autor)

            linha = f"`{id_pg}` *{escape_markdown(texto_pg)}*\n{autor_texto}\n\n"

            if len(message) + len(linha) > 3900:
                self.bot.send_message(
                    self.userid, message,
                    parse_mode='MarkdownV2',
                    reply_markup=markup
                )
                message = ""

            message += linha

        if message:
            self.bot.send_message(
                self.userid, message,
                parse_mode='MarkdownV2',
                reply_markup=markup
            )

    def _get_user_link(self, userid: int) -> str:
        """Gera link markdown para usuário."""
        try:
            user = self.bot.get_chat(userid)
            nome = escape_markdown(user.first_name + (' ' + user.last_name if user.last_name else ''))
            username = escape_markdown(user.username) if user.username else 'sem\\_username'
            return f"[User:](tg://user?id={userid}) {nome} \\- @{username}"
        except Exception:
            return f"[Usuário](tg://user?id={userid})"
