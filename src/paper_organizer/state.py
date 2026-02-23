"""Processed-file tracking via content hashing."""

from __future__ import annotations

import fcntl
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def content_hash(pdf_path: Path, chunk_size: int = 65536) -> str:
    """Return the SHA-256 hex digest of the first *chunk_size* bytes."""
    with open(pdf_path, "rb") as f:
        data = f.read(chunk_size)
    return hashlib.sha256(data).hexdigest()


def _load_state(state_path: Path) -> dict[str, Any]:
    """Load the processed-papers JSON, returning ``{}`` if file is missing."""
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text())


def is_processed(hash_value: str, state_path: Path) -> bool:
    """Check whether *hash_value* is already recorded in *state_path*."""
    return hash_value in _load_state(state_path)


def mark_processed(
    hash_value: str,
    pdf_name: str,
    state_path: Path,
    *,
    note_file: str | None = None,
) -> None:
    """Append *hash_value* to the processed log at *state_path*."""
    lock_path = state_path.with_suffix(".lock")
    with open(lock_path, "w") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        state = _load_state(state_path)
        entry: dict[str, str] = {
            "pdf_name": pdf_name,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        if note_file is not None:
            entry["note_file"] = note_file
        state[hash_value] = entry
        state_path.write_text(json.dumps(state, indent=2) + "\n")
