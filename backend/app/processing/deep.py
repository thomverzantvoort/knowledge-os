import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

from pydantic import BaseModel, Field

from app.agents.factory import get_agent
from app.config import settings
from app.database.models.enums import OutputLanguage
from app.processing.digest import InterestProfileInput, _format_channel_notes
from app.processing.sampling import (
    TranscriptChunk,
    chunk_snippets_for_outline,
    format_transcript_with_timestamps,
    transcript_duration_seconds,
)
from app.prompts.loader import PromptName, load_prompt

logger = logging.getLogger(__name__)

_COVERAGE_RETRY_INSTRUCTION = (
    "Your previous output did not reach the end of the episode. "
    "Include all topics from the final chunk outlines."
)


def format_output_language_instruction(
    preference: OutputLanguage,
    content_language_code: str | None,
) -> str:
    if preference == OutputLanguage.EN:
        return "Write all text fields in English."
    if preference == OutputLanguage.NL:
        return "Write all text fields in Dutch."
    if content_language_code:
        code = content_language_code.lower().split("-", maxsplit=1)[0]
        if code == "en":
            return "Write all text fields in English (the transcript language)."
        if code == "nl":
            return "Write all text fields in Dutch (the transcript language)."
    return (
        "Write all text fields in the same language as the transcript. "
        "Detect the primary language from the transcript and use it consistently."
    )


def _system_prompt(base: str, language_instruction: str) -> str:
    return base + "\n\n" + language_instruction


class ChapterSection(BaseModel):
    start_seconds: int
    title: str
    narrative: str


class OutlineResult(BaseModel):
    chapters: list[ChapterSection] = Field(min_length=3)


class ActionableItem(BaseModel):
    what: str
    why: str
    effort: Literal["low", "medium", "high"]


class SummaryResult(BaseModel):
    overview: str
    key_takeaways: list[str] = Field(min_length=2)
    actionable: list[ActionableItem]
    learn_or_prioritize: list[str]
    skepticism: str
    worth_watching: str


def build_outline_messages(
    *,
    title: str,
    author: str | None,
    timestamped_transcript: str,
    output_language: OutputLanguage,
    content_language_code: str | None,
) -> list[dict[str, str]]:
    language_instruction = format_output_language_instruction(
        output_language,
        content_language_code,
    )
    return [
        {
            "role": "system",
            "content": _system_prompt(
                load_prompt(PromptName.DEEP_OUTLINE_SYSTEM),
                language_instruction,
            ),
        },
        {
            "role": "user",
            "content": _build_outline_user_prompt(
                title=title,
                author=author,
                timestamped_transcript=timestamped_transcript,
            ),
        },
    ]


def build_outline_chunk_messages(
    *,
    title: str,
    author: str | None,
    chunk: TranscriptChunk,
    output_language: OutputLanguage,
    content_language_code: str | None,
) -> list[dict[str, str]]:
    language_instruction = format_output_language_instruction(
        output_language,
        content_language_code,
    )
    return [
        {
            "role": "system",
            "content": _system_prompt(
                load_prompt(PromptName.DEEP_OUTLINE_CHUNK_SYSTEM),
                language_instruction,
            ),
        },
        {
            "role": "user",
            "content": _build_outline_chunk_user_prompt(
                title=title,
                author=author,
                chunk=chunk,
            ),
        },
    ]


def build_outline_merge_messages(
    *,
    title: str,
    author: str | None,
    duration_seconds: float,
    chunk_outlines: list[tuple[TranscriptChunk, OutlineResult]],
    output_language: OutputLanguage,
    content_language_code: str | None,
    extra_instruction: str | None = None,
) -> list[dict[str, str]]:
    language_instruction = format_output_language_instruction(
        output_language,
        content_language_code,
    )
    system_content = _system_prompt(
        load_prompt(PromptName.DEEP_OUTLINE_MERGE_SYSTEM),
        language_instruction,
    )
    if extra_instruction:
        system_content = system_content + "\n\n" + extra_instruction
    return [
        {"role": "system", "content": system_content},
        {
            "role": "user",
            "content": _build_outline_merge_user_prompt(
                title=title,
                author=author,
                duration_seconds=duration_seconds,
                chunk_outlines=chunk_outlines,
            ),
        },
    ]


