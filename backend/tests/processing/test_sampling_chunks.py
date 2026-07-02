from app.processing.sampling import (
    chunk_snippets_for_outline,
    transcript_duration_seconds,
)


def _snippet(start: float, text: str, duration: float = 5.0) -> dict:
    return {"text": text, "start": start, "duration": duration}


def test_transcript_duration_seconds_uses_last_snippet_end():
    snippets = [
        _snippet(0, "a"),
        _snippet(60, "b", duration=30),
    ]
    assert transcript_duration_seconds(snippets) == 90


def test_transcript_duration_seconds_empty():
    assert transcript_duration_seconds(None) == 0.0
    assert transcript_duration_seconds([]) == 0.0


def test_chunk_snippets_single_window_for_short_transcript():
    snippets = [_snippet(index * 10, f"line {index}") for index in range(6)]
    chunks = chunk_snippets_for_outline(
        snippets,
        chunk_seconds=1200,
        overlap_seconds=60,
    )
    assert len(chunks) == 1
    assert chunks[0].start_seconds == 0
    assert chunks[0].end_seconds == 55


def test_chunk_snippets_produces_four_windows_for_72_minute_episode():
    snippets = [_snippet(second, f"line {second}") for second in range(0, 4320, 30)]
    snippets.append(_snippet(4315, "final line", duration=5))
    chunks = chunk_snippets_for_outline(
        snippets,
        chunk_seconds=1200,
        overlap_seconds=60,
    )
    assert len(chunks) == 4
    assert chunks[0].start_seconds == 0
    assert chunks[-1].end_seconds == 4320


def test_chunk_snippets_overlap_includes_boundary_snippet_in_adjacent_chunks():
    snippets = [
        _snippet(1130, "boundary line"),
        _snippet(1190, "overlap line"),
        _snippet(1200, "next window line"),
    ]
    chunks = chunk_snippets_for_outline(
        snippets,
        chunk_seconds=1200,
        overlap_seconds=60,
    )
    assert len(chunks) == 2
    assert "overlap line" in chunks[0].timestamped_text
    assert "overlap line" in chunks[1].timestamped_text
