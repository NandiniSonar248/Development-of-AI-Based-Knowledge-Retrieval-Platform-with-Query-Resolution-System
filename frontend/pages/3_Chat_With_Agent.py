from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.query_service import get_query_service
from state import ensure_session_state
from ui import apply_theme, render_response_details, render_sidebar, require_auth

import api_client

GREETING = (
    "👋 Hello! I'm your Knowledge Assistant.\n\n"
    "Ask me anything about your uploaded documents, policies, manuals, or FAQs. "
    "I'll find the relevant information and provide a clear answer with sources and confidence.\n\n"
    "How can I help you today?"
)

ensure_session_state()
apply_theme()
render_sidebar()
require_auth()

st.title("💬 Knowledge Assistant")

service = get_query_service()

if st.button("Reset chat"):
    st.session_state.thread_id = service.reset_thread()
    st.session_state.chat_messages = []
    st.rerun()

if not st.session_state.chat_messages:
    with st.chat_message("assistant"):
        st.markdown(GREETING)

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "response" in message:
            render_response_details(message["response"])

prompt = st.chat_input("Ask a question about your documents")

if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    tid = st.session_state.thread_id or service.thread_id
    with st.chat_message("assistant"):
        status_box = st.empty()
        answer_box = st.empty()
        shown_tools: list[str] = []
        collected_answer = ""
        last_messages: list[dict] = []
        had_error = False

        try:
            for message_list in service.stream_chat(prompt, tid):
                last_messages = message_list

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
            }
        )

        if not had_error and collected_answer:
            try:
                api_client.record_query(prompt, collected_answer, float(response_dict.get("confidence", 0.0)))
            except Exception:
                pass