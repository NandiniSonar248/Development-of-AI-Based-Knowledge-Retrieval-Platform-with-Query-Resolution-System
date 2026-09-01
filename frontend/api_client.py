from __future__ import annotations

from typing import Any

import httpx

# from frontend.state import get_client
from state import get_client, get_access_token


class FrontendAPIError(Exception):
    """Raised when the backend returns an error response."""


def _auth_headers() -> dict[str, str]:
    """Attach JWT cookies when the httpx jar is empty (common on Streamlit Cloud)."""
    import streamlit as st

    cookies: list[str] = []
    access = get_access_token()
    refresh = str(st.session_state.get("refresh_token", "") or "").strip()
    if access:
        cookies.append(f"access_token={access}")
    if refresh:
        cookies.append(f"refresh_token={refresh}")
    if not cookies:
        return {}
    return {"Cookie": "; ".join(cookies)}


def _raise_for_error(response: httpx.Response) -> None:
    if response.is_success:
        return
    detail: str
    try:
        payload = response.json()
        detail = payload.get("detail") or payload.get("message") or response.text
    except Exception:
        detail = response.text
    raise FrontendAPIError(detail or f"Request failed with status {response.status_code}")


def _extract_tokens(response: httpx.Response) -> dict[str, str]:
    tokens: dict[str, str] = {}
    access = response.cookies.get("access_token")
    refresh = response.cookies.get("refresh_token")
    if access:
        tokens["access_token"] = access
    if refresh:
        tokens["refresh_token"] = refresh
    if tokens:
        from state import store_auth_tokens

        store_auth_tokens(tokens)
    return tokens


def signup(name: str, email: str, password: str) -> tuple[dict[str, Any], dict[str, str]]:
    response = get_client().post(
        "/auth/signup",
        json={"name": name, "email": email, "password": password},
    )
    _raise_for_error(response)
    return response.json(), _extract_tokens(response)


def login(email: str, password: str) -> tuple[dict[str, Any], dict[str, str]]:
    response = get_client().post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    _raise_for_error(response)
    return response.json(), _extract_tokens(response)


def logout() -> dict[str, Any]:
    response = get_client().post("/auth/logout")
    _raise_for_error(response)
    return response.json()


def restore_session(refresh_token: str) -> tuple[dict[str, Any], dict[str, str]]:
    """Refresh the token pair from a stored refresh token, then fetch the user."""
    response = get_client().post(
        "/auth/refresh",
        headers={"Cookie": f"refresh_token={refresh_token}"},
    )
    _raise_for_error(response)
    tokens = _extract_tokens(response)
    me_response = get_client().get("/auth/me")
    _raise_for_error(me_response)
    return me_response.json(), tokens


def list_documents() -> list[str]:
    response = get_client().get("/upload/documents")
    _raise_for_error(response)
    return response.json()


def upload_documents(files: list[tuple[str, bytes, str]]) -> dict[str, Any]:
    multipart_files = [
        ("files", (filename, content, content_type))
        for filename, content, content_type in files
    ]
    response = get_client().post("/upload", files=multipart_files)
    _raise_for_error(response)
    return response.json()


def clear_documents() -> dict[str, Any]:
    response = get_client().delete("/upload")
    _raise_for_error(response)
    return response.json()


def ask_question(question: str, thread_id: str | None) -> dict[str, Any]:
    response = get_client().post(
        "/query",
        json={"question": question, "thread_id": thread_id},
        headers=_auth_headers(),
    )
    _raise_for_error(response)
    return response.json()


def reset_chat() -> dict[str, Any]:
    response = get_client().post("/query/reset", headers=_auth_headers())
    _raise_for_error(response)
    return response.json()


def synthesize_speech(text: str, voice_id: str | None = None) -> bytes:
    payload: dict[str, Any] = {"text": text}
    if voice_id:
        payload["voice_id"] = voice_id
    response = get_client().post("/speech/synthesize", json=payload, headers=_auth_headers())
    _raise_for_error(response)
    return response.content


def record_query(question: str, answer: str, confidence: float) -> dict[str, Any]:
    response = get_client().post(
        "/analytics/records",
        json={"question": question, "answer": answer, "confidence": confidence},
    )
    _raise_for_error(response)
    return response.json()


def get_analytics_summary() -> dict[str, Any]:
    response = get_client().get("/analytics/summary")
    _raise_for_error(response)
    return response.json()


def get_recent_queries(limit: int = 50) -> list[dict[str, Any]]:
    response = get_client().get("/analytics/recent", params={"limit": limit})
    _raise_for_error(response)
    return response.json()
