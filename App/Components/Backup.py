"""Componente: Backup do banco de dados.

Suporta:
    - SQLite: envia o arquivo .db para o CLOUD_ID
    - MariaDB: gera dump SQL e envia para o CLOUD_ID

Funcionalidades:
    - Backup agendado via timer (configurável)
    - Backup on-demand via PainelAdmin

Uso:
    from App.Components.Backup import Backup
    bk = Backup(bot)
    bk.executar_backup()           # on-demand
    bk.iniciar_agendamento()       # schedule periódico
    bk.parar_agendamento()         # cancela timer
"""

import os
import io
import shutil
import threading
from datetime import datetime


class Backup:
    _timer: threading.Timer | None = None
    _lock = threading.RLock()  # RLock permite re-entrada no mesmo thread (evita deadlock)

    def __init__(self, bot=None):
        self.bot = bot

    def executar_backup(self) -> bool:
        """Executa backup e envia para CLOUD_ID. Retorna True se ok."""
        from App.Config.config import DB_BACKEND, CLOUD_ID

        try:
            if DB_BACKEND == 'sqlite':
                return self._backup_sqlite(CLOUD_ID)
            elif DB_BACKEND == 'mariadb':
                return self._backup_mariadb(CLOUD_ID)
            else:
                print(f'[Backup] Backend desconhecido: {DB_BACKEND}')
                return False
        except Exception as e:
            print(f'[Backup] Erro: {e}')
            return False

    def _backup_sqlite(self, cloud_id: int) -> bool:
        """Copia o .db e envia como documento."""
        from App.Config.config import DB_NAME

        if not os.path.exists(DB_NAME):
            print(f'[Backup] Arquivo {DB_NAME} não encontrado.')
            return False

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_{timestamp}.db'
        backup_path = backup_name

        try:
            shutil.copy2(DB_NAME, backup_path)

            with open(backup_path, 'rb') as f:
                self.bot.send_document(
                    cloud_id, f,
                    caption=f'💾 Backup SQLite — {timestamp}',
                    visible_file_name=backup_name,
                )
            return True
        finally:
            try:
                os.remove(backup_path)
            except Exception:
                pass

    def _backup_mariadb(self, cloud_id: int) -> bool:
        """Gera dump SQL via queries e envia como documento."""
        from App.Config.config import (
            MARIADB_HOST, MARIADB_PORT, MARIADB_USER,
            MARIADB_PASSWORD, MARIADB_DATABASE,
        )

        try:
            import subprocess
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dump_name = f'backup_{timestamp}.sql'

            result = subprocess.run(
                [
                    'mysqldump',
                    f'--host={MARIADB_HOST}',
                    f'--port={MARIADB_PORT}',
                    f'--user={MARIADB_USER}',
                    f'--password={MARIADB_PASSWORD}',
                    MARIADB_DATABASE,
                ],
                capture_output=True, text=True, timeout=120,
            )

            if result.returncode != 0:
                print(f'[Backup] mysqldump erro: {result.stderr}')
                return False

            buf = io.BytesIO(result.stdout.encode('utf-8'))
            buf.name = dump_name

            self.bot.send_document(
                cloud_id, buf,
                caption=f'💾 Backup MariaDB — {timestamp}',
                visible_file_name=dump_name,
            )
            return True

        except FileNotFoundError:
            print('[Backup] mysqldump não encontrado. Instale o MySQL client.')
            return False
        except Exception as e:
            print(f'[Backup] Erro MariaDB: {e}')
            return False

    # ── Agendamento ──────────────────────────────────────────────────

    def iniciar_agendamento(self):
        """Inicia timer de backup periódico."""
        from App.Config.runtime_config import get_backup_enabled, get_backup_interval

        if not get_backup_enabled():
            print('[Backup] Agendamento desativado (BACKUP_ENABLED=False).')
            return

        intervalo_s = get_backup_interval() * 3600

        def _run():
            try:
                self.executar_backup()
            except Exception as e:
                print(f'[Backup] Falha no backup agendado: {e}')
            finally:
                # Re-agendar
                with Backup._lock:
                    Backup._timer = threading.Timer(intervalo_s, _run)
                    Backup._timer.daemon = True
                    Backup._timer.start()

        with Backup._lock:
            self.parar_agendamento()
            Backup._timer = threading.Timer(intervalo_s, _run)
            Backup._timer.daemon = True
            Backup._timer.start()

        print(f'[Backup] Agendamento ativo: a cada {get_backup_interval()}h.')

    @classmethod
    def restart(cls, bot=None):
        """Para e reinicia o agendamento (chamado ao alterar configurações)."""
        cls.parar_agendamento()
        bk = cls(bot)
        bk.iniciar_agendamento()

    @classmethod
    def parar_agendamento(cls):
        """Cancela timer de backup agendado."""
        with cls._lock:
            if cls._timer:
                cls._timer.cancel()
                cls._timer = None
