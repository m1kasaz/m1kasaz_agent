from __future__ import annotations

from app.state import Intent

DOCUMENT_SUFFIXES = (".pdf", ".docx")
DOCUMENT_OBJECT_KEYWORDS = (
    "pdf",
    "docx",
    "document",
    "file",
    "文档",
    "文件",
)
DOCUMENT_ACTION_KEYWORDS = (
    "summary",
    "summarize",
    "extract",
    "convert",
    "question about",
    "question on",
    "qa",
    "read",
    "总结",
    "摘要",
    "提取",
    "转换",
    "转成",
    "转为",
    "问答",
)
RECOMMENDATION_VERBS = (
    "recommend",
    "recommended",
    "recommendation",
    "search",
    "find",
    "suggest",
    "looking for",
    "推荐",
    "检索",
    "搜索",
    "查找",
    "找",
)
PAPER_TARGET_KEYWORDS = (
    "paper",
    "papers",
    "arxiv",
    "research",
    "publication",
    "论文",
    "文献",
    "研究",
)
APPLICATION_TARGET_KEYWORDS = (
    "application",
    "applications",
    "app",
    "tool",
    "tools",
    "product",
    "products",
    "site",
    "website",
    "service",
    "应用",
    "工具",
    "产品",
    "网站",
)


def route_intent(user_input: str) -> Intent:
    lowered = " ".join(user_input.lower().split())

    if _contains_document_path(user_input):
        return "document"
    if _looks_like_document_request(lowered):
        return "document"
    if _looks_like_recommendation_request(lowered):
        return "paper"
    return "chat"


def _contains_document_path(user_input: str) -> bool:
    for token in user_input.replace("\n", " ").split():
        cleaned = token.strip().strip('"').strip("'").rstrip(".,)")
        if cleaned.lower().endswith(DOCUMENT_SUFFIXES):
            return True
    return False


def _looks_like_document_request(lowered: str) -> bool:
    has_document_object = any(keyword in lowered for keyword in DOCUMENT_OBJECT_KEYWORDS)
    has_document_action = any(keyword in lowered for keyword in DOCUMENT_ACTION_KEYWORDS)
    if has_document_object and has_document_action:
        return True
    return ("docx" in lowered and "to pdf" in lowered) or ("docx" in lowered and "pdf" in lowered and ("转" in lowered or "convert" in lowered))


def _looks_like_recommendation_request(lowered: str) -> bool:
    if "arxiv" in lowered:
        return True

    has_target = any(keyword in lowered for keyword in PAPER_TARGET_KEYWORDS + APPLICATION_TARGET_KEYWORDS)
    has_verb = any(keyword in lowered for keyword in RECOMMENDATION_VERBS)
    return has_target and has_verb
