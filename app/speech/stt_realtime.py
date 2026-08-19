"""ElevenLabs realtime STT WebSocket proxy."""

from __future__ import annotations

import asyncio
import json
from urllib.parse import urlencode

import httpx
import websockets
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.core.config import Settings
from app.speech.exceptions import SpeechAPIError, SpeechConfigError


def _realtime_ws_url(settings: Settings, *, scribe_token: str) -> str:
    base = settings.elevenlabs_base_url.rstrip("/")
    ws_base = base.replace("https://", "wss://").replace("http://", "ws://")
    query = urlencode(
        {
            "model_id": settings.elevenlabs_stt_realtime_model,
            "token": scribe_token,
            "audio_format": settings.elevenlabs_stt_realtime_audio_format,
            "commit_strategy": settings.elevenlabs_stt_realtime_commit_strategy,
            "vad_silence_threshold_secs": settings.elevenlabs_stt_realtime_vad_silence_secs,
        }
    )
    return f"{ws_base}/speech-to-text/realtime?{query}"


def _validate(settings: Settings) -> None:
    if not settings.speech_enabled:
        raise SpeechConfigError("Speech is disabled. Set SPEECH_ENABLED=true.")
    if not settings.elevenlabs_api_key.strip():
        raise SpeechConfigError("ELEVENLABS_API_KEY is required.")


def _parse_elevenlabs_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
        detail = payload.get("detail")
        if isinstance(detail, dict):
            message = str(detail.get("message") or "").strip()
            code = str(detail.get("code") or "").strip()
            if code == "invalid_api_key" and "API key ID" in message:
                return (
                    "ELEVENLABS_API_KEY looks like an API key ID, not a secret key. "
                    "Copy the full key from ElevenLabs (Profile → API keys)."
                )
            if message:
                return message
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
    except Exception:
        pass
    return response.text or f"HTTP {response.status_code}"


async def _create_scribe_token(settings: Settings) -> str:
    """Mint a single-use ElevenLabs realtime scribe token for the WebSocket connection."""
    url = f"{settings.elevenlabs_base_url.rstrip('/')}/single-use-token/realtime_scribe"
    headers = {"xi-api-key": settings.elevenlabs_api_key}
    async with httpx.AsyncClient(timeout=settings.speech_request_timeout_seconds) as client:
        response = await client.post(url, headers=headers)

    if response.status_code in {401, 403}:
        raise SpeechConfigError(_parse_elevenlabs_error(response))
    if not response.is_success:
        raise SpeechAPIError(f"Could not create ElevenLabs scribe token: {_parse_elevenlabs_error(response)}")

    token = response.json().get("token")
    if not token:
        raise SpeechAPIError("ElevenLabs did not return a realtime scribe token.")
    return str(token)


async def _client_to_elevenlabs(client_ws: WebSocket, elevenlabs_ws: websockets.ClientConnection) -> None:
    try:
        while True:
            message = await client_ws.receive_text()
            payload = json.loads(message)
            if payload.get("message_type") == "input_audio_chunk":
                await elevenlabs_ws.send(message)
    except WebSocketDisconnect:
        return


async def _elevenlabs_to_client(client_ws: WebSocket, elevenlabs_ws: websockets.ClientConnection) -> None:
    try:
        async for message in elevenlabs_ws:
            await client_ws.send_text(message)
    except WebSocketDisconnect:
        return


async def proxy_realtime_transcription(client_ws: WebSocket, settings: Settings) -> None:
    """Relay browser audio chunks to ElevenLabs and stream transcript events back."""
    _validate(settings)
    try:
        scribe_token = await _create_scribe_token(settings)
    except (SpeechConfigError, SpeechAPIError) as exc:
        await client_ws.send_text(json.dumps({"message_type": "auth_error", "error": str(exc)}))
        return

    async with websockets.connect(
        _realtime_ws_url(settings, scribe_token=scribe_token),
        open_timeout=settings.speech_request_timeout_seconds,
    ) as elevenlabs_ws:
        await asyncio.gather(
            _client_to_elevenlabs(client_ws, elevenlabs_ws),
            _elevenlabs_to_client(client_ws, elevenlabs_ws),
        )
