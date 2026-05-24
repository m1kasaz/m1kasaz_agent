from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.agent.orchestrator import invoke_agent
from app.state import AgentState, Intent


@dataclass(slots=True)
class GraphCompatibilityLayer:
    def invoke(self, state: AgentState) -> AgentState:
        return invoke_agent(
            state["user_input"],
            model_config=state.get("model_config"),
            intent=state.get("intent"),
        )


def build_graph() -> GraphCompatibilityLayer:
    return GraphCompatibilityLayer()


@lru_cache(maxsize=1)
def get_graph() -> GraphCompatibilityLayer:
    return build_graph()


def invoke_graph(
    user_input: str,
    model_config: dict[str, Any] | None = None,
    intent: Intent | None = None,
) -> AgentState:
    return invoke_agent(user_input, model_config=model_config, intent=intent)
