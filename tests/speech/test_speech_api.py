"""Speech API route tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.speech import router
from app.auth.dependencies import get_current_user
from app.schemas.auth import UserPublic


def test_synthesize_route_returns_audio() -> None:
    user = UserPublic(id=uuid4(), name="Rahul", email="rahul@gmail.com")
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: user

    with patch("app.api.speech.synthesize_speech", new=AsyncMock(return_value=b"fake-mp3-bytes")):
        client = TestClient(app)
        response = client.post("/speech/synthesize", json={"text": "Hello there."})

    assert response.status_code == 200
    assert response.content == b"fake-mp3-bytes"
    assert response.headers["content-type"].startswith("audio/mpeg")
