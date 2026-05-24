from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


class DocumentParseError(RuntimeError):
    pass


def parse_pdf_text(file_path: Path) -> tuple[str, dict[str, object]]:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime environment
        raise DocumentParseError("pypdf is required for PDF text extraction") from exc

    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(page.strip() for page in pages if page.strip()).strip()
    if not text:
        raise DocumentParseError("No extractable text found in PDF file")
    return text, {"extractor": "pypdf", "page_count": len(reader.pages)}


def parse_docx_text(file_path: Path) -> tuple[str, dict[str, object]]:
    with ZipFile(file_path) as archive:
        try:
            document_xml = archive.read("word/document.xml")
        except KeyError as exc:
            raise DocumentParseError("Invalid DOCX file: missing word/document.xml") from exc

    root = ElementTree.fromstring(document_xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", WORD_NAMESPACE):
        texts = [node.text for node in paragraph.findall(".//w:t", WORD_NAMESPACE) if node.text]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)

    text = "\n".join(paragraphs).strip()
    if not text:
        raise DocumentParseError("No extractable text found in DOCX file")
    return text, {"extractor": "docx-xml", "paragraph_count": len(paragraphs)}
