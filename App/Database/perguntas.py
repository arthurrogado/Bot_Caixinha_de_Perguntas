"""DAO para tabela de perguntas.

Schema:
    perguntas(id, id_caixinha, id_usuario_autor, pergunta, anonima, respondida, created_at, updated_at, deleted_at)

Exemplo:
    Pergunta().criar(id_caixinha=1, id_usuario=456, texto='Qual sua cor favorita?')
    perguntas = Pergunta().get_by_caixinha(1)
"""

from App.Database.DB import DB


class Pergunta(DB):
    TABLE = 'perguntas'

    def __init__(self, bot=None):
        super().__init__(bot)
        self._ensure_columns()

    def _ensure_columns(self):
        """Garante colunas de resposta/notificação em bases já existentes."""
        cols = self.get_all_columns(self.TABLE)

        if 'resposta' not in cols:
            try:
                self.execute_raw('ALTER TABLE perguntas ADD COLUMN resposta TEXT')
            except Exception:
                pass

        if 'autor_notificado' not in cols:
            try:
                self.execute_raw('ALTER TABLE perguntas ADD COLUMN autor_notificado INTEGER NOT NULL DEFAULT 0')
            except Exception:
                pass

        try:
            self.execute_raw('CREATE INDEX IF NOT EXISTS idx_perguntas_respondida ON perguntas(id_caixinha, respondida)')
        except Exception:
            pass

    def criar(self, id_caixinha: int, id_usuario_autor: int, texto: str, anonima: bool = False) -> int | bool:
        """Cria nova pergunta e retorna o ID."""
        return self.insert(self.TABLE, {
            'id_caixinha': id_caixinha,
            'id_usuario_autor': id_usuario_autor,
            'pergunta': texto,
            'anonima': 1 if anonima else 0,
        })

    def get(self, id_pergunta: int):
        """Retorna pergunta por ID."""
        return self.select_one(self.TABLE, ['*'], 'id = ?', params=[id_pergunta])

    def get_by_caixinha(self, id_caixinha: int):
        """Lista todas as perguntas de uma caixinha."""
        return self.select(
            self.TABLE, ['*'],
            'id_caixinha = ?',
            params=[id_caixinha],
            final='ORDER BY created_at ASC'
        )

    def get_nao_respondidas(self, id_caixinha: int):
        """Lista perguntas ainda não respondidas de uma caixinha."""
        return self.select(
            self.TABLE, ['*'],
            'id_caixinha = ? AND respondida = 0',
            params=[id_caixinha],
            final='ORDER BY created_at ASC'
        )

    def marcar_respondida(self, id_pergunta: int) -> bool:
        """Marca pergunta como respondida."""
        return self.update(self.TABLE, {'respondida': 1}, 'id = ?', params=[id_pergunta])

    def salvar_resposta(self, id_pergunta: int, resposta: str) -> bool:
        """Salva resposta e marca como respondida."""
        return self.update(
            self.TABLE,
            {
                'resposta': resposta,
                'respondida': 1,
            },
            'id = ?',
            params=[id_pergunta],
        )

    def get_respostas_by_caixinha(self, id_caixinha: int, termo: str | None = None):
        """Lista respostas já salvas para uma caixinha."""
        params = [id_caixinha]
        where = 'id_caixinha = ? AND respondida = 1 AND resposta IS NOT NULL AND TRIM(resposta) <> ""'
        if termo:
            where += ' AND (resposta LIKE ? OR pergunta LIKE ?)'
            like = f'%{termo}%'
            params.extend([like, like])
        return self.select(
            self.TABLE,
            ['*'],
            where,
            params=params,
            final='ORDER BY updated_at DESC, id DESC'
        )

    def marcar_autor_notificado(self, id_pergunta: int) -> bool:
        """Marca autor como notificado sobre a resposta da pergunta."""
        return self.update(self.TABLE, {'autor_notificado': 1}, 'id = ?', params=[id_pergunta])

    def contar_por_caixinha(self, id_caixinha: int) -> int:
        """Conta perguntas de uma caixinha."""
        return self.count(self.TABLE, 'id_caixinha = ?', params=[id_caixinha])

    def delete_pergunta(self, id_pergunta: int) -> bool:
        """Soft delete."""
        return self.soft_delete(self.TABLE, 'id = ?', params=[id_pergunta])

    def is_anonima(self, id_pergunta: int) -> bool:
        """Verifica se a pergunta é anônima."""
        p = self.get(id_pergunta)
        return p and p['anonima'] == 1

    def desmarcar_respondida(self, id_pergunta: int) -> bool:
        """Desmarca pergunta como respondida (toggle off)."""
        return self.update(self.TABLE, {'respondida': 0}, 'id = ?', params=[id_pergunta])

    def search_all_by_caixinha(self, id_caixinha: int, termo: str = '', offset: int = 0, limit: int = 50,
                               respondida: int | None = None):
        """Lista perguntas de uma caixinha com busca e filtro de respondida opcional."""
        params = [id_caixinha]
        where = 'id_caixinha = ?'
        if respondida is not None:
            where += ' AND respondida = ?'
            params.append(respondida)
        if termo:
            where += ' AND pergunta LIKE ?'
            params.append(f'%{termo}%')
        final = f'ORDER BY created_at DESC LIMIT {int(limit)} OFFSET {int(offset)}'
        return self.select(self.TABLE, ['*'], where, params=params, final=final)

    def count_all(self) -> int:
        """Conta total de perguntas."""
        return self.count(self.TABLE)
