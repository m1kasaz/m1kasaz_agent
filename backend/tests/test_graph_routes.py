from zipfile import ZipFile

from langchain_core.messages import AIMessage

from app.agent.orchestrator import invoke_agent
from app.graph.builder import get_graph, invoke_graph
from app.services.llm.config import ModelOverride, resolve_model_config
from app.nodes.router import route_intent
from app.services.storage import Storage


class FakeChatModel:
    def invoke(self, messages):
        assert messages
        return AIMessage(content="mocked reply")


def build_docx(path) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<?xml version='1.0' encoding='UTF-8' standalone='yes'?><w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body><w:p><w:r><w:t>Hello world from docx.</w:t></w:r></w:p></w:body></w:document>",
        )


def test_route_intent_chat() -> None:
    assert route_intent("hello there") == "chat"


def test_route_intent_document() -> None:
    assert route_intent("summarize this pdf report.pdf") == "document"


def test_route_intent_paper() -> None:
    assert route_intent("recommend one AI paper about agents") == "paper"


def test_route_intent_application() -> None:
    assert route_intent("recommend an AI application for writing") == "paper"


def test_resolve_model_config_applies_override() -> None:
    config = resolve_model_config(ModelOverride(name="claude-3-5-haiku-latest", temperature=0.6))
    assert config.provider == "openai"
    assert config.name == "claude-3-5-haiku-latest"
    assert config.temperature == 0.6


def test_resolve_model_config_applies_openai_compatible_override() -> None:
    config = resolve_model_config(
        ModelOverride(
            provider="openai_compatible",
            name="qwen-plus",
            temperature=0.3,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="test-key",
        )
    )
    assert config.provider == "openai_compatible"
    assert config.name == "qwen-plus"
    assert config.temperature == 0.3
    assert config.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert config.api_key == "test-key"


def test_graph_invokes_chat(monkeypatch) -> None:
    monkeypatch.setattr("app.agent.skills.chat.create_chat_model", lambda config: FakeChatModel())
    get_graph.cache_clear()

    result = invoke_graph("hello there", model_config={"provider": "anthropic", "name": "claude-test"})
    assert result["intent"] == "chat"
    assert result["response"] == "mocked reply"
    assert result["artifacts"]["provider"] == "anthropic"
    assert result["artifacts"]["model"] == "claude-test"


def test_graph_respects_explicit_intent() -> None:
    get_graph.cache_clear()
    result = invoke_graph("hello there", intent="document")
    assert result["intent"] == "document"
    assert result["artifacts"]["document"]["metadata"]["status"] == "error"


def test_graph_invokes_chat_with_openai_compatible(monkeypatch) -> None:
    monkeypatch.setattr("app.agent.skills.chat.create_chat_model", lambda config: FakeChatModel())
    get_graph.cache_clear()

    result = invoke_graph(
        "hello there",
        model_config={
            "provider": "openai_compatible",
            "name": "qwen-plus",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "test-key",
        },
    )
    assert result["intent"] == "chat"
    assert result["response"] == "mocked reply"
    assert result["artifacts"]["provider"] == "openai_compatible"
    assert result["artifacts"]["model"] == "qwen-plus"


def test_graph_extracts_docx_text(tmp_path) -> None:
    docx_path = tmp_path / "sample.docx"
    build_docx(docx_path)
    get_graph.cache_clear()

    result = invoke_graph(f"extract this document {docx_path}", intent="document")
    assert result["intent"] == "document"
    assert result["artifacts"]["document"]["action"] == "extract"
    assert result["artifacts"]["document"]["text_preview"].startswith("Hello world")
    assert result["artifacts"]["document"]["output"]["download_url"].startswith("/artifacts/download/")
    assert result["artifacts"]["links"][0]["url"].startswith("/artifacts/")


def test_graph_recommends_paper_with_links(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.paper_service.search_openalex",
        lambda query: [
            {
                "id": "1234.5678",
                "title": "Agent Planning Paper",
                "summary": "A useful paper.",
                "authors": ["Alice"],
                "published_at": "2026-05-01T00:00:00Z",
                "source_url": "https://arxiv.org/abs/1234.5678",
                "pdf_url": "https://arxiv.org/pdf/1234.5678",
                "source_provider": "arxiv",
                "kind": "paper",
                "citation_count": 321,
                "item_key": "paper:arxiv:1234.5678",
            }
        ],
    )
    get_graph.cache_clear()

    result = invoke_graph("recommend one AI paper about agents", intent="paper")
    assert result["intent"] == "paper"
    assert result["artifacts"]["recommendation"]["kind"] == "paper"
    assert result["artifacts"]["recommendation"]["item"]["citation_count"] == 321
    assert result["artifacts"]["links"][0]["url"].startswith("https://")


def test_orchestrator_keeps_auto_routing_behavior(monkeypatch) -> None:
    monkeypatch.setattr("app.agent.skills.chat.create_chat_model", lambda config: FakeChatModel())

    chat_result = invoke_agent("hello there")
    assert chat_result["intent"] == "chat"
    assert chat_result["response"] == "mocked reply"

    document_result = invoke_agent("summarize this pdf report.pdf")
    assert document_result["intent"] == "document"


def test_orchestrator_preserves_public_paper_intent_for_applications(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.paper_service.search_applications",
        lambda query: [
            {
                "id": "owner/tool",
                "title": "Tool",
                "summary": "Helpful AI app.",
                "source_url": "https://github.com/owner/tool",
                "source_provider": "github",
                "kind": "application",
                "item_key": "application:github:owner/tool",
                "stars": 42,
                "owner": "owner",
            }
        ],
    )

    result = invoke_agent("recommend an AI application for writing")
    assert result["intent"] == "paper"
    assert result["artifacts"]["recommendation"]["kind"] == "application"


def test_storage_initializes_tables(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.db")
    storage.set_preference("favorite_topic", "agents")
    assert storage.get_preferences()["favorite_topic"] == "agents"
    storage.save_document_artifact(
        artifact_id="artifact-1",
        source_path="/tmp/source.docx",
        source_type="docx",
        action="extract",
        output_path="/tmp/output.txt",
        output_url="/artifacts/output.txt",
        status="success",
    )
    storage.save_recommendation(
        {
            "item_key": "paper:arxiv:123",
            "kind": "paper",
            "title": "Title",
            "source_provider": "arxiv",
            "source_url": "https://arxiv.org/abs/123",
            "score": 1.0,
        },
        query="agents",
        topic="agents",
    )
    assert storage.has_recommended("paper:arxiv:123") is True
    assert storage.list_recommendations()[0]["item_type"] == "paper"
