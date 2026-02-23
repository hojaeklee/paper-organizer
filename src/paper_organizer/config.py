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


def flatten_folders(folders: dict[str, Any], prefix: str = "") -> list[str]:
    """Recursively convert nested folder dict to slash-notation paths.

    >>> flatten_folders({"a": {"b": None, "c": {"d": None}}})
    ['a/b', 'a/c/d']
    """
    paths: list[str] = []
    for key, value in folders.items():
        current = f"{prefix}{key}" if not prefix else f"{prefix}/{key}"
        if isinstance(value, dict):
            paths.extend(flatten_folders(value, current))
        else:
            paths.append(current)
    return paths


def load_config(path: Path = Path("config.yaml")) -> Config:
    """Parse *path* and return a validated ``Config``."""
    raw = yaml.safe_load(path.read_text())

    for key in ("paperpile_dir", "obsidian_vault", "model", "taxonomy"):
        if key not in raw:
            raise ValueError(f"Missing required config key: {key}")

    model_raw = raw["model"]
    for key in ("provider", "name", "max_input_chars"):
        if key not in model_raw:
            raise ValueError(f"Missing required model config key: {key}")

    taxonomy_raw = raw["taxonomy"]
    for key in ("folders", "tags"):
        if key not in taxonomy_raw:
            raise ValueError(f"Missing required taxonomy config key: {key}")

    return Config(
        paperpile_dir=Path(raw["paperpile_dir"]).expanduser(),
        obsidian_vault=Path(raw["obsidian_vault"]).expanduser(),
        model=ModelConfig(
            provider=model_raw["provider"],
            name=model_raw["name"],
            max_input_chars=model_raw["max_input_chars"],
        ),
        taxonomy=TaxonomyConfig(
            folders=taxonomy_raw["folders"],
            tags=taxonomy_raw["tags"],
        ),
        notification_email=raw.get("notification_email"),
    )
