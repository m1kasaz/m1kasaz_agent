from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.models import DocumentArtifact
from app.services.artifact_service import ArtifactService
from app.services.document_converter import DocumentConvertError, convert_docx_to_pdf
from app.services.document_parser import DocumentParseError, parse_docx_text, parse_pdf_text
from app.services.llm import create_chat_model, resolve_model_config
from app.services.storage import Storage


def handle_document_request(
    user_input: str,
    *,
    model_config: dict[str, object] | None = None,
    source_path: Path | str | None = None,
    source_name: str | None = None,
    source_origin: str = "local_path",
) -> tuple[str, dict[str, Any]]:
    resolved_source = Path(source_path).expanduser() if source_path is not None else None
    if resolved_source is None:
        detected_source_path = _detect_source_path(user_input)
        resolved_source = Path(detected_source_path).expanduser() if detected_source_path is not None else None
    if resolved_source is None:
        return (
            "Please provide a local .pdf or .docx path for document processing.",
            {
                "mode": "document",
                "document": {
                    "action": _infer_action(user_input),
                    "metadata": {"status": "error", "reason": "missing_file_path"},
                },
                "links": [],
            },
        )

    path = resolved_source
    source_type = path.suffix.lower().lstrip(".")
    action = _infer_action(user_input)
    storage = Storage()
    artifact_service = ArtifactService()
    source_details = _build_source_details(
        path,
        source_type=source_type,
        source_origin=source_origin,
        source_name=source_name,
        artifact_service=artifact_service,
    )
    artifact_id = uuid.uuid4().hex

    if not path.exists():
        storage.save_document_artifact(
            artifact_id=artifact_id,
            source_path=str(path),
            source_type=source_type,
            action=action,
            output_path=None,
            output_url=None,
            status="error",
            error_message="file_not_found",
        )
        return (
            f"Document file not found: {path}",
            {
                "mode": "document",
                "document": {
                    "action": action,
                    "source": source_details,
                    "metadata": {"status": "error", "reason": "file_not_found"},
                },
                "links": [],
            },
        )

    try:
        if action == "convert":
            return _handle_convert(path, storage, artifact_service, artifact_id, source_details)
        return _handle_text_workflow(
            path,
            action=action,
            storage=storage,
            artifact_service=artifact_service,
            artifact_id=artifact_id,
            model_config=model_config,
            user_input=user_input,
            source_details=source_details,
        )
    except (DocumentParseError, DocumentConvertError, ValueError) as exc:
        storage.save_document_artifact(
            artifact_id=artifact_id,
            source_path=str(path),
            source_type=source_type,
            action=action,
            output_path=None,
            output_url=None,
            status="error",
            error_message=str(exc),
        )
        return (
            f"Document processing failed: {exc}",
            {
                "mode": "document",
                "document": {
                    "action": action,
                    "source": source_details,
                    "metadata": {"status": "error", "reason": str(exc)},
                },
                "links": [],
            },
        )


def _handle_convert(
    path: Path,
    storage: Storage,
    artifact_service: ArtifactService,
    artifact_id: str,
    source_details: dict[str, object],
) -> tuple[str, dict[str, Any]]:
    if path.suffix.lower() != ".docx":
        raise ValueError("Only .docx files can be converted to pdf")
    output_path = artifact_service.create_output_path(path, ".pdf")
    metadata = convert_docx_to_pdf(path, output_path)
    output = artifact_service.describe(output_path)
    storage.save_document_artifact(
        artifact_id=artifact_id,
        source_path=str(path),
        source_type="docx",
        action="convert",
        output_path=output["path"],
        output_url=output["url"],
        status="success",
    )
    document = DocumentArtifact(
        action="convert",
        source=source_details,
        output=output,
        metadata={**metadata, "status": "success"},
    ).model_dump()
    links = [
        {"label": "open converted pdf", "url": output["url"], "role": "preview"},
        {"label": "download converted pdf", "url": output["download_url"], "role": "download"},
    ]
    if source_details.get("url"):
        links.append({"label": "open source file", "url": source_details["url"], "role": "source"})
    if source_details.get("download_url"):
        links.append({"label": "download source file", "url": source_details["download_url"], "role": "download"})
    return (
        f"Converted {path.name} to PDF successfully.",
        {"mode": "document", "document": document, "links": links},
    )


