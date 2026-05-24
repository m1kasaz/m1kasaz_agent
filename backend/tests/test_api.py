from zipfile import ZipFile

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.api.server import app
from app.graph.builder import get_graph

client = TestClient(app)


class FakeChatModel:
    def invoke(self, messages):
        assert messages
        return AIMessage(content="api mocked reply")


def build_docx(path) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<?xml version='1.0' encoding='UTF-8' standalone='yes'?><w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body><w:p><w:r><w:t>Hello world from api docx.</w:t></w:r></w:p></w:body></w:document>",
        )


def test_index_page() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "m1kasaz agent" in response.text


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_static_assets() -> None:
    js_response = client.get("/static/app.js")
    css_response = client.get("/static/styles.css")
    assert js_response.status_code == 200
    assert css_response.status_code == 200


def test_invoke_document_route(tmp_path) -> None:
    docx_path = tmp_path / "report.docx"
    build_docx(docx_path)
    response = client.post("/invoke", json={"user_input": f"extract this document {docx_path}"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "document"
    assert body["artifacts"]["document"]["action"] == "extract"
    artifact_url = body["artifacts"]["document"]["output"]["url"]
    download_url = body["artifacts"]["document"]["output"]["download_url"]
    artifact_response = client.get(artifact_url)
    assert artifact_response.status_code == 200
    assert "Hello world from api docx." in artifact_response.text
    download_response = client.get(download_url)
    assert download_response.status_code == 200
    assert 'attachment; filename=' in download_response.headers.get("content-disposition", "")


def test_invoke_document_route_with_explicit_intent() -> None:
    response = client.post(
        "/invoke",
        json={"intent": "document", "user_input": "hello there"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "document"
    assert body["artifacts"]["document"]["metadata"]["status"] == "error"


def test_invoke_chat_route_with_model_override(monkeypatch) -> None:
    monkeypatch.setattr("app.agent.skills.chat.create_chat_model", lambda config: FakeChatModel())
    get_graph.cache_clear()

    response = client.post(
        "/invoke",
        json={
            "user_input": "hello there",
            "model": {"provider": "anthropic", "name": "claude-3-5-haiku-latest", "temperature": 0.4},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "chat"
    assert body["response"] == "api mocked reply"
    assert body["artifacts"]["provider"] == "anthropic"
    assert body["artifacts"]["model"] == "claude-3-5-haiku-latest"


def test_invoke_chat_route_with_openai_compatible_override(monkeypatch) -> None:
    monkeypatch.setattr("app.agent.skills.chat.create_chat_model", lambda config: FakeChatModel())
    get_graph.cache_clear()

    response = client.post(
        "/invoke",
        json={
            "user_input": "hello there",
            "model": {
                "provider": "openai_compatible",
                "name": "qwen-plus",
                "temperature": 0.3,
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "test-key",
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "chat"
    assert body["response"] == "api mocked reply"
    assert body["artifacts"]["provider"] == "openai_compatible"
    assert body["artifacts"]["model"] == "qwen-plus"


def test_invoke_rejects_openai_compatible_without_base_url() -> None:
    response = client.post(
        "/invoke",
        json={
            "user_input": "hello there",
            "model": {
                "provider": "openai_compatible",
                "name": "qwen-plus",
                "api_key": "test-key",
            },
        },
    )
    assert response.status_code == 422


def test_invoke_rejects_openai_compatible_without_api_key() -> None:
    response = client.post(
        "/invoke",
        json={
            "user_input": "hello there",
            "model": {
                "provider": "openai_compatible",
                "name": "qwen-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            },
        },
    )
    assert response.status_code == 422


def test_invoke_paper_route(monkeypatch) -> None:
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

    response = client.post("/invoke", json={"user_input": "recommend one AI paper about agents"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "paper"
    assert body["artifacts"]["recommendation"]["kind"] == "paper"
    assert body["artifacts"]["recommendation"]["item"]["citation_count"] == 321
    assert body["artifacts"]["retrieval"]["candidate_count"] == 1
    assert body["artifacts"]["links"][0]["url"].startswith("https://")


def test_invoke_application_route(monkeypatch) -> None:
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
    get_graph.cache_clear()

    response = client.post("/invoke", json={"user_input": "recommend an AI application for writing"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "paper"
    assert body["artifacts"]["recommendation"]["kind"] == "application"
    assert body["artifacts"]["links"][0]["url"] == "https://github.com/owner/tool"


def test_invoke_rejects_invalid_provider() -> None:
    response = client.post(
        "/invoke",
        json={
            "user_input": "hello there",
            "model": {"provider": "invalid-provider", "name": "x"},
        },
    )
    assert response.status_code == 422
