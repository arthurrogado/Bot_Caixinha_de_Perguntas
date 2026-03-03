"""Componente: Responder Caixinha (enviar pergunta a uma caixinha).

Fluxo conversacional:
    1. Boas-vindas com título/autor da caixinha
    2. Escolher: Sim / Anonimamente / Cancelar
    3. Digitar pergunta (max 180 chars)
    4. Confirmar: Sim / Editar / Cancelar
    5. Salva no DB, notifica dono com imagem

Rotas:
    ResponderCaixinha__iniciar__<id_caixinha>  (via deep link)
    ResponderCaixinha__iniciar                 (pede ID manualmente)
"""

import io

from telebot.types import CallbackQuery, Message, ReplyKeyboardRemove
from telebot.formatting import escape_markdown

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.caixinhas import Caixinha
from App.Database.perguntas import Pergunta
from App.Database.users import Usuario
from App.Utils.Markup import Markup


class ResponderCaixinha(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)
        self.id_caixinha = None  # id público (uid)
        self.id_caixinha_db = None  # id interno numérico
        self.caixinha = None
        self.titulo = None
        self.id_autor_caixinha = None
        self.pergunta_texto = None
        self.anonimo = False

        # Strings traduzidas para comparação no ReplyKeyboard
        self._sim = self.msg.SIM
        self._nao = self.msg.NAO
        self._editar = self.msg.EDITAR
        self._cancelar = self.msg.CANCELAR
        self._anonimo = self.msg.RESPONDER_ANONIMAMENTE

    def iniciar(self, id_caixinha: str = None):
        """Ponto de entrada. Se id_caixinha for passado, carrega diretamente."""
        if id_caixinha:
            if str(id_caixinha).strip().isdigit():
                self.bot.send_message(self.userid, '🔒 Use o novo código UUID da caixinha.')
                return
            self._carregar_caixinha(id_caixinha)
        else:
            # Pedir ID manualmente
            msg = self.bot.send_message(
                self.userid,
                self.msg.DIGITE_ID_CAIXINHA + '\n\n/cancel \u2022 ' + self.msg.CANCELAR
            )
            self.bot.register_next_step_handler(msg, self._receber_id)

    def _receber_id(self, msg: Message):
        """Recebe ID digitado manualmente."""
        if not msg.text:
            self.bot.send_message(self.userid, self.msg.CAIXINHA_NAO_ENCONTRADA.format('?'))
            return

        if self._is_cancel(msg.text):
            self.bot.send_message(self.userid, self.msg.OK_CANCELADO)
            return

        id_cx = msg.text.strip()
        if id_cx.startswith('cx-'):
            id_cx = id_cx[3:]

        if id_cx.isdigit():
            self.bot.send_message(self.userid, '🔒 Use o novo código UUID da caixinha.')
            return

        self._carregar_caixinha(id_cx)

    def _carregar_caixinha(self, id_caixinha: str):
        """Carrega dados da caixinha e exibe boas-vindas."""
        # Garantir registro do usuário
        db_user = Usuario(self.bot)
        if not db_user.check_exists(self.userid):
            info = self.bot.get_chat(self.userid)
            nome = info.first_name + (' ' + info.last_name if info.last_name else '')
            db_user.registrar(self.userid, nome, info.username)

        db_cx = Caixinha(self.bot)
        caixinha = db_cx.get(id_caixinha)

        if not caixinha:
            self.bot.send_message(self.userid, self.msg.CAIXINHA_NAO_ENCONTRADA.format(id_caixinha))
            return

        if caixinha.get('concluida', 0) == 1:
            self.bot.send_message(self.userid, self.msg.CAIXINHA_JA_CONCLUIDA)
            return

        self.id_caixinha_db = caixinha['id']
        self.id_caixinha = caixinha.get('uid') or str(caixinha['id'])
        self.caixinha = caixinha
        self.titulo = caixinha['titulo']
        self.id_autor_caixinha = caixinha['id_usuario']

        # Se o usuário é o dono da caixinha, redirecionar para gerenciamento
        if self.id_autor_caixinha == self.userid:
            from App.Components.GerenciarCaixinha import GerenciarCaixinha
            GerenciarCaixinha(self.bot, self.userid, self.call).ver(self.id_caixinha)
            return

        # Boas-vindas
        autor_link = self._get_user_link(self.id_autor_caixinha)

        markup_opcoes = Markup.generate_keyboard([
            [self._sim],
            [self._anonimo],
            [self._cancelar],
        ])

        text = self.msg.OLA_BEM_VINDO_CAIXINHAS.format(autor_link, self.titulo)
        msg = self.bot.send_message(
            self.userid, text,
            parse_mode='Markdown',
            reply_markup=markup_opcoes
        )
        self.bot.register_next_step_handler(msg, self._confirmar)

    def _confirmar(self, msg: Message):
        """Confirma participação: Sim / Anônimo / Cancelar."""
        if not msg.text:
            return self._reperguntar(msg)

        texto = msg.text.strip()

        if self._sim in texto:
            self.anonimo = False
            msg = self.bot.send_message(
                self.userid,
                self.msg.ENVIE_SUA_PERGUNTA,
                reply_markup=ReplyKeyboardRemove()
            )
            self.bot.register_next_step_handler(msg, self._receber_pergunta)

        elif self._anonimo in texto:
            self.anonimo = True
            msg = self.bot.send_message(
                self.userid,
                self.msg.OK_AUTOR_NAO_VERA_IDENTIDADE,
                reply_markup=ReplyKeyboardRemove()
            )
            self.bot.register_next_step_handler(msg, self._receber_pergunta)

        elif self._cancelar in texto or self._nao in texto:
            self.bot.send_message(
                self.userid,
                self.msg.OK_CANCELADO,
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            self._reperguntar(msg)

    def _reperguntar(self, msg):
        """Repete a pergunta de confirmação."""
        markup_opcoes = Markup.generate_keyboard([
            [self._sim],
            [self._anonimo],
            [self._cancelar],
        ])
        retry = self.bot.send_message(
            self.userid,
            self.msg.NAO_ENTENDI_CONFIRME_NOVAMENTE,
            reply_markup=markup_opcoes
        )
        self.bot.register_next_step_handler(retry, self._confirmar)

    def _receber_pergunta(self, msg: Message):
        """Recebe texto da pergunta."""
        if not msg.text:
            msg = self.bot.send_message(self.userid, self.msg.ENVIE_SUA_PERGUNTA)
            self.bot.register_next_step_handler(msg, self._receber_pergunta)
            return

        if len(msg.text) > 180:
            retry = self.bot.send_message(self.userid, self.msg.PERGUNTA_MAX_180)
            self.bot.register_next_step_handler(retry, self._receber_pergunta)
            return

        self.pergunta_texto = msg.text.strip()

        # Pedir confirmação final
        markup_confirma = Markup.generate_keyboard([
            [self._sim],
            [self._editar],
            [self._cancelar],
        ])
        msg = self.bot.send_message(
            self.userid,
            self.msg.CONFIRMA_ENVIO_PERGUNTA,
            reply_markup=markup_confirma
        )
        self.bot.register_next_step_handler(msg, self._salvar)

    def _salvar(self, msg: Message):
        """Salva pergunta ou edita/cancela."""
        if not msg.text:
            return self._receber_pergunta(msg)

        texto = msg.text.strip()

        if self._editar in texto:
            edit_msg = self.bot.send_message(
                self.userid,
                self.msg.ENVIE_SUA_PERGUNTA_EDITADA,
                reply_markup=ReplyKeyboardRemove()
            )
            self.bot.register_next_step_handler(edit_msg, self._receber_pergunta)
            return

        if self._cancelar in texto:
            self.bot.send_message(
                self.userid,
                self.msg.OK_CANCELADO,
                reply_markup=ReplyKeyboardRemove()
            )
            return

        if self._sim in texto:
            # Salvar no DB
            db_pg = Pergunta(self.bot)
            id_pergunta = db_pg.criar(
                self.id_caixinha_db, self.userid,
                self.pergunta_texto, self.anonimo
            )

            # Incrementar contador
            Caixinha(self.bot).incrementar_perguntas(self.id_caixinha_db)

            self.bot.send_message(
                self.userid,
                self.msg.PERGUNTA_SALVA_COM_SUCESSO,
                reply_markup=ReplyKeyboardRemove()
            )

            # Notificar dono da caixinha
            self._notificar_dono(id_pergunta)
        else:
            # Não entendeu
            markup_confirma = Markup.generate_keyboard([
                [self._sim],
                [self._editar],
                [self._cancelar],
            ])
            retry = self.bot.send_message(
                self.userid,
                self.msg.NAO_ENTENDI_CONFIRME_NOVAMENTE,
                reply_markup=markup_confirma
            )
            self.bot.register_next_step_handler(retry, self._salvar)

    def _notificar_dono(self, id_pergunta):
        """Notifica dono da caixinha sobre nova pergunta."""
        # Verificar se a caixinha está silenciada
        db_cx = Caixinha(self.bot)
        caixinha = db_cx.get(self.id_caixinha_db)
        if caixinha and caixinha.get('silenciada', 0) == 1:
            return  # Não notificar

        if self.anonimo:
            autor = self.msg.AUTOR_ANONIMO
        else:
            autor = self._get_user_link_html(self.userid)

        titulo_safe = (self.titulo or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        pergunta_safe = (self.pergunta_texto or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        texto = self.msg.NOVA_PERGUNTA.format(titulo_safe, pergunta_safe, autor)

        markup = Markup.generate_inline([
            [[self.msg.MARCAR_RESPONDIDA, f'ResponderPergunta__m__{id_pergunta}']],
        ])

        # Enviar cartão de imagem + notificação ao dono
        try:
            self._enviar_cartao_pergunta(
                self.id_autor_caixinha,
                self.id_caixinha,
                id_pergunta,
                texto,
                markup
            )
        except Exception as e:
            print(f'[ResponderCaixinha] Erro ao notificar dono: {e}')
            try:
                self.bot.send_message(
                    self.id_autor_caixinha, texto,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except Exception:
                pass

    def _enviar_cartao_pergunta(self, userid, id_caixinha, id_pergunta, caption, markup):
        """Gera e envia cartão de pergunta."""
        try:
            from App.Utils.ImageGenerator import criar_cartao
            db_cx = Caixinha(self.bot)
            caixinha = db_cx.get(id_caixinha)
            db_pg = Pergunta(self.bot)
            pergunta = db_pg.get(id_pergunta)

            img = criar_cartao(caixinha['titulo'], pergunta['pergunta'])
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.name = 'cartao.png'
            buffer.seek(0)

            self.bot.send_photo(
                userid, buffer,
                caption=caption,
                parse_mode='HTML',
                reply_markup=markup
            )
        except Exception as e:
            print(f'[ResponderCaixinha] Erro imagem: {e}')
            self.bot.send_message(userid, caption, parse_mode='HTML', reply_markup=markup)

    def _get_user_link(self, userid: int) -> str:
        """Gera link markdown para usuário."""
        try:
            user = self.bot.get_chat(userid)
            nome = user.first_name + (' ' + user.last_name if user.last_name else '')
            username = user.username if user.username else 'sem username'
            return f"[{nome}](tg://user?id={userid}) - @{username}"
        except Exception:
            return f"[Usuário](tg://user?id={userid})"

    def _get_user_link_html(self, userid: int) -> str:
        """Gera link HTML para usuário."""
        try:
            user = self.bot.get_chat(userid)
            nome = user.first_name + (' ' + user.last_name if user.last_name else '')
            nome_safe = nome.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            username = f' @{user.username}' if user.username else ''
            return f'<a href="tg://user?id={userid}">{nome_safe}</a>{username}'
        except Exception:
            return f'<a href="tg://user?id={userid}">Usuário</a>'
