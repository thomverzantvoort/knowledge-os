from openai import OpenAI

from app.agents.client import ModelTier, T
from app.config import settings


class OpenAIAgent:
    def __init__(self, api_key: str) -> None:
        self._client = OpenAI(api_key=api_key)

    def complete_json(
        self,
        model: ModelTier,
        messages: list[dict[str, str]],
        response_model: type[T],
    ) -> T:
        model_name = (
            settings.openai_simple_model if model == "simple" else settings.openai_model
        )
        completion = self._client.chat.completions.parse(
            model=model_name,
            messages=messages,
            response_format=response_model,
        )
        message = completion.choices[0].message
        if message.parsed is not None:
            return message.parsed
        if message.refusal:
            raise ValueError(message.refusal)
        raise ValueError("OpenAI returned no parsed response")
