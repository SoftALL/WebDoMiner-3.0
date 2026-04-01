from __future__ import annotations

from pathlib import Path

from docx import Document


def load_rs_text(file_path: str | Path) -> str:
    """
    Load requirements specification text from a .txt or .docx file.

    Supported formats:
    - .txt
    - .docx
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"RS file not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".txt":
        text = path.read_text(encoding="utf-8").strip()
    elif suffix == ".docx":
        text = _load_docx_text(path).strip()
    else:
        raise ValueError(
            f"Unsupported RS file format: {suffix}. Supported formats are .txt and .docx"
        )

    if not text:
        raise ValueError("RS file is empty after loading.")

    return text


def _load_docx_text(path: Path) -> str:
    """Extract plain text from a .docx document."""
    doc = Document(path)
    paragraphs = [paragraph.text.strip() for paragraph in doc.paragraphs]
    non_empty_paragraphs = [paragraph for paragraph in paragraphs if paragraph]
    return "\n".join(non_empty_paragraphs)