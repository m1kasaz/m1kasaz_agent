from __future__ import annotations

from typing import Any


class RetrievalError(RuntimeError):
    pass


def build_link(label: str, url: str, role: str) -> dict[str, str]:
    return {"label": label, "url": url, "role": role}


def item_key(kind: str, provider: str, item_id: str) -> str:
    return f"{kind}:{provider}:{item_id}"


def normalize_candidate(kind: str, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    candidate = dict(payload)
    candidate["kind"] = kind
    candidate["source_provider"] = provider
    candidate["item_key"] = item_key(kind, provider, str(candidate["id"]))
    return candidate
