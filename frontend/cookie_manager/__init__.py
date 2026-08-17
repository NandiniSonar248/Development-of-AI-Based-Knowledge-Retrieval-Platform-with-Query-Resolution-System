from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

_COOKIE_MANAGER_DIR = Path(__file__).parent


@st.cache_resource
def _get_cookie_manager() -> Any:
    """Return the cached custom component instance."""
    return components.declare_component("cookie_manager", path=str(_COOKIE_MANAGER_DIR))


def get_tokens() -> dict[str, str] | None:
    """Read access/refresh tokens from browser cookies (via the component)."""
    value = _get_cookie_manager()()
    if isinstance(value, dict):
        tokens = {k: str(v) for k, v in value.items() if v}
        return tokens or None
    return None


def set_tokens(access_token: str, refresh_token: str) -> None:
    """Persist token cookies in the browser."""
    _get_cookie_manager()(
        set_tokens={"access_token": access_token, "refresh_token": refresh_token},
        clear=False,
    )


def clear_tokens() -> None:
    """Remove token cookies from the browser."""
    _get_cookie_manager()(clear=True)