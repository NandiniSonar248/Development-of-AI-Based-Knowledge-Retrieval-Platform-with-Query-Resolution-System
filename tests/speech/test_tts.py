"""ElevenLabs TTS tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.config import Settings
from app.speech.exceptions import SpeechAPIError
from app.speech.tts import FREE_TTS_VOICE_ID, synthesize_speech


@pytest.mark.asyncio
async def test_synthesize_returns_audio_bytes() -> None:
    settings = Settings(
        speech_enabled=True,
        elevenlabs_api_key="test-key",
        elevenlabs_voice_id="voice-123",
    )
    mock_response = httpx.Response(200, content=b"fake-mp3-bytes", request=httpx.Request("POST", "http://test"))

    with patch("app.speech.tts.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        audio = await synthesize_speech("Hello there.", settings=settings)

    assert audio == b"fake-mp3-bytes"


@pytest.mark.asyncio
async def test_synthesize_uses_default_voice_when_unset() -> None:
    settings = Settings(
        speech_enabled=True,
        elevenlabs_api_key="test-key",
        elevenlabs_voice_id="",
    )
    mock_response = httpx.Response(200, content=b"fake-mp3-bytes", request=httpx.Request("POST", "http://test"))

    with patch("app.speech.tts.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        audio = await synthesize_speech("Hello there.", settings=settings)

    assert audio == b"fake-mp3-bytes"
    assert FREE_TTS_VOICE_ID in str(mock_client.post.call_args)


@pytest.mark.asyncio
async def test_synthesize_falls_back_to_free_voice_on_library_error() -> None:
    settings = Settings(
        speech_enabled=True,
        elevenlabs_api_key="test-key",
        elevenlabs_voice_id="library-voice-id",
    )
    library_error = httpx.Response(
        403,
        json={"detail": {"message": "Free users cannot use library voices via the API."}},
        request=httpx.Request("POST", "http://test/library"),
    )
    ok_response = httpx.Response(200, content=b"fallback-mp3", request=httpx.Request("POST", "http://test/free"))

    with patch("app.speech.tts.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.side_effect = [library_error, ok_response]
        mock_client_cls.return_value = mock_client

        audio = await synthesize_speech("Hello there.", settings=settings)

    assert audio == b"fallback-mp3"
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_synthesize_raises_on_provider_error() -> None:
    settings = Settings(
        speech_enabled=True,
        elevenlabs_api_key="test-key",
        elevenlabs_voice_id="voice-123",
    )
    mock_response = httpx.Response(
        401,
        json={"detail": {"message": "Invalid API key"}},
        request=httpx.Request("POST", "http://test"),
    )

    with patch("app.speech.tts.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with pytest.raises(SpeechAPIError, match="Invalid API key"):
            await synthesize_speech("Hello there.", settings=settings)
