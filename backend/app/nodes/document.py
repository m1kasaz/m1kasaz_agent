from __future__ import annotations

from app.agent.skills.base import SkillContext
from app.agent.skills.document import DocumentSkill
from app.state import AgentState


def document_node(state: AgentState) -> AgentState:
    result = DocumentSkill().run(
        SkillContext(
            user_input=state["user_input"],
            requested_intent=state.get("intent"),
            model_config=state.get("model_config"),
        )
    )
    return {
        "response": result.response,
        "artifacts": result.artifacts,
    }
