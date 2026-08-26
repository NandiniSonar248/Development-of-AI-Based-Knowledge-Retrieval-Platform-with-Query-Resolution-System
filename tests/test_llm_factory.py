"""Unit tests for the multi-provider LLM factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings, resolve_ollama_reasoning, resolve_structured_output_method
from app.llm.exceptions import LLMConfigError
from app.llm.factory import create_chat_llm


def test_create_chat_llm_ollama() -> None:
    settings = Settings(llm_provider="ollama", llm_model="granite4.1:8b")
    with patch("app.llm.factory.create_ollama_chat_llm") as mock_ollama:
        mock_ollama.return_value = MagicMock(name="ChatOllama")
        llm = create_chat_llm(settings)
        mock_ollama.assert_called_once_with(settings)
        assert llm is mock_ollama.return_value


def test_create_chat_llm_openai() -> None:
    settings = Settings(
        llm_provider="openai",
        openai_api_key="sk-test",
        openai_model="gpt-4o-mini",
    )
    with patch("app.llm.factory.create_openai_chat_llm") as mock_openai:
        mock_openai.return_value = MagicMock(name="ChatOpenAI")
        llm = create_chat_llm(settings)
        mock_openai.assert_called_once_with(settings)
        assert llm is mock_openai.return_value


def test_create_chat_llm_unknown_provider() -> None:
    # A Literal field rejects unknown providers at construction, so the invalid
    # value has to reach the factory through a stand-in object.
    settings_mock = MagicMock(spec=Settings)
    settings_mock.llm_provider = "anthropic"
    with pytest.raises(LLMConfigError, match="Unsupported LLM_PROVIDER"):
        create_chat_llm(settings_mock)


def test_openai_requires_api_key() -> None:
    from app.llm.openai_client import create_openai_chat_llm

    settings = Settings(llm_provider="openai", openai_api_key="")
    with pytest.raises(LLMConfigError, match="OPENAI_API_KEY"):
        create_openai_chat_llm(settings)


def test_openai_builds_chat_openai() -> None:
    from app.llm.openai_client import create_openai_chat_llm

    settings = Settings(
        llm_provider="openai",
        openai_api_key="sk-test-key",
        openai_model="gpt-4o-mini",
        llm_temperature=0.0,
    )
    with patch("app.llm.openai_client.ChatOpenAI") as mock_cls:
        mock_cls.return_value = MagicMock()
        create_openai_chat_llm(settings)
        mock_cls.assert_called_once_with(
            model="gpt-4o-mini",
            api_key="sk-test-key",
            base_url="https://api.openai.com/v1",
            temperature=0.0,
        )


def test_resolve_defaults_for_granite() -> None:
    settings = Settings(llm_provider="ollama", llm_model="granite4.1:8b")
    assert resolve_ollama_reasoning(settings) is None
    assert resolve_structured_output_method(settings) == "json_schema"


def test_resolve_auto_for_gpt_oss() -> None:
    settings = Settings(llm_provider="ollama", llm_model="gpt-oss:20b-cloud")
    assert resolve_ollama_reasoning(settings) == "low"
    assert resolve_structured_output_method(settings) == "function_calling"


def test_resolve_respects_explicit_overrides() -> None:
    settings = Settings(
        llm_provider="ollama",
        llm_model="gpt-oss:20b-cloud",
        llm_reasoning="high",
        llm_structured_output_method="json_schema",
    )
    assert resolve_ollama_reasoning(settings) == "high"
    assert resolve_structured_output_method(settings) == "json_schema"


def test_ollama_gpt_oss_passes_reasoning() -> None:
    from app.llm.ollama_client import create_ollama_chat_llm

    settings = Settings(llm_provider="ollama", llm_model="gpt-oss:20b-cloud")
    with patch("app.llm.ollama_client.ChatOllama") as mock_cls:
        mock_cls.return_value = MagicMock()
        create_ollama_chat_llm(settings)
        kwargs = mock_cls.call_args.kwargs
        assert kwargs["model"] == "gpt-oss:20b-cloud"
        assert kwargs["reasoning"] == "low"


def test_ollama_granite_omits_reasoning() -> None:
    from app.llm.ollama_client import create_ollama_chat_llm

    settings = Settings(llm_provider="ollama", llm_model="granite4.1:8b")
    with patch("app.llm.ollama_client.ChatOllama") as mock_cls:
        mock_cls.return_value = MagicMock()
        create_ollama_chat_llm(settings)
        kwargs = mock_cls.call_args.kwargs
        assert "reasoning" not in kwargs
