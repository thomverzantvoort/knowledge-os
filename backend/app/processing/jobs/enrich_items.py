import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.content_body import ContentBody
from app.database.models.content_item import ContentItem
from app.database.models.enums import BodyKind, BodyStatus
from app.database.models.user_interest_profile import UserInterestProfile
from app.processing.digest import InterestProfileInput, run_digest
from app.processing.operations.enrichment import (
    compute_relevance,
    items_needing_enrichment,
    load_interest_profile,
    save_enrichment,
)
from app.processing.sampling import excerpt_transcript

logger = logging.getLogger(__name__)


def enrich_pending_items(
    session: Session,
    *,
    window_hours: int | None,
) -> dict[str, int]:
    profile = load_interest_profile(session)
    items = items_needing_enrichment(session, profile, window_hours)

    processed = 0
    failed = 0

    for item in items:
        try:
            payload = _enrich_item(session, item, profile)
            save_enrichment(session, item, payload)
            session.commit()
            processed += 1
        except Exception as error:
            session.rollback()
            failed += 1
            logger.exception(
                "Enrichment failed for item %s (%s): %s",
                item.id,
                item.title,
                error,
            )

    return {"processed": processed, "failed": failed}


def _enrich_item(
    session: Session,
    item: ContentItem,
    profile: UserInterestProfile,
) -> dict:
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

    return {
        "blurb": result.blurb,
        "tags": result.tags,
        "content_type": result.content_type,
        "domain_matches": domain_matches,
        "relevance_score": relevance_score,
        "input_kind": input_kind,
        "profile_version": profile.version,
        "model": settings.openai_simple_model,
        "enriched_at": datetime.now(timezone.utc).isoformat(),
    }


def _load_transcript_snippets(session: Session, item_id) -> list[dict] | None:
    body = session.scalar(
        select(ContentBody).where(
            ContentBody.content_item_id == item_id,
            ContentBody.body_kind == BodyKind.TRANSCRIPT,
        )
    )
    if body is None:
        return None
    return body.snippets
