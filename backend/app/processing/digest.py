import json
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from app.agents.factory import get_agent
from app.processing.sampling import truncate_description

ContentType = Literal[
    "tutorial",
    "explainer",
    "opinion",
    "interview",
    "news",
    "demo",
    "other",
]

_SYSTEM_PROMPT = """\
You classify YouTube videos for a personal weekly digest.

Return JSON matching the schema with:
- blurb: 1-2 sentences on what the video is actually about, not a restatement of the title
- tags: 3-7 lowercase topic tags
- content_type: one of tutorial, explainer, opinion, interview, news, demo, other
- domain_matches: only keys from the allowed domain list that genuinely apply to this video
"""


@dataclass
class InterestProfileInput:
    domain_keys: list[str]
    context_prose: str | None
    channel_notes: dict | None
    author: str | None


class DigestResult(BaseModel):
    blurb: str
    tags: list[str] = Field(min_length=3, max_length=7)
    content_type: ContentType
    domain_matches: list[str]


def build_digest_messages(
    *,
    title: str,
    description: str | None,
    transcript_excerpt: str | None,
    profile: InterestProfileInput,
) -> list[dict[str, str]]:
    excerpt = (transcript_excerpt or "").strip()
    metadata_only = not excerpt
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": _build_user_prompt(
                title=title,
                description=truncate_description(description),
                transcript_excerpt=excerpt if not metadata_only else None,
                profile=profile,
                metadata_only=metadata_only,
            ),
        },
    ]


def run_digest(
    *,
    title: str,
    description: str | None,
    transcript_excerpt: str | None,
    profile: InterestProfileInput,
) -> DigestResult:
    messages = build_digest_messages(
        title=title,
        description=description,
        transcript_excerpt=transcript_excerpt,
        profile=profile,
    )
    return get_agent().complete_json("simple", messages, DigestResult)


def _build_user_prompt(
    *,
    title: str,
    description: str | None,
    transcript_excerpt: str | None,
    profile: InterestProfileInput,
    metadata_only: bool,
) -> str:
    sections = [
        "## Interest profile",
        profile.context_prose or "(none)",
        "",
        f"Allowed domain keys: {', '.join(profile.domain_keys)}",
    ]

    channel_context = _format_channel_notes(profile.channel_notes, profile.author)
    if channel_context:
        sections.extend(["", "## Channel context", channel_context])

    sections.extend(["", "## Video", f"Title: {title}"])
    if description:
        sections.append(f"Description: {description}")

    if metadata_only:
        sections.append(
            "Transcript: not available. Classify from title and description only; "
            "confidence is lower."
        )
    else:
        sections.extend(["", "## Transcript excerpt (first ~15 minutes)", transcript_excerpt])

    return "\n".join(sections)


def _format_channel_notes(notes: dict | None, author: str | None) -> str:
    lines: list[str] = []
    if author:
        lines.append(f"Author/channel: {author}")
    if notes:
        boost = notes.get("boost")
        deprioritize = notes.get("deprioritize")
        if boost:
            lines.append(f"Boost: {json.dumps(boost)}")
        if deprioritize:
            lines.append(f"Deprioritize: {json.dumps(deprioritize)}")
    return "\n".join(lines)
