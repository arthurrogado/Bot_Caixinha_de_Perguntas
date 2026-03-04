"""Camada base de acesso a dados com suporte a SQLite e MariaDB.

Fornece CRUD genérico, soft-delete automático e conversão para dict.
Tabelas com coluna `deleted_at` são filtradas automaticamente no select.

O backend é selecionado via App.Config.DB_BACKEND ('sqlite' ou 'mariadb').

Padrão de uso:
    db = DB()
    db.insert('usuarios', {'id': 123, 'nome': 'João'})
    users = db.select('usuarios', ['*'])
    db.close()

    # Ou via context manager:
    with DB() as db:
        db.insert('usuarios', {'id': 123, 'nome': 'João'})
"""

import os
import sqlite3
from datetime import datetime as dt

from App.Config.config import DB_BACKEND, DB_NAME

# MariaDB imports (optional)
try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False


def _get_mariadb_config():
    """Importa configuração do MariaDB sob demanda."""
    from App.Config.secrets import MARIADB_HOST, MARIADB_PORT, MARIADB_USER, MARIADB_PASSWORD, MARIADB_DATABASE
    return {
        'host': MARIADB_HOST,
        'port': MARIADB_PORT,
        'user': MARIADB_USER,
        'password': MARIADB_PASSWORD,
        'database': MARIADB_DATABASE,
    }


