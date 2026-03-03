"""Componente: Enviar Comunicado (admin only).

Fluxo:
    1. Admin envia mensagem/mídia
    2. Exibe contagem de destinatários
    3. Pede confirmação digitando "confirma enviar"
    4. Forward para todos os usuários

Rota: Comunicado__start
"""

from telebot.types import CallbackQuery, Message, ReplyKeyboardRemove

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.users import Usuario
from App.Utils.Markup import Markup


class Comunicado(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)
        # Verifica permissão
        self.permission.check_is_admin()

    def start(self):
        """Pede a mensagem de comunicado."""
        msg = self.bot.send_message(
            self.userid,
            self.msg.COMUNICADO_QUAL_MSG,
            reply_markup=ReplyKeyboardRemove()
        )
        self.bot.register_next_step_handler(msg, self._receber_comunicado)

    def _receber_comunicado(self, msg: Message):
        """Recebe comunicado e mostra contagem + pede confirmação."""
        if msg.text and self._is_cancel(msg.text):
            self.bot.send_message(self.userid, self.msg.OK_CANCELADO, reply_markup=ReplyKeyboardRemove())
            return

        self.comunicado_msg = msg

        db = Usuario(self.bot)
        todos = db.get_all()
        total = len(todos) if todos else 0

        # Mostrar contagem e pedir confirmação
        response = self.bot.send_message(
            self.userid,
            self.msg.COMUNICADO_CONTAGEM.format(total),
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove(),
        )
        self.bot.register_next_step_handler(response, self._confirmar_envio)

    def _confirmar_envio(self, msg: Message):
        """Verifica se o admin digitou 'confirma enviar' para confirmar."""
        if not msg.text:
            self.bot.send_message(self.userid, self.msg.OK_CANCELADO, reply_markup=ReplyKeyboardRemove())
            return

        if self._is_cancel(msg.text):
            self.bot.send_message(self.userid, self.msg.OK_CANCELADO, reply_markup=ReplyKeyboardRemove())
            return

        if msg.text.strip().lower() != 'confirma enviar':
            self.bot.send_message(
                self.userid,
                self.msg.OK_CANCELADO + '\n\n(Esperava: <b>confirma enviar</b>)',
                parse_mode='HTML',
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        # Confirmar e enviar
        db = Usuario(self.bot)
        todos = db.get_all()

        if not todos:
            self.bot.send_message(
                self.userid,
                '😢 Nenhum usuário encontrado',
                reply_markup=ReplyKeyboardRemove()
            )
            return

        enviados = 0
        for user in todos:
            try:
                self.bot.forward_message(
                    user['id'],
                    self.userid,
                    self.comunicado_msg.message_id
                )
                enviados += 1
            except Exception:
                pass

        self.bot.send_message(
            self.userid,
            f"{self.msg.COMUNICADO_ENVIADO}\n📊 {enviados}/{len(todos)} entregues",
            reply_markup=ReplyKeyboardRemove()
        )
