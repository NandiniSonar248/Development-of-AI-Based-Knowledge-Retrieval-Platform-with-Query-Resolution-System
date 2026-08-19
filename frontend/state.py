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
    if "access_token" not in st.session_state:
        st.session_state.access_token = ""
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = ""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "signup"


def store_auth_tokens(tokens: dict[str, str]) -> None:
    """Persist JWT tokens for API calls and browser WebSocket auth."""
    ensure_session_state()
    access = str(tokens.get("access_token", "") or "").strip()
    refresh = str(tokens.get("refresh_token", "") or "").strip()
    if access:
        st.session_state.access_token = access
    if refresh:
        st.session_state.refresh_token = refresh


def clear_auth_tokens() -> None:
    """Remove cached JWT tokens from session state."""
    st.session_state.access_token = ""
    st.session_state.refresh_token = ""


def get_access_token() -> str:
    """Return the current access token from session, httpx cookies, or browser cookies."""
    ensure_session_state()
    access = str(st.session_state.get("access_token", "") or "").strip()
    if access:
        return access

    client = get_client()
    cookie_access = client.cookies.get("access_token", "")
    if cookie_access:
        st.session_state.access_token = cookie_access
        return cookie_access

    try:
        from cookie_manager import get_tokens

        tokens = get_tokens() or {}
        browser_access = str(tokens.get("access_token", "") or "").strip()
        if browser_access:
            st.session_state.access_token = browser_access
            return browser_access
    except Exception:
        pass
    return ""


def reset_app_state() -> None:
    st.session_state.current_user = None
    st.session_state.thread_id = None
    st.session_state.chat_messages = []
    clear_auth_tokens()


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
