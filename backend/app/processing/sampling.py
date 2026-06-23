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


def truncate_description(description: str | None, max_chars: int = 1000) -> str | None:
    if description is None:
        return None
    if len(description) <= max_chars:
        return description
    return description[:max_chars]
