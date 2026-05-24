from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[2]


class AppSettings(BaseSettings):
    app_name: str = "m1kasaz_agent"
    data_dir: Path = REPO_ROOT / "data"
    db_path: Path = REPO_ROOT / "data/app.db"
    artifact_dir: Path = REPO_ROOT / "data/artifacts"
    artifact_url_prefix: str = "/artifacts"
    retrieval_timeout_seconds: float = 10.0
    model_provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    model_temperature: float = 0.2
    model_base_url: str | None = None
    model_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="M1KASAZ_",
        env_file="..env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    return settings
