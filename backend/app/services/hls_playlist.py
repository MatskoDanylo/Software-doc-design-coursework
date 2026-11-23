import re
from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import Self

_ATTRIBUTE = re.compile(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)')
_STREAM_INF = "#EXT-X-STREAM-INF:"


class PlaylistError(ValueError):
    pass


@dataclass(frozen=True)
class Variant:
    width: int
    height: int
    bandwidth: int
    uri: str
    codecs: str | None = None

    def render(self) -> str:
        attributes = [f"BANDWIDTH={self.bandwidth}", f"RESOLUTION={self.width}x{self.height}"]
        if self.codecs:
            attributes.append(f'CODECS="{self.codecs}"')
        return f"{_STREAM_INF}{','.join(attributes)}\n{self.uri}"


@dataclass(frozen=True)
class MasterPlaylist:
    variants: tuple[Variant, ...]

    @classmethod
    def of(cls, variants: Iterable[Variant]) -> Self:
        return cls(tuple(sorted(variants, key=lambda v: (v.height, v.bandwidth))))

    @classmethod
    def parse(cls, text: str) -> Self:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines or lines[0] != "#EXTM3U":
            raise PlaylistError("Master playlist must start with #EXTM3U")
        variants: list[Variant] = []
        for index, line in enumerate(lines):
            if not line.startswith(_STREAM_INF):
                continue
            uri = next((u for u in lines[index + 1:] if not u.startswith("#")), None)
            if uri is None:
                raise PlaylistError("Variant without URI")
            variants.append(_parse_variant(line.removeprefix(_STREAM_INF), uri))
        return cls.of(variants)

    @property
    def heights(self) -> list[int]:
        return [v.height for v in self.variants]

    def limited_to(self, max_height: int) -> Self:
        return type(self)(tuple(v for v in self.variants if v.height <= max_height))

    def with_uri_prefix(self, prefix: str) -> Self:
        base = prefix.rstrip("/")
        return type(self)(tuple(
            v if _is_absolute(v.uri) else replace(v, uri=f"{base}/{v.uri}") for v in self.variants
        ))

    def render(self) -> str:
        header = ["#EXTM3U", "#EXT-X-VERSION:3", "#EXT-X-INDEPENDENT-SEGMENTS"]
        return "\n".join([*header, *(v.render() for v in self.variants)]) + "\n"


def _parse_variant(raw_attributes: str, uri: str) -> Variant:
    attributes = {key: value.strip('"') for key, value in _ATTRIBUTE.findall(raw_attributes)}
    try:
        width, height = (int(part) for part in attributes["RESOLUTION"].split("x"))
        bandwidth = int(attributes["BANDWIDTH"])
    except (KeyError, ValueError) as exc:
        raise PlaylistError(f"Variant {uri} needs numeric BANDWIDTH and RESOLUTION") from exc
    return Variant(width=width, height=height, bandwidth=bandwidth, uri=uri, codecs=attributes.get("CODECS"))


def _is_absolute(uri: str) -> bool:
    return uri.startswith("/") or "://" in uri
