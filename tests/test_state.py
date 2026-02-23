"""Tests for content hashing and processed-file tracking."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paper_organizer.state import content_hash, is_processed, mark_processed


@pytest.fixture
def state_path(tmp_path: Path) -> Path:
    return tmp_path / ".processed_papers.json"


class TestContentHash:
    def test_deterministic(self, tmp_path: Path) -> None:
        f = tmp_path / "test.pdf"
        f.write_bytes(b"hello world")
        assert content_hash(f) == content_hash(f)

    def test_differs_for_different_content(self, tmp_path: Path) -> None:
        a = tmp_path / "a.pdf"
        b = tmp_path / "b.pdf"
        a.write_bytes(b"content A")
        b.write_bytes(b"content B")
        assert content_hash(a) != content_hash(b)

    def test_only_reads_first_chunk(self, tmp_path: Path) -> None:
        f = tmp_path / "large.pdf"
        data = b"A" * 65536 + b"B" * 65536
        f.write_bytes(data)

        g = tmp_path / "same_prefix.pdf"
        g.write_bytes(b"A" * 65536 + b"C" * 65536)

        assert content_hash(f) == content_hash(g)

    def test_small_file_hashes_all_content(self, tmp_path: Path) -> None:
        f = tmp_path / "tiny.pdf"
        f.write_bytes(b"small")
        h = content_hash(f)
        assert len(h) == 64  # SHA-256 hex digest


class TestIsProcessed:
    def test_false_when_no_state_file(self, state_path: Path) -> None:
        assert not is_processed("abc123", state_path)

    def test_false_for_unknown_hash(self, state_path: Path) -> None:
        state_path.write_text(json.dumps({"known": {"pdf_name": "x.pdf"}}))
        assert not is_processed("unknown", state_path)

    def test_true_for_known_hash(self, state_path: Path) -> None:
        state_path.write_text(json.dumps({"abc123": {"pdf_name": "x.pdf"}}))
        assert is_processed("abc123", state_path)


class TestMarkProcessed:
    def test_creates_state_file(self, state_path: Path) -> None:
        mark_processed("hash1", "paper.pdf", state_path)
        assert state_path.exists()
        state = json.loads(state_path.read_text())
        assert "hash1" in state
        assert state["hash1"]["pdf_name"] == "paper.pdf"

    def test_records_timestamp(self, state_path: Path) -> None:
        mark_processed("hash1", "paper.pdf", state_path)
        state = json.loads(state_path.read_text())
        assert "processed_at" in state["hash1"]

    def test_records_note_file(self, state_path: Path) -> None:
        mark_processed("hash1", "paper.pdf", state_path, note_file="note.md")
        state = json.loads(state_path.read_text())
        assert state["hash1"]["note_file"] == "note.md"

    def test_omits_note_file_when_none(self, state_path: Path) -> None:
        mark_processed("hash1", "paper.pdf", state_path)
        state = json.loads(state_path.read_text())
        assert "note_file" not in state["hash1"]

    def test_appends_entries(self, state_path: Path) -> None:
        mark_processed("hash1", "a.pdf", state_path)
        mark_processed("hash2", "b.pdf", state_path)
        state = json.loads(state_path.read_text())
        assert len(state) == 2
        assert "hash1" in state
        assert "hash2" in state

    def test_idempotent_overwrite(self, state_path: Path) -> None:
        mark_processed("hash1", "paper.pdf", state_path)
        mark_processed("hash1", "paper.pdf", state_path, note_file="updated.md")
        state = json.loads(state_path.read_text())
        assert state["hash1"]["note_file"] == "updated.md"

    def test_roundtrip_with_is_processed(self, state_path: Path) -> None:
        assert not is_processed("hash1", state_path)
        mark_processed("hash1", "paper.pdf", state_path)
        assert is_processed("hash1", state_path)
