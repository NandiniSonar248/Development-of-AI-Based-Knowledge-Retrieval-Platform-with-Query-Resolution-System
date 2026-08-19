"""Voice UI helpers."""

from __future__ import annotations

import streamlit as st

import api_client
from voice_agent import VoiceWidgetResult, build_ws_url, listen_for_transcript

_INTERACTION_MODES = ("Text Chat", "Voice Agent")


def _format_interaction_mode_label(mode: str) -> str:
    labels = {
        "Text Chat": "💬  Text Chat",
        "Voice Agent": "🎙️  Voice Agent",
    }
    return labels.get(mode, mode)


def _inject_interaction_mode_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) {
            background: linear-gradient(155deg, #eef5fc 0%, #f7faff 48%, #ffffff 100%);
            border: none !important;
            border-radius: 18px;
            padding: 1rem 1.2rem 1.1rem;
            margin: 0 0 1rem;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.95),
                0 10px 30px rgba(10, 61, 110, 0.08);
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor)::before {
            content: "Interaction mode";
            display: block;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #1e6bb8;
            margin-bottom: 0.75rem;
        }

        #interaction-mode-anchor {
            display: none;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-testid="stSegmentedControl"] {
            width: 100%;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] {
            width: 100%;
            background: rgba(10, 61, 110, 0.07) !important;
            border: none !important;
            border-radius: 14px;
            padding: 5px;
            gap: 6px;
            box-shadow: inset 0 1px 2px rgba(10, 61, 110, 0.06);
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] > button {
            flex: 1 1 0;
            min-height: 2.65rem;
            border: none !important;
            border-radius: 11px !important;
            background: transparent !important;
            color: #355a7a !important;
            font-size: 0.94rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em;
            box-shadow: none !important;
            outline: none !important;
            transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] > button:hover {
            background: rgba(255, 255, 255, 0.72) !important;
            color: #0a3d6e !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] > button:active,
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] > button:focus,
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] > button:focus-visible {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] > button[aria-checked="true"],
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] > button[aria-selected="true"] {
            background: linear-gradient(135deg, #1e6bb8 0%, #0a3d6e 100%) !important;
            color: #ffffff !important;
            border: none !important;
            outline: none !important;
            box-shadow: 0 6px 16px rgba(10, 61, 110, 0.28) !important;
            transform: translateY(-1px);
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] > button[aria-checked="true"]:hover,
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-baseweb="button-group"] > button[aria-selected="true"]:hover {
            background: linear-gradient(135deg, #1e6bb8 0%, #0a3d6e 100%) !important;
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_mode_switch() -> str:
    _inject_interaction_mode_styles()

    with st.container(border=False):
        st.markdown('<div id="interaction-mode-anchor"></div>', unsafe_allow_html=True)
        mode = st.segmented_control(
            "Interaction mode",
            options=list(_INTERACTION_MODES),
            format_func=_format_interaction_mode_label,
            default="Text Chat",
            key="agent_mode",
            label_visibility="collapsed",
            width="stretch",
        )

    if mode in _INTERACTION_MODES:
        return mode
    return str(st.session_state.get("agent_mode", "Text Chat"))


def _ensure_voice_state() -> None:
    if "voice_active" not in st.session_state:
        st.session_state.voice_active = False
    if "voice_listen_token" not in st.session_state:
        st.session_state.voice_listen_token = 0
    if "voice_turn_token" not in st.session_state:
        st.session_state.voice_turn_token = 0


def schedule_voice_turn_continuation() -> None:
    """After an assistant reply, play TTS and resume listening while audio plays."""
    _ensure_voice_state()
    st.session_state.voice_active = True
    st.session_state.voice_turn_token = int(st.session_state.voice_turn_token) + 1
    st.rerun()


def render_voice_controls() -> bool:
    """Start/stop buttons for voice capture."""
    _ensure_voice_state()

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Start listening",
            type="primary",
            use_container_width=True,
            key="voice_start",
        ):
            st.session_state.voice_active = True
            st.session_state.voice_listen_token = int(st.session_state.voice_listen_token) + 1
            st.session_state.pop("voice_last_error", None)
            st.rerun()
    with col2:
        if st.button("Stop", use_container_width=True, key="voice_stop"):
            st.session_state.voice_active = False
            st.rerun()

    return True


def listen_for_voice_transcript(api_base_url: str, access_token: str) -> VoiceWidgetResult | None:
    """Mic/WebSocket widget; returns transcript or error details from the browser."""
    if not access_token:
        return None

    _ensure_voice_state()
    return listen_for_transcript(
        build_ws_url(api_base_url, access_token),
        active=bool(st.session_state.voice_active),
        listen_token=int(st.session_state.get("voice_listen_token", 0)),
        turn_token=int(st.session_state.get("voice_turn_token", 0)),
    )


def render_voice_agent(api_base_url: str, access_token: str) -> VoiceWidgetResult | None:
    if not access_token:
        st.warning("Sign in again from the home page to use voice mode.")
        return None

    render_voice_controls()
    return listen_for_voice_transcript(api_base_url, access_token)


def play_answer_audio(answer_text: str) -> None:
    cleaned = answer_text.strip()
    if not cleaned:
        return
    with st.spinner("Generating speech..."):
        audio = api_client.synthesize_speech(cleaned)
    st.audio(audio, format="audio/mpeg", autoplay=True)
