from __future__ import annotations

from app.agent.routing import route_intent
from app.state import AgentState


def router_node(state: AgentState) -> AgentState:
    if state.get("intent"):
        return {"intent": state["intent"]}
    return {"intent": route_intent(state["user_input"])}


__all__ = ["route_intent", "router_node"]
