from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.agent.skills.base import SkillContext, SkillResult
from app.services.llm import create_chat_model, resolve_model_config


class ChatSkill:
    skill_name = "chat"
    public_intent = "chat"

    def run(self, context: SkillContext) -> SkillResult:
        provider = _requested_provider(context)
        try:
            model_config = resolve_model_config(context.model_config)
            provider = model_config.provider
            model = create_chat_model(model_config)
            reply = model.invoke([HumanMessage(content=context.user_input)])
        except Exception as exc:
            if _is_model_auth_error(exc):
                return SkillResult(
                    intent="chat",
                    response=_build_model_auth_message(provider, exc),
                    artifacts={
                        "mode": "chat",
                        "provider": provider,
                        "error": "model_auth_error",
                    },
                )
            raise

        return SkillResult(
            intent="chat",
            response=_stringify_content(reply.content),
            artifacts={
                "received": context.user_input,
                "mode": "chat",
                "provider": model_config.provider,
                "model": model_config.name,
                "temperature": model_config.temperature,
            },
        )


def _requested_provider(context: SkillContext) -> str:
    if context.model_config and isinstance(context.model_config.get("provider"), str):
        return context.model_config["provider"]
    return "openai"


def _is_model_auth_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "missing credentials",
            "openai_api_key",
            "openai_admin_key",
            "anthropic_api_key",
            "api_key client option must be set",
            "could not resolve authentication method",
            "incorrect api key",
            "invalid_api_key",
            "authentication failed",
            "401",
        )
    )


def _build_model_auth_message(provider: str, exc: Exception) -> str:
    message = str(exc).lower()
    if any(marker in message for marker in ("incorrect api key", "invalid_api_key", "authentication failed", "401")):
        if provider == "anthropic":
            return "Anthropic API Key 无效：请在设置中检查或重新填写 ANTHROPIC_API_KEY。"
        if provider == "openai":
            return "OpenAI API Key 无效：请在设置中检查或重新填写 OPENAI_API_KEY。"
        return "当前模型认证失败：请在设置中检查对应的 API Key。"
    if provider == "anthropic":
        return "Anthropic 模型暂时不可用：请先在设置中配置 ANTHROPIC_API_KEY。"
    if provider == "openai":
        return "OpenAI 模型暂时不可用：请先在设置中配置 OPENAI_API_KEY。"
    return "当前模型暂时不可用：请先在设置中补充对应模型服务的 API Key。"


def _stringify_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(part for part in parts if part)
    return str(content)
