"""LLM-based paper classification."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import anthropic

from paper_organizer.config import Config, flatten_folders


@dataclass
class Classification:
    title: str
    authors: list[str]
    folder: str
    tags: list[str]
    one_line_summary: str


def _build_system_prompt(config: Config) -> str:
    """Build the system prompt with taxonomy context and JSON schema."""
    categories = flatten_folders(config.taxonomy.folders)
    tags = config.taxonomy.tags

    return f"""\
You are a research paper classifier. Given the extracted text of an academic paper,
return a JSON object with the following fields:

{{
  "title": "exact paper title",
  "authors": ["Author One", "Author Two"],
  "folder": "category/subcategory",
  "tags": ["tag1", "tag2"],
  "one_line_summary": "One sentence describing the paper's contribution."
}}

Rules:
- Extract the title and authors directly from the paper text.
- Pick the single best folder from the categories below, using slash notation.
- If no existing category fits, suggest a new one following the same slash notation convention.
- Assign 2-5 tags from the list below. You may combine tags from different groups.
- The summary should be one concise sentence.
- Return ONLY valid JSON, no markdown fences or extra text.

Available categories:
{chr(10).join(f"  - {c}" for c in categories)}

Available tags:
{chr(10).join(f"  - {t}" for t in tags)}"""


def _parse_json_response(raw: str) -> dict:
    """Strip optional code fences and parse JSON, validating required keys."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    data = json.loads(text)

    required = {"title", "authors", "folder", "tags", "one_line_summary"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Missing keys in LLM response: {missing}")

    return data


def classify(text: str, config: Config) -> Classification:
    """Send *text* to the configured LLM and return a ``Classification``."""
    truncated = text[: config.model.max_input_chars]
    client = anthropic.Anthropic()
    system_prompt = _build_system_prompt(config)

    last_error: Exception | None = None
    for _ in range(2):
        response = client.messages.create(
            model=config.model.name,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": truncated}],
        )
        raw = response.content[0].text
        try:
            data = _parse_json_response(raw)
            return Classification(
                title=data["title"],
                authors=data["authors"],
                folder=data["folder"],
                tags=data["tags"],
                one_line_summary=data["one_line_summary"],
            )
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            last_error = exc

    raise ValueError(f"Failed to parse LLM response after retry: {last_error}")


def estimate_cost(texts: list[str], config: Config) -> float:
    """Estimate the API cost in USD for classifying *texts*.

    Uses ~4 chars/token heuristic and Haiku pricing
    ($0.80/M input, $4.00/M output tokens).
    """
    system_prompt = _build_system_prompt(config)
    system_tokens = len(system_prompt) / 4

    total_input_tokens = 0.0
    total_output_tokens = 0.0
    for text in texts:
        truncated = text[: config.model.max_input_chars]
        input_tokens = system_tokens + len(truncated) / 4
        total_input_tokens += input_tokens
        total_output_tokens += 200  # estimated output per paper

    input_cost = (total_input_tokens / 1_000_000) * 0.80
    output_cost = (total_output_tokens / 1_000_000) * 4.00
    return input_cost + output_cost
