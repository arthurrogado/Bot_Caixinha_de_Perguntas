from App.custom_bot import CustomBot
from App.Components.BaseComponent import BaseComponent
from App.Utils.Markup import *

class OtherMenu(BaseComponent):

    def __init__(self, bot: CustomBot, userid):
        super().__init__(bot, userid)
        self.bot = bot
        self.userid = userid

        # self.start() # can be omitted because it's called in the parent class (BaseComponent)

    def start(self):
        msg = self.bot.send_message(self.userid, "*OTHER MENU\!*", parse_mode='MarkdownV2', reply_markup=Markup.generate_keyboard([['Hello other!']]))
        self.bot.register_next_step_handler(msg, self.handle)

    def handle(self, callback):
        self.bot.edit_message_from_callback(self.userid, "Hello another!", callback, reply_markup=Markup.generate_inline([
            [['Hello another!', '_hello_another']]
        ]))
        self.bot.register_callback_query_handler(self.handle_another, lambda call: call.from_user.id == self.userid)
        
        # self.bot.clear_step_handler_by_chat_id(self.userid)