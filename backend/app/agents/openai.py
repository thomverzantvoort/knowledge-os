import logging

from openai import OpenAI
from pydantic import ValidationError

from app.agents.client import ModelTier, T
from app.agents.json_parse import parse_model_json
from app.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_MAX_ATTEMPTS = 3


class OpenAIAgent:
    def __init__(self, api_key: str) -> None:
        self._client = OpenAI(api_key=api_key)

    def complete_json(
        self,
        model: ModelTier,
        messages: list[dict[str, str]],
        response_model: type[T],
        *,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    ) -> T:
        model_name = (
            settings.openai_simple_model if model == "simple" else settings.openai_model
        )
        last_error: Exception | None = None

        for attempt in range(max_attempts):
            use_create = attempt > 0
            try:
                if use_create:
                    completion = self._client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        response_format=response_model,
                    )
                    message = completion.choices[0].message
                    if message.content:
                        return parse_model_json(message.content, response_model)
                    if message.refusal:
                        raise ValueError(message.refusal)
                    raise ValueError("OpenAI returned empty content")

                completion = self._client.chat.completions.parse(
                    model=model_name,
                    messages=messages,
                    response_format=response_model,
                )
                message = completion.choices[0].message
                if message.parsed is not None:
                    return message.parsed
                if message.content:
                    return parse_model_json(message.content, response_model)
                if message.refusal:
                    raise ValueError(message.refusal)
                raise ValueError("OpenAI returned no parsed response")
            except ValidationError as error:
                last_error = error
                logger.warning(
                    "OpenAI JSON validation failed attempt %d/%d using_%s: %s",
                    attempt + 1,
                    max_attempts,
                    "create" if use_create else "parse",
                    error,
                )

        if last_error is not None:
            raise last_error
        raise ValueError("OpenAI JSON completion failed")
