"""Rate limiter baseado em token bucket, per-user e per-kind.

Arquitetura:
    RateLimitManager (fachada)
      └── RateLimiter (core)
            └── _TokenBucket (por usuário+tipo)

Configuração padrão (ajustar conforme necessidade):
    - command: 20/min + burst 5
    - callback: 20/min + burst 5
    - inline: 10/min + burst 3

Uso no bot.py:
    tracker = rate_limit.begin(userid, "callback", data_text)
    if not tracker.allowed:
        # responder com mensagem de rate limit
        tracker.log_blocked()
        return
    # ... processar ...
    tracker.finish_ok()
"""

import json
import logging
import os
import random
import threading
import time
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Tuple

from App.Config.config import ADMINS_IDS


# ─── Configurações padrão (override via Config) ─────────────────────
RATE_LIMIT_ENABLED = True
RATE_LIMIT_ADMINS_BYPASS = False
RATE_LIMIT_LOG_ENABLED = True
RATE_LIMIT_LOG_PATH = "logs/rate_limit.jsonl"
RATE_LIMIT_LOG_MAX_BYTES = 2 * 1024 * 1024
RATE_LIMIT_LOG_BACKUP_COUNT = 5
RATE_LIMIT_LOG_SAMPLE_ALLOWED = 0.0
RATE_LIMIT_SLOW_MS = 0

# Limites por tipo (por minuto + burst)
RATE_LIMIT_COMMANDS_PER_MIN = 20
RATE_LIMIT_COMMANDS_BURST = 5
RATE_LIMIT_CALLBACKS_PER_MIN = 20
RATE_LIMIT_CALLBACKS_BURST = 5
RATE_LIMIT_INLINE_PER_MIN = 10
RATE_LIMIT_INLINE_BURST = 3


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_s: float
    remaining_tokens: float


class _TokenBucket:
    """Token bucket individual — um por (userid, kind)."""
    __slots__ = ("capacity", "tokens", "refill_per_s", "last_ts")

    def __init__(self, capacity: float, refill_per_s: float):
        self.capacity = float(max(0.0, capacity))
        self.tokens = float(capacity)
        self.refill_per_s = float(max(0.0, refill_per_s))
        self.last_ts = time.monotonic()

    def _refill(self, now: float) -> None:
        elapsed = max(0.0, now - self.last_ts)
        if elapsed <= 0.0 or self.refill_per_s <= 0.0:
            self.last_ts = now
            return
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_s)
        self.last_ts = now

    def consume(self, cost: float = 1.0) -> RateLimitResult:
        now = time.monotonic()
        self._refill(now)

        cost = float(max(0.0, cost))
        if self.capacity <= 0.0:
            return RateLimitResult(False, retry_after_s=60.0, remaining_tokens=0.0)

        if self.tokens >= cost:
            self.tokens -= cost
            return RateLimitResult(True, retry_after_s=0.0, remaining_tokens=self.tokens)

        needed = cost - self.tokens
        retry = (needed / self.refill_per_s) if self.refill_per_s > 0.0 else 60.0
        return RateLimitResult(False, retry_after_s=max(0.1, retry), remaining_tokens=self.tokens)


