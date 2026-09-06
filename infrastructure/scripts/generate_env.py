import secrets
from pathlib import Path

pg_pass = secrets.token_hex(24)
redis_pass = secrets.token_hex(24)
owner_pass = "Owner_" + secrets.token_urlsafe(16) + "!"

env_content = f"""ENVIRONMENT=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

POSTGRES_DB=motorscope
POSTGRES_USER=motorscope
POSTGRES_PASSWORD={pg_pass}
DATABASE_URL=postgresql+psycopg://motorscope:{pg_pass}@postgres:5432/motorscope

REDIS_PASSWORD={redis_pass}
REDIS_URL=redis://:{redis_pass}@redis:6379/0

CORS_ORIGINS=["http://localhost:3080","http://192.168.1.3:3080","http://localhost","http://127.0.0.1:3080"]
ALLOWED_HOSTS=["localhost","127.0.0.1","192.168.1.3","api","web","caddy"]
SESSION_COOKIE_NAME=motorscope_session
CSRF_COOKIE_NAME=motorscope_csrf
SESSION_COOKIE_SECURE=false
SESSION_TTL_SECONDS=28800
LOGIN_RATE_LIMIT=10
LOGIN_RATE_WINDOW_SECONDS=900

OWNER_EMAIL=owner@motorscope.local
OWNER_PASSWORD={owner_pass}

NEXT_PUBLIC_API_BASE_URL=/api/v1
CADDY_HTTP_PORT=3080
CADDY_HTTPS_PORT=8443
CADDY_SITE_ADDRESS=:80
"""

target = Path(".env")
if not target.exists():
    target.write_text(env_content, encoding="utf-8")
    print("Created .env successfully")
else:
    print(".env already exists")
