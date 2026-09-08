FROM node:24-slim AS panel

WORKDIR /panel
RUN corepack enable
COPY panel/package.json panel/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY panel ./
RUN pnpm build


FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

RUN useradd --create-home appuser && chown appuser /app

COPY app ./app
COPY schema.sql ./
COPY seed ./seed
COPY --from=panel /panel/dist ./panel/dist

USER appuser

CMD ["sh", "-c", "exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
