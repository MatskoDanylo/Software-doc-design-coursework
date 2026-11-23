import argparse
import shutil
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.storage import LocalVideoStore
from app.models import VideoAsset, VideoStatus
from app.repositories.season_repository import EpisodeRepository
from app.repositories.title_repository import TitleRepository
from app.repositories.video_asset_repository import VideoAssetRepository, video_asset_transaction
from app.services.hls_transcoder import RENDITION_720P, HlsTranscoder, TranscodeError, run_ffmpeg
from app.services.video_service import VideoProcessingService, VideoUploadService

FONT_CANDIDATES = (
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
)
AD_CAPTION = "Реклама"
AD_SECONDS = 8
AD_DIR = Path("ads") / "preroll"
DEMO_SOURCE_MAX_BYTES = 1024 * 1024 * 1024


def drawtext_path(path: str | Path) -> str:
    value = str(path).replace("\\", "/").replace("'", "\\'").replace(":", "\\:")
    return "'" + value.replace("'", "'\\''") + "'"


def find_font(configured: str | None = None, candidates: Sequence[str] = FONT_CANDIDATES) -> str | None:
    if configured:
        return configured
    return next((c for c in candidates if Path(c).is_file()), None)


@dataclass(frozen=True)
class DemoTarget:
    kind: str
    owner_id: int
    caption: str


class DemoClipGenerator:
    def __init__(self, ffmpeg_path: str, font_file: str | None, timeout_sec: int) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.font_file = font_file
        self.timeout_sec = timeout_sec

    def generate(self, caption: str, target: Path, duration: int, size: str = "1920x1080") -> Path:
        caption_file = target.with_suffix(".txt")
        caption_file.write_text(caption, encoding="utf-8")
        height = int(size.split("x")[1])
        drawtext = [
            f"textfile={drawtext_path(caption_file)}",
            "expansion=none",
            f"fontsize={height // 12}",
            "fontcolor=white",
            "box=1",
            "boxcolor=black@0.6",
            f"boxborderw={height // 50}",
            "x=(w-text_w)/2",
            "y=h-text_h-h/8",
        ]
        if self.font_file:
            drawtext.insert(0, f"fontfile={drawtext_path(self.font_file)}")
        run_ffmpeg([
            self.ffmpeg_path, "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=25:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
            "-vf", "drawtext=" + ":".join(drawtext),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest",
            str(target),
        ], self.timeout_sec)
        return target


def select_targets(movies: int, episodes: int, force: bool) -> list[DemoTarget]:
    with SessionLocal() as session, session.begin():
        assets = VideoAssetRepository(session)
        targets = [
            DemoTarget("title", t.id, t.name)
            for t in TitleRepository(session).list_movies(movies)
            if force or not _is_ready(assets.get_by_title(t.id))
        ]
        targets += [
            DemoTarget("episode", e.id, f"{e.season.title.name} · S{e.season.number:02d}E{e.number:02d}")
            for e in EpisodeRepository(session).list_first(episodes)
            if force or not _is_ready(assets.get_by_episode(e.id))
        ]
    return targets


def _is_ready(asset: VideoAsset | None) -> bool:
    return asset is not None and asset.status == VideoStatus.READY


def upload_demo_source(target: DemoTarget, clip: Path, store: LocalVideoStore) -> int:
    with SessionLocal() as session, session.begin(), clip.open("rb") as stream:
        uploads = VideoUploadService(
            TitleRepository(session), EpisodeRepository(session), VideoAssetRepository(session),
            store, DEMO_SOURCE_MAX_BYTES,
        )
        upload = uploads.upload_for_title if target.kind == "title" else uploads.upload_for_episode
        return upload(target.owner_id, stream, clip.name).id


def build_ad(generator: DemoClipGenerator, transcoder: HlsTranscoder, media_root: Path, workdir: Path) -> None:
    clip = generator.generate(AD_CAPTION, workdir / "ad.mp4", AD_SECONDS, size="1280x720")
    transcoder.transcode(clip, media_root / AD_DIR, renditions=(RENDITION_720P,))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.demo_media", description="Generate demo HLS videos and a pre-roll ad with ffmpeg."
    )
    parser.add_argument("--titles", type=int, default=5, help="number of movies to give a demo video")
    parser.add_argument("--episodes", type=int, default=3, help="number of episodes to give a demo video")
    parser.add_argument("--duration", type=int, default=40, help="clip length in seconds")
    parser.add_argument("--force", action="store_true", help="regenerate videos that are already ready")
    args = parser.parse_args(argv)

    media_root = Path(settings.media_dir)
    store = LocalVideoStore(media_root)
    transcoder = HlsTranscoder(settings.ffmpeg_path, settings.ffmpeg_timeout_sec)
    processor = VideoProcessingService(video_asset_transaction, transcoder, store)
    generator = DemoClipGenerator(settings.ffmpeg_path, find_font(settings.demo_font_file), settings.ffmpeg_timeout_sec)

    targets = select_targets(args.titles, args.episodes, args.force)
    if not targets and (args.titles or args.episodes):
        print("Nothing to generate: catalog is empty or videos are ready (run `python -m app.seed --demo`, or --force)")

    workdir = Path(tempfile.mkdtemp(prefix="cinema-demo-"))
    failures = 0
    try:
        for target in targets:
            clip = generator.generate(target.caption, workdir / "clip.mp4", args.duration)
            asset_id = upload_demo_source(target, clip, store)
            status = processor.process(asset_id)
            failures += status is not VideoStatus.READY
            print(f"{target.kind} {target.owner_id} '{target.caption}': asset {asset_id} {status}")

        if args.force or not (media_root / AD_DIR / "master.m3u8").is_file():
            build_ad(generator, transcoder, media_root, workdir)
            print(f"Pre-roll ad: /media/{AD_DIR.as_posix()}/master.m3u8")
    except TranscodeError as exc:
        print(f"ffmpeg failed: {exc}")
        return 1
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
