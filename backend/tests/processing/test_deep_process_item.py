import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.database.models.content_artifact import ContentArtifact
from app.database.models.content_body import ContentBody
from app.database.models.content_item import ContentItem
from app.database.models.enums import (
    BodyKind,
    BodyStatus,
    ContentKind,
    OutputLanguage,
    ProcessingStatus,
    UserStatus,
)
from app.database.models.user_interest_profile import UserInterestProfile
from app.processing.deep import OutlineResult, SummaryResult, ChapterSection
from app.processing.jobs.deep_process_item import process_deep_item


def _item(*, body_status: BodyStatus = BodyStatus.AVAILABLE) -> ContentItem:
    return ContentItem(
        id=uuid.uuid4(),
        subscription_id=uuid.uuid4(),
        external_id="abc123xyz01",
        kind=ContentKind.VIDEO,
        title="Test video",
        url="https://youtube.com/watch?v=abc123xyz01",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        body_status=body_status,
        user_status=UserStatus.INTERESTED,
        processing_status=ProcessingStatus.INGESTED,
        author="Test Channel",
    )


def _body(item_id: uuid.UUID) -> ContentBody:
    return ContentBody(
        id=uuid.uuid4(),
        content_item_id=item_id,
        body_kind=BodyKind.TRANSCRIPT,
        language_code="en",
        text="hello world",
        snippets=[{"text": "hello world", "start": 0.0, "duration": 1.0}],
        fetched_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _profile() -> UserInterestProfile:
    return UserInterestProfile(
        id=uuid.uuid4(),
        version=1,
        domain_weights={"ai": 1.0},
        context_prose="likes AI",
        channel_notes={},
        output_language=OutputLanguage.EN,
    )


def _outline() -> OutlineResult:
    return OutlineResult(
        chapters=[
            ChapterSection(start_seconds=0, title="Intro", narrative="Starts"),
            ChapterSection(start_seconds=60, title="Middle", narrative="Core"),
            ChapterSection(start_seconds=120, title="End", narrative="Wrap"),
        ]
    )


def _summary() -> SummaryResult:
    return SummaryResult(
        overview="Overview",
        key_takeaways=["one", "two"],
        actionable=[],
        learn_or_prioritize=["learn this"],
        skepticism="none",
        worth_watching="yes",
    )


def test_process_deep_item_skips_when_artifact_complete():
    session = MagicMock()
    item = _item()
    artifact = ContentArtifact(
        id=uuid.uuid4(),
        content_item_id=item.id,
        chapters=[{"start_seconds": 0, "title": "A", "narrative": "a"}],
        summary={"overview": "done"},
        model="gpt-test",
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    session.get.return_value = item

    with patch(
        "app.processing.jobs.deep_process_item.load_artifact",
        return_value=artifact,
    ):
        result = process_deep_item(session, item.id)

    assert result == "skipped"
    session.commit.assert_not_called()


def test_process_deep_item_skips_when_transcript_unavailable():
    session = MagicMock()
    item = _item(body_status=BodyStatus.PENDING)
    session.get.return_value = item

    with (
        patch("app.processing.jobs.deep_process_item.load_artifact", return_value=None),
        patch(
            "app.processing.jobs.deep_process_item.load_transcript_body",
            return_value=None,
        ),
    ):
        result = process_deep_item(session, item.id)

    assert result == "skipped"
    session.commit.assert_not_called()


def test_process_deep_item_runs_outline_and_summary_and_saves():
    session = MagicMock()
    item = _item()
    body = _body(item.id)
    session.get.return_value = item

    with (
        patch("app.processing.jobs.deep_process_item.load_artifact", return_value=None),
        patch(
            "app.processing.jobs.deep_process_item.load_transcript_body",
            return_value=body,
        ),
        patch(
            "app.processing.jobs.deep_process_item.load_interest_profile",
            return_value=_profile(),
        ),
        patch(
            "app.processing.jobs.deep_process_item.run_outline",
            return_value=_outline(),
        ) as run_outline,
        patch(
            "app.processing.jobs.deep_process_item.run_summary",
            return_value=_summary(),
        ) as run_summary,
        patch("app.processing.jobs.deep_process_item.save_artifact") as save_artifact,
        patch(
            "app.processing.jobs.deep_process_item.reset_processing_status"
        ) as reset_status,
    ):
        result = process_deep_item(session, item.id)

    assert result == "processed"
    run_outline.assert_called_once()
    run_summary.assert_called_once()
    save_artifact.assert_called_once()
    reset_status.assert_called_once_with(session, item)
    session.commit.assert_called_once()


def test_process_deep_item_marks_failed_on_llm_error():
    session = MagicMock()
    item = _item()
    body = _body(item.id)
    session.get.side_effect = [item, item]

    with (
        patch("app.processing.jobs.deep_process_item.load_artifact", return_value=None),
        patch(
            "app.processing.jobs.deep_process_item.load_transcript_body",
            return_value=body,
        ),
        patch(
            "app.processing.jobs.deep_process_item.load_interest_profile",
            return_value=_profile(),
        ),
        patch(
            "app.processing.jobs.deep_process_item.run_outline",
            side_effect=RuntimeError("llm down"),
        ),
        patch("app.processing.jobs.deep_process_item.mark_deep_failed") as mark_failed,
    ):
        result = process_deep_item(session, item.id)

    assert result == "failed"
    session.rollback.assert_called_once()
    mark_failed.assert_called_once_with(session, item)
    session.commit.assert_called_once()
