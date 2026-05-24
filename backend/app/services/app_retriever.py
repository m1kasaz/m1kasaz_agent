from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from app.config import get_settings
from app.services.retrieval import RetrievalError, normalize_candidate


def search_applications(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    encoded_query = quote_plus(query)
    url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page={max_results}"
    request = Request(
        url,
        headers={
            "User-Agent": "m1kasaz-agent/0.1",
            "Accept": "application/vnd.github+json",
        },
    )
    timeout = get_settings().retrieval_timeout_seconds
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network failure path
        raise RetrievalError(f"Failed to query GitHub repositories: {exc}") from exc

    results: list[dict[str, Any]] = []
    for item in payload.get("items") or []:
        if item.get("private"):
            continue
        repo_id = item.get("full_name") or item.get("name")
        if not repo_id:
            continue
        topics = item.get("topics") or []
        summary = item.get("description") or f"GitHub repository. Topics: {', '.join(topics[:4]) or 'none'}."
        results.append(
            normalize_candidate(
                "application",
                "github",
                {
                    "id": repo_id,
                    "title": item.get("name") or repo_id,
                    "summary": summary,
                    "source_url": item.get("html_url") or f"https://github.com/{repo_id}",
                    "stars": item.get("stargazers_count", 0),
                    "owner": (item.get("owner") or {}).get("login"),
                    "published_at": item.get("updated_at"),
                },
            )
        )
    if not results:
        raise RetrievalError("No application results returned from GitHub")
    return results