def build_summary_messages(
    *,
    title: str,
    author: str | None,
    outline: OutlineResult,
    profile: InterestProfileInput,
    content_language_code: str | None,
) -> list[dict[str, str]]:
    language_instruction = format_output_language_instruction(
        profile.output_language,
        content_language_code,
    )
    return [
        {
            "role": "system",
            "content": _system_prompt(
                load_prompt(PromptName.DEEP_SUMMARY_SYSTEM),
                language_instruction,
            ),
        },
        {
            "role": "user",
            "content": _build_summary_user_prompt(
                title=title,
                author=author,
                outline=outline,
                profile=profile,
            ),
        },
    ]


def run_outline(
    *,
    title: str,
    author: str | None,
    timestamped_transcript: str,
    output_language: OutputLanguage,
    content_language_code: str | None,
) -> OutlineResult:
    messages = build_outline_messages(
        title=title,
        author=author,
        timestamped_transcript=timestamped_transcript,
        output_language=output_language,
        content_language_code=content_language_code,
    )
    return get_agent().complete_json("standard", messages, OutlineResult)


def run_outline_chunk(
    *,
    title: str,
    author: str | None,
    chunk: TranscriptChunk,
    output_language: OutputLanguage,
    content_language_code: str | None,
) -> OutlineResult:
    messages = build_outline_chunk_messages(
        title=title,
        author=author,
        chunk=chunk,
        output_language=output_language,
        content_language_code=content_language_code,
    )
    return get_agent().complete_json("standard", messages, OutlineResult)


def run_outline_merge(
    *,
    title: str,
    author: str | None,
    duration_seconds: float,
    chunk_outlines: list[tuple[TranscriptChunk, OutlineResult]],
    output_language: OutputLanguage,
    content_language_code: str | None,
    extra_instruction: str | None = None,
) -> OutlineResult:
    messages = build_outline_merge_messages(
        title=title,
        author=author,
        duration_seconds=duration_seconds,
        chunk_outlines=chunk_outlines,
        output_language=output_language,
        content_language_code=content_language_code,
        extra_instruction=extra_instruction,
    )
    return get_agent().complete_json("standard", messages, OutlineResult)


def validate_outline_coverage(
    outline: OutlineResult,
    duration_seconds: float,
) -> bool:
    if not outline.chapters or duration_seconds <= 0:
        return False
    last_start = outline.chapters[-1].start_seconds
    return last_start >= duration_seconds * 0.85


def run_outline_pipeline(
    *,
    snippets: list[dict],
    title: str,
    author: str | None,
    output_language: OutputLanguage,
    content_language_code: str | None,
) -> OutlineResult:
    duration_seconds = transcript_duration_seconds(snippets)
    timestamped_transcript = format_transcript_with_timestamps(snippets)
    if not timestamped_transcript:
        raise ValueError("Transcript snippets produced empty text")

    if duration_seconds < settings.deep_outline_chunk_threshold_seconds:
        logger.info(
            "Deep outline pipeline=single duration_seconds=%.0f",
            duration_seconds,
        )
        return run_outline(
            title=title,
            author=author,
            timestamped_transcript=timestamped_transcript,
            output_language=output_language,
            content_language_code=content_language_code,
        )

    chunks = chunk_snippets_for_outline(
        snippets,
        chunk_seconds=settings.deep_outline_chunk_seconds,
        overlap_seconds=settings.deep_outline_chunk_overlap_seconds,
    )
    if len(chunks) <= 1:
        logger.info(
            "Deep outline pipeline=single chunk_count=%d duration_seconds=%.0f",
            len(chunks),
            duration_seconds,
        )
        return run_outline(
            title=title,
            author=author,
            timestamped_transcript=timestamped_transcript,
            output_language=output_language,
            content_language_code=content_language_code,
        )

    logger.info(
        "Deep outline pipeline=chunked chunk_count=%d duration_seconds=%.0f",
        len(chunks),
        duration_seconds,
    )

    def outline_one_chunk(chunk: TranscriptChunk) -> tuple[TranscriptChunk, OutlineResult]:
        result = run_outline_chunk(
            title=title,
            author=author,
            chunk=chunk,
            output_language=output_language,
            content_language_code=content_language_code,
        )
        return chunk, result

    with ThreadPoolExecutor(max_workers=len(chunks)) as pool:
        chunk_outlines = list(pool.map(outline_one_chunk, chunks))

    chunk_outlines.sort(key=lambda pair: pair[0].index)

    outline = run_outline_merge(
        title=title,
        author=author,
        duration_seconds=duration_seconds,
        chunk_outlines=chunk_outlines,
        output_language=output_language,
        content_language_code=content_language_code,
    )
    coverage_ok = validate_outline_coverage(outline, duration_seconds)
    if not coverage_ok:
        logger.warning(
            "Deep outline merge coverage failed; retrying duration_seconds=%.0f last_start=%d",
            duration_seconds,
            outline.chapters[-1].start_seconds if outline.chapters else -1,
        )
        outline = run_outline_merge(
            title=title,
            author=author,
            duration_seconds=duration_seconds,
            chunk_outlines=chunk_outlines,
            output_language=output_language,
            content_language_code=content_language_code,
            extra_instruction=_COVERAGE_RETRY_INSTRUCTION,
        )
        coverage_ok = validate_outline_coverage(outline, duration_seconds)

    logger.info(
        "Deep outline pipeline=chunked coverage_ok=%s chapter_count=%d last_start=%d",
        coverage_ok,
        len(outline.chapters),
        outline.chapters[-1].start_seconds if outline.chapters else -1,
    )
    if not coverage_ok:
        raise ValueError(
            "Merged outline does not cover the end of the episode "
            f"(duration={duration_seconds:.0f}s, "
            f"last_start={outline.chapters[-1].start_seconds}s)"
        )
    return outline


