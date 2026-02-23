"""PDF text extraction via pypdf."""

from __future__ import annotations

from pathlib import Path


def extract_text(pdf_path: Path, max_pages: int = 5) -> str:
    """Return the first *max_pages* pages of *pdf_path* as plain text."""
    raise NotImplementedError
