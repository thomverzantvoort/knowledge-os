from dataclasses import dataclass

from app.config import settings


def excerpt_transcript(
    snippets: list[dict] | None,
    max_seconds: float | None = None,
) -> str:
    if not snippets:
        return ""
    cutoff = (
        float(settings.enrichment_transcript_max_seconds)
        if max_seconds is None
        else max_seconds
    )
    parts: list[str] = []
    for snippet in snippets:
        if snippet["start"] >= cutoff:
            break
        text = snippet["text"]
        if text:
            parts.append(text)
    return " ".join(parts)


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_transcript_with_timestamps(snippets: list[dict] | None) -> str:
    if not snippets:
        return ""
    lines: list[str] = []
    for snippet in snippets:
        text = snippet.get("text", "").strip()
        if not text:
            continue
        timestamp = _format_timestamp(snippet["start"])
        lines.append(f"[{timestamp}] {text}")
    return "\n".join(lines)


def truncate_description(description: str | None, max_chars: int = 1000) -> str | None:
    if description is None:
        return None
    if len(description) <= max_chars:
        return description
    return description[:max_chars]


@dataclass(frozen=True)
class TranscriptChunk:
    index: int
    start_seconds: float
    end_seconds: float
    timestamped_text: str


def transcript_duration_seconds(snippets: list[dict] | None) -> float:
    if not snippets:
        return 0.0
    last = snippets[-1]
    start = float(last["start"])
    duration = float(last.get("duration") or 0.0)
    return start + duration if duration > 0 else start


def _snippets_in_window(
    snippets: list[dict],
    window_start: float,
    window_end: float,
) -> list[dict]:
    return [
        snippet
        for snippet in snippets
        if window_start <= float(snippet["start"]) < window_end
    ]


def chunk_snippets_for_outline(
    snippets: list[dict],
    *,
    chunk_seconds: int,
    overlap_seconds: int,
) -> list[TranscriptChunk]:
    if not snippets:
        return []

    duration = transcript_duration_seconds(snippets)
    if duration <= 0:
        return []

    chunks: list[TranscriptChunk] = []
    window_start = 0.0
    index = 0
    step = max(chunk_seconds - overlap_seconds, 1)

    while window_start < duration:
        window_end = min(window_start + chunk_seconds, duration)
        window_snippets = _snippets_in_window(snippets, window_start, window_end)
        timestamped_text = format_transcript_with_timestamps(window_snippets)
        if timestamped_text:
            chunks.append(
                TranscriptChunk(
                    index=index,
                    start_seconds=window_start,
                    end_seconds=window_end,
                    timestamped_text=timestamped_text,
                )
            )
            index += 1

        if window_end >= duration:
            break
        window_start += step

    return chunks
