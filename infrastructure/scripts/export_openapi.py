import json
import os
from pathlib import Path
import sys

API_DIR = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://motorscope:export-openapi@127.0.0.1:5432/motorscope"
)
os.environ.setdefault("REDIS_URL", "redis://:export-openapi@127.0.0.1:6379/0")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost"]')
os.environ.setdefault("ALLOWED_HOSTS", '["localhost"]')
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")

from app.main import app


def main() -> None:
    target = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
