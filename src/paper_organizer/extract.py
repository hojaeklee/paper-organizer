"""PDF text extraction via pypdf."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_text(pdf_path: Path, max_pages: int = 5) -> str:
    """Return the first *max_pages* pages of *pdf_path* as plain text."""
    reader = PdfReader(pdf_path)
    pages = reader.pages[:max_pages]
    return "\n".join(page.extract_text() or "" for page in pages)
