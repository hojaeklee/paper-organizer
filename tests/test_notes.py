"""Tests for Obsidian note generation and file writing."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
import yaml

from paper_organizer.classify import Classification
from paper_organizer.notes import (
    MAX_FILENAME_LEN,
    generate_note,
    sanitize_filename,
    write_note,
)


class TestSanitizeFilename:
    def test_strips_forbidden_chars(self) -> None:
        assert sanitize_filename('a<b>c:d"e/f\\g|h?i*j') == "abcdefghij"

    def test_collapses_whitespace(self) -> None:
        assert sanitize_filename("hello   world") == "hello world"

    def test_strips_leading_trailing_whitespace(self) -> None:
        assert sanitize_filename("  hello  ") == "hello"

    def test_returns_untitled_for_empty(self) -> None:
        assert sanitize_filename("") == "untitled"

    def test_returns_untitled_for_only_forbidden(self) -> None:
        assert sanitize_filename(':<>"/\\|?*') == "untitled"

    def test_truncates_long_names(self) -> None:
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) == MAX_FILENAME_LEN


class TestGenerateNote:
    def test_valid_yaml_frontmatter(self, sample_classification) -> None:
        note = generate_note(sample_classification, "paper.pdf", "2026-02-22")
        parts = note.split("---")
        frontmatter = yaml.safe_load(parts[1])

        assert frontmatter["title"] == "Attention Is All You Need"
        assert frontmatter["category"] == "deep_learning/nlp"
        assert frontmatter["date_added"] == datetime.date(2026, 2, 22)
        assert isinstance(frontmatter["tags"], list)
        assert isinstance(frontmatter["authors"], list)

    def test_authors_as_wikilinks(self, sample_classification) -> None:
        note = generate_note(sample_classification, "paper.pdf", "2026-02-22")
        parts = note.split("---")
        frontmatter = yaml.safe_load(parts[1])

        for author in frontmatter["authors"]:
            assert author.startswith("[[")
            assert author.endswith("]]")

    def test_title_link_in_body(self, sample_classification) -> None:
        note = generate_note(sample_classification, "paper.pdf", "2026-02-22")
        assert "[[paper.pdf|Attention Is All You Need]]" in note

    def test_escapes_quotes_in_title(self) -> None:
        c = Classification(
            title='A "Quoted" Title',
            authors=["Author"],
            folder="misc",
            tags=["test"],
            one_line_summary="Summary.",
        )
        note = generate_note(c, "paper.pdf", "2026-02-22")
        parts = note.split("---")
        frontmatter = yaml.safe_load(parts[1])
        assert frontmatter["title"] == 'A "Quoted" Title'

    def test_escapes_quotes_in_summary(self) -> None:
        c = Classification(
            title="Title",
            authors=["Author"],
            folder="misc",
            tags=["test"],
            one_line_summary='Uses "attention" mechanism.',
        )
        note = generate_note(c, "paper.pdf", "2026-02-22")
        parts = note.split("---")
        frontmatter = yaml.safe_load(parts[1])
        assert "attention" in frontmatter["summary"]

    def test_contains_tldr_callout(self, sample_classification) -> None:
        note = generate_note(sample_classification, "paper.pdf", "2026-02-22")
        assert "> [!tldr] Critical Summary" in note


class TestWriteNote:
    def test_creates_file(self, tmp_path: Path) -> None:
        dest = tmp_path / "notes" / "paper.md"
        write_note("content", dest)
        assert dest.exists()
        assert dest.read_text() == "content"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        dest = tmp_path / "a" / "b" / "paper.md"
        write_note("content", dest)
        assert dest.exists()

    def test_raises_on_existing_file(self, tmp_path: Path) -> None:
        dest = tmp_path / "paper.md"
        dest.write_text("existing")
        with pytest.raises(FileExistsError):
            write_note("new content", dest)
