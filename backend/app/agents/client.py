from typing import Literal, Protocol, TypeVar

from pydantic import BaseModel

ModelTier = Literal["simple", "standard"]

T = TypeVar("T", bound=BaseModel)


class AgentClient(Protocol):
    def complete_json(
        self,
        model: ModelTier,
        messages: list[dict[str, str]],
        response_model: type[T],
    ) -> T: ...
