"""Shared chat agent turn handling for text and voice modes."""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.services.query_service import QueryService
from ui import render_response_details

import api_client
from voice_ui import schedule_voice_turn_continuation


def process_user_prompt(
    prompt: str,
    service: QueryService,
    *,
    auto_read_aloud: bool = False,
) -> None:
    """Run one user turn through the agent and append messages to session state."""
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    tid = st.session_state.thread_id or service.thread_id
    with st.chat_message("assistant"):
        status_box = st.empty()
        answer_box = st.empty()
        shown_tools: list[str] = []
        collected_answer = ""
        had_error = False
        response_dict: dict[str, Any] = {}
        audio_bytes: bytes | None = None

        try:
            for message_list in service.stream_chat(prompt, tid):
                for msg in message_list:
                    if "metadata" in msg:
                        title = msg["metadata"].get("title")
                        if title and title not in shown_tools:
                            shown_tools.append(title)
                            status_box.info(msg.get("content", f"Running `{title}`..."))

                answer_text = ""
                for msg in reversed(message_list):
                    if msg.get("role") == "assistant" and "metadata" not in msg:
                        answer_text = msg.get("content", "")
                        break

                if answer_text and answer_text != collected_answer:
                    collected_answer = answer_text
                    answer_box.markdown(collected_answer)

            status_box.empty()

            config = service.get_run_config(tid)
            final_state = service.agent_graph.get_state(config)
            values = getattr(final_state, "values", {}) or {}
            response = service._build_response(
                values, tid, pending_interrupt=bool(final_state.next)
            )
            response_dict = response.model_dump()

            if not collected_answer:
                collected_answer = response.answer or ""
                answer_box.markdown(collected_answer)

            render_response_details(response_dict)

            if auto_read_aloud and collected_answer:
                try:
                    with st.spinner("Generating speech..."):
                        audio_bytes = api_client.synthesize_speech(collected_answer.strip())
                except Exception as exc:
                    st.warning(f"Could not read answer aloud: {exc}")
        except Exception as exc:
            had_error = True
            status_box.empty()
            st.error(f"Agent error: {exc}")

        st.session_state.thread_id = tid
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
