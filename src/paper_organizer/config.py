"""Load and validate config.yaml into frozen dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    name: str
    max_input_chars: int


@dataclass(frozen=True)
class TaxonomyConfig:
    folders: dict[str, Any]
    tags: list[str]


@dataclass(frozen=True)
class Config:
    paperpile_dir: Path
    obsidian_vault: Path
    model: ModelConfig
    taxonomy: TaxonomyConfig
    notification_email: str | None = None


def load_config(path: Path = Path("config.yaml")) -> Config:
    """Parse *path* and return a validated ``Config``."""
    raise NotImplementedError
