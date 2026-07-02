from unittest.mock import patch

import pytest

from app.database.models.enums import OutputLanguage
from app.processing.deep import (
    OutlineResult,
    ChapterSection,
    build_outline_chunk_messages,
    build_outline_merge_messages,
    run_outline_pipeline,
    validate_outline_coverage,
)
from app.processing.sampling import TranscriptChunk, transcript_duration_seconds


def _snippet(start: float, text: str, duration: float = 5.0) -> dict:
    return {"text": text, "start": start, "duration": duration}


def _outline(*starts: int) -> OutlineResult:
    return OutlineResult(
        chapters=[
            ChapterSection(start_seconds=start, title=f"Ch {start}", narrative="text")
            for start in starts
        ]
    )


def test_validate_outline_coverage_passes_near_end():
    outline = _outline(0, 3600, 3800)
    assert validate_outline_coverage(outline, 4320) is True


def test_validate_outline_coverage_fails_when_last_chapter_too_early():
    outline = _outline(0, 1200, 2355)
    assert validate_outline_coverage(outline, 4320) is False


def test_validate_outline_coverage_fails_on_empty():
    outline = OutlineResult.model_construct(chapters=[])
    assert validate_outline_coverage(outline, 100) is False


def test_run_outline_pipeline_uses_single_shot_for_short_transcript():
    snippets = [_snippet(0, "hello"), _snippet(60, "world")]
    with patch("app.processing.deep.run_outline", return_value=_outline(0, 60, 120)) as run_outline:
        result = run_outline_pipeline(
            snippets=snippets,
            title="Short",
            author=None,
            output_language=OutputLanguage.EN,
            content_language_code="en",
        )
    run_outline.assert_called_once()
    assert result.chapters[0].start_seconds == 0


def test_run_outline_pipeline_runs_chunk_and_merge_for_long_transcript():
    snippets = [_snippet(second, f"line {second}") for second in range(0, 3600, 30)]
    chunk_a = TranscriptChunk(0, 0, 1200, "[00:00] a")
    chunk_b = TranscriptChunk(1, 1140, 2400, "[19:00] b")
    chunk_outline_a = _outline(0, 600, 1100)
    chunk_outline_b = _outline(1200, 1800, 2300)
    merged = _outline(0, 600, 1200, 1800, 3200)

    with (
        patch(
            "app.processing.deep.settings.deep_outline_chunk_threshold_seconds",
            1800,
        ),
        patch("app.processing.deep.chunk_snippets_for_outline", return_value=[chunk_a, chunk_b]),
        patch("app.processing.deep.run_outline_chunk", side_effect=[chunk_outline_a, chunk_outline_b]) as run_chunk,
        patch("app.processing.deep.run_outline_merge", return_value=merged) as run_merge,
        patch("app.processing.deep.validate_outline_coverage", return_value=True),
    ):
        result = run_outline_pipeline(
            snippets=snippets,
            title="Long",
            author="Host",
            output_language=OutputLanguage.EN,
            content_language_code="en",
        )

    assert run_chunk.call_count == 2
    run_merge.assert_called_once()
    assert result.chapters[-1].start_seconds == 3200


def test_run_outline_pipeline_retries_merge_when_coverage_fails():
    snippets = [_snippet(second, f"line {second}") for second in range(0, 3600, 30)]
    chunk = TranscriptChunk(0, 0, 1200, "[00:00] a")
    bad_merge = _outline(0, 600, 1200)
    good_merge = _outline(0, 600, 1200, 3200)

    with (
        patch(
            "app.processing.deep.settings.deep_outline_chunk_threshold_seconds",
            1800,
        ),
        patch("app.processing.deep.chunk_snippets_for_outline", return_value=[chunk, chunk]),
        patch("app.processing.deep.run_outline_chunk", return_value=_outline(0, 600, 1100)),
        patch(
            "app.processing.deep.run_outline_merge",
            side_effect=[bad_merge, good_merge],
        ) as run_merge,
        patch(
            "app.processing.deep.validate_outline_coverage",
            side_effect=[False, True],
        ),
    ):
        result = run_outline_pipeline(
            snippets=snippets,
            title="Long",
            author=None,
            output_language=OutputLanguage.EN,
            content_language_code="en",
        )

    assert run_merge.call_count == 2
    assert result.chapters[-1].start_seconds == 3200


def test_run_outline_pipeline_raises_when_coverage_never_passes():
    snippets = [_snippet(second, f"line {second}") for second in range(0, 3600, 30)]
    chunk = TranscriptChunk(0, 0, 1200, "[00:00] a")
    bad_merge = _outline(0, 600, 1200)

    with (
        patch(
            "app.processing.deep.settings.deep_outline_chunk_threshold_seconds",
            1800,
        ),
        patch("app.processing.deep.chunk_snippets_for_outline", return_value=[chunk, chunk]),
        patch("app.processing.deep.run_outline_chunk", return_value=_outline(0, 600, 1100)),
        patch("app.processing.deep.run_outline_merge", return_value=bad_merge),
        patch("app.processing.deep.validate_outline_coverage", return_value=False),
    ):
        with pytest.raises(ValueError, match="does not cover the end"):
            run_outline_pipeline(
                snippets=snippets,
                title="Long",
                author=None,
                output_language=OutputLanguage.EN,
                content_language_code="en",
            )


def test_build_outline_chunk_messages_include_window_bounds():
    chunk = TranscriptChunk(1, 1200, 2400, "[20:00] hello")
    messages = build_outline_chunk_messages(
        title="Episode",
        author="Host",
        chunk=chunk,
        output_language=OutputLanguage.EN,
        content_language_code="en",
    )
    user_content = messages[1]["content"]
    assert "START: 1200s" in user_content
    assert "END: 2400s" in user_content
    assert "[20:00] hello" in user_content


def test_build_outline_merge_messages_include_chunk_json():
    chunk = TranscriptChunk(0, 0, 1200, "[00:00] hello")
    outline = _outline(0, 600, 1100)
    messages = build_outline_merge_messages(
        title="Episode",
        author=None,
        duration_seconds=transcript_duration_seconds(
            [_snippet(0, "a"), _snippet(3600, "b", duration=60)]
        ),
        chunk_outlines=[(chunk, outline)],
        output_language=OutputLanguage.EN,
        content_language_code="en",
    )
    user_content = messages[1]["content"]
    assert "Episode duration:" in user_content
    assert '"start_seconds": 0' in user_content
