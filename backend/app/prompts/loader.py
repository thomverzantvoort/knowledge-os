from enum import StrEnum
from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


class PromptName(StrEnum):
    DIGEST_SYSTEM = "digest.system"
    DEEP_OUTLINE_SYSTEM = "deep_outline.system"
    DEEP_OUTLINE_CHUNK_SYSTEM = "deep_outline_chunk.system"
    DEEP_OUTLINE_MERGE_SYSTEM = "deep_outline_merge.system"
    DEEP_SUMMARY_SYSTEM = "deep_summary.system"


@lru_cache
def load_prompt(name: PromptName | str) -> str:
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
