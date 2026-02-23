"""Obsidian markdown note generation."""

from __future__ import annotations

from pathlib import Path

from paper_organizer.classify import Classification


def generate_note(classification: Classification, date_added: str) -> str:
    """Return the full markdown content for an Obsidian note."""
    raise NotImplementedError


def write_note(content: str, dest: Path) -> None:
    """Write *content* to *dest*, refusing to overwrite an existing file."""
    raise NotImplementedError