class RateLimiter:
    def __init__(
        self,
        enabled: bool = RATE_LIMIT_ENABLED,
        admins_bypass: bool = RATE_LIMIT_ADMINS_BYPASS,
        log_enabled: bool = RATE_LIMIT_LOG_ENABLED,
        log_path: str = RATE_LIMIT_LOG_PATH,
        log_max_bytes: int = RATE_LIMIT_LOG_MAX_BYTES,
        log_backup_count: int = RATE_LIMIT_LOG_BACKUP_COUNT,
        log_sample_allowed: float = RATE_LIMIT_LOG_SAMPLE_ALLOWED,
    ):
        self.enabled = bool(enabled)
        self.admins_bypass = bool(admins_bypass)
        self.log_enabled = bool(log_enabled)
        self.log_path = log_path
        self.log_sample_allowed = float(max(0.0, min(1.0, log_sample_allowed)))

        self._lock = threading.Lock()
        self._buckets: Dict[Tuple[int, str], _TokenBucket] = {}
        self._limits_per_min: Dict[str, float] = {}
        self._bursts: Dict[str, float] = {}

        self._logger = logging.getLogger("bot.rate_limit")
        self._logger.propagate = False
        self._logger.setLevel(logging.INFO)

        if self.log_enabled and not self._logger.handlers:
            self._install_logger_handler(log_path, log_max_bytes, log_backup_count)

    def _install_logger_handler(self, log_path: str, log_max_bytes: int, log_backup_count: int) -> None:
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
        handler = RotatingFileHandler(
            log_path,
            maxBytes=int(max(64 * 1024, log_max_bytes)),
            backupCount=int(max(1, log_backup_count)),
            encoding="utf-8",
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)

    def configure_kind(self, kind: str, per_minute: float, burst: float = 0.0) -> None:
        kind = str(kind).strip().lower()
        per_minute = float(max(0.0, per_minute))
        burst = float(max(0.0, burst))

        with self._lock:
            self._limits_per_min[kind] = per_minute
            self._bursts[kind] = burst
            keys_to_delete = [k for k in self._buckets.keys() if k[1] == kind]
            for key in keys_to_delete:
                del self._buckets[key]

    def _get_bucket(self, userid: int, kind: str) -> _TokenBucket:
        kind = str(kind).strip().lower()
        per_min = float(self._limits_per_min.get(kind, 0.0))
        burst = float(self._bursts.get(kind, 0.0))

        capacity = per_min + burst
        refill_per_s = per_min / 60.0 if per_min > 0 else 0.0

        key = (int(userid), kind)
        bucket = self._buckets.get(key)
        if bucket is None or bucket.capacity != capacity or bucket.refill_per_s != refill_per_s:
            bucket = _TokenBucket(capacity=capacity, refill_per_s=refill_per_s)
            self._buckets[key] = bucket
        return bucket

    def check(self, userid: int, kind: str, cost: float = 1.0) -> RateLimitResult:
        if not self.enabled:
            return RateLimitResult(True, retry_after_s=0.0, remaining_tokens=0.0)

        if self.admins_bypass and int(userid) in ADMINS_IDS:
            return RateLimitResult(True, retry_after_s=0.0, remaining_tokens=0.0)

        kind = str(kind).strip().lower()
        with self._lock:
            bucket = self._get_bucket(userid, kind)
            return bucket.consume(cost=cost)

    def log(self, payload: Dict[str, Any]) -> None:
        if not self.log_enabled:
            return
        try:
            self._logger.info(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        except Exception:
            pass

    def should_sample_allowed(self) -> bool:
        if self.log_sample_allowed <= 0.0:
            return False
        return random.random() < self.log_sample_allowed


# ─── Instância global ───────────────────────────────────────────────

rate_limiter = RateLimiter()

rate_limiter.configure_kind("command", RATE_LIMIT_COMMANDS_PER_MIN, burst=RATE_LIMIT_COMMANDS_BURST)
rate_limiter.configure_kind("callback", RATE_LIMIT_CALLBACKS_PER_MIN, burst=RATE_LIMIT_CALLBACKS_BURST)
rate_limiter.configure_kind("inline", RATE_LIMIT_INLINE_PER_MIN, burst=RATE_LIMIT_INLINE_BURST)


def _utc_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class RequestTracker:
    """Rastreia o ciclo de vida de um request (begin → finish_ok/finish_error)."""

    def __init__(self, *, userid: int, kind: str, action: str, allowed: bool, retry_after_s: float):
        self.userid = int(userid)
        self.kind = str(kind)
        self.action = (action or "")[:180]
        self.allowed = bool(allowed)
        self.retry_after_s = float(retry_after_s or 0.0)
        self._started = time.monotonic()
        self._finished = False

    def duration_ms(self) -> int:
        return int((time.monotonic() - self._started) * 1000)

    def log_blocked(self) -> None:
        rate_limiter.log({
            "ts": _utc_ts(),
            "userid": self.userid,
            "kind": self.kind,
            "action": self.action,
            "blocked": True,
            "retry_after_s": round(self.retry_after_s, 3),
            "duration_ms": self.duration_ms(),
        })

    def finish_ok(self) -> None:
        if self._finished:
            return
        self._finished = True

        duration_ms = self.duration_ms()
        if (RATE_LIMIT_SLOW_MS and duration_ms >= RATE_LIMIT_SLOW_MS) or rate_limiter.should_sample_allowed():
            rate_limiter.log({
                "ts": _utc_ts(),
                "userid": self.userid,
                "kind": self.kind,
                "action": self.action,
                "blocked": False,
                "retry_after_s": 0.0,
                "duration_ms": duration_ms,
            })

    def finish_error(self, error: Exception) -> None:
        if self._finished:
            return
        self._finished = True

        rate_limiter.log({
            "ts": _utc_ts(),
            "userid": self.userid,
            "kind": self.kind,
            "action": self.action,
            "blocked": False,
            "retry_after_s": 0.0,
            "duration_ms": self.duration_ms(),
            "error": str(error)[:500],
        })


class RateLimitManager:
    """Fachada para iniciar tracking de rate limit com uma chamada."""

    def begin(self, userid: int, kind: str, action: str, *, cost: float = 1.0) -> RequestTracker:
        res = rate_limiter.check(userid, kind, cost=cost)
        return RequestTracker(
            userid=userid,
            kind=str(kind).strip().lower(),
            action=action,
            allowed=res.allowed,
            retry_after_s=res.retry_after_s,
        )


rate_limit = RateLimitManager()
