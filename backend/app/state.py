from __future__ import annotations

from typing import Any, Literal, TypedDict

Intent = Literal["chat", "document", "paper"]


class AgentState(TypedDict, total=False):
    user_input: str
    intent: Intent
    response: str
    artifacts: dict[str, Any]
    model_config: dict[str, Any]
    thread_id: str | None
    messages: list[dict[str, str]]
    user_preferences: dict[str, Any]
