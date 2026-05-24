from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.state import Intent


@dataclass(slots=True)
class SkillContext:
    user_input: str
    requested_intent: Intent | None = None
    model_config: dict[str, Any] | None = None


@dataclass(slots=True)
class SkillResult:
    intent: Intent
    response: str
    artifacts: dict[str, Any] = field(default_factory=dict)
