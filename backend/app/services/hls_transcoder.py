import re
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.services.hls_playlist import MasterPlaylist, Variant

SEGMENT_SECONDS = 6
MAX_FPS = 30
AUDIO_KBPS = 128
AUDIO_CODEC = "mp4a.40.2"

_RESOLUTION = re.compile(r"\b(\d{2,5})x(\d{2,5})\b")
_FPS = re.compile(r"(\d+(?:\.\d+)?) fps")
_EXTINF = re.compile(r"#EXTINF:([\d.]+)")


@dataclass(frozen=True)
class Rendition:
    height: int
    video_kbps: int
    level: str
    video_codec: str

    @property
    def name(self) -> str:
        return f"{self.height}p"


RENDITION_360P = Rendition(360, 800, "3.1", "avc1.64001f")
RENDITION_720P = Rendition(720, 2800, "3.1", "avc1.64001f")
RENDITION_1080P = Rendition(1080, 5000, "4.0", "avc1.640028")
DEFAULT_RENDITIONS: tuple[Rendition, ...] = (RENDITION_360P, RENDITION_720P, RENDITION_1080P)


@dataclass(frozen=True)
class SourceInfo:
    width: int
    height: int
    fps: float | None
    has_audio: bool


class TranscodeError(Exception):
    pass


class VideoTranscoder(Protocol):
    def transcode(
        self, source: Path, output_dir: Path, renditions: Sequence[Rendition] = DEFAULT_RENDITIONS
    ) -> MasterPlaylist: ...


class HlsTranscoder:
    def __init__(self, ffmpeg_path: str = "ffmpeg", timeout_sec: int = 3600) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.timeout_sec = timeout_sec

    def transcode(
        self, source: Path, output_dir: Path, renditions: Sequence[Rendition] = DEFAULT_RENDITIONS
    ) -> MasterPlaylist:
        info = self.probe(source)
        selected = [r for r in renditions if r.height <= info.height]
        if not selected:
            lowest = min(r.height for r in renditions)
            raise TranscodeError(f"Source is {info.height}p, below the minimum rendition {lowest}p")

        staging = output_dir.with_name(f"{output_dir.name}.tmp-{uuid4().hex}")
        try:
            variants = [self._encode(source, info, rendition, staging) for rendition in selected]
            playlist = MasterPlaylist.of(variants)
            (staging / "master.m3u8").write_text(playlist.render(), encoding="utf-8")
            if output_dir.exists():
                shutil.rmtree(output_dir)
            staging.rename(output_dir)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        return playlist

    def probe(self, source: Path) -> SourceInfo:
        probe_args = [self.ffmpeg_path, "-hide_banner", "-nostdin", "-i", str(source)]
        stderr = run_ffmpeg(probe_args, self.timeout_sec, check=False)
        video = next((line for line in stderr.splitlines() if "Stream #" in line and "Video:" in line), None)
        resolution = _RESOLUTION.search(video) if video else None
        if video is None or resolution is None:
            raise TranscodeError(f"No video stream found in {source.name}")
        fps = _FPS.search(video)
        return SourceInfo(
            width=int(resolution.group(1)),
            height=int(resolution.group(2)),
            fps=float(fps.group(1)) if fps else None,
            has_audio=any("Stream #" in line and "Audio:" in line for line in stderr.splitlines()),
        )

    def _encode(self, source: Path, info: SourceInfo, rendition: Rendition, root: Path) -> Variant:
        target = root / rendition.name
        target.mkdir(parents=True)
        width = round(info.width * rendition.height / info.height / 2) * 2
        filters = [f"scale={width}:{rendition.height}"]
        if info.fps is not None and info.fps > MAX_FPS:
            filters.append(f"fps={MAX_FPS}")
        kbps = rendition.video_kbps
        run_ffmpeg([
            self.ffmpeg_path, "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
            "-i", str(source),
            "-map", "0:v:0", "-map", "0:a:0?",
            "-vf", ",".join(filters),
            "-c:v", "libx264", "-preset", "veryfast", "-profile:v", "high", "-level:v", rendition.level,
            "-pix_fmt", "yuv420p",
            "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{kbps * 2}k",
            "-force_key_frames", f"expr:gte(t,n_forced*{SEGMENT_SECONDS})",
            "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-ac", "2",
            "-f", "hls", "-hls_time", str(SEGMENT_SECONDS), "-hls_playlist_type", "vod",
            "-hls_segment_filename", (target / "seg_%03d.ts").as_posix(),
            (target / "index.m3u8").as_posix(),
        ], self.timeout_sec)
        codecs = f"{rendition.video_codec},{AUDIO_CODEC}" if info.has_audio else rendition.video_codec
        return Variant(
            width=width,
            height=rendition.height,
            bandwidth=_peak_bandwidth(target / "index.m3u8"),
            uri=f"{rendition.name}/index.m3u8",
            codecs=codecs,
        )


def run_ffmpeg(args: list[str], timeout_sec: int, check: bool = True) -> str:
    try:
        completed = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_sec
        )
    except FileNotFoundError as exc:
        raise TranscodeError(f"ffmpeg not found at '{args[0]}'") from exc
    except subprocess.TimeoutExpired as exc:
        raise TranscodeError(f"ffmpeg timed out after {timeout_sec} s") from exc
    if check and completed.returncode != 0:
        raise TranscodeError(f"ffmpeg exited with code {completed.returncode}: {completed.stderr[-500:].strip()}")
    return completed.stderr


def _peak_bandwidth(index: Path) -> int:
    peak, duration = 0, None
    for line in index.read_text(encoding="utf-8").splitlines():
        if match := _EXTINF.match(line):
            duration = float(match.group(1))
        elif line and not line.startswith("#") and duration:
            peak = max(peak, round((index.parent / line).stat().st_size * 8 / duration))
            duration = None
    if peak == 0:
        raise TranscodeError(f"ffmpeg produced no segments in {index.parent.name}")
    return peak
