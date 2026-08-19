"""ElevenLabs text-to-speech client."""

from __future__ import annotations

import httpx

from app.core.config import Settings, get_settings
from app.speech.exceptions import SpeechAPIError, SpeechConfigError

# Premade voice that works on ElevenLabs free-tier API (Voice Library IDs are blocked).
FREE_TTS_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"


def _headers(settings: Settings) -> dict[str, str]:
    return {"xi-api-key": settings.elevenlabs_api_key}


def _parse_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
        detail = payload.get("detail")
        if isinstance(detail, dict) and detail.get("message"):
            return str(detail["message"])
        if isinstance(detail, str):
            return detail
        if payload.get("message"):
            return str(payload["message"])
    except Exception:
        pass
    return response.text or f"ElevenLabs request failed ({response.status_code})"


def _is_library_voice_error(message: str) -> bool:
    lowered = message.lower()
    return "library voice" in lowered or "upgrade your subscription" in lowered


def _resolve_voice_id(voice_id: str | None, settings: Settings) -> str:
    configured = (voice_id or settings.elevenlabs_voice_id or FREE_TTS_VOICE_ID).strip()
    return configured or FREE_TTS_VOICE_ID


async def synthesize_speech(text: str, voice_id: str | None = None, settings: Settings | None = None) -> bytes:
    """Convert text to MP3 bytes via ElevenLabs TTS."""
    cfg = settings or get_settings()
    if not cfg.speech_enabled:
        raise SpeechConfigError("Speech is disabled. Set SPEECH_ENABLED=true.")
    if not cfg.elevenlabs_api_key.strip():
        raise SpeechConfigError("ELEVENLABS_API_KEY is required.")

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Text is required for speech synthesis.")
    if len(cleaned) > cfg.speech_max_tts_chars:
        raise ValueError(f"Text exceeds the {cfg.speech_max_tts_chars} character limit.")

    resolved_voice = _resolve_voice_id(voice_id, cfg)
    base = cfg.elevenlabs_base_url.rstrip("/")
    headers = {**_headers(cfg), "Content-Type": "application/json", "Accept": "audio/mpeg"}
    body = {"text": cleaned, "model_id": cfg.elevenlabs_tts_model}
    params = {"output_format": cfg.elevenlabs_tts_output_format}

    async with httpx.AsyncClient(timeout=cfg.speech_request_timeout_seconds) as client:
        url = f"{base}/text-to-speech/{resolved_voice}"
        response = await client.post(url, headers=headers, params=params, json=body)

        if not response.is_success:
            error = _parse_error(response)
            if _is_library_voice_error(error) and resolved_voice != FREE_TTS_VOICE_ID:
                fallback_url = f"{base}/text-to-speech/{FREE_TTS_VOICE_ID}"
                response = await client.post(fallback_url, headers=headers, params=params, json=body)

    if not response.is_success:
        raise SpeechAPIError(_parse_error(response))
    if not response.content:
        raise SpeechAPIError("ElevenLabs TTS returned empty audio.")
    return response.content
