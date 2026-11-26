import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from app.api.deps import get_transcoder, get_video_processor, get_video_store
from app.api.errors import register_error_handlers
from app.api.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        interrupted = get_video_processor(get_transcoder(), get_video_store()).fail_interrupted()
    except OperationalError:
        logger.warning("Database unavailable on startup; interrupted video assets were not reset")
    else:
        if interrupted:
            logger.warning("Marked %s interrupted video asset(s) as failed", interrupted)
    yield


app = FastAPI(title="Cinema Platform API", version="0.1.0", lifespan=lifespan)

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
