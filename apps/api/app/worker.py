import dramatiq
from dramatiq.brokers.redis import RedisBroker

from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
broker = RedisBroker(url=settings.redis_dsn)  # type: ignore[no-untyped-call]
dramatiq.set_broker(broker)
