from __future__ import annotations

from app.state import Intent

DOCUMENT_KEYWORDS = (
    "pdf",
    "docx",
    "document",
    "summary",
    "summarize",
    "extract",
    "convert",
    "question about",
)
PAPER_KEYWORDS = (
    "paper",
    "papers",
    "arxiv",
    "recommend",
    "recommendation",
    "application",
    "applications",
    "app",
    "tool",
    "tools",
    "product",
    "products",
    "site",
)


def route_intent(user_input: str) -> Intent:
    lowered = user_input.lower()
    if any(keyword in lowered for keyword in DOCUMENT_KEYWORDS):
        return "document"
    if any(keyword in lowered for keyword in PAPER_KEYWORDS):
        return "paper"
    return "chat"
