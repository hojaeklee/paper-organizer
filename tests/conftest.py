"""Shared fixtures for paper-organizer tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from paper_organizer.classify import Classification
from paper_organizer.config import Config, ModelConfig, TaxonomyConfig


@pytest.fixture
def sample_config() -> Config:
    return Config(
        paperpile_dir=Path("/tmp/papers"),
        obsidian_vault=Path("/tmp/vault"),
        model=ModelConfig(
            provider="anthropic",
            name="claude-haiku-4-5-20251001",
            max_input_chars=8000,
        ),
        taxonomy=TaxonomyConfig(
            folders={
                "deep_learning": {"computer_vision": None, "nlp": None},
                "reinforcement_learning": None,
            },
            tags=["transformer", "cnn", "survey", "benchmark"],
        ),
    )


@pytest.fixture
def sample_classification() -> Classification:
    return Classification(
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        folder="deep_learning/nlp",
        tags=["transformer", "benchmark"],
        one_line_summary="Introduces the Transformer architecture.",
    )
