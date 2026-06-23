from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, and_, cast, or_, select
from sqlalchemy.orm import Session

from app.database.models.content_item import ContentItem
from app.database.models.enums import BodyStatus
from app.database.models.user_interest_profile import UserInterestProfile


def load_interest_profile(session: Session) -> UserInterestProfile:
    profile = session.scalar(select(UserInterestProfile).limit(1))
    if profile is None:
        raise RuntimeError(
            "No user interest profile found. Run scripts/seed_interest_profile.py first."
        )
    return profile


def items_needing_enrichment(
    session: Session,
    profile: UserInterestProfile,
    window_hours: int | None,
) -> list[ContentItem]:
    stale_version = cast(
        ContentItem.enrichment["profile_version"].astext,
        Integer,
    ) < profile.version
    needs_full_rerun = and_(
        ContentItem.enrichment["input_kind"].astext == "metadata_only",
        ContentItem.body_status == BodyStatus.AVAILABLE,
    )
    query = select(ContentItem).where(
        or_(
            ContentItem.enrichment.is_(None),
            stale_version,
            needs_full_rerun,
        )
    )

    if window_hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        query = query.where(ContentItem.published_at >= cutoff)

    return list(
        session.scalars(query.order_by(ContentItem.published_at.desc())).all()
    )


def save_enrichment(session: Session, item: ContentItem, payload: dict) -> None:
    item.enrichment = payload


def compute_relevance(domain_matches: list[str], domain_weights: dict) -> float:
    weights = [domain_weights[key] for key in domain_matches if key in domain_weights]
    if not weights:
        return 0.0
    return max(weights)
