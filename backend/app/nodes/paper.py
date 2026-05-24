from __future__ import annotations

from app.agent.skills.base import SkillContext
from app.agent.skills.recommendation import RecommendationSkill
from app.state import AgentState


def paper_node(state: AgentState) -> AgentState:
    result = RecommendationSkill().run(
        SkillContext(
            user_input=state["user_input"],
            requested_intent=state.get("intent"),
        )
    )
    return {
        "response": result.response,
        "artifacts": result.artifacts,
    }