def run_summary(
    *,
    title: str,
    author: str | None,
    outline: OutlineResult,
    profile: InterestProfileInput,
    content_language_code: str | None,
) -> SummaryResult:
    messages = build_summary_messages(
        title=title,
        author=author,
        outline=outline,
        profile=profile,
        content_language_code=content_language_code,
    )
    return get_agent().complete_json("standard", messages, SummaryResult)


def _build_outline_user_prompt(
    *,
    title: str,
    author: str | None,
    timestamped_transcript: str,
) -> str:
    sections = ["## Video", f"Title: {title}"]
    if author:
        sections.append(f"Author/channel: {author}")
    sections.extend(["", "## Transcript (timestamped)", timestamped_transcript])
    return "\n".join(sections)


def _format_window_label(start_seconds: float, end_seconds: float) -> str:
    start_label = _format_timestamp_label(int(start_seconds))
    end_label = _format_timestamp_label(int(end_seconds))
    return f"{start_label}-{end_label}"


def _format_timestamp_label(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _build_outline_chunk_user_prompt(
    *,
    title: str,
    author: str | None,
    chunk: TranscriptChunk,
) -> str:
    start_label = _format_timestamp_label(int(chunk.start_seconds))
    end_label = _format_timestamp_label(int(chunk.end_seconds))
    sections = ["## Video", f"Title: {title}"]
    if author:
        sections.append(f"Author/channel: {author}")
    sections.extend(
        [
            "",
            "## Transcript window",
            f"START: {int(chunk.start_seconds)}s ({start_label})",
            f"END: {int(chunk.end_seconds)}s ({end_label})",
            "",
            "## Transcript (timestamped)",
            chunk.timestamped_text,
        ]
    )
    return "\n".join(sections)


def _build_outline_merge_user_prompt(
    *,
    title: str,
    author: str | None,
    duration_seconds: float,
    chunk_outlines: list[tuple[TranscriptChunk, OutlineResult]],
) -> str:
    duration_label = _format_timestamp_label(int(duration_seconds))
    sections = [
        "## Video",
        f"Title: {title}",
        f"Episode duration: {int(duration_seconds)}s ({duration_label})",
    ]
    if author:
        sections.append(f"Author/channel: {author}")
    sections.extend(["", "## Chunk outlines (in order)"])
    for chunk, outline in chunk_outlines:
        window_label = _format_window_label(chunk.start_seconds, chunk.end_seconds)
        sections.extend(
            [
                "",
                f"### Window {window_label}",
                outline.model_dump_json(indent=2),
            ]
        )
    return "\n".join(sections)


def _build_summary_user_prompt(
    *,
    title: str,
    author: str | None,
    outline: OutlineResult,
    profile: InterestProfileInput,
) -> str:
    sections = [
        "## Interest profile",
        profile.context_prose or "(none)",
        "",
        f"Allowed domain keys: {', '.join(profile.domain_keys)}",
    ]

    channel_context = _format_channel_notes(profile.channel_notes, author)
    if channel_context:
        sections.extend(["", "## Channel context", channel_context])

    sections.extend(
        [
            "",
            "## Video",
            f"Title: {title}",
            "",
            "## Timestamped outline",
            outline.model_dump_json(indent=2),
        ]
    )
    return "\n".join(sections)


def parse_outline_json(raw: str) -> OutlineResult:
    return OutlineResult.model_validate_json(raw)
