from uuid import uuid4

from app.core.errors import NotFoundError, PayloadTooLargeError, UnsupportedMediaTypeError
from app.core.storage import FileStorage
from app.models import Title
from app.schemas.catalog import TitleRead
from app.services.ports import EntityStore

MAX_POSTER_BYTES = 5 * 1024 * 1024
POSTER_EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def detect_image_type(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


class PosterService:
    def __init__(self, titles: EntityStore[Title], storage: FileStorage) -> None:
        self.titles = titles
        self.storage = storage

    def upload(self, title_id: int, data: bytes, content_type: str | None) -> TitleRead:
        title = self.titles.get(title_id)
        if title is None:
            raise NotFoundError("Title not found", code="title_not_found")
        if len(data) > MAX_POSTER_BYTES:
            raise PayloadTooLargeError(f"Poster must be at most {MAX_POSTER_BYTES // (1024 * 1024)} MB")
        detected = detect_image_type(data)
        if detected is None or detected != content_type:
            raise UnsupportedMediaTypeError("Poster must be a JPEG, PNG or WebP image")

        previous = title.poster_url
        title.poster_url = self.storage.save(f"posters/{title.id}-{uuid4().hex}.{POSTER_EXTENSIONS[detected]}", data)
        if previous:
            self.storage.delete(previous)
        return TitleRead.model_validate(title)
