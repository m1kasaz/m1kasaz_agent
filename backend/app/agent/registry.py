from __future__ import annotations

from app.agent.skills.chat import ChatSkill
from app.agent.skills.document import DocumentSkill
from app.agent.skills.recommendation import RecommendationSkill
from app.state import Intent


def build_skill_registry() -> dict[Intent, object]:
    return {
        "chat": ChatSkill(),
        "document": DocumentSkill(),
        "paper": RecommendationSkill(),
    }
