"""Componente: Painel Administrativo.

Exibe estatísticas, configurações e ações de backup para admins.

Rotas:
    PainelAdmin__start           - Menu principal do painel
    PainelAdmin__stats           - Exibe estatísticas
    PainelAdmin__backup          - Executa backup on-demand
    PainelAdmin__backup_settings - Configurações do backup automático
    PainelAdmin__toggle_backup   - Liga/desliga backup automático
    PainelAdmin__set_interval    - Define intervalo de backup (horas)
    PainelAdmin__toggle_engine   - Alterna motor de imagens
"""

from telebot.types import CallbackQuery

from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Database.users import Usuario
from App.Database.caixinhas import Caixinha
from App.Database.perguntas import Pergunta
from App.Utils.Markup import Markup
from App.Config.runtime_config import (
    get_image_engine, toggle_image_engine,
    get_backup_enabled, toggle_backup_enabled,
    get_backup_interval, set_backup_interval,
)


class PainelAdmin(BaseComponent):

    def __init__(self, bot: CustomBot, userid, call: CallbackQuery = None) -> None:
        super().__init__(bot, userid, call)
        self.permission.check_is_admin()

    def start(self):
        """Menu principal do painel admin."""
        engine = get_image_engine()
        engine_label = f'🖼 Motor de imagens: {engine}'
        engine_btn_text = '🔄 Trocar para playwright' if engine == 'pillow' else '🔄 Trocar para pillow'

        backup_on  = get_backup_enabled()
        backup_ico = '✅' if backup_on else '❌'
        backup_label = f'📅 Backup automático: {backup_ico} | a cada {get_backup_interval()}h'

        markup = Markup.generate_inline([
            [[self.msg.ESTATISTICAS, 'PainelAdmin__stats']],
            [[self.msg.BACKUP_AGORA, 'PainelAdmin__backup']],
            [['📢 Comunicado', 'Comunicado__start']],
            [[engine_btn_text, 'PainelAdmin__toggle_engine']],
            [['⚙️ Configurações de backup', 'PainelAdmin__backup_settings']],
            [['⬅️ Início', 'MainMenu__start']],
        ])

        text = (
            f"{self.msg.PAINEL_ADMIN}\n\n"
            f"{engine_label}\n"
            f"{backup_label}"
        )

        if self.call:
            self.bot.try_edit_message_text(
                text, chat_id=self.userid, call=self.call,
                reply_markup=markup
            )
        else:
            self.bot.send_message(
                self.userid,
                text,
                reply_markup=markup,
            )

    def backup_settings(self):
        """Tela de configurações do backup automático."""
        enabled  = get_backup_enabled()
        interval = get_backup_interval()
        status   = '✅ Ativado' if enabled else '❌ Desativado'
        toggle_lbl = '🔴 Desativar backup' if enabled else '🟢 Ativar backup'

        text = (
            f"⚙️ <b>Backup automático</b>\n\n"
            f"Estado: <b>{status}</b>\n"
            f"Intervalo: <b>{interval}h</b>\n"
        )

        markup = Markup.generate_inline([
            [[toggle_lbl, 'PainelAdmin__toggle_backup']],
            [['6h',  'PainelAdmin__set_interval__6'],
             ['12h', 'PainelAdmin__set_interval__12']],
            [['24h', 'PainelAdmin__set_interval__24'],
             ['48h', 'PainelAdmin__set_interval__48']],
            [['✏️ Personalizado', 'PainelAdmin__custom_interval']],
            [['⬅️ Voltar', 'PainelAdmin__start']],
        ])

        if self.call:
            self.bot.try_edit_message_text(
                text, chat_id=self.userid, call=self.call,
                parse_mode='HTML', reply_markup=markup
            )
        else:
            self.bot.send_message(
                self.userid, text,
                parse_mode='HTML', reply_markup=markup
            )

    def toggle_backup(self):
        """Liga/desliga backup automático e reinicia o scheduler."""
        from App.Components.Backup import Backup
        new_val = toggle_backup_enabled()
        Backup.restart(self.bot)
        label = 'ativado ✅' if new_val else 'desativado ❌'
        if self.call:
            self.bot.answer_callback_query(
                self.call.id, f'Backup automático {label}', show_alert=True
            )
        self.backup_settings()

    def set_interval(self, horas: str):
        """Define intervalo de backup em horas e reinicia o scheduler."""
        from App.Components.Backup import Backup
        try:
            h = int(horas)
        except (ValueError, TypeError):
            h = 24
        set_backup_interval(h)
        Backup.restart(self.bot)
        if self.call:
            self.bot.answer_callback_query(
                self.call.id, f'Intervalo definido para {h}h', show_alert=True
            )
        self.backup_settings()

    def custom_interval(self):
        """Pede intervalo personalizado de backup ao admin."""
        from telebot.types import Message as TGMessage
        msg = self.bot.send_message(
            self.userid,
            '✏️ Digite o intervalo em horas (número inteiro, mín. 1):'
        )

        def _receber(tmsg: TGMessage):
            if not tmsg.text or not tmsg.text.strip().isdigit():
                self.bot.send_message(self.userid, '❌ Valor inválido. Operação cancelada.')
                return
            from App.Components.Backup import Backup
            h = max(1, int(tmsg.text.strip()))
            set_backup_interval(h)
            Backup.restart(self.bot)
            self.bot.send_message(self.userid, f'✅ Intervalo definido para {h}h')
            self.backup_settings()

        self.bot.register_next_step_handler(msg, _receber)

    def stats(self):
        """Exibe estatísticas gerais do bot."""
        db_u = Usuario(self.bot)
        db_c = Caixinha(self.bot)
        db_p = Pergunta(self.bot)

        total_users      = db_u.count_all()
        total_caixinhas  = db_c.count_all()
        total_concluidas = db_c.count_concluidas()
        total_perguntas  = db_p.count_all()

        text = (
            f"📊 <b>{self.msg.ESTATISTICAS}</b>\n\n"
            f"👤 Usuários: <b>{total_users}</b>\n"
            f"📦 Caixinhas ativas: <b>{total_caixinhas}</b>\n"
            f"✅ Caixinhas concluídas: <b>{total_concluidas}</b>\n"
            f"📝 Perguntas: <b>{total_perguntas}</b>"
        )

        markup = Markup.generate_inline([
            [['⬅️ Voltar', 'PainelAdmin__start']],
        ])

        if self.call:
            self.bot.try_edit_message_text(
                text, chat_id=self.userid, call=self.call,
                parse_mode='HTML', reply_markup=markup
            )
        else:
            self.bot.send_message(
                self.userid, text,
                parse_mode='HTML', reply_markup=markup
            )

    def toggle_engine(self):
        """Alterna IMAGE_ENGINE entre 'pillow' e 'playwright' em runtime."""
        new_engine = toggle_image_engine()
        label = 'pillow (leve) ✅' if new_engine == 'pillow' else 'playwright (pesado) ✅'
        if self.call:
            self.bot.answer_callback_query(
                self.call.id,
                f'Motor de imagens alterado para {label}',
                show_alert=True,
            )
        self.start()

    def backup(self):
        """Executa backup on-demand."""
        from App.Components.Backup import Backup
        bk = Backup(self.bot)
        ok = bk.executar_backup()

        if self.call:
            feedback = self.msg.BACKUP_ENVIADO if ok else self.msg.BACKUP_ERRO
            self.bot.answer_callback_query(self.call.id, feedback, show_alert=True)
        else:
            msg = self.msg.BACKUP_ENVIADO if ok else self.msg.BACKUP_ERRO
            self.bot.send_message(self.userid, msg)
