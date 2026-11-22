from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_error_handlers
from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title="Cinema Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)
app.include_router(api_router)

media_root = Path(settings.media_dir)
media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_root), name="media")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
