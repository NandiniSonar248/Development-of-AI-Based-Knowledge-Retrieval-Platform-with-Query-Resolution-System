"""Speech API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SynthesizeRequest(BaseModel):
    """Text-to-speech request body."""

    text: str = Field(..., min_length=1)
    voice_id: str | None = None
