"""Obsidian markdown note generation."""

from __future__ import annotations

import re
from pathlib import Path

from paper_organizer.classify import Classification

FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*]')
MAX_FILENAME_LEN = 200


def sanitize_filename(title: str) -> str:
    """Strip forbidden chars, collapse whitespace, truncate to safe length."""
    name = FORBIDDEN_CHARS.sub("", title)
    name = re.sub(r"\s+", " ", name).strip()
    name = name[:MAX_FILENAME_LEN]
    return name if name else "untitled"


def generate_note(
    classification: Classification,
    pdf_filename: str,
    date_added: str,
) -> str:
    """Return the full markdown content for an Obsidian note."""
    c = classification

    title_escaped = c.title.replace('"', '\\"')
    summary_escaped = c.one_line_summary.replace('"', '\\"')

    authors_yaml = "\n".join(f'  - "[[{a}]]"' for a in c.authors)
    tags_yaml = "\n".join(f"  - {t}" for t in c.tags)

    return f"""\
---
title: "{title_escaped}"
authors:
{authors_yaml}
doi: ""
rating:
category: {c.folder}
tags:
{tags_yaml}
summary: "{summary_escaped}"
date_added: {date_added}
---

# [[{pdf_filename}|{c.title}]]

> [!tldr] Critical Summary
> Write summary here
"""


def write_note(content: str, dest: Path) -> None:
    """Write *content* to *dest*, refusing to overwrite an existing file."""
    if dest.exists():
        raise FileExistsError(f"Note already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