class DB:
    """Camada genérica de acesso a dados (SQLite ou MariaDB)."""

    _placeholder = '?' if DB_BACKEND == 'sqlite' else '%s'

    def __init__(self, bot=None):
        self.bot = bot
        self._backend = DB_BACKEND

        if self._backend == 'mariadb':
            if not HAS_MYSQL:
                raise ImportError("mysql-connector-python não instalado. pip install mysql-connector-python")
            cfg = _get_mariadb_config()
            self.conn = mysql.connector.connect(**cfg)
            self.cursor = self.conn.cursor()
        else:
            self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
            self.cursor = self.conn.cursor()

        self._init_schema()

    def _init_schema(self):
        """Inicializa as tabelas se não existirem (SQLite).
        
        Executa cada statement individualmente para tolerar tabelas já existentes
        com schema antigo (migrações de colunas são feitas nos DAOs).
        """
        if self._backend != 'sqlite':
            return
        schema_path = os.path.join(os.path.dirname(__file__), 'architecture.sql')
        if not os.path.exists(schema_path):
            return
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        # Corta a seção MariaDB
        sqlite_sql = sql.split('-- ============================================================\n-- MariaDB VARIANT', 1)[0]
        # Executa cada statement individualmente — tolerante a colunas/índices já existentes
        for statement in sqlite_sql.split(';'):
            stmt = statement.strip()
            if stmt:
                try:
                    self.cursor.execute(stmt)
                    self.conn.commit()
                except Exception:
                    pass

    @property
    def ph(self):
        """Retorna placeholder correto para o backend (? ou %s)."""
        return self._placeholder

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception:
            pass

    def dictify_query(self, cursor, columns: list = None):
        """Converte resultado do cursor em lista de dicts."""
        try:
            if columns:
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(e)
            return []

    def dictify_result(self, cursor, result: list):
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in result]

    def get_all_columns(self, table: str):
        if self._backend == 'mariadb':
            self.cursor.execute(f"SHOW COLUMNS FROM {table}")
            return [column[0] for column in self.cursor.fetchall()]
        else:
            self.cursor.execute(f"PRAGMA table_info({table})")
            return [column[1] for column in self.cursor.fetchall()]

    def has_deleted_at(self, table: str):
        """Verifica se a tabela possui coluna deleted_at (soft delete)."""
        cols = self.get_all_columns(table)
        return 'deleted_at' in cols

    # ─── Generic CRUD ────────────────────────────────────────────────

    def insert(self, table: str, data: dict):
        """Insere um registro. data deve ser um dict {coluna: valor}.

        Retorna lastrowid em caso de sucesso, False em caso de erro.
        """
        try:
            placeholders = ','.join([self.ph for _ in data.values()])
            sql = f'INSERT INTO {table} ({",".join(data.keys())}) VALUES ({placeholders})'
            self.cursor.execute(sql, list(data.values()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"[DB.insert] {e}")
            return False

    def select(self, table: str, columns: list, where: str = None, params: list = None, final: str = None):
        """Seleciona registros com soft-delete automático.

        Args:
            table: Nome da tabela
            columns: Lista de colunas ou ['*']
            where: Cláusula WHERE com placeholders ? (ex: 'id = ?')
            params: Valores para os placeholders
            final: SQL adicional (ORDER BY, LIMIT, etc.)
        """
        column_exists = self.has_deleted_at(table)
        where_clause = self._adapt_placeholders(where) if where else None

        if column_exists:
            sql = f"SELECT {','.join(columns)}"
            sql += f" FROM {table}"
            sql += f" WHERE {where_clause} AND deleted_at IS NULL" if where_clause else " WHERE deleted_at IS NULL"
            sql += f" {final}" if final else ""
        else:
            sql = f"SELECT {','.join(columns)}"
            sql += f" FROM {table}"
            sql += f" WHERE {where_clause}" if where_clause else ""
            sql += f" {final}" if final else ""

        self.cursor.execute(sql, params or [])
        rows = self.cursor.fetchall()
        return [dict(zip([key[0] for key in self.cursor.description], row)) for row in rows]

    def select_one(self, table: str, columns: list, where: str = None, params: list = None, final: str = None):
        """Retorna o primeiro resultado como dict ou None."""
        result = self.select(table, columns, where, params=params, final=final)
        return result[0] if result else None

    def update(self, table: str, data: dict, where: str = None, params: list = None) -> bool:
        """Atualiza registros. data deve ser um dict {coluna: novo_valor}."""
        try:
            set_clause = ','.join([f"{col} = {self.ph}" for col in data.keys()])
            where_clause = self._adapt_placeholders(where) if where else None
            sql = f'UPDATE {table} SET {set_clause}'
            if where_clause:
                sql += f' WHERE {where_clause}'

            values = list(data.values())
            if params:
                values.extend(params)

            self.cursor.execute(sql, values)
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"[DB.update] {e}")
            return False

    def delete(self, table: str, where: str = None, params: list = None):
        """Hard delete."""
        where_clause = self._adapt_placeholders(where) if where else None
        self.cursor.execute(
            f'DELETE FROM {table}' + (f' WHERE {where_clause}' if where_clause else ''),
            params or []
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def soft_delete(self, table: str, where: str = None, params: list = None):
        """Soft delete - marca deleted_at com timestamp atual."""
        now = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        where_clause = self._adapt_placeholders(where) if where else None
        sql = f"UPDATE {table} SET deleted_at = {self.ph}"
        if where_clause:
            sql += f' WHERE {where_clause}'
        all_params = [now] + (params or [])
        self.cursor.execute(sql, all_params)
        self.conn.commit()
        return self.cursor.rowcount > 0

    def count(self, table: str, where: str = None, params: list = None) -> int:
        """Conta registros (respeita soft-delete)."""
        result = self.select(table, ['COUNT(*) as total'], where, params)
        return result[0]['total'] if result else 0

    def _adapt_placeholders(self, sql_fragment: str) -> str:
        """Converte placeholders ? para %s quando backend é MariaDB."""
        if self._backend == 'mariadb' and sql_fragment:
            return sql_fragment.replace('?', '%s')
        return sql_fragment

    def execute_raw(self, sql: str, params: list = None):
        """Executa SQL raw."""
        adapted = self._adapt_placeholders(sql)
        self.cursor.execute(adapted, params or [])
        self.conn.commit()
        if self.cursor.description:
            rows = self.cursor.fetchall()
            return [dict(zip([key[0] for key in self.cursor.description], row)) for row in rows]
        return self.cursor.rowcount