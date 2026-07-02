from app.prompts.loader import PromptName, load_prompt
from app.processing.deep import (
    ChapterSection,
    OutlineResult,
    build_outline_chunk_messages,
    build_outline_messages,
    build_outline_merge_messages,
)
from app.processing.digest import build_digest_messages, InterestProfileInput
from app.database.models.enums import OutputLanguage


def test_all_prompt_files_load():
    for name in PromptName:
        content = load_prompt(name)
        assert content
        assert len(content) > 20


def test_digest_system_message_uses_loaded_prompt():
    messages = build_digest_messages(
        title="Test video",
        description=None,
        transcript_excerpt=None,
        profile=InterestProfileInput(
            domain_keys=["ai"],
            context_prose=None,
            channel_notes=None,
            author=None,
        ),
    )
    assert messages[0]["content"] == load_prompt(PromptName.DIGEST_SYSTEM)


def test_deep_outline_system_message_starts_with_loaded_prompt():
    messages = build_outline_messages(
        title="Test video",
        author=None,
        timestamped_transcript="[00:00] Hello",
        output_language=OutputLanguage.EN,
        content_language_code="en",
    )
    assert messages[0]["content"].startswith(load_prompt(PromptName.DEEP_OUTLINE_SYSTEM))


def test_deep_outline_chunk_system_message_starts_with_loaded_prompt():
    from app.processing.sampling import TranscriptChunk

    messages = build_outline_chunk_messages(
        title="Test video",
        author=None,
        chunk=TranscriptChunk(0, 0, 1200, "[00:00] Hello"),
        output_language=OutputLanguage.EN,
        content_language_code="en",
    )
    assert messages[0]["content"].startswith(
        load_prompt(PromptName.DEEP_OUTLINE_CHUNK_SYSTEM)
    )


def test_deep_outline_merge_system_message_starts_with_loaded_prompt():
    from app.processing.sampling import TranscriptChunk

    chunk = TranscriptChunk(0, 0, 1200, "[00:00] Hello")
    outline = OutlineResult(
        chapters=[
            ChapterSection(start_seconds=0, title="Intro", narrative="Starts"),
            ChapterSection(start_seconds=60, title="Middle", narrative="Core"),
            ChapterSection(start_seconds=120, title="End", narrative="Wrap"),
        ]
    )
    messages = build_outline_merge_messages(
        title="Test video",
        author=None,
        duration_seconds=3600,
        chunk_outlines=[(chunk, outline)],
        output_language=OutputLanguage.EN,
        content_language_code="en",
    )
    assert messages[0]["content"].startswith(
        load_prompt(PromptName.DEEP_OUTLINE_MERGE_SYSTEM)
    )
