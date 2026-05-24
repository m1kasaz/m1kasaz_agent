from __future__ import annotations

from datetime import datetime, timezone
from math import log1p
from typing import Any


def rank_candidates(
    candidates: list[dict[str, Any]],
    *,
    query: str,
    topic: str,
    favorite_topic: str | None,
    seen_keys: set[str],
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    query_terms = [term for term in query.lower().replace("/", " ").split() if term]
    for candidate in candidates:
        score = 0.0
        haystack = " ".join(
            str(value)
            for value in [candidate.get("title", ""), candidate.get("summary", ""), candidate.get("owner", "")]
        ).lower()
        score += sum(3.0 for term in query_terms if term in haystack)
        if topic and topic.lower() in haystack:
            score += 4.0
        if favorite_topic and favorite_topic.lower() == topic.lower():
            score += 2.0
        if candidate["item_key"] in seen_keys:
            score -= 100.0
        published_at = candidate.get("published_at")
        if isinstance(published_at, str) and published_at:
            try:
                published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
                age_days = max((datetime.now(timezone.utc) - published).days, 0)
                recency_boost = max(0.0, 30.0 - age_days) / 10.0
                score += recency_boost if candidate.get("kind") == "application" else recency_boost / 2.0
            except ValueError:
                pass
        stars = candidate.get("stars")
        if isinstance(stars, int):
            stars_boost = log1p(max(stars, 0))
            score += stars_boost if candidate.get("kind") == "application" else stars_boost / 2.0
        citation_count = candidate.get("citation_count")
        if isinstance(citation_count, int):
            score += log1p(max(citation_count, 0))
        enriched = dict(candidate)
        enriched["score"] = round(score, 3)
        scored.append(enriched)
    return sorted(scored, key=lambda item: item["score"], reverse=True)
