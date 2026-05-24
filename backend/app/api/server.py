from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.graph.builder import invoke_graph
from app.models import (
    InvokeRequest,
    InvokeResponse,
    ModelProviderSettings,
    ModelSettingsResponse,
    ModelSettingsUpdateRequest,
)
from app.services.storage import Storage

app = FastAPI(title="m1kasaz_agent")

repo_root = Path(__file__).resolve().parents[3]
frontend_dir = repo_root / "frontend" / "static"
settings = get_settings()
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(f"{settings.artifact_url_prefix}/download/{{filename}}")
def download_artifact(filename: str) -> FileResponse:
    artifact_path = (settings.artifact_dir / filename).resolve()
    artifact_root = settings.artifact_dir.resolve()
    if artifact_root not in artifact_path.parents or not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path=artifact_path, filename=artifact_path.name)


app.mount(settings.artifact_url_prefix, StaticFiles(directory=settings.artifact_dir), name="artifacts")


@app.get("/settings/model", response_model=ModelSettingsResponse)
def get_model_settings() -> ModelSettingsResponse:
    storage = Storage()
    return ModelSettingsResponse(
        providers=[
            _build_provider_settings("openai", storage),
            _build_provider_settings("anthropic", storage),
        ]
    )


@app.put("/settings/model/{provider}", response_model=ModelProviderSettings)
def update_model_settings(provider: str, request: ModelSettingsUpdateRequest) -> ModelProviderSettings:
    if provider not in {"openai", "anthropic"}:
        raise HTTPException(status_code=404, detail="Unsupported provider")
    storage = Storage()
    api_key = (request.api_key or "").strip()
    if request.clear_api_key or not api_key:
        storage.clear_model_api_key(provider)
    else:
        storage.set_model_api_key(provider, api_key)
    return _build_provider_settings(provider, storage)


@app.post("/invoke", response_model=InvokeResponse)
def invoke(request: InvokeRequest) -> InvokeResponse:
    model_config = request.model.model_dump(exclude_none=True) if request.model else None
    result = invoke_graph(request.user_input, model_config=model_config, intent=request.intent)
    return InvokeResponse(
        intent=result["intent"],
        response=result["response"],
        artifacts=result.get("artifacts") or {},
    )


def _build_provider_settings(provider: str, storage: Storage) -> ModelProviderSettings:
    env_key = _get_env_api_key(provider)
    stored_key = storage.get_model_api_key(provider)
    api_key = stored_key or env_key
    source = "stored" if stored_key else "env" if env_key else "none"
    return ModelProviderSettings(
        provider=provider,
        configured=bool(api_key),
        source=source,
        masked_api_key=_mask_api_key(api_key),
    )


def _get_env_api_key(provider: str) -> str | None:
    if provider == "openai":
        return os.environ.get("OPENAI_API_KEY") or (
            settings.model_api_key if settings.model_provider == "openai" else None
        )
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY") or (
            settings.model_api_key if settings.model_provider == "anthropic" else None
        )
    return None


def _mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}...{api_key[-4:]}"
