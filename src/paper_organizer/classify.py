"""LLM-based paper classification."""

from __future__ import annotations

from dataclasses import dataclass

from paper_organizer.config import Config


@dataclass
class Classification:
    title: str
    authors: list[str]
    folder: str
    tags: list[str]
    one_line_summary: str


def classify(text: str, config: Config) -> Classification:
    """Send *text* to the configured LLM and return a ``Classification``."""
    raise NotImplementedError


def estimate_cost(texts: list[str], config: Config) -> float:
    """Estimate the API cost in USD for classifying *texts*."""
    raise NotImplementedError
