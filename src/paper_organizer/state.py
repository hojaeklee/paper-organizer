"""Processed-file tracking via content hashing."""

from __future__ import annotations

from pathlib import Path


def content_hash(pdf_path: Path, chunk_size: int = 65536) -> str:
    """Return the SHA-256 hex digest of the first *chunk_size* bytes."""
    raise NotImplementedError


def is_processed(hash_value: str, state_path: Path) -> bool:
    """Check whether *hash_value* is already recorded in *state_path*."""
    raise NotImplementedError


def mark_processed(hash_value: str, pdf_name: str, state_path: Path) -> None:
    """Append *hash_value* to the processed log at *state_path*."""
    raise NotImplementedError
