import pytest

from app.services.hls_playlist import MasterPlaylist, PlaylistError, Variant

MASTER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-INDEPENDENT-SEGMENTS
#EXT-X-STREAM-INF:BANDWIDTH=5741520,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2"
1080p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1018960,RESOLUTION=640x360,CODECS="avc1.64001f,mp4a.40.2"
360p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=3280725,RESOLUTION=1280x720,CODECS="avc1.64001f,mp4a.40.2"
720p/index.m3u8
"""


def test_parse_reads_variants_sorted_by_height() -> None:
    playlist = MasterPlaylist.parse(MASTER)

    assert playlist.heights == [360, 720, 1080]
    assert playlist.variants[0] == Variant(640, 360, 1018960, "360p/index.m3u8", "avc1.64001f,mp4a.40.2")


def test_render_round_trip() -> None:
    playlist = MasterPlaylist.parse(MASTER)

    assert MasterPlaylist.parse(playlist.render()) == playlist
    assert 'CODECS="avc1.640028,mp4a.40.2"\n1080p/index.m3u8' in playlist.render()


def test_render_omits_unknown_codecs() -> None:
    rendered = MasterPlaylist.of([Variant(640, 360, 900000, "360p/index.m3u8")]).render()

    assert "#EXT-X-STREAM-INF:BANDWIDTH=900000,RESOLUTION=640x360\n360p/index.m3u8" in rendered
    assert "CODECS" not in rendered


@pytest.mark.parametrize(("max_height", "expected"), [(1080, [360, 720, 1080]), (720, [360, 720]), (240, [])])
def test_limited_to_keeps_variants_up_to_height(max_height: int, expected: list[int]) -> None:
    assert MasterPlaylist.parse(MASTER).limited_to(max_height).heights == expected


def test_with_uri_prefix_rewrites_only_relative_uris() -> None:
    playlist = MasterPlaylist.of(
        [
            Variant(640, 360, 1, "360p/index.m3u8"),
            Variant(1280, 720, 2, "/media/other/720p/index.m3u8"),
            Variant(1920, 1080, 3, "https://cdn.example.com/1080p/index.m3u8"),
        ]
    )

    assert [v.uri for v in playlist.with_uri_prefix("/media/hls/7/").variants] == [
        "/media/hls/7/360p/index.m3u8",
        "/media/other/720p/index.m3u8",
        "https://cdn.example.com/1080p/index.m3u8",
    ]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "#EXT-X-VERSION:3\n",
        "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1,RESOLUTION=640x360\n",
        "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1\n360p/index.m3u8\n",
        "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=x,RESOLUTION=640x360\n360p/index.m3u8\n",
    ],
)
def test_parse_rejects_invalid_playlists(text: str) -> None:
    with pytest.raises(PlaylistError):
        MasterPlaylist.parse(text)
