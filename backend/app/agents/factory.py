from app.agents.client import AgentClient
from app.agents.openai import OpenAIAgent
from app.config import settings


def get_agent() -> AgentClient:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for agent calls. "
            "Set it in backend/.env or the environment."
        )
    return OpenAIAgent(settings.openai_api_key)
