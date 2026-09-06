FROM python:3.14.7-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6 AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app
RUN pip install --no-cache-dir uv==0.10.2
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.14.7-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6 AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN groupadd --system --gid 10001 motorscope \
    && useradd --system --uid 10001 --gid motorscope --home-dir /nonexistent --shell /usr/sbin/nologin motorscope
COPY --from=builder --chown=motorscope:motorscope /app/.venv /app/.venv
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --chown=motorscope:motorscope apps/api/app ./app
COPY --chown=motorscope:motorscope apps/api/alembic ./alembic
COPY --chown=motorscope:motorscope apps/api/alembic.ini apps/api/pyproject.toml ./
# El runtime ejecuta uvicorn/alembic desde /app/.venv; el pip del sistema no se
# usa y arrastra copias vendorizadas (msgpack, setuptools) que dispara Trivy.
RUN rm -rf /usr/local/lib/python3.14/site-packages/pip* \
    /usr/local/lib/python3.14/site-packages/setuptools* \
    /usr/local/lib/python3.14/site-packages/pkg_resources \
    /usr/local/lib/python3.14/site-packages/wheel* \
    /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.14
USER motorscope
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
