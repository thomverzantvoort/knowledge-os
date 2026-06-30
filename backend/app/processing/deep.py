from typing import Literal

from pydantic import BaseModel, Field

from app.agents.factory import get_agent
from app.database.models.enums import OutputLanguage
from app.processing.digest import InterestProfileInput, _format_channel_notes
from app.prompts.loader import PromptName, load_prompt


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
        {"role": "system", "content": _system_prompt(load_prompt(PromptName.DEEP_OUTLINE_SYSTEM), language_instruction)},
        {
            "role": "user",
            "content": _build_outline_user_prompt(
                title=title,
                author=author,
                timestamped_transcript=timestamped_transcript,
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
        {"role": "system", "content": _system_prompt(load_prompt(PromptName.DEEP_SUMMARY_SYSTEM), language_instruction)},
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
