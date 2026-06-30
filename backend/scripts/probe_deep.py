import logging
from typing import Literal
from uuid import UUID

from sqlalchemy import select

from app.database.models.content_body import ContentBody
from app.database.models.content_item import ContentItem
from app.database.models.enums import BodyKind, BodyStatus, OutputLanguage
from app.database.session import get_session
from app.processing.deep import (
    OutlineResult,
    build_outline_messages,
    build_summary_messages,
    parse_outline_json,
    run_outline,
    run_summary,
)
from app.processing.digest import InterestProfileInput
from app.processing.operations.enrichment import load_interest_profile
from app.processing.sampling import format_transcript_with_timestamps

logger = logging.getLogger(__name__)

ProbeMode = Literal["outline", "summary", "both"]


def _print_messages(label: str, messages: list[dict[str, str]]) -> None:
    print(label)
    for message in messages:
        print(f"=== {message['role'].upper()} ===")
        print(message["content"])
        print()


def _load_item(
    session, *, video_id: str | None, content_item_id: UUID | None
) -> ContentItem:
    if content_item_id is not None:
        item = session.get(ContentItem, content_item_id)
        if item is None:
            raise RuntimeError(f"No content item with id {content_item_id}")
        return item

    if video_id is None:
        raise RuntimeError("Set VIDEO_ID or CONTENT_ITEM_ID at the top of this script")

    item = session.scalar(
        select(ContentItem).where(ContentItem.external_id == video_id)
    )
    if item is None:
        raise RuntimeError(f"No content item with external_id {video_id}")
    return item


def _load_transcript_body(session, item_id: UUID) -> ContentBody:
    body = session.scalar(
        select(ContentBody).where(
            ContentBody.content_item_id == item_id,
            ContentBody.body_kind == BodyKind.TRANSCRIPT,
        )
    )
    if body is None:
        raise RuntimeError(f"No transcript body for content item {item_id}")
    return body


def _require_transcript(item: ContentItem, body: ContentBody) -> str:
    if item.body_status != BodyStatus.AVAILABLE:
        raise RuntimeError(
            f"Transcript not available (body_status={item.body_status.value})"
        )
    if not body.snippets:
        raise RuntimeError("Transcript body has no snippets")
    formatted = format_transcript_with_timestamps(body.snippets)
    if not formatted:
        raise RuntimeError("Transcript snippets produced empty text")
    return formatted


def _load_outline_from_json(raw: str | None) -> OutlineResult:
    if not raw:
        raise RuntimeError(
            "MODE=summary requires OUTLINE_JSON from a prior outline run"
        )
    return parse_outline_json(raw)


def probe_deep(
    *,
    video_id: str | None,
    content_item_id: UUID | None,
    mode: ProbeMode,
    call_model: bool,
    outline_json: str | None,
    output_language: OutputLanguage | None,
) -> None:
    with get_session() as session:
        profile = load_interest_profile(session)
        item = _load_item(session, video_id=video_id, content_item_id=content_item_id)
        body = _load_transcript_body(session, item.id)

        resolved_output_language = (
            output_language if output_language is not None else profile.output_language
        )
        profile_input = InterestProfileInput(
            domain_keys=list(profile.domain_weights.keys()),
            context_prose=profile.context_prose,
            channel_notes=profile.channel_notes,
            author=item.author,
            output_language=resolved_output_language,
        )

        timestamped_transcript = _require_transcript(item, body)
        outline_for_summary = (
            _load_outline_from_json(outline_json) if mode == "summary" else None
        )

    print("Item:", item.id)
    print("  external_id:", item.external_id)
    print("  title:", item.title)
    print("  body_status:", item.body_status.value)
    print("  transcript_language:", body.language_code)
    print("  output_language:", resolved_output_language.value)
    print("  snippet_count:", len(body.snippets or []))
    print("  transcript_chars:", len(timestamped_transcript))
    print("  mode:", mode)
    print()

    outline_result: OutlineResult | None = outline_for_summary

    if mode in ("outline", "both"):
        outline_messages = build_outline_messages(
            title=item.title,
            author=item.author,
            timestamped_transcript=timestamped_transcript,
            output_language=resolved_output_language,
            content_language_code=body.language_code,
        )
        _print_messages("=== OUTLINE PROMPT ===", outline_messages)

        if call_model:
            outline_result = run_outline(
                title=item.title,
                author=item.author,
                timestamped_transcript=timestamped_transcript,
                output_language=resolved_output_language,
                content_language_code=body.language_code,
            )
            print("=== OUTLINE ===")
            print(outline_result.model_dump_json(indent=2))
            print()

    if mode in ("summary", "both"):
        if outline_result is None:
            raise RuntimeError("Summary mode requires an outline result")

        summary_messages = build_summary_messages(
            title=item.title,
            author=item.author,
            outline=outline_result,
            profile=profile_input,
            content_language_code=body.language_code,
        )
        _print_messages("=== SUMMARY PROMPT ===", summary_messages)

        if call_model:
            summary_result = run_summary(
                title=item.title,
                author=item.author,
                outline=outline_result,
                profile=profile_input,
                content_language_code=body.language_code,
            )
            print("=== SUMMARY ===")
            print(summary_result.model_dump_json(indent=2))
            print()

    if not call_model:
        print("(CALL_MODEL=False, skipping API calls)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # Set one of these (YouTube video id or DB content_items.id UUID)
    VIDEO_ID: str | None = None
    CONTENT_ITEM_ID: UUID | None = "73f1977c-7862-45e5-8656-f78cc0abfecf"

    # outline | summary | both
    MODE: ProbeMode = "both"

    # Set False to only print prompts without calling OpenAI
    CALL_MODEL = True

    # For MODE=summary: paste JSON from a prior outline run (chapters object or full OutlineResult)
    OUTLINE_JSON: str | None = None

    # en | nl | content | None (None = use profile setting from DB)
    OUTPUT_LANGUAGE: OutputLanguage | None = None

    probe_deep(
        video_id=VIDEO_ID,
        content_item_id=CONTENT_ITEM_ID,
        mode=MODE,
        call_model=CALL_MODEL,
        outline_json=OUTLINE_JSON,
        output_language=OUTPUT_LANGUAGE,
    )
