import os

from fastapi import FastAPI

app = FastAPI()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

app.frontend("/", directory=os.environ.get("SITE_DIR", "/srv/dist"))
