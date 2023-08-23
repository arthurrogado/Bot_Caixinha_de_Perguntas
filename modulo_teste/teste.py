# ./modulo_teste/teste.py

from telebot import TeleBot

class Teste:
    def __init__(self, bot : TeleBot, userid):
        self.bot = bot
        self.userid = userid
        
        self.teste()

    def teste(self):
        msg = self.bot.send_message(self.userid, "nome?")
        self.bot.register_next_step_handler(msg, self.pegarNome)

    def pegarNome(self, msg):
        nome = msg.text
        self.bot.send_message(self.userid, "nome: " + nome)
