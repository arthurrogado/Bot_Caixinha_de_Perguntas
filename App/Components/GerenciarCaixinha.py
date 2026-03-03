"""Componente: Gerenciar Caixinha.

Visão de gerenciamento, concluir, reativar, silenciar e toggle público/privado.

Rotas (métodos curtos para caber no limite de 64 bytes de callback_data com UUID):
    GerenciarCaixinha__ver__<uid>   - Visão de gerenciamento
    GerenciarCaixinha__c__<uid>     - Concluir
    GerenciarCaixinha__r__<uid>     - Reativar
    GerenciarCaixinha__s__<uid>     - Toggle silenciar/ativar notificações
    GerenciarCaixinha__p__<uid>     - Toggle público/privado
"""

import io

from telebot.types import CallbackQuery

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.caixinhas import Caixinha
from App.Utils.Markup import Markup


class GerenciarCaixinha(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)

    # ── helpers ──────────────────────────────────────────────────────

    def _build_markup(self, uid: str, concluida: bool, silenciada: bool, publica: bool = False):
        """Monta teclado inline de gerenciamento com toggles corretos."""
        buttons = [
            [[self.msg.VER_PERGUNTAS, f'switch_inline_query_current_chat=p:{uid} ']],
        ]
        if silenciada:
            buttons.append([[self.msg.ATIVAR_NOTIFICACOES, f'GerenciarCaixinha__s__{uid}']])
        else:
            buttons.append([[self.msg.SILENCIAR_NOTIFICACOES, f'GerenciarCaixinha__s__{uid}']])

        # Toggle público/privado
        if publica:
            buttons.append([[self.msg.TORNAR_PRIVADA, f'GerenciarCaixinha__p__{uid}']])
        else:
            buttons.append([[self.msg.TORNAR_PUBLICA, f'GerenciarCaixinha__p__{uid}']])

        if concluida:
            buttons.append([[self.msg.REATIVAR_CAIXINHA, f'GerenciarCaixinha__r__{uid}']])
        else:
            buttons.append([[self.msg.MARCAR_CONCLUIDA, f'GerenciarCaixinha__c__{uid}']])

        buttons.append([[self.msg.VOLTAR, 'MinhasCaixinhas__start']])
        return Markup.generate_inline(buttons)

    @staticmethod
    def _safe_html(text: str) -> str:
        return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # ── visão de gerenciamento ───────────────────────────────────────

    def ver(self, id_caixinha: str):
        """Mostra visão de gerenciamento da caixinha com imagem e botões."""
        db = Caixinha(self.bot)
        caixinha = db.get(id_caixinha)
        if not caixinha:
            self.bot.send_message(self.userid, self.msg.CAIXINHA_NAO_ENCONTRADA.format(id_caixinha))
            return

        if not db.is_owner(caixinha['id'], self.userid):
            self.bot.send_message(self.userid, self.msg.VOCE_NAO_AUTOR)
            return

        uid = caixinha.get('uid') or str(caixinha['id'])
        titulo = caixinha['titulo']
        total = caixinha['total_perguntas']
        concluida = caixinha.get('concluida', 0) == 1
        silenciada = caixinha.get('silenciada', 0) == 1
        publica = caixinha.get('publica', 0) == 1

        link = f"https://t.me/{self.bot.get_me().username}?start=cx-{uid}"
        markup = self._build_markup(uid, concluida, silenciada, publica)

        caption = (
            f"📦 <b>{self._safe_html(titulo)}</b>\n\n"
            f"📊 Perguntas: <b>{total}</b>\n"
            f"🔗 <code>{link}</code>"
        )

        try:
            from App.Utils.ImageGenerator import criar_cartao_caixinha
            img = criar_cartao_caixinha(titulo)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.name = 'caixinha.png'
            buf.seek(0)
            self.bot.send_photo(self.userid, buf, caption=caption, parse_mode='HTML', reply_markup=markup)
        except Exception:
            self.bot.send_message(self.userid, caption, parse_mode='HTML', reply_markup=markup)

    # ── concluir (c) ─────────────────────────────────────────────────

    def c(self, id_caixinha: str):
        """Marca caixinha como concluída."""
        db = Caixinha(self.bot)
        caixinha = db.get(id_caixinha)
        if not caixinha:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.ERRO_OPERACAO, show_alert=True)
            return

        uid = caixinha.get('uid') or str(caixinha['id'])

        if db.concluir(id_caixinha):
            silenciada = caixinha.get('silenciada', 0) == 1
            publica = caixinha.get('publica', 0) == 1
            markup = self._build_markup(uid, concluida=True, silenciada=silenciada, publica=publica)
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.CAIXINHA_CONCLUIDA_OK)
                try:
                    self.bot.edit_message_reply_markup(self.userid, self.call.message.message_id, reply_markup=markup)
                except Exception:
                    pass
            else:
                self.bot.send_message(self.userid, self.msg.CAIXINHA_CONCLUIDA_OK)
        else:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.ERRO_OPERACAO, show_alert=True)
            else:
                self.bot.send_message(self.userid, self.msg.ERRO_OPERACAO)

    # ── reativar (r) ─────────────────────────────────────────────────

    def r(self, id_caixinha: str):
        """Reativa caixinha concluída."""
        db = Caixinha(self.bot)
        caixinha = db.get(id_caixinha)
        if not caixinha:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.ERRO_OPERACAO, show_alert=True)
            return

        uid = caixinha.get('uid') or str(caixinha['id'])

        if db.reativar(id_caixinha):
            silenciada = caixinha.get('silenciada', 0) == 1
            publica = caixinha.get('publica', 0) == 1
            markup = self._build_markup(uid, concluida=False, silenciada=silenciada, publica=publica)
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.CAIXINHA_REATIVADA_OK)
                try:
                    self.bot.edit_message_reply_markup(self.userid, self.call.message.message_id, reply_markup=markup)
                except Exception:
                    pass
            else:
                self.bot.send_message(self.userid, self.msg.CAIXINHA_REATIVADA_OK)
        else:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.ERRO_OPERACAO, show_alert=True)
            else:
                self.bot.send_message(self.userid, self.msg.ERRO_OPERACAO)

    # ── silenciar/ativar toggle (s) ──────────────────────────────────

    def s(self, id_caixinha: str):
        """Toggle silenciar/ativar notificações de novas perguntas."""
        db = Caixinha(self.bot)
        caixinha = db.get(id_caixinha)
        if not caixinha:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.ERRO_OPERACAO, show_alert=True)
            return

        if not db.is_owner(caixinha['id'], self.userid):
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.VOCE_NAO_AUTOR, show_alert=True)
            return

        uid = caixinha.get('uid') or str(caixinha['id'])
        silenciada = caixinha.get('silenciada', 0) == 1
        concluida = caixinha.get('concluida', 0) == 1
        publica = caixinha.get('publica', 0) == 1

        if silenciada:
            db.ativar_notificacoes(caixinha['id'])
            feedback = self.msg.ATIVAR_NOTIFICACOES
        else:
            db.silenciar(caixinha['id'])
            feedback = self.msg.SILENCIAR_NOTIFICACOES

        new_silenciada = not silenciada
        markup = self._build_markup(uid, concluida=concluida, silenciada=new_silenciada, publica=publica)

        if self.call:
            self.bot.answer_callback_query(self.call.id, feedback)
            try:
                self.bot.edit_message_reply_markup(self.userid, self.call.message.message_id, reply_markup=markup)
            except Exception:
                pass
        else:
            self.bot.send_message(self.userid, feedback)

    # ── toggle público/privado (p) ───────────────────────────────────

    def p(self, id_caixinha: str):
        """Toggle público/privado da caixinha."""
        db = Caixinha(self.bot)
        caixinha = db.get(id_caixinha)
        if not caixinha:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.ERRO_OPERACAO, show_alert=True)
            return

        if not db.is_owner(caixinha['id'], self.userid):
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.VOCE_NAO_AUTOR, show_alert=True)
            return

        uid = caixinha.get('uid') or str(caixinha['id'])
        novo_estado = db.toggle_publica(id_caixinha)

        if novo_estado is None:
            if self.call:
                self.bot.answer_callback_query(self.call.id, self.msg.ERRO_OPERACAO, show_alert=True)
            return

        concluida = caixinha.get('concluida', 0) == 1
        silenciada = caixinha.get('silenciada', 0) == 1
        feedback = self.msg.CAIXINHA_PUBLICA if novo_estado else self.msg.CAIXINHA_PRIVADA
        markup = self._build_markup(uid, concluida=concluida, silenciada=silenciada, publica=novo_estado)

        if self.call:
            self.bot.answer_callback_query(self.call.id, feedback)
            try:
                self.bot.edit_message_reply_markup(self.userid, self.call.message.message_id, reply_markup=markup)
            except Exception:
                pass
        else:
            self.bot.send_message(self.userid, feedback)
