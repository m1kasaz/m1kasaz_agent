from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.config import get_settings
from app.services.storage import Storage

Provider = Literal["openai", "anthropic", "openai_compatible"]


class ModelConfig(BaseModel):
    provider: Provider
    name: str
    temperature: float = 0.2
    base_url: str | None = None
    api_key: str | None = None

    @model_validator(mode="after")
    def validate_openai_compatible(self) -> "ModelConfig":
        if self.provider == "openai_compatible":
            if not self.base_url:
                raise ValueError("base_url is required for openai_compatible provider")
            if not self.api_key:
                raise ValueError("api_key is required for openai_compatible provider")
        return self


class ModelOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Provider | None = None
    name: str | None = None
    temperature: float | None = None
    base_url: str | None = None
    api_key: str | None = None

    @model_validator(mode="after")
    def validate_openai_compatible(self) -> "ModelOverride":
        if self.provider == "openai_compatible":
            if not self.base_url:
                raise ValueError("base_url is required for openai_compatible provider")
            if not self.api_key:
                raise ValueError("api_key is required for openai_compatible provider")
        return self


def resolve_model_config(override: ModelOverride | dict[str, object] | None = None) -> ModelConfig:
    settings = get_settings()
    payload = {
        "provider": settings.model_provider,
        "name": settings.model_name,
        "temperature": settings.model_temperature,
        "base_url": settings.model_base_url,
        "api_key": settings.model_api_key,
    }
    if isinstance(override, ModelOverride):
        override_payload = override.model_dump(exclude_none=True)
    elif override is None:
        override_payload = {}
    else:
        override_payload = {key: value for key, value in override.items() if value is not None}

    payload.update(override_payload)
    payload = _apply_stored_credentials(payload, Storage())
    return ModelConfig.model_validate(payload)


def _apply_stored_credentials(payload: dict[str, object], storage: Storage) -> dict[str, object]:
    provider = payload.get("provider")
    if provider not in {"openai", "anthropic", "openai_compatible"}:
        return payload
    if not payload.get("api_key"):
        stored_api_key = storage.get_model_api_key(str(provider))
        if stored_api_key:
            payload["api_key"] = stored_api_key
    if provider == "openai_compatible" and not payload.get("base_url"):
        stored_base_url = storage.get_model_base_url(str(provider))
        if stored_base_url:
            payload["base_url"] = stored_base_url
    return payload
