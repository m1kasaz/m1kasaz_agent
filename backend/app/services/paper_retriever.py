from __future__ import annotations

import json
import ssl
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import certifi

from app.config import get_settings
from app.services.retrieval import RetrievalError, normalize_candidate


def search_openalex(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    encoded_query = quote_plus(query)
    fields = quote_plus("id,display_name,publication_date,primary_location,authorships,abstract_inverted_index,cited_by_count")
    url = f"https://api.openalex.org/works?search={encoded_query}&per-page={max_results}&select={fields}"
    request = Request(url, headers={"User-Agent": "m1kasaz-agent/0.1 (local validation)"})
    timeout = get_settings().retrieval_timeout_seconds
    ssl_context = _build_ssl_context()
    try:
        with urlopen(request, timeout=timeout, context=ssl_context) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network failure path
        raise RetrievalError(f"Failed to query OpenAlex: {exc}") from exc

    results: list[dict[str, Any]] = []
    for item in payload.get("results") or []:
        title = item.get("display_name") or "Untitled paper"
        summary = _build_abstract(item.get("abstract_inverted_index")) or "No abstract available from OpenAlex."
        source_url = ((item.get("primary_location") or {}).get("landing_page_url")) or item.get("id")
        pdf_url = (item.get("primary_location") or {}).get("pdf_url")
        authors = [
            authorship.get("author", {}).get("display_name", "")
            for authorship in item.get("authorships") or []
            if authorship.get("author", {}).get("display_name")
        ]
        results.append(
            normalize_candidate(
                "paper",
                "openalex",
                {
                    "id": item.get("id", title),
                    "title": title,
                    "summary": summary,
                    "authors": authors,
                    "published_at": item.get("publication_date"),
                    "source_url": source_url,
                    "pdf_url": pdf_url,
                    "citation_count": item.get("cited_by_count"),
                },
            )
        )
    if not results:
        raise RetrievalError("No paper results returned from OpenAlex")
    return results


def _build_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _build_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    tokens = sorted(
        ((position, token) for token, positions in inverted_index.items() for position in positions),
        key=lambda item: item[0],
    )
    return " ".join(token for _, token in tokens)
