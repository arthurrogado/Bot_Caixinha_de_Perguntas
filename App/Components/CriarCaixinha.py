"""Componente: Criar Caixinha.

Wizard de criação de caixinha de perguntas.
Fluxo: verificação de canal → título → confirmação → visibilidade → salva → imagem → link.

Rota: CriarCaixinha__start
"""

import io

from telebot.types import CallbackQuery, Message
from telebot.formatting import escape_markdown

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.caixinhas import Caixinha
from App.Utils.Markup import Markup


class CriarCaixinha(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)
        self.titulo = None
        self.publica = False  # default: privada

    # ── helpers ──────────────────────────────────────────────────────

    def _check_canal(self) -> bool:
        """Verifica se o usuário pertence ao canal obrigatório.

        Retorna True se ok, False se não é membro (e já envia mensagem).
        """
        from App.Config.config import CANAL_ID
        if not CANAL_ID:
            return True
        try:
            member = self.bot.get_chat_member(CANAL_ID, self.userid)
            if member.status in ('left', 'kicked'):
                self._enviar_aviso_canal(CANAL_ID)
                return False
            return True
        except Exception:
            # Se não conseguir verificar, libera
            return True

    def _enviar_aviso_canal(self, canal_id):
        """Envia mensagem pedindo para entrar no canal."""
        try:
            chat = self.bot.get_chat(canal_id)
            link = chat.invite_link or f'https://t.me/{chat.username}' if chat.username else None
        except Exception:
            link = None

        buttons = []
        if link:
            buttons.append([[self.msg.ENTRAR_NO_CANAL, f'url={link}']])

        markup = Markup.generate_inline(buttons) if buttons else None
        self.bot.send_message(
            self.userid,
            self.msg.ENTRE_NO_CANAL,
            reply_markup=markup,
        )

    # ── fluxo principal ─────────────────────────────────────────────

    def start(self):
        """Ponto de entrada: verifica canal e pede título."""
        if not self._check_canal():
            return

        msg = self.bot.send_message(
            self.userid,
            self.msg.QUAL_O_TITULO_DA_CAIXINHA + '\n\n/cancel • ' + self.msg.CANCELAR,
        )
        self.bot.register_next_step_handler(msg, self.receber_titulo)

    def receber_titulo(self, msg: Message):
        """Recebe e valida o título."""
        if not msg.text:
            return self.start()

        if self._is_cancel(msg.text):
            self.bot.send_message(self.userid, self.msg.OK_CANCELADO)
            return

        titulo = msg.text.strip()

        if len(titulo) > 80:
            error_msg = self.bot.send_message(
                self.userid,
                self.msg.TITULO_MAX_80_CARACTERES
            )
            self.bot.register_next_step_handler(error_msg, self.receber_titulo)
            return

        self.titulo = titulo
        self._pedir_confirmacao()

    def _pedir_confirmacao(self):
        """Pergunta se o usuário confirma o título antes de escolher visibilidade."""
        markup = Markup.generate_inline([
            [[self.msg.SIM, '_cx_confirmar']],
            [[self.msg.EDITAR, '_cx_editar']],
            [[self.msg.CANCELAR, '_cx_cancelar']],
        ])
        texto = self.msg.CONFIRMAR_TITULO.format(self.titulo)
        self.bot.send_message(
            self.userid, texto,
            parse_mode='Markdown',
            reply_markup=markup
        )
        self.bot.once_callback_query_handler(
            self.userid,
            self._processar_confirmacao,
            lambda call: call.data in ['_cx_confirmar', '_cx_editar', '_cx_cancelar']
        )

    def _processar_confirmacao(self, call):
        """Processa a confirmação do título."""
        if call.data == '_cx_cancelar':
            self.bot.try_edit_message_text(
                call.message.text + '\n\n❌ Cancelado',
                call=call, reply_markup=None
            )
            return

        if call.data == '_cx_editar':
            self.bot.try_edit_message_text(
                call.message.text + '\n\n✏️',
                call=call, reply_markup=None
            )
            msg = self.bot.send_message(
                self.userid,
                self.msg.QUAL_O_TITULO_DA_CAIXINHA
            )
            self.bot.register_next_step_handler(msg, self.receber_titulo)
            return

        # _cx_confirmar → pedir visibilidade
        self.bot.try_edit_message_text(
            f"✅ Título: *{self.titulo}*",
            call=call, reply_markup=None, parse_mode='Markdown'
        )
        self._pedir_visibilidade()

    def _pedir_visibilidade(self):
        """Pergunta se a caixinha será pública ou privada (default: privada)."""
        markup = Markup.generate_inline([
            [[self.msg.CAIXINHA_PRIVADA, '_cx_vis_privada']],
            [[self.msg.CAIXINHA_PUBLICA, '_cx_vis_publica']],
        ])
        self.bot.send_message(
            self.userid,
            self.msg.ESCOLHA_VISIBILIDADE,
            parse_mode='HTML',
            reply_markup=markup,
        )
        self.bot.once_callback_query_handler(
            self.userid,
            self._processar_visibilidade,
            lambda call: call.data in ['_cx_vis_privada', '_cx_vis_publica']
        )

    def _processar_visibilidade(self, call):
        """Processa escolha de visibilidade e salva a caixinha."""
        self.publica = call.data == '_cx_vis_publica'
        label = self.msg.CAIXINHA_PUBLICA if self.publica else self.msg.CAIXINHA_PRIVADA
        self.bot.try_edit_message_text(
            f"✅ {label}",
            call=call, reply_markup=None,
        )
        self.salvar_caixinha()

    def salvar_caixinha(self):
        """Salva a caixinha no banco e envia confirmação com imagem e link."""
        db = Caixinha(self.bot)
        id_caixinha = db.criar(self.userid, self.titulo, publica=self.publica)

        if not id_caixinha:
            self.bot.send_message(self.userid, self.msg.ERRO_OPERACAO)
            return

        self.bot.send_message(self.userid, self.msg.CAIXINHA_CRIADA_COM_SUCESSO)

        # Gerar imagem da caixinha
        try:
            from App.Utils.ImageGenerator import criar_cartao_caixinha
            img = criar_cartao_caixinha(self.titulo)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.name = 'caixinha.png'
            buffer.seek(0)
        except Exception as e:
            print(f"[CriarCaixinha] Erro ao gerar imagem: {e}")
            buffer = None

        link = f"https://t.me/{self.bot.get_me().username}?start=cx-{id_caixinha}"

        markup_caixinha = Markup.generate_inline([
            [[self.msg.VER_PERGUNTAS, f'switch_inline_query_current_chat=p:{id_caixinha} ']],
            [[self.msg.MARCAR_CONCLUIDA, f'GerenciarCaixinha__c__{id_caixinha}']],
        ])

        caption = (
            f"📦 <b>{self.titulo}</b>\n\n"
            f"🔗 <code>{link}</code>"
        )

        if buffer:
            self.bot.send_photo(
                self.userid, buffer,
                caption=caption,
                parse_mode='HTML',
                reply_markup=markup_caixinha
            )
        else:
            self.bot.send_message(
                self.userid, caption,
                parse_mode='HTML',
                reply_markup=markup_caixinha
            )
