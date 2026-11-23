from pathlib import Path

import pytest

from app.tools.demo_media import drawtext_path, find_font


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("C:/Windows/Fonts/arial.ttf", r"'C\:/Windows/Fonts/arial.ttf'"),
        (r"C:\Windows\Fonts\arial.ttf", r"'C\:/Windows/Fonts/arial.ttf'"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'"),
        ("D:/media/it's here/caption.txt", r"'D\:/media/it\'\''s here/caption.txt'"),
    ],
)
def test_drawtext_path_escapes_for_ffmpeg_filtergraph(path: str, expected: str) -> None:
    assert drawtext_path(path) == expected


def test_drawtext_path_accepts_path_objects() -> None:
    assert drawtext_path(Path("fonts") / "a.ttf") == "'fonts/a.ttf'"


def test_find_font_prefers_configured_then_first_existing(tmp_path: Path) -> None:
    font = tmp_path / "font.ttf"
    font.write_bytes(b"")

    assert find_font("custom.ttf", [str(font)]) == "custom.ttf"
    assert find_font(None, [str(tmp_path / "missing.ttf"), str(font)]) == str(font)
    assert find_font("", [str(tmp_path / "missing.ttf")]) is None
