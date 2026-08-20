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
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 0 0.85rem !important;
            margin: 0 0 0.35rem !important;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor)::before {
            content: "Interaction mode";
            display: block;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #1e6bb8;
            margin-bottom: 0.45rem;
        }

        #interaction-mode-anchor {
            display: none;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) [data-testid="stButtonGroup"] {
            width: 100%;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) .react-aria-ToggleButtonGroup {
            width: 100%;
            display: flex !important;
            gap: 0 !important;
            background: rgba(255, 255, 255, 0.72) !important;
            border: 1px solid rgba(10, 61, 110, 0.1) !important;
            border-radius: 14px !important;
            padding: 4px !important;
            box-shadow: 0 8px 20px rgba(10, 61, 110, 0.05) !important;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"] {
            flex: 1 1 0 !important;
            min-height: 2.55rem !important;
            margin: 0 !important;
            border: 1px solid transparent !important;
            border-radius: 10px !important;
            background: transparent !important;
            color: #475569 !important;
            font-size: 0.94rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em;
            box-shadow: none !important;
            outline: none !important;
            transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"]:hover,
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"][data-hovered="true"] {
            background: rgba(255, 255, 255, 0.88) !important;
            color: #0a3d6e !important;
            border-color: rgba(10, 61, 110, 0.08) !important;
            box-shadow: none !important;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"]:focus,
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"]:focus-visible,
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"][data-focus-visible="true"] {
            border-color: rgba(30, 107, 184, 0.35) !important;
            outline: none !important;
            box-shadow: none !important;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"][data-selected="true"],
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"][kind="segmented_controlActive"] {
            background: linear-gradient(135deg, #1e6bb8 0%, #0a3d6e 100%) !important;
            color: #ffffff !important;
            border-color: transparent !important;
            outline: none !important;
            box-shadow: 0 6px 16px rgba(10, 61, 110, 0.22) !important;
        }

        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"][data-selected="true"]:hover,
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"][data-selected="true"][data-hovered="true"],
        [data-testid="stVerticalBlock"]:has(#interaction-mode-anchor) button[data-variant="segmented_control"][kind="segmented_controlActive"]:hover {
            background: linear-gradient(135deg, #1e6bb8 0%, #0a3d6e 100%) !important;
            color: #ffffff !important;
            border-color: transparent !important;
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
