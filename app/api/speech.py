"""Speech-to-text and text-to-speech API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from fastapi.responses import Response

from app.auth.dependencies import get_current_user
from app.auth.jwt import JWTService, TokenError
from app.core.config import Settings, get_settings
from app.schemas.auth import UserPublic
from app.schemas.speech import SynthesizeRequest
from app.speech.exceptions import SpeechAPIError, SpeechConfigError
from app.speech.stt_realtime import proxy_realtime_transcription
from app.speech.tts import synthesize_speech

router = APIRouter(prefix="/speech", tags=["speech"])


def _ws_user_id(websocket: WebSocket, settings: Settings) -> UUID:
    token = websocket.query_params.get("token", "").strip() or websocket.cookies.get(
        settings.access_cookie_name, ""
    )
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")
    try:
        payload = JWTService(settings).decode_token(token, expected_type="access")
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc
    return UUID(str(payload["sub"]))


@router.websocket("/transcribe/stream")
async def transcribe_stream(websocket: WebSocket) -> None:
    """Proxy browser mic audio to ElevenLabs Scribe realtime STT."""
    settings = get_settings()
    try:
        _ws_user_id(websocket, settings)
    except HTTPException as exc:
        await websocket.close(code=4401, reason=str(exc.detail)[:120])
        return

    await websocket.accept()
    try:
        await proxy_realtime_transcription(websocket, settings)
    except SpeechConfigError as exc:
        await websocket.close(code=4403, reason=str(exc)[:120])
    except Exception as exc:
        await websocket.close(code=1011, reason=str(exc)[:120])


@router.post("/synthesize")
async def synthesize_endpoint(
    body: SynthesizeRequest,
    _user: UserPublic = Depends(get_current_user),
) -> Response:
    """Convert answer text to MP3 via ElevenLabs TTS."""
    try:
        audio = await synthesize_speech(body.text, voice_id=body.voice_id)
        return Response(content=audio, media_type="audio/mpeg")
    except SpeechConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SpeechAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
