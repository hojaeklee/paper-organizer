"""Tests for LLM classification — prompt assembly and JSON parsing."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from paper_organizer.classify import (
    Classification,
    _build_system_prompt,
    _parse_json_response,
    classify,
    estimate_cost,
)


VALID_RESPONSE = {
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "folder": "deep_learning/nlp",
    "tags": ["transformer"],
    "one_line_summary": "Introduces the Transformer architecture.",
}


class TestBuildSystemPrompt:
    def test_includes_categories(self, sample_config) -> None:
        prompt = _build_system_prompt(sample_config)
        assert "deep_learning/computer_vision" in prompt
        assert "deep_learning/nlp" in prompt
        assert "reinforcement_learning" in prompt

    def test_includes_tags(self, sample_config) -> None:
        prompt = _build_system_prompt(sample_config)
        for tag in sample_config.taxonomy.tags:
            assert tag in prompt

    def test_includes_json_schema(self, sample_config) -> None:
        prompt = _build_system_prompt(sample_config)
        assert '"title"' in prompt
        assert '"authors"' in prompt
        assert '"folder"' in prompt


class TestParseJsonResponse:
    def test_valid_json(self) -> None:
        data = _parse_json_response(json.dumps(VALID_RESPONSE))
        assert data["title"] == "Attention Is All You Need"
        assert len(data["authors"]) == 2

    def test_strips_code_fences(self) -> None:
        fenced = f"```json\n{json.dumps(VALID_RESPONSE)}\n```"
        data = _parse_json_response(fenced)
        assert data["title"] == VALID_RESPONSE["title"]

    def test_strips_bare_fences(self) -> None:
        fenced = f"```\n{json.dumps(VALID_RESPONSE)}\n```"
        data = _parse_json_response(fenced)
        assert data["title"] == VALID_RESPONSE["title"]

    def test_raises_on_missing_keys(self) -> None:
        incomplete = {"title": "Test", "authors": []}
        with pytest.raises(ValueError, match="Missing keys"):
            _parse_json_response(json.dumps(incomplete))

    def test_raises_on_invalid_json(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            _parse_json_response("not json at all")

    def test_raises_if_authors_not_list(self) -> None:
        bad = {**VALID_RESPONSE, "authors": "single string"}
        with pytest.raises(ValueError, match="authors.*list"):
            _parse_json_response(json.dumps(bad))

    def test_raises_if_tags_not_list(self) -> None:
        bad = {**VALID_RESPONSE, "tags": "single string"}
        with pytest.raises(ValueError, match="tags.*list"):
            _parse_json_response(json.dumps(bad))


class TestClassify:
    def _mock_client(self, response_text: str) -> MagicMock:
        mock_content = MagicMock()
        mock_content.text = response_text
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        client = MagicMock()
        client.messages.create.return_value = mock_response
        return client

    def test_returns_classification(self, sample_config) -> None:
        client = self._mock_client(json.dumps(VALID_RESPONSE))
        result = classify("some paper text", sample_config, client=client)

        assert isinstance(result, Classification)
        assert result.title == "Attention Is All You Need"
        assert result.folder == "deep_learning/nlp"

    def test_truncates_input(self, sample_config) -> None:
        client = self._mock_client(json.dumps(VALID_RESPONSE))
        long_text = "x" * 20_000
        classify(long_text, sample_config, client=client)

        call_args = client.messages.create.call_args
        sent_text = call_args.kwargs["messages"][0]["content"]
        assert len(sent_text) == sample_config.model.max_input_chars

    def test_retries_on_bad_json(self, sample_config) -> None:
        bad_content = MagicMock()
        bad_content.text = "not json"
        good_content = MagicMock()
        good_content.text = json.dumps(VALID_RESPONSE)

        bad_resp = MagicMock()
        bad_resp.content = [bad_content]
        good_resp = MagicMock()
        good_resp.content = [good_content]

        client = MagicMock()
        client.messages.create.side_effect = [bad_resp, good_resp]

        result = classify("text", sample_config, client=client)
        assert result.title == "Attention Is All You Need"
        assert client.messages.create.call_count == 2

    def test_raises_after_retry_exhausted(self, sample_config) -> None:
        client = self._mock_client("not json")
        with pytest.raises(ValueError, match="Failed to parse"):
            classify("text", sample_config, client=client)


class TestEstimateCost:
    def test_returns_positive_float(self, sample_config) -> None:
        cost = estimate_cost(["some text"] * 5, sample_config)
        assert cost > 0
        assert isinstance(cost, float)

    def test_scales_with_count(self, sample_config) -> None:
        cost_one = estimate_cost(["text"], sample_config)
        cost_ten = estimate_cost(["text"] * 10, sample_config)
        assert cost_ten > cost_one
