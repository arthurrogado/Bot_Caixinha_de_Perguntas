"""DAO para tabela de usuários.

Schema:
    usuarios(id BIGINT PK, nome, username, idioma, fuso_horario, is_admin, created_at, updated_at, deleted_at)

Exemplo:
    user = Usuario().get(12345)
    Usuario().registrar(12345, 'João', 'joao123')
"""

from App.Database.DB import DB


class Usuario(DB):
    TABLE = 'usuarios'

    def __init__(self, bot=None):
        super().__init__(bot)
        self._ensure_fuso_column()

    def _ensure_fuso_column(self):
        """Garante coluna fuso_horario em bases existentes."""
        cols = self.get_all_columns(self.TABLE)
        if 'fuso_horario' not in cols:
            try:
                self.execute_raw("ALTER TABLE usuarios ADD COLUMN fuso_horario TEXT NOT NULL DEFAULT 'America/Sao_Paulo'")
            except Exception:
                pass

    def registrar(self, userid: int, nome: str, username: str = None):
        """Registra novo usuário ou atualiza se já existir."""
        existing = self.get(userid)
        if existing:
            return self.update_user(userid, nome=nome, username=username)
        return self.insert(self.TABLE, {
            'id': userid,
            'nome': nome,
            'username': username,
        })

    def get(self, userid: int):
        return self.select_one(self.TABLE, ['*'], 'id = ?', params=[userid])

    def get_all(self):
        return self.select(self.TABLE, ['*'])

    def get_idioma(self, userid: int) -> str:
        """Retorna idioma do usuário (default: 'pt')."""
        user = self.get(userid)
        return user['idioma'] if user else 'pt'

    def set_idioma(self, userid: int, idioma: str) -> bool:
        return self.update(self.TABLE, {'idioma': idioma}, 'id = ?', params=[userid])

    def get_fuso_horario(self, userid: int) -> str:
        """Retorna fuso horário do usuário (default: 'America/Sao_Paulo')."""
        user = self.get(userid)
        return (user.get('fuso_horario') if user else None) or 'America/Sao_Paulo'

    def set_fuso_horario(self, userid: int, fuso: str) -> bool:
        return self.update(self.TABLE, {'fuso_horario': fuso}, 'id = ?', params=[userid])

    def update_user(self, userid: int, **fields):
        """Atualiza campos do usuário. Ex: update_user(123, nome='Novo')"""
        if not fields:
            return False
        return self.update(self.TABLE, fields, 'id = ?', params=[userid])

    def delete_user(self, userid: int):
        return self.soft_delete(self.TABLE, 'id = ?', params=[userid])

    def is_admin(self, userid: int) -> bool:
        from App.Config.config import ADMINS_IDS
        return userid in ADMINS_IDS

    def check_exists(self, userid: int) -> bool:
        return self.get(userid) is not None

    def count_all(self) -> int:
        """Conta total de usuários ativos."""
        return self.count(self.TABLE)