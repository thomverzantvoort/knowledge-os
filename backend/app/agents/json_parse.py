import json

from pydantic import ValidationError

from app.agents.client import T


def parse_model_json(content: str, response_model: type[T]) -> T:
    stripped = _strip_markdown_fence(content)
    try:
        return response_model.model_validate_json(stripped)
    except ValidationError:
        data, _end = json.JSONDecoder().raw_decode(stripped)
        return response_model.model_validate(data)


def _strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
