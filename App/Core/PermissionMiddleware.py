from telebot.types import CallbackQuery

from App.custom_bot import CustomBot
from App.Config.config import ADMINS_IDS
from App.Core.Exceptions import SilentException
from App.Core.Messages import get_msg


class PermissionMiddleware:
    """Guard de permissão instanciado automaticamente em cada BaseComponent.
    
    Uso nos componentes:
        self.permission.check_is_admin()       # em handlers de mensagem
        self.permission.check_is_admin_callback("Texto")  # em handlers de callback
    
    Ao falhar, envia mensagem ao usuário e levanta SilentException,
    que interrompe a execução sem exibir erro genérico.
    """

    def __init__(self, bot: CustomBot, userid: int, call: CallbackQuery = None):
        self.userid = userid
        self.call = call
        self.bot = bot
        self.msg = get_msg(userid=userid)
        self.default_text = self.msg.ADMIN_ONLY

    def check_is_admin(self, text: str = None):
        """Verifica se o usuário é admin. Se não for, envia mensagem e levanta SilentException."""
        text = text if text else self.default_text

        if self.userid not in ADMINS_IDS:
            self.bot.send_message(self.userid, text)
            raise SilentException(text)

    def check_is_admin_callback(self, text: str = None):
        """Versão para callbacks — responde via answer_callback_query com show_alert."""
        text = text if text else self.default_text

        if self.userid in ADMINS_IDS:
            return
        else:
            self.bot.answer_callback_query(self.call.id, text, show_alert=True)
            raise SilentException(text)
