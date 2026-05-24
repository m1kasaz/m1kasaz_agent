from __future__ import annotations

from typing import Any

from app.models import RecommendationArtifact, RecommendationItem, RetrievalArtifact
from app.services.app_retriever import search_applications
from app.services.paper_retriever import search_openalex
from app.services.ranker import rank_candidates
from app.services.retrieval import RetrievalError, build_link
from app.services.storage import Storage


def recommend_paper(user_input: str, storage: Storage) -> tuple[str, dict[str, Any]]:
    preferences = storage.get_preferences()
    recommendation_kind = _infer_kind(user_input)
    topic = _infer_topic(user_input, preferences)
    if topic:
        storage.set_preference("favorite_topic", topic)

    query = _build_query(user_input, topic, recommendation_kind)
    retriever = search_openalex if recommendation_kind == "paper" else search_applications
    candidates = retriever(query)
    ranked = rank_candidates(
        candidates,
        query=query,
        topic=topic,
        favorite_topic=preferences.get("favorite_topic"),
        seen_keys=storage.list_recommended_keys(),
    )
    if not ranked:
        raise RetrievalError("No ranked recommendation candidates available")
    selected = ranked[0]
    alternatives = ranked[1:4]
    storage.save_recommendation(selected, query=query, topic=topic)

    item = RecommendationItem(**_to_item_payload(selected))
    alternative_items = [RecommendationItem(**_to_item_payload(candidate)) for candidate in alternatives]
    recommendation = RecommendationArtifact(
        kind=recommendation_kind,
        query=query,
        topic=topic,
        item=item,
        alternatives=alternative_items,
        reason=_build_reason(selected, topic, preferences.get("favorite_topic")),
    ).model_dump()
    retrieval = RetrievalArtifact(
        provider=selected["source_provider"],
        query=query,
        candidate_count=len(candidates),
        selected_from=min(len(ranked), 4),
    ).model_dump()
    links = [build_link("open result", item.source_url, "landing")]
    if item.pdf_url:
        links.append(build_link("open pdf", item.pdf_url, "pdf"))

    label = "paper" if recommendation_kind == "paper" else "application"
    response = f"Recommended {label}: {item.title}. {item.summary}"
    artifacts: dict[str, Any] = {
        "mode": "paper",
        "recommendation": recommendation,
        "retrieval": retrieval,
        "links": links,
        "history_count": len(storage.list_recommendations()),
        "favorite_topic": storage.get_preferences().get("favorite_topic"),
    }
    return response, artifacts


def _build_query(user_input: str, topic: str, kind: str) -> str:
    cleaned = " ".join(user_input.split())
    keywords = _extract_keywords(cleaned)
    if kind == "application":
        return " ".join(keywords) or topic or "ai"
    return " ".join(keywords) or topic or "artificial intelligence"


def _infer_kind(user_input: str) -> str:
    lowered = user_input.lower()
    if any(keyword in lowered for keyword in ("application", "applications", "app", "tool", "tools", "product")):
        return "application"
    return "paper"


def _extract_keywords(user_input: str) -> list[str]:
    stopwords = {
        "recommend",
        "recommended",
        "one",
        "an",
        "a",
        "the",
        "ai",
        "paper",
        "papers",
        "application",
        "applications",
        "app",
        "tool",
        "tools",
        "product",
        "products",
        "about",
        "for",
        "of",
    }
    keywords = [word for word in user_input.lower().replace("/", " ").split() if word not in stopwords]
    return keywords


def _infer_topic(user_input: str, preferences: dict[str, str]) -> str:
    lowered = user_input.lower()
    if "agent" in lowered:
        return "agents"
    if "rag" in lowered or "retrieval" in lowered:
        return "rag"
    if "multimodal" in lowered or "document" in lowered:
        return "multimodal"
    if "writer" in lowered or "writing" in lowered:
        return "writing"
    if "coding" in lowered or "code" in lowered:
        return "coding"
    return preferences.get("favorite_topic", "agents")


def _to_item_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(candidate["id"]),
        "title": candidate["title"],
        "summary": candidate["summary"],
        "source_provider": candidate["source_provider"],
        "source_url": candidate["source_url"],
        "pdf_url": candidate.get("pdf_url"),
        "authors": candidate.get("authors") or [],
        "published_at": candidate.get("published_at"),
        "stars": candidate.get("stars"),
        "citation_count": candidate.get("citation_count"),
        "owner": candidate.get("owner"),
        "score": candidate.get("score"),
    }


def _build_reason(selected: dict[str, Any], topic: str, favorite_topic: str | None) -> str:
    reasons = [f"matched topic {topic}"]
    if favorite_topic and favorite_topic == topic:
        reasons.append("aligned with saved preference")
    if selected.get("citation_count"):
        reasons.append("high citation impact")
    if selected.get("published_at"):
        reasons.append("recent result")
    if selected.get("stars"):
        reasons.append("strong repository popularity")
    return ", ".join(reasons)
