from telebot import TeleBot
from telebot.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from App.Database.caixinhas import Caixinha
from App.Database.perguntas import Pergunta


class Queries:
    """Inline queries do bot.

    Prefixos suportados:
    - ``cx <termo>``: busca caixinhas públicas (mais recentes)
    - ``cxp <termo>``: caixinhas públicas mais perguntadas
    - ``cxt <termo>``: caixinhas públicas em alta (24h)
    - ``mc <termo>``: minhas caixinhas ativas
    - ``mc:c <termo>``: minhas caixinhas concluídas
    - ``p:<uid> <termo>``: perguntas de uma caixinha (somente dono)
    - vazio: lista caixinhas públicas recentes
    """

    def __init__(self, bot: TeleBot, userid: int = None, query: str = None, chat_type: str = None) -> list:
        self.userid = userid
        self.query = (query or '').strip()
        self.bot = bot
        self.chat_type = chat_type
        self.deep_link_base = f"https://t.me/{self.bot.get_me().username}?start="
        self._user_tz = None  # lazy load

    def _get_user_tz(self):
        """Retorna timezone do usuário (lazy, cached)."""
        if self._user_tz is None:
            try:
                from App.Database.users import Usuario
                db = Usuario(self.bot)
                self._user_tz = db.get_fuso_horario(self.userid)
            except Exception:
                self._user_tz = 'America/Sao_Paulo'
        return self._user_tz

    def get_results(self, offset: int, limit: int = 10):
        text = self.query

        # Prefixos mais específicos primeiro
        if text.startswith('mc:c'):
            return self._search_minhas_concluidas(text, offset, limit)

        if text.startswith('mc'):
            return self._search_minhas_caixinhas(text, offset, limit)

        if text.startswith('p:'):
            return self._search_perguntas(text, offset, limit)

        if text.startswith('cxp'):
            return self._search_caixinhas_populares(text[3:].strip(), offset, limit)

        if text.startswith('cxt'):
            return self._search_caixinhas_trending(text[3:].strip(), offset, limit)

        if text.startswith('cx '):
            return self._search_caixinhas(text[3:].strip(), offset, limit)

        if text.startswith('cx') and len(text) <= 3:
            return self._search_caixinhas('', offset, limit)

        if not text:
            return self._search_caixinhas('', offset, limit)

        return self._search_caixinhas(text, offset, limit)

    # ── Caixinhas públicas (mais recentes) ───────────────────────────

    def _search_caixinhas(self, termo: str, offset: int, limit: int):
        db = Caixinha(self.bot)
        items = db.search_publicas(termo=termo, offset=offset, limit=limit)
        return self._format_caixinhas_results(items, 'cx', 'Nenhuma caixinha encontrada')

    # ── Caixinhas públicas (mais perguntadas) ────────────────────────

    def _search_caixinhas_populares(self, termo: str, offset: int, limit: int):
        db = Caixinha(self.bot)
        items = db.search_populares(termo=termo, offset=offset, limit=limit)
        return self._format_caixinhas_results(items, 'cxp', 'Nenhuma caixinha encontrada')

    # ── Caixinhas públicas (em alta 24h) ─────────────────────────────

    def _search_caixinhas_trending(self, termo: str, offset: int, limit: int):
        db = Caixinha(self.bot)
        items = db.search_trending(termo=termo, offset=offset, limit=limit)
        return self._format_caixinhas_results(items, 'cxt', 'Nenhuma caixinha encontrada')

    # ── Formatador comum de caixinhas ────────────────────────────────

    def _format_caixinhas_results(self, items, prefix: str, empty_msg: str):
        if not items:
            return self._resultados_nao_encontrados(empty_msg)

        results = []
        for cx in items:
            uid = cx.get('uid') or str(cx['id'])
            titulo = cx.get('titulo') or 'Sem título'
            total = cx.get('total_perguntas', 0)
            created = cx.get('created_at', '')
            link = self.deep_link_base + f'cx-{uid}'

            message_text = (
                f"📦 <b>{self._safe_html(titulo)}</b>\n"
                f"📅 {self._format_date(created)}\n"
                f"📊 Perguntas: <b>{total}</b>\n\n"
                f"🔗 {link}"
            )

            results.append(
                InlineQueryResultArticle(
                    id=f"{prefix}-{uid}",
                    title=titulo,
                    description=f"📅 {self._format_date(created)} • 📊 {total} perguntas",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode='HTML',
                        disable_web_page_preview=True,
                    ),
                    reply_markup=self._box_public_markup(uid),
                )
            )

        return results

    # ── Minhas caixinhas (ativas) ────────────────────────────────────

    def _search_minhas_caixinhas(self, text: str, offset: int, limit: int):
        termo = text[2:].strip() if len(text) > 2 else ''
        db = Caixinha(self.bot)
        items = db.search_by_usuario(self.userid, termo=termo, concluida=0, offset=offset, limit=limit)

        if not items:
            return self._resultados_nao_encontrados('📭 Nenhuma caixinha ativa')

        results = []
        for cx in items:
            uid = cx.get('uid') or str(cx['id'])
            titulo = cx.get('titulo') or 'Sem título'
            total = cx.get('total_perguntas', 0)
            created = cx.get('created_at', '')

            deep_link = self.deep_link_base + f'GerenciarCaixinha__ver__{uid}'

            message_text = (
                f'<a href="{deep_link}">📦 {self._safe_html(titulo)}</a>'
            )

            results.append(
                InlineQueryResultArticle(
                    id=f"my-{uid}",
                    title=f"📦 {titulo}",
                    description=f"📅 {self._format_date(created)} • 📊 {total} perguntas",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode='HTML',
                        disable_web_page_preview=True,
                    ),
                )
            )

        return results

    # ── Minhas caixinhas (concluídas) ────────────────────────────────

    def _search_minhas_concluidas(self, text: str, offset: int, limit: int):
        termo = text[4:].strip() if len(text) > 4 else ''
        db = Caixinha(self.bot)
        items = db.search_by_usuario(self.userid, termo=termo, concluida=1, offset=offset, limit=limit)

        if not items:
            return self._resultados_nao_encontrados('📭 Nenhuma caixinha concluída')

        results = []
        for cx in items:
            uid = cx.get('uid') or str(cx['id'])
            titulo = cx.get('titulo') or 'Sem título'
            total = cx.get('total_perguntas', 0)
            created = cx.get('created_at', '')

            deep_link = self.deep_link_base + f'GerenciarCaixinha__ver__{uid}'

            message_text = (
                f'<a href="{deep_link}">✅ {self._safe_html(titulo)}</a>'
            )

            results.append(
                InlineQueryResultArticle(
                    id=f"done-{uid}",
                    title=f"✅ {titulo}",
                    description=f"📅 {self._format_date(created)} • 📊 {total} perguntas",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode='HTML',
                        disable_web_page_preview=True,
                    ),
                )
            )

        return results

    # ── Perguntas de uma caixinha ────────────────────────────────────

    def _search_perguntas(self, text: str, offset: int, limit: int):
        payload = text[2:].strip()
        parts = payload.split(' ', 1)
        uid = parts[0].strip() if parts else ''
        termo = parts[1].strip() if len(parts) > 1 else ''

        if not uid:
            return self._resultados_nao_encontrados('Use: p:<id_da_caixinha> termo')

        db_cx = Caixinha(self.bot)
        caixinha = db_cx.get(uid)
        if not caixinha:
            return self._resultados_nao_encontrados('Caixinha não encontrada')

        if caixinha['id_usuario'] != self.userid:
            return self._resultados_nao_encontrados('Só o dono pode ver as perguntas')

        db_pg = Pergunta(self.bot)

        # Separar em não respondidas e respondidas
        nao_resp = db_pg.search_all_by_caixinha(caixinha['id'], termo=termo, offset=offset, limit=limit, respondida=0)
        respondidas = db_pg.search_all_by_caixinha(caixinha['id'], termo=termo, offset=offset, limit=limit, respondida=1)

        results = []

        # Header de seção: não respondidas
        if nao_resp:
            results.append(
                InlineQueryResultArticle(
                    id='header-pending',
                    title=f'⏳ Não respondidas ({len(nao_resp)})',
                    description='Perguntas aguardando resposta',
                    input_message_content=InputTextMessageContent('⏳ Perguntas não respondidas'),
                )
            )
            for pg in nao_resp:
                results.append(self._format_pergunta(pg))

        # Header de seção: respondidas
        if respondidas:
            results.append(
                InlineQueryResultArticle(
                    id='header-answered',
                    title=f'✅ Respondidas ({len(respondidas)})',
                    description='Perguntas já respondidas',
                    input_message_content=InputTextMessageContent('✅ Perguntas respondidas'),
                )
            )
            for pg in respondidas:
                results.append(self._format_pergunta(pg))

        if not results:
            return self._resultados_nao_encontrados('Nenhuma pergunta encontrada')

        return results

    def _format_pergunta(self, pg):
        """Formata uma pergunta como InlineQueryResultArticle."""
        id_pg = pg['id']
        texto_pg = pg.get('pergunta') or ''
        anonima = pg.get('anonima', 0) == 1
        respondida = pg.get('respondida', 0) == 1
        created = pg.get('created_at', '')

        autor_desc = '🙈 Anônimo' if anonima else self._get_user_desc(pg.get('id_usuario_autor'))
        status = '✅' if respondida else '⏳'

        title = f"{status} {texto_pg[:55]}{'…' if len(texto_pg) > 55 else ''}"
        desc = f"{autor_desc} • {self._format_date(created)}"

        deep_link = self.deep_link_base + f'ResponderPergunta__v__{id_pg}'
        message_text = f'<a href="{deep_link}">{status} {self._safe_html(texto_pg[:100])}</a>'

        return InlineQueryResultArticle(
            id=f"pg-{id_pg}",
            title=title,
            description=desc,
            input_message_content=InputTextMessageContent(
                message_text=message_text,
                parse_mode='HTML',
                disable_web_page_preview=True,
            ),
        )

    # ── Markups ──────────────────────────────────────────────────────

    def _box_public_markup(self, uid: str):
        from App.Utils.Markup import Markup

        return Markup.generate_inline([
            [['📩 Abrir caixinha', f'url={self.deep_link_base}cx-{uid}']],
            [['🔎 Pesquisar respostas', f'switch_inline_query_current_chat=p:{uid} ']],
        ])

    # ── Helpers ──────────────────────────────────────────────────────

    def _resultados_nao_encontrados(self, mensagem: str = 'Não encontrado'):
        return [
            InlineQueryResultArticle(
                id='none',
                title=mensagem,
                input_message_content=InputTextMessageContent(mensagem)
            )
        ]

    def _get_user_desc(self, user_id: int | None) -> str:
        if not user_id:
            return 'Autor desconhecido'
        try:
            chat = self.bot.get_chat(user_id)
            nome = chat.first_name + (f" {chat.last_name}" if chat.last_name else '')
            if chat.username:
                return f"{nome} (@{chat.username})"
            return nome
        except Exception:
            return f"Usuário {user_id}"

    def _safe_html(self, text: str) -> str:
        return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _format_date(self, dt_str) -> str:
        if not dt_str:
            return '??'
        try:
            from datetime import datetime, timezone
            from zoneinfo import ZoneInfo
            dt = datetime.fromisoformat(str(dt_str).replace(' ', 'T'))
            # Assume UTC se sem tzinfo (SQLite CURRENT_TIMESTAMP é UTC)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            user_tz = ZoneInfo(self._get_user_tz())
            dt_local = dt.astimezone(user_tz)
            return dt_local.strftime('%d/%m/%Y %H:%M')
        except Exception:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(str(dt_str).replace(' ', 'T'))
                return dt.strftime('%d/%m/%Y %H:%M')
            except Exception:
                return str(dt_str)[:16]
