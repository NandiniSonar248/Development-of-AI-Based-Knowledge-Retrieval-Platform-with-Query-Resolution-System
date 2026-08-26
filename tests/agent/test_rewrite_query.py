"""Unit tests for query rewrite structured-output fallback."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage

from app.agents.nodes import _parse_query_analysis, rewrite_query
from app.agents.schemas import QueryAnalysis


def test_parse_query_analysis_uses_parsed_model() -> None:
    parsed = QueryAnalysis(
        is_clear=True,
        questions=["What is PTO?"],
        clarification_needed="",
    )
    result = _parse_query_analysis({"raw": None, "parsed": parsed, "parsing_error": None}, "ignored")
    assert result is parsed


def test_parse_query_analysis_falls_back_on_invalid_json() -> None:
    result = _parse_query_analysis(
        {"raw": None, "parsed": None, "parsing_error": ValueError("Invalid json output")},
        "What is the leave policy?",
    )
    assert result.is_clear is True
    assert result.questions == ["What is the leave policy?"]


def test_rewrite_query_falls_back_when_parser_raises() -> None:
    llm = MagicMock()
    llm.model_copy.return_value = llm
    structured = MagicMock()
    structured.invoke.side_effect = ValueError("Invalid json output: Query unclear.")
    llm.with_structured_output.return_value = structured
    state = {"messages": [HumanMessage(content="What is the leave policy?")]}

    with patch("app.agents.nodes.resolve_structured_output_method", return_value="function_calling"):
        with patch("app.agents.nodes.log_error"):
            result = rewrite_query(state, llm)

    assert result["questionIsClear"] is True
    assert result["rewrittenQuestions"] == ["What is the leave policy?"]
    llm.with_structured_output.assert_called_once_with(
        QueryAnalysis, method="function_calling", include_raw=True
    )
