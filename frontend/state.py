from __future__ import annotations

import httpx
import streamlit as st

# from frontend.config import DEFAULT_API_BASE_URL, REQUEST_TIMEOUT_SECONDS
from config import DEFAULT_API_BASE_URL, REQUEST_TIMEOUT_SECONDS


def sanitize_base_url(url: str | None) -> str:
    """Ensure the API base URL always has a scheme; fall back to the default when empty."""
    url = (url or "").strip()
    if not url:
        return DEFAULT_API_BASE_URL
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url.rstrip("/")


def ensure_session_state() -> None:
    if "api_base_url" not in st.session_state:
        st.session_state.api_base_url = DEFAULT_API_BASE_URL
    if "http_client" not in st.session_state:
        st.session_state.http_client = httpx.Client(
            base_url=sanitize_base_url(st.session_state.api_base_url),
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "signup"


def reset_app_state() -> None:
    st.session_state.current_user = None
    st.session_state.thread_id = None
    st.session_state.chat_messages = []


def get_client() -> httpx.Client:
    ensure_session_state()
    client: httpx.Client = st.session_state.http_client
    base_url = sanitize_base_url(st.session_state.api_base_url)
    if str(client.base_url).rstrip("/") != base_url:
        client = httpx.Client(
            base_url=base_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        st.session_state.http_client = client
        reset_app_state()
    return client
