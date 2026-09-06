"""Broker Dramatiq compartido por API (envío) y worker (consumo).

Se configura de forma perezosa y memoizada para no conectar a Redis salvo que
realmente se encole un trabajo (ADR-0004).
"""

from __future__ import annotations

from functools import lru_cache

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from app.core.config import get_settings


@lru_cache(maxsize=1)
def configure_broker() -> RedisBroker:
    broker = RedisBroker(url=get_settings().redis_dsn)  # type: ignore[no-untyped-call]
    dramatiq.set_broker(broker)
    return broker
