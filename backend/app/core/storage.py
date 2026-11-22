from pathlib import Path, PurePosixPath
from typing import Protocol


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
        if relative.is_absolute():
            return None
        target = (self.root / relative).resolve()
        return target if target.is_relative_to(self.root) and target != self.root else None
