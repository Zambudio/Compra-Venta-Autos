import app.sources.tasks  # noqa: F401 - registra los actores en el broker
from app.core.broker import configure_broker
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging(get_settings().log_level)
broker = configure_broker()
