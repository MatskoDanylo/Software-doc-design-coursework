import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import settings
from app.services.hls_playlist import MasterPlaylist
from app.services.hls_transcoder import MAX_FPS, HlsTranscoder, TranscodeError, run_ffmpeg

needs_ffmpeg = pytest.mark.skipif(shutil.which(settings.ffmpeg_path) is None, reason="ffmpeg is not installed")


def make_clip(target: Path, size: str, seconds: int = 2, audio: bool = True, rate: int = 25) -> Path:
    args = [
        settings.ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size={size}:rate={rate}:duration={seconds}",
    ]
    if audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-c:a", "aac", "-shortest"]
    subprocess.run([*args, "-c:v", "libx264", "-preset", "ultrafast", str(target)], check=True)
    return target


@pytest.fixture(scope="module")
def clip_720p(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return make_clip(tmp_path_factory.mktemp("src") / "clip.mp4", "1280x720")


@pytest.fixture
def transcoder() -> HlsTranscoder:
    return HlsTranscoder(settings.ffmpeg_path, timeout_sec=120)


@needs_ffmpeg
def test_probe_reads_resolution_fps_and_audio(transcoder: HlsTranscoder, clip_720p: Path) -> None:
    info = transcoder.probe(clip_720p)

    assert (info.width, info.height, info.fps, info.has_audio) == (1280, 720, 25.0, True)


@needs_ffmpeg
def test_transcode_skips_renditions_taller_than_source(
    transcoder: HlsTranscoder, clip_720p: Path, tmp_path: Path
) -> None:
    output = tmp_path / "hls" / "1"
    output.mkdir(parents=True)
    (output / "stale.txt").write_text("old")

    result = transcoder.transcode(clip_720p, output)
    playlist = result.playlist

    assert result.duration_sec == 2
    assert playlist.heights == [360, 720]
    assert [(v.width, v.codecs) for v in playlist.variants] == [
        (640, "avc1.64001f,mp4a.40.2"),
        (1280, "avc1.64001f,mp4a.40.2"),
    ]
    assert MasterPlaylist.parse((output / "master.m3u8").read_text(encoding="utf-8")) == playlist
    assert sorted(p.name for p in output.iterdir()) == ["360p", "720p", "master.m3u8"]
    for variant in playlist.variants:
        index = output / variant.uri
        assert "#EXT-X-PLAYLIST-TYPE:VOD" in index.read_text(encoding="utf-8")
        assert any(index.parent.glob("seg_*.ts"))
        assert variant.bandwidth > 0
    assert list(tmp_path.joinpath("hls").iterdir()) == [output]


@needs_ffmpeg
def test_transcode_without_audio_declares_video_codec_only(transcoder: HlsTranscoder, tmp_path: Path) -> None:
    source = make_clip(tmp_path / "silent.mp4", "640x360", seconds=1, audio=False)

    playlist = transcoder.transcode(source, tmp_path / "out").playlist

    assert [(v.height, v.codecs) for v in playlist.variants] == [(360, "avc1.64001f")]


@needs_ffmpeg
def test_source_below_lowest_rendition_fails(transcoder: HlsTranscoder, tmp_path: Path) -> None:
    source = make_clip(tmp_path / "tiny.mp4", "320x180", seconds=1)

    with pytest.raises(TranscodeError, match="180p"):
        transcoder.transcode(source, tmp_path / "out")
    assert not (tmp_path / "out").exists()


@needs_ffmpeg
def test_non_video_source_fails(transcoder: HlsTranscoder, tmp_path: Path) -> None:
    source = tmp_path / "notes.mp4"
    source.write_text("not a video")

    with pytest.raises(TranscodeError, match="No video stream"):
        transcoder.transcode(source, tmp_path / "out")


def test_missing_ffmpeg_binary_fails_with_clear_message(tmp_path: Path) -> None:
    transcoder = HlsTranscoder(str(tmp_path / "no-ffmpeg"), timeout_sec=5)

    with pytest.raises(TranscodeError, match="ffmpeg not found"):
        transcoder.transcode(tmp_path / "clip.mp4", tmp_path / "out")


@needs_ffmpeg
def test_high_frame_rate_source_is_capped(transcoder: HlsTranscoder, tmp_path: Path) -> None:
    source = make_clip(tmp_path / "fast.mp4", "640x360", seconds=1, audio=False, rate=60)

    transcoder.transcode(source, tmp_path / "out")

    assert transcoder.probe(tmp_path / "out" / "360p" / "index.m3u8").fps == MAX_FPS


def test_ffmpeg_failure_carries_exit_code_and_stderr() -> None:
    script = "import sys; sys.stderr.write('bad input'); sys.exit(3)"

    with pytest.raises(TranscodeError, match="code 3: bad input"):
        run_ffmpeg([sys.executable, "-c", script], timeout_sec=30)
    assert run_ffmpeg([sys.executable, "-c", script], timeout_sec=30, check=False) == "bad input"


def test_hanging_ffmpeg_is_stopped_by_timeout() -> None:
    with pytest.raises(TranscodeError, match="timed out after 1 s"):
        run_ffmpeg([sys.executable, "-c", "import time; time.sleep(30)"], timeout_sec=1)
