from __future__ import annotations

from app.agent.skills.base import SkillContext
from app.agent.skills.chat import ChatSkill
from app.state import AgentState


def chat_node(state: AgentState) -> AgentState:
    result = ChatSkill().run(
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
