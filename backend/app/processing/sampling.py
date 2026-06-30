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
