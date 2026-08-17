from __future__ import annotations

from collections.abc import Generator
from time import sleep

import streamlit as st

import api_client
from api_client import FrontendAPIError
from cookie_manager import clear_tokens, set_tokens
from state import ensure_session_state, reset_app_state


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 28%),
                    radial-gradient(circle at top left, rgba(234, 179, 8, 0.12), transparent 25%),
                    linear-gradient(180deg, #f7faf8 0%, #eef4f2 100%);
            }
            .hero-card, .glass-card, .chunk-card {
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid rgba(15, 23, 42, 0.08);
                border-radius: 20px;
                padding: 1.25rem 1.4rem;
                box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
                backdrop-filter: blur(8px);
            }
            .hero-title {
                font-size: 2.4rem;
                font-weight: 700;
                color: #0f172a;
                margin-bottom: 0.35rem;
            }
            .hero-subtitle {
                color: #334155;
                font-size: 1rem;
                line-height: 1.65;
            }
            .section-title {
                font-size: 1.15rem;
                font-weight: 700;
                color: #0f172a;
                margin-bottom: 0.2rem;
            }
            .metric-strip {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin-top: 1rem;
            }
            .metric-box {
                background: linear-gradient(135deg, #0f766e, #155e75);
                color: white;
                border-radius: 18px;
                padding: 1rem;
            }
            .metric-box strong {
                display: block;
                font-size: 1.4rem;
                margin-bottom: 0.1rem;
            }
            .chunk-title {
                font-weight: 700;
                color: #0f172a;
                margin-bottom: 0.35rem;
            }
            .chunk-meta {
                color: #475569;
                font-size: 0.92rem;
                margin-bottom: 0.55rem;
            }
            .auth-toggle {
                color: #0f172a;
                font-size: 0.95rem;
                margin-top: 0.7rem;
                text-align: center;
            }
            .auth-toggle button {
                color: #0f766e !important;
            }
            .score-row {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                margin: 0.25rem 0 0.4rem;
            }
            .score-bar-wrap {
                flex: 1;
                height: 10px;
                background: rgba(15, 23, 42, 0.08);
                border-radius: 999px;
                overflow: hidden;
            }
            .score-bar-fill {
                height: 100%;
                border-radius: 999px;
            }
            .score-pill {
                min-width: 3.4rem;
                text-align: right;
                font-weight: 700;
                font-size: 0.9rem;
                color: #0f172a;
            }
            .citation-chip {
                display: inline-block;
                background: rgba(15, 118, 110, 0.10);
                color: #0f766e;
                border: 1px solid rgba(15, 118, 110, 0.25);
                border-radius: 999px;
                padding: 0.15rem 0.7rem;
                margin: 0.15rem 0.2rem 0.15rem 0;
                font-size: 0.88rem;
                font-weight: 600;
            }
            .clarify-banner {
                background: rgba(234, 179, 8, 0.12);
                border: 1px solid rgba(234, 179, 8, 0.35);
                color: #7c5f00;
                border-radius: 12px;
                padding: 0.5rem 0.8rem;
                margin-bottom: 0.6rem;
                font-weight: 600;
            }
            .step-row {
                display: flex;
                align-items: flex-start;
                gap: 0.8rem;
                margin-top: 0.85rem;
            }
            .step-num {
                flex: 0 0 auto;
                width: 2.1rem;
                height: 2.1rem;
                border-radius: 999px;
                background: linear-gradient(135deg, #0f766e, #155e75);
                color: #ffffff;
                font-weight: 700;
                font-size: 0.95rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .step-body strong {
                display: block;
                color: #0f172a;
                margin-bottom: 0.1rem;
            }
            .step-body span {
                color: #475569;
                font-size: 0.92rem;
                line-height: 1.55;
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.7rem;
                margin-top: 0.8rem;
            }
            .feature-box {
                background: #ffffff;
                border: 1px solid rgba(15, 23, 42, 0.1);
                border-radius: 14px;
                padding: 0.75rem 0.9rem;
                box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
            }
            .feature-box strong {
                display: block;
                color: #0f172a;
                margin-bottom: 0.15rem;
                font-size: 0.95rem;
            }
            .feature-box span {
                color: #475569;
                font-size: 0.88rem;
                line-height: 1.5;
            }
            .format-chip {
                display: inline-block;
                background: rgba(15, 118, 110, 0.10);
                color: #0f766e;
                border: 1px solid rgba(15, 118, 110, 0.25);
                border-radius: 999px;
                padding: 0.2rem 0.85rem;
                margin: 0.2rem 0.3rem 0.2rem 0;
                font-size: 0.88rem;
                font-weight: 600;
            }
            [data-testid="stPageLink"] {
                display: flex;
                margin-bottom: 0.6rem;
            }
            [data-testid="stPageLink"] a {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                width: 100%;
                background: #ffffff;
                color: #000000 !important;
                border: 1px solid rgba(15, 23, 42, 0.1);
                border-radius: 14px;
                padding: 0.8rem 1rem;
                box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
                text-decoration: none !important;
                font-weight: 700;
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }
            [data-testid="stPageLink"] a:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 24px rgba(15, 23, 42, 0.14);
                color: #000000 !important;
                text-decoration: none !important;
            }
            [data-testid="stSkeleton"],
            [data-testid="stCustomComponentV1"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    ensure_session_state()
    pending_set = st.session_state.pop("_pending_set", None)
    if pending_set:
        set_tokens(
            str(pending_set.get("access_token", "")),
            str(pending_set.get("refresh_token", "")),
        )
    if st.session_state.pop("_pending_clear", False):
        clear_tokens()
    if not st.session_state.current_user:
        return
    with st.sidebar:
        name = st.session_state.current_user["name"]
        email = st.session_state.current_user["email"]
        st.markdown(
            f"""
            <div class="glass-card" style="padding:0.8rem 1rem;margin-bottom:0.8rem;">
                <div style="font-weight:700;color:#0f172a;font-size:0.95rem;">Signed in as {name}</div>
                <div style="color:#64748b;font-size:0.85rem;margin-top:0.15rem;">{email}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Logout", use_container_width=True):
            try:
                message = api_client.logout()
            except FrontendAPIError:
                message = None
            st.session_state["_pending_clear"] = True
            reset_app_state()
            st.session_state.auth_view = "login"
            if message:
                st.success(message["message"])
            st.rerun()


def require_auth() -> None:
    ensure_session_state()
    if st.session_state.current_user:
        return
    st.warning("Please sign up or log in from the home page first.")
    home_page = st.session_state.get("home_page")
    if home_page is not None:
        st.page_link(home_page, label="🏠 Home")
    st.stop()


def render_about_header() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Development of AI-Based Knowledge Retrieval Platform with Query Resolution System</div>
            <div class="hero-subtitle">
                Upload organizational documents, ask natural-language questions, and review grounded
                answers with citations, confidence, source chunks, and retrieval scores.
            </div>
            <div class="metric-strip">
                <div class="metric-box"><strong>Auth</strong>Signup and login with backend cookies</div>
                <div class="metric-box"><strong>RAG</strong>PDF and DOCX ingestion into ChromaDB</div>
                <div class="metric-box"><strong>Agent</strong>Transparent answers with source evidence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stream_text(text: str) -> Generator[str, None, None]:
    for word in text.split():
        yield word + " "
        sleep(0.012)


def _score_color(score: float) -> str:
    if score >= 0.7:
        return "#0f766e"
    if score >= 0.5:
        return "#0891b2"
    if score >= 0.35:
        return "#d97706"
    return "#dc2626"


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "High"
    if score >= 0.5:
        return "Moderate"
    if score >= 0.3:
        return "Low"
    return "Very low"


def render_response_details(response: dict[str, object]) -> None:
    confidence = float(response["confidence"])
    clarification_needed = bool(response["clarification_needed"])
    citations = response["citations"]
    source_chunks = response["source_chunks"]

    if clarification_needed:
        st.markdown(
            '<div class="clarify-banner">Clarification may be needed — the agent may ask a follow-up.</div>',
            unsafe_allow_html=True,
        )

    conf_color = _score_color(confidence)
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:0.8rem;margin:0.2rem 0 0.6rem;">
            <div style="font-weight:700;color:#0f172a;">Confidence</div>
            <div class="score-bar-wrap" style="max-width:220px;height:12px;">
                <div class="score-bar-fill" style="width:{confidence * 100:.0f}%;background:{conf_color};"></div>
            </div>
            <div class="score-pill" style="color:{conf_color};">{confidence:.2f}</div>
            <div style="color:#64748b;font-size:0.9rem;">{_confidence_label(confidence)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_chunks = sorted(
        source_chunks,
        key=lambda c: float(c["score"]) if c["score"] is not None else -1.0,
        reverse=True,
    )[:3]
    top_filenames: list[str] = []
    for c in top_chunks:
        fn = c["filename"]
        if fn not in top_filenames:
            top_filenames.append(fn)

    if top_filenames:
        chips = "".join(f'<span class="citation-chip">{fn}</span>' for fn in top_filenames)
        st.markdown(
            f'<div style="margin-bottom:0.6rem;"><span style="font-weight:700;color:#0f172a;">Citations</span><div style="margin-top:0.3rem;">{chips}</div></div>',
            unsafe_allow_html=True,
        )

    if top_chunks:
        with st.expander(f"Source chunks and scores ({len(top_chunks)})", expanded=False):
            for chunk in top_chunks:
                score = chunk["score"]
                score_value = float(score) if score is not None else 0.0
                score_label = f"{score:.4f}" if score is not None else "N/A"
                color = _score_color(score_value) if score is not None else "#94a3b8"
                width = score_value * 100 if score is not None else 0
                st.markdown(
                    f"""
                    <div class="chunk-card">
                        <div class="chunk-title">{chunk['filename']}</div>
                        <div class="chunk-meta">Document ID: {chunk['document_id']}</div>
                        <div class="score-row">
                            <div class="score-bar-wrap">
                                <div class="score-bar-fill" style="width:{width:.1f}%;background:{color};"></div>
                            </div>
                            <div class="score-pill" style="color:{color};">{score_label}</div>
                        </div>
                        <div style="color:#334155;line-height:1.6;">{chunk['content']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


