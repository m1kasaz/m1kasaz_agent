from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.services.llm.config import ModelOverride
from app.state import Intent


class LinkArtifact(BaseModel):
    label: str
    url: str
    role: Literal["landing", "pdf", "download", "preview", "source"]


class DocumentSource(BaseModel):
    path: str
    type: Literal["pdf", "docx"]
    origin: Literal["local_path", "uploaded"] = "local_path"
    name: str | None = None
    url: str | None = None
    download_url: str | None = None


class DocumentOutput(BaseModel):
    path: str
    url: str
    download_url: str | None = None
    mime_type: str
    size_bytes: int | None = None


class DocumentArtifact(BaseModel):
    action: Literal["convert", "extract", "summarize", "qa"]
    source: DocumentSource
    output: DocumentOutput | None = None
    text_preview: str | None = None
    summary: str | None = None
    answer: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecommendationItem(BaseModel):
    id: str
    title: str
    summary: str
    source_provider: str
    source_url: str
    pdf_url: str | None = None
    authors: list[str] = Field(default_factory=list)
    published_at: str | None = None
    stars: int | None = None
    citation_count: int | None = None
    owner: str | None = None
    score: float | None = None


class RecommendationArtifact(BaseModel):
    kind: Literal["paper", "application"]
    query: str
    topic: str
    item: RecommendationItem
    alternatives: list[RecommendationItem] = Field(default_factory=list)
    reason: str


class RetrievalArtifact(BaseModel):
    provider: str
    query: str
    candidate_count: int
    selected_from: int


class ModelSettingsUpdateRequest(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    clear_api_key: bool = False
    clear_base_url: bool = False


class ModelProviderSettings(BaseModel):
    provider: Literal["openai", "anthropic", "openai_compatible"]
    configured: bool
    source: Literal["env", "stored", "none"]
    masked_api_key: str | None = None
    base_url: str | None = None
    base_url_source: Literal["env", "stored", "none"] | None = None


class ModelSettingsResponse(BaseModel):
    providers: list[ModelProviderSettings]


class InvokeRequest(BaseModel):
    user_input: str = Field(min_length=1)
    intent: Intent | None = None
    model: ModelOverride | None = None


class InvokeResponse(BaseModel):
    intent: Intent
    response: str
    artifacts: dict[str, Any] = Field(default_factory=dict)
