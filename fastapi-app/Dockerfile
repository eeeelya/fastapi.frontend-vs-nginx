# Build the React app from the repo root's frontend/ (build context = repo root).
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /usr/local/bin/uv

# Use the image's Python, never download another one.
ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY fastapi-app/pyproject.toml fastapi-app/uv.lock fastapi-app/.python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

COPY fastapi-app/main.py .
COPY --from=frontend /frontend/dist /srv/dist

ENV PATH="/app/.venv/bin:$PATH" \
    WORKERS=1

CMD uvicorn main:app --host 0.0.0.0 --port 80 --workers ${WORKERS} --no-access-log --log-level warning
