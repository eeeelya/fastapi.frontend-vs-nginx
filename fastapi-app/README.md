# fastapi-app

FastAPI server for the nginx vs FastAPI benchmark. It serves a static SPA with
`app.frontend()` and has one endpoint: `GET /api/health`.

## Run locally

```bash
uv sync
SITE_DIR=../frontend/dist uv run uvicorn main:app --port 8000
```

`SITE_DIR` is the folder to serve (default `/srv/dist`, the path inside Docker).

## Run in Docker

From the repo root (the image builds `frontend/` itself):

```bash
docker compose up --build fastapi
```

Then open http://localhost:8081.
