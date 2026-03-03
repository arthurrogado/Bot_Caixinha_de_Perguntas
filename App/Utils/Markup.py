"""Utilitários para construção de teclados do Telegram.

DSL para inline/reply keyboards via listas aninhadas:
    Markup.generate_inline([
        [['Botão 1', 'callback_1'], ['Botão 2', 'callback_2']],  # row 1
        [['Link', 'url=https://example.com']],                    # row 2 (URL)
        [['Buscar', 'switch_inline_query_current_chat=o: ']],     # row 3 (inline)
    ])

Detecção automática: se algum elemento contém '=', trata como kwarg
do InlineKeyboardButton (url=, switch_inline_query_current_chat=, etc).
"""

from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    WebAppInfo
)


class Markup():

    @staticmethod
    def generate_inline(buttons: list, sufix: str = '') -> InlineKeyboardMarkup:
        """Gera InlineKeyboardMarkup a partir de lista aninhada.
        
        Formato: [ [row], [row], ... ]
        Cada row: [ [text, action], [text, action], ... ]
        
        Se action contém '=', é parseado como kwarg (ex: 'url=https://...')
        Caso contrário, é usado como callback_data.
        """
        keyboard = InlineKeyboardMarkup()
        for row in buttons:
            row_buttons = []
            for button in row:
                kwargs = {}
                if any('=' in b for b in button):
                    key, value = button[1].split('=', 1)
                    kwargs = {key: value}
                    row_buttons.append(
                        InlineKeyboardButton(text=button[0], **kwargs)
                    )
                else:
                    row_buttons.append(
                        InlineKeyboardButton(text=button[0], callback_data=f'{button[1]}{sufix}')
                    )
            keyboard.row(*row_buttons)
        return keyboard

    @staticmethod
    def generate_keyboard(buttons: list, **kwargs) -> ReplyKeyboardMarkup:
        """Gera ReplyKeyboardMarkup a partir de lista aninhada.
        
        Formato: [ ['Btn1', 'Btn2'], ['Btn3'] ]
        """
        reply_markup = ReplyKeyboardMarkup(**kwargs)
        for line in buttons:
            linha = []
            for button in line:
                linha.append(KeyboardButton(button))
            reply_markup.row(*linha)
        return reply_markup

    @staticmethod
    def clear_markup():
        """Remove ReplyKeyboard."""
        return ReplyKeyboardRemove()

    @staticmethod
    def cancelar_keyboard():
        return Markup.generate_keyboard([['CANCELAR']])

    @staticmethod
    def cancelar_inline():
        return Markup.generate_inline([[['CANCELAR', 'cancelar']]])

    @staticmethod
    def webapp_button(text: str, url: str) -> InlineKeyboardMarkup:
        """Gera botão para abrir WebApp/MiniApp."""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url)))
        return keyboard