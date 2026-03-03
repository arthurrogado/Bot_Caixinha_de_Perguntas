"""Singleton thread-safe com lazy initialization e double-checked locking.

Padrão genérico para manter UMA instância global de um manager/processor.
Evita importações circulares usando import local.

Uso:
    1. Copie este arquivo e ajuste o import + instanciação para sua classe.
    2. Importe get_instance() onde precisar da instância.

Exemplo (para um UploadManager):
    _instance = None
    _lock = threading.Lock()

    def get_upload_manager():
        global _instance
        if _instance is not None:
            return _instance

        with _lock:
            if _instance is None:
                from App.Components.Upload.UploadManager import UploadManager
                _instance = UploadManager()

        return _instance
"""

from __future__ import annotations

import threading

_instance = None
_lock = threading.Lock()


def get_instance():
    """Retorna a instância global do singleton, criando se necessário.
    
    Ajustar o import e a instanciação conforme a classe desejada.
    """
    global _instance
    if _instance is not None:
        return _instance

    with _lock:
        if _instance is None:
            # === AJUSTAR AQUI ===
            # from App.Components.SeuModulo.SuaClasse import SuaClasse
            # _instance = SuaClasse()
            raise NotImplementedError(
                "Ajuste o import e a instanciação no singleton.py para sua classe."
            )

    return _instance
