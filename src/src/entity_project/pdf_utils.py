from __future__ import annotations

from pathlib import Path
from typing import Any
import re


def load_pdf_pages(pdf_path: str | Path) -> list[dict[str, Any]]:
    """Load selectable text from a PDF with LangChain PyPDFLoader."""
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("The input file must have a .pdf extension.")

    try:
        from langchain_community.document_loaders import PyPDFLoader
    except ImportError as exc:
        raise ImportError(
            "PDF dependencies are missing. Run: pip install -r requirements.txt"
        ) from exc

    documents = PyPDFLoader(str(path)).load()
    pages: list[dict[str, Any]] = []

    for index, document in enumerate(documents, start=1):
        content = (document.page_content or "").strip()
        if content:
            page_number = int(document.metadata.get("page", index - 1)) + 1
            pages.append({"page": page_number, "text": content})

    if not pages:
        raise ValueError(
            "No selectable text was found. Scanned/image-only PDFs need OCR first."
        )

    return pages


def split_text_blocks(text: str) -> list[str]:
    """Split a page into non-empty paragraph blocks."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [
        re.sub(r"[ \t]+", " ", block).strip()
        for block in re.split(r"\n\s*\n", normalized)
    ]
    return [block for block in blocks if block] or (
        [normalized.strip()] if normalized.strip() else []
    )


def chunk_text(text: str, max_chars: int = 900, overlap: int = 100) -> list[str]:
    """Create overlapping chunks for token-classification inference."""
    if max_chars <= 0 or overlap < 0 or overlap >= max_chars:
        raise ValueError("Require max_chars > overlap >= 0.")

    text = " ".join(text.split())
    if not text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start + max_chars // 2:
                end = boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks
