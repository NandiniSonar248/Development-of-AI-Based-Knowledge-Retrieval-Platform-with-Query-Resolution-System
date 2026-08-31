from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import api_client
from api_client import FrontendAPIError
from chat_flow import process_user_prompt
from state import ensure_session_state, get_access_token, sanitize_base_url
from ui import apply_theme, render_page_header, render_response_details, render_sidebar, require_auth
from voice_ui import (
    listen_for_voice_transcript,
    play_answer_audio,
    render_mode_switch,
    render_voice_controls,
)

GREETING = (
    "👋 Hello! I'm your Knowledge Assistant.\n\n"
    "Ask me anything about your uploaded documents, policies, manuals, or FAQs. "
    "I'll find the relevant information and provide a clear answer with sources and confidence.\n\n"
    "How can I help you today?"
)

VOICE_GREETING = (
    "🎙️ **Voice Agent** — press **Start listening**, ask your question, then pause briefly. "
    "While the answer plays you can keep listening or pause it and ask a follow-up anytime."
)

ensure_session_state()
apply_theme()
render_sidebar()
require_auth()

render_page_header(
    "Knowledge Assistant",
    "Ask questions about your uploaded documents and get grounded answers with citations and confidence scores.",
)

mode = render_mode_switch()

if st.button("Reset chat"):
    try:
        reset_payload = api_client.reset_chat()
        st.session_state.thread_id = reset_payload.get("thread_id")
    except FrontendAPIError as exc:
        st.error(f"Could not reset chat: {exc}")
    st.session_state.chat_messages = []
    st.session_state.pop("last_voice_transcript_id", None)
    st.session_state.pop("voice_partial", None)
    st.session_state.voice_turn_token = 0
    st.session_state.voice_active = False
    st.rerun()

voice_token: str | None = None
if mode == "Voice Agent":
    voice_token = get_access_token()
    if not voice_token:
        st.warning("Sign in again from the home page to use voice mode.")
    else:
        render_voice_controls()

if not st.session_state.chat_messages:
    greeting = VOICE_GREETING if mode == "Voice Agent" else GREETING
    with st.chat_message("assistant"):
        st.markdown(greeting)

for index, message in enumerate(st.session_state.chat_messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "response" in message:
            render_response_details(message["response"])
            audio_bytes = message.get("audio_bytes")
            if mode == "Voice Agent" and audio_bytes:
                is_latest_assistant = index == len(st.session_state.chat_messages) - 1
                st.audio(
                    audio_bytes,
                    format="audio/mpeg",
                    autoplay=is_latest_assistant,
                )
            elif mode == "Text Chat" and message.get("content"):
                if st.button("Read aloud", key=f"read_aloud_{index}"):
                    play_answer_audio(message["content"])

if mode == "Text Chat":
    prompt = st.chat_input("Ask a question about your documents")
    if prompt:
        process_user_prompt(prompt, auto_read_aloud=False)
else:
    interim_box = st.empty()
    partial = str(st.session_state.get("voice_partial", "") or "").strip()
    if partial:
        with interim_box.container():
            with st.chat_message("user"):
                st.markdown(partial)

    result = listen_for_voice_transcript(
        sanitize_base_url(st.session_state.api_base_url),
        voice_token or "",
    )
    if result and result.partial:
        st.session_state.voice_partial = result.partial
        with interim_box.container():
            with st.chat_message("user"):
                st.markdown(result.partial)
    if result and result.error:
        st.error(result.error)
        st.session_state.pop("voice_partial", None)
        interim_box.empty()
    elif result and result.transcript and result.transcript_id is not None:
        if st.session_state.get("last_voice_transcript_id") != result.transcript_id:
            st.session_state.last_voice_transcript_id = result.transcript_id
            st.session_state.voice_active = False
            st.session_state.pop("voice_partial", None)
            interim_box.empty()
            process_user_prompt(
                result.transcript,
                auto_read_aloud=True,
            )
