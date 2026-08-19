"""Realtime STT URL builder tests."""

from __future__ import annotations

from app.core.config import Settings
from app.speech.stt_realtime import _realtime_ws_url


def test_realtime_ws_url() -> None:
    settings = Settings(
        elevenlabs_base_url="https://api.elevenlabs.io/v1",
        elevenlabs_stt_realtime_model="scribe_v2_realtime",
        elevenlabs_stt_realtime_audio_format="pcm_16000",
        elevenlabs_stt_realtime_commit_strategy="vad",
        elevenlabs_stt_realtime_vad_silence_secs=1.0,
    )
    url = _realtime_ws_url(settings, scribe_token="sutkn_test")
    assert url.startswith("wss://api.elevenlabs.io/v1/speech-to-text/realtime?")
    assert "model_id=scribe_v2_realtime" in url
    assert "token=sutkn_test" in url
    assert "audio_format=pcm_16000" in url
