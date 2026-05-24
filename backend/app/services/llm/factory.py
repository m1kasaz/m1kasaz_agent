from __future__ import annotations

from functools import lru_cache

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.services.llm.config import ModelConfig


@lru_cache(maxsize=16)
def _build_chat_model(
    provider: str,
    name: str,
    temperature: float,
    base_url: str | None,
    api_key: str | None,
) -> BaseChatModel:
    if provider == "openai":
        return ChatOpenAI(model=name, temperature=temperature, api_key=api_key)
    if provider == "anthropic":
        return ChatAnthropic(model=name, temperature=temperature, api_key=api_key)
    if provider == "openai_compatible":
        return ChatOpenAI(model=name, temperature=temperature, base_url=base_url, api_key=api_key)
    raise ValueError(f"Unsupported model provider: {provider}")


def create_chat_model(config: ModelConfig) -> BaseChatModel:
    return _build_chat_model(
        config.provider,
        config.name,
        config.temperature,
        config.base_url,
        config.api_key,
    )
