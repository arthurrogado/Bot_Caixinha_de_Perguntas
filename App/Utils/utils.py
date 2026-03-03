"""Funções utilitárias genéricas."""

from urllib.parse import quote
from App.Config.config import ADMINS_IDS


def is_admin(userid) -> bool:
    """Verifica se o userid está na lista de admins."""
    return userid in ADMINS_IDS


def dict_to_url_params(params: dict) -> str:
    """Converte dict em query string URL-encoded.
    
    Exemplo: {'name': 'João', 'age': '25'} -> '?name=Jo%C3%A3o&age=25'
    """
    return "?" + '&'.join([f"{quote(str(key))}={quote(str(value))}" for key, value in params.items()])


def get_deep_link(bot) -> str:
    """Retorna base URL para deep links do bot."""
    return f"https://t.me/{bot.get_me().username}?start="
