"""Configurações em tempo de execução com persistência em JSON.

Permite alterar configurações sem reiniciar o bot, sobrescrevendo os defaults
de config.py. Os valores são salvos em App/Config/runtime.json.

Uso:
    from App.Config.runtime_config import get_runtime, set_runtime

    engine = get_runtime('IMAGE_ENGINE')          # lê (fallback para config.py)
    set_runtime('IMAGE_ENGINE', 'playwright')     # persiste no arquivo
"""

import json
import os
import threading

_RUNTIME_FILE = os.path.join(os.path.dirname(__file__), 'runtime.json')
_lock = threading.RLock()
_cache: dict = {}


def _load() -> dict:
    """Carrega runtime.json para o cache (thread-safe)."""
    global _cache
    with _lock:
        if _cache:
            return _cache
        if os.path.exists(_RUNTIME_FILE):
            try:
                with open(_RUNTIME_FILE, 'r', encoding='utf-8') as f:
                    _cache = json.load(f)
            except Exception:
                _cache = {}
        else:
            _cache = {}
        return _cache


def _save(data: dict):
    """Persiste dados no runtime.json (thread-safe)."""
    with _lock:
        try:
            with open(_RUNTIME_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'[RuntimeConfig] Erro ao salvar: {e}')


def get_runtime(key: str, default=None):
    """Retorna valor do runtime override; se não existir, lê do config.py."""
    data = _load()
    if key in data:
        return data[key]
    # Fallback para config.py
    try:
        import importlib
        cfg = importlib.import_module('App.Config.config')
        return getattr(cfg, key, default)
    except Exception:
        return default


def set_runtime(key: str, value):
    """Define e persiste um valor no runtime override."""
    global _cache
    with _lock:
        data = _load()
        data[key] = value
        _cache = data
        _save(data)


def get_image_engine() -> str:
    """Retorna engine de imagem ativa: 'pillow' ou 'playwright'."""
    return get_runtime('IMAGE_ENGINE', 'pillow').lower()


def toggle_image_engine() -> str:
    """Alterna entre 'pillow' e 'playwright'. Retorna o novo valor."""
    current = get_image_engine()
    new_engine = 'playwright' if current == 'pillow' else 'pillow'
    set_runtime('IMAGE_ENGINE', new_engine)
    return new_engine


# ── Backup ──────────────────────────────────────────────────────────

def get_backup_enabled() -> bool:
    """Retorna se o backup automático está ativo."""
    return bool(get_runtime('BACKUP_ENABLED', True))


def toggle_backup_enabled() -> bool:
    """Liga/desliga backup automático. Retorna o novo estado."""
    new_val = not get_backup_enabled()
    set_runtime('BACKUP_ENABLED', new_val)
    return new_val


def get_backup_interval() -> int:
    """Retorna intervalo de backup em horas."""
    return int(get_runtime('BACKUP_INTERVAL_HOURS', 24))


def set_backup_interval(hours: int):
    """Define intervalo de backup em horas e persiste."""
    set_runtime('BACKUP_INTERVAL_HOURS', max(1, int(hours)))
