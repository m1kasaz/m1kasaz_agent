from __future__ import annotations

from app.agent.skills.base import SkillContext, SkillResult
from app.services.document_service import handle_document_request


class DocumentSkill:
    skill_name = "document"
    public_intent = "document"

    def run(self, context: SkillContext) -> SkillResult:
        response, artifacts = handle_document_request(
            context.user_input,
            model_config=context.model_config,
        )
        return SkillResult(intent="document", response=response, artifacts=artifacts)
