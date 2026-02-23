"""Tests for PDF text extraction."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from paper_organizer.extract import extract_text


@pytest.fixture
def pdf_with_text(tmp_path: Path) -> Path:
    """Create a minimal PDF with readable text via pypdf."""
    from pypdf import PdfWriter
    from pypdf._page import PageObject

    writer = PdfWriter()
    for i in range(3):
        page = PageObject.create_blank_page(width=72, height=72)
        writer.add_page(page)

    path = tmp_path / "sample.pdf"
    with open(path, "wb") as f:
        writer.write(f)
    return path


class TestExtractText:
    def test_returns_string(self, pdf_with_text: Path) -> None:
        result = extract_text(pdf_with_text)
        assert isinstance(result, str)

    def test_respects_max_pages(self) -> None:
        mock_pages = [MagicMock() for _ in range(10)]
        for i, p in enumerate(mock_pages):
            p.extract_text.return_value = f"page{i}"

        mock_reader = MagicMock()
        mock_reader.pages = mock_pages

        with patch("paper_organizer.extract.PdfReader", return_value=mock_reader):
            result = extract_text(Path("dummy.pdf"), max_pages=3)

        assert result == "page0\npage1\npage2"
        assert mock_pages[3].extract_text.call_count == 0

    def test_empty_pages_produce_empty_strings(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("paper_organizer.extract.PdfReader", return_value=mock_reader):
            result = extract_text(Path("dummy.pdf"))

        assert result == ""

    def test_concatenates_pages_with_newline(self) -> None:
        pages = []
        for text in ["Hello", "World"]:
            p = MagicMock()
            p.extract_text.return_value = text
            pages.append(p)

        mock_reader = MagicMock()
        mock_reader.pages = pages

        with patch("paper_organizer.extract.PdfReader", return_value=mock_reader):
            result = extract_text(Path("dummy.pdf"))

        assert result == "Hello\nWorld"
