from __future__ import annotations

from app.agent.skills.base import SkillContext, SkillResult
from app.services.paper_service import recommend_paper
from app.services.retrieval import RetrievalError
from app.services.storage import Storage


class RecommendationSkill:
    skill_name = "recommendation"
    public_intent = "paper"

    def run(self, context: SkillContext) -> SkillResult:
        try:
            response, artifacts = recommend_paper(context.user_input, Storage())
        except RetrievalError as exc:
            return SkillResult(
                intent="paper",
                response=f"Recommendation retrieval failed: {exc}",
                artifacts={
                    "mode": "paper",
                    "recommendation": None,
                    "retrieval": {
                        "provider": "unknown",
                        "query": context.user_input,
                        "candidate_count": 0,
                        "selected_from": 0,
                    },
                    "links": [],
                },
            )
        return SkillResult(intent="paper", response=response, artifacts=artifacts)
