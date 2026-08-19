from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import streamlit.components.v2 as components_v2

_COMPONENT_DIR = Path(__file__).parent


def _read(name: str) -> str:
    return (_COMPONENT_DIR / name).read_text(encoding="utf-8")


_voice_agent = components_v2.component(
    "voice_agent_mic",
    html=_read("mic.html"),
    css=_read("mic.css"),
    js=_read("mic.js"),
)


@dataclass(frozen=True)
class VoiceWidgetResult:
    transcript: str | None = None
    transcript_id: int | None = None
    partial: str | None = None
    error: str | None = None


def build_ws_url(api_base_url: str, access_token: str) -> str:
    base = api_base_url.rstrip("/")
    ws_base = base.replace("https://", "wss://").replace("http://", "ws://")
    return f"{ws_base}/speech/transcribe/stream?token={quote(access_token, safe='')}"


def listen_for_transcript(
    ws_url: str,
    *,
    active: bool,
    listen_token: int = 0,
    turn_token: int = 0,
) -> VoiceWidgetResult | None:
    """Run the mic/WebSocket widget when active; return transcript or error events."""
    result: Any = _voice_agent(
        data={
            "ws_url": ws_url,
            "active": active,
            "listen_token": listen_token,
            "turn_token": turn_token,
        },
        key="voice_agent_mic",
        on_partial_change=lambda: None,
        on_transcript_change=lambda: None,
        on_error_change=lambda: None,
    )

    error = str(getattr(result, "error", "") or "").strip()
    if error:
        return VoiceWidgetResult(error=error)

    raw_transcript = getattr(result, "transcript", None)
    if raw_transcript:
        try:
            payload = json.loads(str(raw_transcript))
            text = str(payload.get("text", "")).strip()
            result_id = payload.get("id")
            if text and result_id is not None:
                return VoiceWidgetResult(transcript=text, transcript_id=int(result_id))
        except (json.JSONDecodeError, TypeError, ValueError):
            text = str(raw_transcript).strip()
            if text:
                return VoiceWidgetResult(transcript=text, transcript_id=0)

    partial = str(getattr(result, "partial", "") or "").strip()
    if partial:
        return VoiceWidgetResult(partial=partial)

    return None
