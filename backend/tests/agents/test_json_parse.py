from app.processing.deep import ChapterSection, OutlineResult
from app.agents.json_parse import parse_model_json


def test_parse_model_json_ignores_trailing_second_json_object():
    content = (
        '{"chapters":['
        '{"start_seconds":0,"title":"A","narrative":"one"},'
        '{"start_seconds":60,"title":"B","narrative":"two"},'
        '{"start_seconds":120,"title":"C","narrative":"three"}'
        ']}\n'
        '{"chapters":[]}'
    )
    result = parse_model_json(content, OutlineResult)
    assert len(result.chapters) == 3
    assert result.chapters[0].title == "A"


def test_parse_model_json_accepts_markdown_fence():
    content = """```json
{"chapters":[
{"start_seconds":0,"title":"A","narrative":"one"},
{"start_seconds":60,"title":"B","narrative":"two"},
{"start_seconds":120,"title":"C","narrative":"three"}
]}
```"""
    result = parse_model_json(content, OutlineResult)
    assert len(result.chapters) == 3
