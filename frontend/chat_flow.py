"""Shared chat agent turn handling for text and voice modes."""

from __future__ import annotations

from typing import Any

import streamlit as st

from api_client import FrontendAPIError
import api_client
from ui import render_response_details
from voice_ui import schedule_voice_turn_continuation


def process_user_prompt(
    prompt: str,
    *,
    auto_read_aloud: bool = False,
) -> None:
    """Run one user turn through the backend API and append messages to session state."""
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    thread_id = st.session_state.thread_id
    with st.chat_message("assistant"):
        answer_box = st.empty()
        collected_answer = ""
        had_error = False
        response_dict: dict[str, Any] = {}
        audio_bytes: bytes | None = None

        try:
            with st.spinner("Thinking..."):
                response_dict = api_client.ask_question(prompt, thread_id)

            collected_answer = str(response_dict.get("answer", "") or "")
            answer_box.markdown(collected_answer)
            render_response_details(response_dict)

            if auto_read_aloud and collected_answer:
                try:
                    with st.spinner("Generating speech..."):
                        audio_bytes = api_client.synthesize_speech(collected_answer.strip())
                except Exception as exc:
                    st.warning(f"Could not read answer aloud: {exc}")
        except FrontendAPIError as exc:
            had_error = True
            st.error(f"Agent error: {exc}")
        except Exception as exc:
            had_error = True
            st.error(f"Agent error: {exc}")

        if response_dict.get("thread_id"):
            st.session_state.thread_id = response_dict["thread_id"]

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": collected_answer or ("(no answer)" if had_error else ""),
                "response": response_dict if not had_error else {},
                "audio_bytes": audio_bytes,
            }
        )

        if not had_error and collected_answer:
            try:
                api_client.record_query(
                    prompt,
                    collected_answer,
                    float(response_dict.get("confidence", 0.0)),
                )
            except Exception:
                pass

        if auto_read_aloud and not had_error:
            schedule_voice_turn_continuation()
