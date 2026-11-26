import shutil
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Protocol

from app.core.errors import PayloadTooLargeError


def resolve_inside(root: Path, relative: PurePosixPath) -> Path | None:
    if relative.is_absolute():
        return None
    target = (root / relative).resolve()
    return target if target.is_relative_to(root) and target != root else None


class FileStorage(Protocol):
    def save(self, relative_path: str, data: bytes) -> str: ...

    def delete(self, url: str) -> None: ...


class LocalMediaStorage:
    def __init__(self, root: Path, url_prefix: str = "/media") -> None:
        self.root = root.resolve()
        self.url_prefix = url_prefix.rstrip("/")

    def save(self, relative_path: str, data: bytes) -> str:
        target = self._resolve(PurePosixPath(relative_path))
        if target is None:
            raise ValueError(f"Path escapes media root: {relative_path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return f"{self.url_prefix}/{target.relative_to(self.root).as_posix()}"

    def delete(self, url: str) -> None:
        prefix = f"{self.url_prefix}/"
        if not url.startswith(prefix):
            return
        target = self._resolve(PurePosixPath(url.removeprefix(prefix)))
        if target is not None and target.is_file():
            target.unlink()

    def _resolve(self, relative: PurePosixPath) -> Path | None:
        return resolve_inside(self.root, relative)


class VideoFileStore(Protocol):
    def save_source(self, asset_id: int, stream: BinaryIO, extension: str, max_bytes: int) -> Path: ...

    def source_path(self, asset_id: int) -> Path | None: ...

    def remove_source(self, asset_id: int) -> None: ...

    def hls_dir(self, asset_id: int) -> Path: ...

    def master_path(self, asset_id: int) -> str: ...


class LocalVideoStore:
    CHUNK_BYTES = 1024 * 1024

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def save_source(self, asset_id: int, stream: BinaryIO, extension: str, max_bytes: int) -> Path:
        self.remove_source(asset_id)
        target = self._uploads(asset_id) / f"source.{extension}"
        target.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with target.open("wb") as out:
            while chunk := stream.read(self.CHUNK_BYTES):
                written += len(chunk)
                if written > max_bytes:
                    break
                out.write(chunk)
        if written > max_bytes:
            self.remove_source(asset_id)
            raise PayloadTooLargeError(f"Video must be at most {max_bytes // (1024 * 1024)} MB")
        return target

    def source_path(self, asset_id: int) -> Path | None:
        return next(self._uploads(asset_id).glob("source.*"), None)

    def remove_source(self, asset_id: int) -> None:
        shutil.rmtree(self._uploads(asset_id), ignore_errors=True)

    def hls_dir(self, asset_id: int) -> Path:
        return self.root / "hls" / str(asset_id)

    def master_path(self, asset_id: int) -> str:
        return f"hls/{asset_id}/master.m3u8"

    def _uploads(self, asset_id: int) -> Path:
        return self.root / "uploads" / str(asset_id)


class LocalManifestSource:
    def __init__(self, root: Path, url_prefix: str = "/media") -> None:
        self.root = root.resolve()
        self.url_prefix = url_prefix.rstrip("/")

    def read(self, relative_path: str) -> str | None:
        target = resolve_inside(self.root, PurePosixPath(relative_path))
        if target is None or not target.is_file():
            return None
        return target.read_text(encoding="utf-8")

    def base_url(self, relative_path: str) -> str:
        return f"{self.url_prefix}/{PurePosixPath(relative_path).parent.as_posix()}"


class LocalAdProvider:
    PREROLL_PATH = "ads/preroll/master.m3u8"

    def __init__(self, root: Path, url_prefix: str = "/media") -> None:
        self.root = root.resolve()
        self.url_prefix = url_prefix.rstrip("/")

    def preroll_url(self) -> str | None:
        if not (self.root / self.PREROLL_PATH).is_file():
            return None
        return f"{self.url_prefix}/{self.PREROLL_PATH}"
