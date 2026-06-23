import logging
from uuid import UUID

from sqlalchemy import select

from app.database.models.content_body import ContentBody
from app.database.models.content_item import ContentItem
from app.database.models.enums import BodyKind, BodyStatus
from app.database.session import get_session
from app.processing.digest import (
    InterestProfileInput,
    build_digest_messages,
    run_digest,
)
from app.processing.operations.enrichment import (
    compute_relevance,
    load_interest_profile,
)
from app.processing.sampling import excerpt_transcript

logger = logging.getLogger(__name__)


def _print_messages(messages: list[dict[str, str]]) -> None:
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


def _load_transcript_snippets(session, item_id: UUID) -> list[dict] | None:
    body = session.scalar(
        select(ContentBody).where(
            ContentBody.content_item_id == item_id,
            ContentBody.body_kind == BodyKind.TRANSCRIPT,
        )
    )
    if body is None:
        return None
    return body.snippets


def probe_digest(
    *,
    video_id: str | None,
    content_item_id: UUID | None,
    call_model: bool,
) -> None:
    with get_session() as session:
        profile = load_interest_profile(session)
        item = _load_item(session, video_id=video_id, content_item_id=content_item_id)

        snippets = _load_transcript_snippets(session, item.id)
        excerpt = (
            excerpt_transcript(snippets)
            if item.body_status == BodyStatus.AVAILABLE
            else ""
        )
        input_kind = "full" if excerpt else "metadata_only"

        profile_input = InterestProfileInput(
            domain_keys=list(profile.domain_weights.keys()),
            context_prose=profile.context_prose,
            channel_notes=profile.channel_notes,
            author=item.author,
        )
        messages = build_digest_messages(
            title=item.title,
            description=item.description,
            transcript_excerpt=excerpt or None,
            profile=profile_input,
        )

    print("Item:", item.id)
    print("  external_id:", item.external_id)
    print("  title:", item.title)
    print("  body_status:", item.body_status)
    print("  input_kind:", input_kind)
    print()
    _print_messages(messages)

    if not call_model:
        print("(CALL_MODEL=False, skipping API call)")
        return

    result = run_digest(
        title=item.title,
        description=item.description,
        transcript_excerpt=excerpt or None,
        profile=profile_input,
    )
    domain_matches = [
        key for key in result.domain_matches if key in profile.domain_weights
    ]
    relevance_score = compute_relevance(domain_matches, profile.domain_weights)

    print("=== RESPONSE ===")
    print(result.model_dump_json(indent=2))
    print()
    print("relevance_score:", relevance_score)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # Set one of these (YouTube video id or DB content_items.id UUID)
    VIDEO_ID: str | None = None
    CONTENT_ITEM_ID: UUID | None = "39ee362c-94b2-44dc-b4c9-828aaa0b21ac"

    # Set False to only print the prompt without calling OpenAI
    CALL_MODEL = True

    probe_digest(
        video_id=VIDEO_ID,
        content_item_id=CONTENT_ITEM_ID,
        call_model=CALL_MODEL,
    )
