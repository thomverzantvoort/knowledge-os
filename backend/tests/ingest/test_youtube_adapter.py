import pytest

from app.ingest.adapters.youtube import _video_id_from_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://example.com/not-youtube", None),
        ("https://www.youtube.com/watch?v=tooshort", None),
    ],
)
def test_video_id_from_url(url: str, expected: str | None):
    assert _video_id_from_url(url) == expected
