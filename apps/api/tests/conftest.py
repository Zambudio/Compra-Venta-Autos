import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://motorscope:unit-test@127.0.0.1:5432/motorscope_test"
)
os.environ.setdefault("REDIS_URL", "redis://:unit-test@127.0.0.1:6379/15")
os.environ.setdefault("CORS_ORIGINS", '["http://testserver"]')
os.environ.setdefault("ALLOWED_HOSTS", '["testserver"]')
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")
