from __future__ import annotations

from typing import Any

from app.agent.registry import build_skill_registry
from app.agent.routing import route_intent
from app.agent.skills.base import SkillContext
from app.state import AgentState, Intent


def invoke_agent(
    user_input: str,
    model_config: dict[str, Any] | None = None,
    intent: Intent | None = None,
) -> AgentState:
    effective_intent = intent or route_intent(user_input)
    registry = build_skill_registry()
    skill = registry[effective_intent]
    result = skill.run(
        SkillContext(
            user_input=user_input,
            requested_intent=intent,
            model_config=dict(model_config) if model_config else None,
        )
    )
    return {
        "intent": result.intent,
        "response": result.response,
        "artifacts": result.artifacts,
    }