def _handle_text_workflow(
    path: Path,
    *,
    action: str,
    storage: Storage,
    artifact_service: ArtifactService,
    artifact_id: str,
    model_config: dict[str, object] | None,
    user_input: str,
    source_details: dict[str, object],
) -> tuple[str, dict[str, Any]]:
    text, metadata = _extract_text(path)
    text_output = artifact_service.write_text(path, text)
    summary = None
    answer = None
    response = f"Extracted text from {path.name}."
    if action == "summarize":
        summary = _summarize_text(text, model_config)
        response = f"Summarized {path.name} successfully."
    elif action == "qa":
        answer = _answer_question(text, question=user_input, model_config=model_config)
        response = f"Answered a question about {path.name}."
    storage.save_document_artifact(
        artifact_id=artifact_id,
        source_path=str(path),
        source_type=path.suffix.lower().lstrip("."),
        action=action,
        output_path=text_output["path"],
        output_url=text_output["url"],
        status="success",
    )
    document = DocumentArtifact(
        action=action,
        source=source_details,
        output=text_output,
        text_preview=text[:500],
        summary=summary,
        answer=answer,
        metadata={**metadata, "status": "success"},
    ).model_dump()
    links = [
        {"label": "open extracted text", "url": text_output["url"], "role": "preview"},
        {"label": "download extracted text", "url": text_output["download_url"], "role": "download"},
    ]
    if source_details.get("url"):
        links.append({"label": "open source file", "url": source_details["url"], "role": "source"})
    if source_details.get("download_url"):
        links.append({"label": "download source file", "url": source_details["download_url"], "role": "download"})
    return response, {"mode": "document", "document": document, "links": links}


def _extract_text(path: Path) -> tuple[str, dict[str, object]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf_text(path)
    if suffix == ".docx":
        return parse_docx_text(path)
    raise ValueError(f"Unsupported document type: {suffix}")


def _summarize_text(text: str, model_config: dict[str, object] | None) -> str:
    config = resolve_model_config(model_config)
    model = create_chat_model(config)
    reply = model.invoke(
        [
            SystemMessage(content="You summarize documents into concise Chinese bullet-free paragraphs."),
            HumanMessage(content=f"请总结以下文档内容：\n\n{text[:6000]}"),
        ]
    )
    return _stringify_content(reply.content)


def _answer_question(text: str, *, question: str, model_config: dict[str, object] | None) -> str:
    config = resolve_model_config(model_config)
    model = create_chat_model(config)
    reply = model.invoke(
        [
            SystemMessage(content="Answer the user's question using only the provided document text."),
            HumanMessage(content=f"文档内容：\n{text[:6000]}\n\n问题：{question}"),
        ]
    )
    return _stringify_content(reply.content)


def _detect_source_path(user_input: str) -> str | None:
    for token in user_input.replace("\n", " ").split():
        cleaned = token.strip().strip('"').strip("'").rstrip(".,)")
        if cleaned.lower().endswith((".pdf", ".docx")):
            return cleaned
    return None


def _infer_action(user_input: str) -> str:
    lowered = user_input.lower()
    if any(keyword in lowered for keyword in ("question", "qa", "ask", "问", "回答", "问答")):
        return "qa"
    if any(keyword in lowered for keyword in ("summary", "summarize", "概述", "总结")):
        return "summarize"
    if any(keyword in lowered for keyword in ("convert", "转换", "转成", "导出pdf", "to pdf")):
        return "convert"
    return "extract"


def _build_source_details(
    path: Path,
    *,
    source_type: str,
    source_origin: str,
    source_name: str | None,
    artifact_service: ArtifactService,
) -> dict[str, object]:
    details: dict[str, object] = {
        "path": str(path),
        "type": source_type,
        "origin": source_origin,
        "name": source_name or path.name,
    }
    if path.exists() and path.parent == artifact_service.artifact_dir:
        details["url"] = artifact_service.to_url(path)
        details["download_url"] = artifact_service.to_download_url(path)
    return details


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
