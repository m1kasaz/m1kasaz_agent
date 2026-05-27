from __future__ import annotations

import mimetypes
import re
import uuid
from pathlib import Path

from app.config import get_settings


class ArtifactService:
    def __init__(self) -> None:
        settings = get_settings()
        self.artifact_dir = settings.artifact_dir
        self.url_prefix = settings.artifact_url_prefix.rstrip("/")
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def create_output_path(self, source_path: Path, suffix: str) -> Path:
        unique = uuid.uuid4().hex[:8]
        filename = f"{source_path.stem}-{unique}{suffix}"
        return self.artifact_dir / filename

    def write_text(self, source_path: Path, content: str) -> dict[str, object]:
        output_path = self.create_output_path(source_path, ".txt")
        output_path.write_text(content, encoding="utf-8")
        return self.describe(output_path)

    def save_upload(self, original_name: str, content: bytes) -> dict[str, object]:
        safe_name = _sanitize_filename(original_name)
        suffix = Path(safe_name).suffix or ".bin"
        stem = Path(safe_name).stem or "upload"
        unique = uuid.uuid4().hex[:8]
        output_path = self.artifact_dir / f"{stem}-{unique}{suffix}"
        output_path.write_bytes(content)
        return self.describe(output_path)

    def describe(self, file_path: Path) -> dict[str, object]:
        mime_type, _ = mimetypes.guess_type(file_path.name)
        return {
            "path": str(file_path),
            "url": self.to_url(file_path),
            "download_url": self.to_download_url(file_path),
            "mime_type": mime_type or "application/octet-stream",
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        }

    def to_url(self, file_path: Path) -> str:
        return f"{self.url_prefix}/{file_path.name}"

    def to_download_url(self, file_path: Path) -> str:
        return f"{self.url_prefix}/download/{file_path.name}"


def _sanitize_filename(filename: str) -> str:
    cleaned = Path(filename or "upload").name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", cleaned).strip(".-")
    return cleaned or "upload"
