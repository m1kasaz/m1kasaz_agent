from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
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
from app.services.document_service import handle_document_request
from app.services.llm.config import ModelOverride
from app.services.artifact_service import ArtifactService
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
            _build_provider_settings("openai_compatible", storage),
        ]
    )


@app.put("/settings/model/{provider}", response_model=ModelProviderSettings)
def update_model_settings(provider: str, request: ModelSettingsUpdateRequest) -> ModelProviderSettings:
    if provider not in {"openai", "anthropic", "openai_compatible"}:
        raise HTTPException(status_code=404, detail="Unsupported provider")
    storage = Storage()
    api_key = (request.api_key or "").strip()
    if request.clear_api_key or not api_key:
        storage.clear_model_api_key(provider)
    else:
        storage.set_model_api_key(provider, api_key)

    if provider == "openai_compatible":
        base_url = (request.base_url or "").strip()
        if request.clear_base_url or not base_url:
            storage.clear_model_base_url(provider)
        else:
            storage.set_model_base_url(provider, base_url)

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


@app.post("/invoke/upload", response_model=InvokeResponse)
async def invoke_upload(
    user_input: str = Form(""),
    model: str | None = Form(None),
    file: UploadFile = File(...),
) -> InvokeResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Only .pdf and .docx uploads are supported")

    artifact_service = ArtifactService()
    upload_payload = artifact_service.save_upload(file.filename or f"upload{suffix}", await file.read())
    model_config = _parse_model_override(model)
    prompt = (user_input or "").strip() or "提取这个文档"
    response, artifacts = handle_document_request(
        prompt,
        model_config=model_config,
        source_path=upload_payload["path"],
        source_name=file.filename or Path(upload_payload["path"]).name,
        source_origin="uploaded",
    )
    return InvokeResponse(intent="document", response=response, artifacts=artifacts)


def _build_provider_settings(provider: str, storage: Storage) -> ModelProviderSettings:
    env_key = _get_env_api_key(provider)
    stored_key = storage.get_model_api_key(provider)
    api_key = stored_key or env_key
    source = "stored" if stored_key else "env" if env_key else "none"
    env_base_url = _get_env_base_url(provider)
    stored_base_url = storage.get_model_base_url(provider)
    base_url = stored_base_url or env_base_url
    base_url_source = "stored" if stored_base_url else "env" if env_base_url else "none"
    return ModelProviderSettings(
        provider=provider,
        configured=bool(api_key),
        source=source,
        masked_api_key=_mask_api_key(api_key),
        base_url=base_url,
        base_url_source=base_url_source if provider == "openai_compatible" else None,
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
    if provider == "openai_compatible":
        return os.environ.get("OPENAI_API_KEY") or (
            settings.model_api_key if settings.model_provider == "openai_compatible" else None
        )
    return None


def _get_env_base_url(provider: str) -> str | None:
    if provider == "openai_compatible":
        return settings.model_base_url if settings.model_provider == "openai_compatible" else None
    return None


def _mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}...{api_key[-4:]}"


def _parse_model_override(model_payload: str | None) -> dict[str, object] | None:
    if not model_payload:
        return None
    try:
        parsed = json.loads(model_payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid model payload") from exc
    try:
        return ModelOverride.model_validate(parsed).model_dump(exclude_none=True)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
