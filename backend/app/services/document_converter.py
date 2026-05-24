from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class DocumentConvertError(RuntimeError):
    pass


def convert_docx_to_pdf(source_path: Path, output_path: Path) -> dict[str, object]:
    binary = shutil.which("soffice") or shutil.which("libreoffice")
    if binary is None:
        raise DocumentConvertError("LibreOffice is required for docx to pdf conversion")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_output_dir = Path(tmp_dir)
        command = [
            binary,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmp_output_dir),
            str(source_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            raise DocumentConvertError(completed.stderr.strip() or completed.stdout.strip() or "LibreOffice conversion failed")

        generated_path = tmp_output_dir / f"{source_path.stem}.pdf"
        if not generated_path.exists():
            raise DocumentConvertError("LibreOffice did not produce a PDF output")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(generated_path), str(output_path))

    return {"converter": "libreoffice"}
