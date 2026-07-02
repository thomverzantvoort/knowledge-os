import logging
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.content_item import ContentItem
from app.database.models.enums import ProcessingStatus
from app.processing.deep import run_outline_pipeline, run_summary
from app.processing.digest import InterestProfileInput
from app.processing.operations.artifacts import (
    artifact_is_complete,
    load_artifact,
    load_transcript_body,
    mark_deep_failed,
    reset_processing_status,
    save_artifact,
    transcript_is_available,
)
from app.processing.operations.enrichment import load_interest_profile
from app.processing.sampling import format_transcript_with_timestamps

logger = logging.getLogger(__name__)

DeepProcessResult = Literal["processed", "skipped", "failed"]


def process_pending_deep_items(session: Session) -> dict[str, int]:
    from app.processing.operations.artifacts import items_needing_deep

    counts = {"processed": 0, "failed": 0, "skipped": 0}
    for item in items_needing_deep(session):
        result = process_deep_item(session, item.id)
        counts[result] += 1
    return counts


def process_deep_item(session: Session, item_id: UUID) -> DeepProcessResult:
    item = session.get(ContentItem, item_id)
    if item is None:
        logger.warning("Deep processing skipped: no content item %s", item_id)
        return "skipped"

    artifact = load_artifact(session, item_id)
    if artifact_is_complete(artifact):
        return "skipped"

    if item.processing_status == ProcessingStatus.FAILED:
        reset_processing_status(session, item)

    body = load_transcript_body(session, item_id)
    if not transcript_is_available(item, body):
        logger.info(
            "Deep processing skipped: transcript unavailable for item %s (%s)",
            item.id,
            item.title,
        )
        return "skipped"

    try:
        return _run_deep_for_item(session, item, body)
    except Exception as error:
        session.rollback()
        item = session.get(ContentItem, item_id)
        if item is not None:
            mark_deep_failed(session, item)
            session.commit()
        logger.exception(
            "Deep processing failed for item %s (%s): %s",
            item_id,
            item.title if item else "unknown",
            error,
        )
        return "failed"


def _run_deep_for_item(session: Session, item: ContentItem, body) -> DeepProcessResult:
    profile = load_interest_profile(session)
    profile_input = InterestProfileInput(
        domain_keys=list(profile.domain_weights.keys()),
        context_prose=profile.context_prose,
        channel_notes=profile.channel_notes,
        author=item.author,
        output_language=profile.output_language,
    )
    if not body.snippets or not format_transcript_with_timestamps(body.snippets):
        logger.info(
            "Deep processing skipped: empty transcript for item %s (%s)",
            item.id,
            item.title,
        )
        return "skipped"

    outline = run_outline_pipeline(
        snippets=body.snippets,
        title=item.title,
        author=item.author,
        output_language=profile.output_language,
        content_language_code=body.language_code,
    )
    summary = run_summary(
        title=item.title,
        author=item.author,
        outline=outline,
        profile=profile_input,
        content_language_code=body.language_code,
    )
    generated_at = datetime.now(timezone.utc)
    save_artifact(
        session,
        item.id,
        chapters=[chapter.model_dump() for chapter in outline.chapters],
        summary=summary.model_dump(),
        model=settings.openai_model,
        generated_at=generated_at,
    )
    reset_processing_status(session, item)
    session.commit()
    return "processed"
