"""Componente: Responder Pergunta (dono da caixinha gerencia perguntas).

Funções:
    - Visualizar pergunta com imagem e botão toggle
    - Marcar/desmarcar como respondida com notificação com delay de 15s
    - Toggle visual no botão

Rotas (métodos curtos para caber no limite de callback_data):
    ResponderPergunta__v__<id_pergunta>   - Visualizar pergunta
    ResponderPergunta__m__<id_pergunta>   - Marcar como respondida
    ResponderPergunta__dm__<id_pergunta>  - Desmarcar (desfazer)
"""

import io
import threading

from telebot.types import CallbackQuery
from telebot.formatting import escape_markdown

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.caixinhas import Caixinha
from App.Database.perguntas import Pergunta
from App.Utils.Markup import Markup


# Timers pendentes de notificação: {id_pergunta: threading.Timer}
_pending_notifications: dict[int, threading.Timer] = {}


class ResponderPergunta(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _safe_html(text: str) -> str:
        return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _get_user_link_html(self, userid: int) -> str:
        try:
            user = self.bot.get_chat(userid)
            nome = user.first_name + (' ' + user.last_name if user.last_name else '')
            username = f" @{user.username}" if user.username else ''
            return f'<a href="tg://user?id={userid}">{self._safe_html(nome)}</a>{username}'
        except Exception:
            return f'<a href="tg://user?id={userid}">Usuário</a>'

    def _build_toggle_markup(self, id_pergunta: int, respondida: bool, uid_caixinha: str):
        """Monta markup com botão toggle de respondida."""
        if respondida:
            btn_text = self.msg.RESPONDIDA_DESFAZER
            btn_data = f'ResponderPergunta__dm__{id_pergunta}'
        else:
            btn_text = self.msg.MARCAR_RESPONDIDA
            btn_data = f'ResponderPergunta__m__{id_pergunta}'

        return Markup.generate_inline([
            [[btn_text, btn_data]],
            [[self.msg.VER_PERGUNTAS, f'switch_inline_query_current_chat=p:{uid_caixinha} ']],
        ])

    # ── visualizar pergunta (v) ──────────────────────────────────────

    def v(self, id_pergunta: str):
        """Visualiza pergunta com imagem e botão de marcar respondida."""
        try:
            id_pg = int(id_pergunta)
        except Exception:
            self.bot.send_message(self.userid, self.msg.PERGUNTA_NAO_ENCONTRADA)
            return

        db_pg = Pergunta(self.bot)
        pergunta = db_pg.get(id_pg)
        if not pergunta:
            self.bot.send_message(self.userid, self.msg.PERGUNTA_NAO_ENCONTRADA)
            return

        db_cx = Caixinha(self.bot)
        caixinha = db_cx.get(pergunta['id_caixinha'])
        if not caixinha or not db_cx.is_owner(caixinha['id'], self.userid):
            self.bot.send_message(self.userid, self.msg.VOCE_NAO_AUTOR)
            return

        uid = caixinha.get('uid') or str(caixinha['id'])
        titulo = caixinha['titulo']
        texto_pg = pergunta['pergunta']
        anonima = pergunta.get('anonima', 0) == 1
        respondida = pergunta.get('respondida', 0) == 1

        if anonima:
            autor_desc = self.msg.AUTOR_ANONIMO
        else:
            autor_desc = self._get_user_link_html(pergunta.get('id_usuario_autor'))

        markup = self._build_toggle_markup(id_pg, respondida, uid)

        caption = (
            f"📦 <b>{self._safe_html(titulo)}</b>\n\n"
            f"❓ {self._safe_html(texto_pg)}\n\n"
            f"👤 {autor_desc}\n\n"
            f"<i>{self.msg.INSTRUCAO_POSTAR}</i>"
        )

        try:
            from App.Utils.ImageGenerator import criar_cartao
            img = criar_cartao(titulo, texto_pg)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.name = 'pergunta.png'
            buf.seek(0)
            self.bot.send_document(self.userid, buf, caption=caption, parse_mode='HTML', reply_markup=markup)
        except Exception:
            self.bot.send_message(self.userid, caption, parse_mode='HTML', reply_markup=markup)

    # ── marcar como respondida (m) ───────────────────────────────────

    def m(self, id_pergunta: str):
        """Marca pergunta como respondida e agenda notificação em 15s."""
        try:
            id_pg = int(id_pergunta)
        except Exception:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.PERGUNTA_NAO_ENCONTRADA)
            return

        db_pg = Pergunta(self.bot)
        pergunta = db_pg.get(id_pg)
        if not pergunta:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.PERGUNTA_NAO_ENCONTRADA)
            return

        db_cx = Caixinha(self.bot)
        if not db_cx.is_owner(pergunta['id_caixinha'], self.userid):
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.VOCE_NAO_AUTOR)
            return

        caixinha = db_cx.get(pergunta['id_caixinha'])
        uid = (caixinha.get('uid') if caixinha else '') or str(pergunta['id_caixinha'])

        # Marcar no DB
        db_pg.marcar_respondida(id_pg)

        # Toggle visual do botão
        markup = self._build_toggle_markup(id_pg, respondida=True, uid_caixinha=uid)
        if self.call:
            self.bot.answer_callback_query(self.call.id, self.msg.RESPONDIDA_PENDENTE)
            try:
                self.bot.edit_message_reply_markup(
                    self.userid, self.call.message.message_id, reply_markup=markup
                )
            except Exception:
                pass

        # Cancelar timer anterior se existir
        old_timer = _pending_notifications.pop(id_pg, None)
        if old_timer:
            old_timer.cancel()

        # Agendar notificação em 15s
        timer = threading.Timer(15.0, self._notificar_autor_delayed, args=[id_pg])
        _pending_notifications[id_pg] = timer
        timer.start()

    # ── desmarcar (dm) ───────────────────────────────────────────────

    def dm(self, id_pergunta: str):
        """Desmarca pergunta (toggle off) e cancela notificação pendente."""
        try:
            id_pg = int(id_pergunta)
        except Exception:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.PERGUNTA_NAO_ENCONTRADA)
            return

        db_pg = Pergunta(self.bot)
        pergunta = db_pg.get(id_pg)
        if not pergunta:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.PERGUNTA_NAO_ENCONTRADA)
            return

        db_cx = Caixinha(self.bot)
        if not db_cx.is_owner(pergunta['id_caixinha'], self.userid):
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.VOCE_NAO_AUTOR)
            return

        caixinha = db_cx.get(pergunta['id_caixinha'])
        uid = (caixinha.get('uid') if caixinha else '') or str(pergunta['id_caixinha'])

        # Cancelar notificação pendente
        timer = _pending_notifications.pop(id_pg, None)
        if timer:
            timer.cancel()

        # Desmarcar no DB
        db_pg.desmarcar_respondida(id_pg)

        # Toggle visual do botão
        markup = self._build_toggle_markup(id_pg, respondida=False, uid_caixinha=uid)
        if self.call:
            self.bot.answer_callback_query(self.call.id, self.msg.DESMARCADA_RESPONDIDA)
            try:
                self.bot.edit_message_reply_markup(
                    self.userid, self.call.message.message_id, reply_markup=markup
                )
            except Exception:
                pass

    # ── notificação delayed ──────────────────────────────────────────

    def _notificar_autor_delayed(self, id_pergunta: int):
        """Envia notificação ao autor após 15s (chamado pelo Timer)."""
        _pending_notifications.pop(id_pergunta, None)

        db_pg = Pergunta(self.bot)
        pergunta = db_pg.get(id_pergunta)
        if not pergunta:
            return

        # Se foi desmarcada no intervalo, não notificar
        if pergunta.get('respondida', 0) != 1:
            return

        # Se já foi notificado antes, não notificar novamente
        if int(pergunta.get('autor_notificado', 0)) == 1:
            return

        id_autor = pergunta['id_usuario_autor']
        if id_autor == self.userid:
            return

        try:
            db_cx = Caixinha(self.bot)
            caixinha = db_cx.get(pergunta['id_caixinha'])
            dono_link = self._get_user_link_html(self.userid)
            pergunta_text = self._safe_html(pergunta.get('pergunta', ''))

            texto = (
                f"📣 <b>Sua pergunta foi marcada como respondida!</b>\n\n"
                f"❓ {pergunta_text}\n\n"
                f"👤 Dono da caixinha: {dono_link}"
            )
            self.bot.send_message(id_autor, texto, parse_mode='HTML')
            db_pg.marcar_autor_notificado(id_pergunta)
        except Exception:
            pass
