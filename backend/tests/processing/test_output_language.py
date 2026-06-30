from app.database.models.enums import OutputLanguage
from app.processing.deep import format_output_language_instruction


def test_output_language_fixed_english():
    result = format_output_language_instruction(OutputLanguage.EN, "nl")
    assert result == "Write all text fields in English."


def test_output_language_fixed_dutch():
    result = format_output_language_instruction(OutputLanguage.NL, "en")
    assert result == "Write all text fields in Dutch."


def test_output_language_content_from_transcript_code():
    result = format_output_language_instruction(OutputLanguage.CONTENT, "nl")
    assert "Dutch" in result


def test_output_language_content_without_code():
    result = format_output_language_instruction(OutputLanguage.CONTENT, None)
    assert "same language as the transcript" in result
