"""DAO para tabela de caixinhas (question boxes).

Schema:
    caixinhas(id, uid, titulo, id_usuario, concluida, publica, silenciada, total_perguntas, created_at, updated_at, deleted_at)

Exemplo:
    caixinha = Caixinha().criar(userid=123, titulo='Pergunte-me algo')
    minhas = Caixinha().get_by_usuario(123)
"""

from App.Database.DB import DB
import uuid


class Caixinha(DB):
    TABLE = 'caixinhas'

    def __init__(self, bot=None):
        super().__init__(bot)
        self._ensure_columns()

    def _ensure_columns(self):
        """Garante colunas uid, silenciada e publica, e preenche registros antigos."""
        cols = self.get_all_columns(self.TABLE)

        if 'uid' not in cols:
            try:
                self.execute_raw('ALTER TABLE caixinhas ADD COLUMN uid TEXT')
            except Exception:
                pass

        if 'silenciada' not in cols:
            try:
                self.execute_raw('ALTER TABLE caixinhas ADD COLUMN silenciada INTEGER NOT NULL DEFAULT 0')
            except Exception:
                pass

        if 'publica' not in cols:
            try:
                self.execute_raw('ALTER TABLE caixinhas ADD COLUMN publica INTEGER NOT NULL DEFAULT 0')
            except Exception:
                pass

        try:
            self.execute_raw('CREATE UNIQUE INDEX IF NOT EXISTS idx_caixinhas_uid ON caixinhas(uid)')
        except Exception:
            pass

        antigos = self.select(self.TABLE, ['id'], 'uid IS NULL OR uid = ""')
        for row in antigos:
            self.update(self.TABLE, {'uid': str(uuid.uuid4())}, 'id = ?', params=[row['id']])

    def _resolve_identifier_where(self, id_caixinha: str | int):
        """Resolve identificador (id interno numérico ou uid público UUID)."""
        if isinstance(id_caixinha, int):
            return 'id = ?', [id_caixinha]

        raw = str(id_caixinha).strip()
        if raw.isdigit():
            return 'id = ?', [int(raw)]
        return 'uid = ?', [raw]

    def criar(self, id_usuario: int, titulo: str, publica: bool = False) -> str | bool:
        """Cria nova caixinha e retorna o uid público (UUID)."""
        uid = str(uuid.uuid4())
        ok = self.insert(self.TABLE, {
            'uid': uid,
            'titulo': titulo,
            'id_usuario': id_usuario,
            'publica': 1 if publica else 0,
        })
        return uid if ok else False

    def get(self, id_caixinha: str | int):
        """Retorna caixinha por id interno ou uid público."""
        where, params = self._resolve_identifier_where(id_caixinha)
        return self.select_one(self.TABLE, ['*'], where, params=params)

    def get_by_usuario(self, id_usuario: int, concluida: int = 0):
        """Lista caixinhas ativas de um usuário."""
        return self.select(
            self.TABLE, ['*'],
            'id_usuario = ? AND concluida = ?',
            params=[id_usuario, concluida],
            final='ORDER BY created_at DESC'
        )

    def get_concluidas(self, id_usuario: int):
        """Lista caixinhas concluídas de um usuário."""
        return self.get_by_usuario(id_usuario, concluida=1)

    def get_publicas(self):
        """Lista todas as caixinhas públicas e ativas (nuvem)."""
        return self.select(
            self.TABLE, ['*'],
            'publica = 1 AND concluida = 0',
            final='ORDER BY created_at DESC'
        )

    def search_publicas(self, termo: str | None = None, offset: int = 0, limit: int = 25):
        """Busca caixinhas públicas ativas por título."""
        params = []
        where = 'publica = 1 AND concluida = 0'
        if termo:
            where += ' AND titulo LIKE ?'
            params.append(f'%{termo}%')
        final = f'ORDER BY updated_at DESC, created_at DESC LIMIT {int(limit)} OFFSET {int(offset)}'
        return self.select(self.TABLE, ['*'], where, params=params, final=final)

    def concluir(self, id_caixinha: str | int) -> bool:
        """Marca caixinha como concluída."""
        caixinha = self.get(id_caixinha)
        if not caixinha:
            return False
        return self.update(self.TABLE, {'concluida': 1}, 'id = ?', params=[caixinha['id']])

    def reativar(self, id_caixinha: str | int) -> bool:
        """Reativa caixinha concluída."""
        caixinha = self.get(id_caixinha)
        if not caixinha:
            return False
        return self.update(self.TABLE, {'concluida': 0}, 'id = ?', params=[caixinha['id']])

    def incrementar_perguntas(self, id_caixinha: str | int) -> bool:
        """Incrementa contador de perguntas."""
        caixinha = self.get(id_caixinha)
        if not caixinha:
            return False
        novo_total = caixinha['total_perguntas'] + 1
        return self.update(self.TABLE, {'total_perguntas': novo_total}, 'id = ?', params=[caixinha['id']])

    def delete_caixinha(self, id_caixinha: str | int) -> bool:
        """Soft delete."""
        caixinha = self.get(id_caixinha)
        if not caixinha:
            return False
        return self.soft_delete(self.TABLE, 'id = ?', params=[caixinha['id']])

    def is_owner(self, id_caixinha: str | int, id_usuario: int) -> bool:
        """Verifica se o usuário é dono da caixinha."""
        caixinha = self.get(id_caixinha)
        return caixinha and caixinha['id_usuario'] == id_usuario

    def silenciar(self, id_caixinha: str | int) -> bool:
        """Silencia notificações de novas perguntas."""
        caixinha = self.get(id_caixinha)
        if not caixinha:
            return False
        return self.update(self.TABLE, {'silenciada': 1}, 'id = ?', params=[caixinha['id']])

    def ativar_notificacoes(self, id_caixinha: str | int) -> bool:
        """Ativa notificações de novas perguntas."""
        caixinha = self.get(id_caixinha)
        if not caixinha:
            return False
        return self.update(self.TABLE, {'silenciada': 0}, 'id = ?', params=[caixinha['id']])

    def search_by_usuario(self, id_usuario: int, termo: str = '', concluida: int = 0, offset: int = 0, limit: int = 25):
        """Busca caixinhas de um usuário por título."""
        params = [id_usuario, concluida]
        where = 'id_usuario = ? AND concluida = ?'
        if termo:
            where += ' AND titulo LIKE ?'
            params.append(f'%{termo}%')
        final = f'ORDER BY created_at DESC LIMIT {int(limit)} OFFSET {int(offset)}'
        return self.select(self.TABLE, ['*'], where, params=params, final=final)

    def toggle_publica(self, id_caixinha: str | int) -> bool | None:
        """Toggle público/privado. Retorna novo estado (True=pública) ou None se erro."""
        caixinha = self.get(id_caixinha)
        if not caixinha:
            return None
        novo = 0 if caixinha.get('publica', 0) == 1 else 1
        ok = self.update(self.TABLE, {'publica': novo}, 'id = ?', params=[caixinha['id']])
        return bool(novo) if ok else None

    def search_populares(self, termo: str | None = None, offset: int = 0, limit: int = 25):
        """Busca caixinhas públicas ordenadas por mais perguntas."""
        params = []
        where = 'publica = 1 AND concluida = 0'
        if termo:
            where += ' AND titulo LIKE ?'
            params.append(f'%{termo}%')
        final = f'ORDER BY total_perguntas DESC, created_at DESC LIMIT {int(limit)} OFFSET {int(offset)}'
        return self.select(self.TABLE, ['*'], where, params=params, final=final)

    def search_trending(self, termo: str | None = None, offset: int = 0, limit: int = 25):
        """Busca caixinhas públicas em alta (mais perguntas nas últimas 24h).

        Usa subquery para contar perguntas recentes. Fallback: ordena por total_perguntas.
        """
        try:
            sql = """
                SELECT c.*, COALESCE(t.cnt, 0) as trend_count
                FROM caixinhas c
                LEFT JOIN (
                    SELECT id_caixinha, COUNT(*) as cnt
                    FROM perguntas
                    WHERE created_at >= datetime('now', '-24 hours')
                      AND deleted_at IS NULL
                    GROUP BY id_caixinha
                ) t ON c.id = t.id_caixinha
                WHERE c.publica = 1 AND c.concluida = 0 AND c.deleted_at IS NULL
            """
            params = []
            if termo:
                sql += ' AND c.titulo LIKE ?'
                params.append(f'%{termo}%')
            sql += f' ORDER BY trend_count DESC, c.total_perguntas DESC LIMIT {int(limit)} OFFSET {int(offset)}'
            return self.execute_raw(sql, params) or []
        except Exception:
            return self.search_populares(termo, offset, limit)

    def count_all(self) -> int:
        """Conta total de caixinhas ativas."""
        return self.count(self.TABLE, 'concluida = 0')

    def count_concluidas(self) -> int:
        """Conta total de caixinhas concluídas."""
        return self.count(self.TABLE, 'concluida = 1')
