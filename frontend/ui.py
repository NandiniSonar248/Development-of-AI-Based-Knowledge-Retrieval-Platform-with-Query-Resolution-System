from __future__ import annotations

import base64
import mimetypes
from collections.abc import Generator
from pathlib import Path
from time import sleep

import streamlit as st

import api_client
from api_client import FrontendAPIError
from cookie_manager import clear_tokens, set_tokens
from state import ensure_session_state, get_access_token, reset_app_state, store_auth_tokens

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
LOGIN_BANNER = ASSETS_DIR / "login_banner_bg.png"

NAVY = "#0a3d6e"
BLUE = "#1e6bb8"
SKY = "#007bff"
PALE = "#e8f4fc"
MIST = "#f0f7ff"


def _banner_data_uri(path: Path = LOGIN_BANNER) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"


def apply_theme(*, auth_page: bool = False) -> None:
    auth_css = ""
    if auth_page:
        auth_css = f"""
            .block-container {{
                max-width: 980px;
                padding-top: 0.5rem;
            }}
            .auth-hero-full {{
                position: relative;
                width: 100vw;
                margin-left: calc(-50vw + 50%);
                min-height: 380px;
                overflow: hidden;
                border-bottom: 1px solid rgba(10, 61, 110, 0.08);
            }}
            .auth-hero-bg {{
                position: absolute;
                inset: 0;
                background-size: cover;
                background-position: center 35%;
            }}
            .auth-hero-shade {{
                position: absolute;
                inset: 0;
                background: linear-gradient(
                    115deg,
                    rgba(10, 61, 110, 0.92) 0%,
                    rgba(30, 107, 184, 0.82) 48%,
                    rgba(0, 123, 255, 0.55) 100%
                );
            }}
            .auth-hero-inner {{
                position: relative;
                z-index: 1;
                max-width: 920px;
                margin: 0 auto;
                padding: 2.6rem 2rem 3.4rem;
                color: #ffffff;
                text-align: center;
            }}
            .auth-hero-title {{
                font-size: clamp(1.85rem, 3.2vw, 2.65rem);
                font-weight: 800;
                line-height: 1.2;
                letter-spacing: -0.03em;
                margin: 0.35rem 0 0.55rem;
            }}
            .auth-hero-tagline {{
                font-size: 1.2rem;
                font-weight: 700;
                color: rgba(255, 255, 255, 0.95);
                margin: 0 0 0.65rem;
            }}
            .auth-hero-desc {{
                font-size: 1.02rem;
                line-height: 1.65;
                color: rgba(255, 255, 255, 0.88);
                max-width: 680px;
                margin: 0 auto 1.1rem;
            }}
            .auth-feature-row {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 0.55rem;
            }}
            .auth-feature-pill {{
                display: inline-block;
                background: rgba(255, 255, 255, 0.14);
                border: 1px solid rgba(255, 255, 255, 0.24);
                border-radius: 999px;
                padding: 0.35rem 0.9rem;
                font-size: 0.84rem;
                font-weight: 600;
                color: #ffffff;
            }}
            .auth-form-shell {{
                margin-top: -2.4rem;
                position: relative;
                z-index: 2;
            }}
            .auth-form-header {{
                text-align: center;
                margin-bottom: 1rem;
            }}
            .auth-form-header h2 {{
                color: {NAVY};
                font-size: 1.85rem;
                font-weight: 800;
                margin: 0 0 0.35rem;
                letter-spacing: -0.02em;
            }}
            .auth-form-header p {{
                color: #475569;
                font-size: 1rem;
                margin: 0;
                line-height: 1.55;
            }}
            div[data-testid="stForm"] {{
                padding: 1.75rem 2rem 1.1rem;
                border-radius: 24px;
                box-shadow: 0 28px 60px rgba(10, 61, 110, 0.14);
            }}
            [data-testid="stTextInput"] input {{
                font-size: 1.02rem !important;
                padding: 0.85rem 1rem !important;
                min-height: 3rem;
                border-radius: 12px !important;
            }}
            [data-testid="stTextInput"] label {{
                font-size: 0.95rem !important;
                font-weight: 600 !important;
                color: {NAVY} !important;
            }}
            div[data-testid="stForm"] button[kind="primaryFormSubmit"] {{
                min-height: 3rem;
                font-size: 1.02rem !important;
                border-radius: 12px !important;
                margin-top: 0.35rem;
            }}
            .auth-toggle {{
                margin-top: 1rem;
                font-size: 1rem;
            }}
            .stButton > button {{
                min-height: 2.75rem;
                font-size: 0.98rem !important;
                border-radius: 12px !important;
            }}
        """
    st.markdown(
        f"""
        <style>
            {"body, .stApp { background: #eef4fb !important; }" if auth_page else ""}
            :root {{
                --navy: {NAVY};
                --blue: {BLUE};
                --sky: {SKY};
                --pale: {PALE};
                --mist: {MIST};
            }}
            .stApp {{
                background:
                    radial-gradient(circle at 85% 10%, rgba(0, 123, 255, 0.14), transparent 32%),
                    radial-gradient(circle at 10% 20%, rgba(30, 107, 184, 0.12), transparent 28%),
                    linear-gradient(165deg, #f7fbff 0%, #e8f2fb 45%, #dbeafe 100%);
            }}
            .block-container {{
                padding-top: 1.5rem;
                max-width: 1180px;
            }}
            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, {NAVY} 0%, {BLUE} 100%);
                border-right: 1px solid rgba(255, 255, 255, 0.12);
            }}
            [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
            [data-testid="stSidebar"] [data-testid="stMarkdown"] li,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stRadio label {{
                color: rgba(255, 255, 255, 0.92) !important;
            }}
            [data-testid="stSidebar"] .stButton > button {{
                background: rgba(255, 255, 255, 0.14);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.28);
            }}
            [data-testid="stSidebar"] .stButton > button:hover {{
                background: rgba(255, 255, 255, 0.24);
                border-color: rgba(255, 255, 255, 0.45);
                color: #ffffff;
            }}
            [data-testid="stSidebarHeader"] {{
                background: transparent;
            }}
            [data-testid="stSidebarCollapseButton"] {{
                color: rgba(255, 255, 255, 0.85) !important;
            }}
            [data-testid="stSidebarNav"] {{
                padding-top: 0.25rem;
            }}
            [data-testid="stSidebarNav"]::before {{
                content: "Query Resolution";
                display: block;
                color: #ffffff;
                font-size: 1rem;
                font-weight: 800;
                line-height: 1.35;
                letter-spacing: -0.01em;
                padding: 0.15rem 0.85rem 0.75rem;
                margin-bottom: 0.55rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.14);
            }}
            [data-testid="stSidebarNav"] ul[data-testid="stSidebarNavItems"] {{
                gap: 0.35rem;
            }}
            [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"] {{
                background: transparent !important;
                border: 1px solid transparent !important;
                border-radius: 12px !important;
                padding: 0.6rem 0.85rem !important;
                margin-bottom: 0.15rem;
                transition: background 0.15s ease, border-color 0.15s ease;
            }}
            [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"] span {{
                color: rgba(255, 255, 255, 0.88) !important;
                font-weight: 600 !important;
                font-size: 0.95rem !important;
            }}
            [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"] * {{
                color: rgba(255, 255, 255, 0.88) !important;
            }}
            [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"] svg,
            [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {{
                color: rgba(255, 255, 255, 0.9) !important;
                fill: rgba(255, 255, 255, 0.9) !important;
            }}
            [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"]:hover {{
                background: rgba(255, 255, 255, 0.12) !important;
                border-color: rgba(255, 255, 255, 0.14) !important;
            }}
            [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"]:hover span {{
                color: #ffffff !important;
            }}
            [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"][aria-current="page"] {{
                background: rgba(255, 255, 255, 0.2) !important;
                border-color: rgba(255, 255, 255, 0.28) !important;
                box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
            }}
            [data-testid="stSidebarNav"] a[data-testid="stSidebarNavLink"][aria-current="page"] span {{
                color: #ffffff !important;
                font-weight: 700 !important;
            }}
            .hero-card, .glass-card, .chunk-card, .auth-panel {{
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid rgba(10, 61, 110, 0.1);
                border-radius: 20px;
                padding: 1.25rem 1.4rem;
                box-shadow: 0 18px 40px rgba(10, 61, 110, 0.08);
                backdrop-filter: blur(10px);
            }}
            .auth-panel {{
                padding: 1.5rem 1.6rem 1.2rem;
            }}
            .login-banner-wrap {{
                position: relative;
                border-radius: 24px;
                overflow: hidden;
                min-height: 520px;
                box-shadow: 0 24px 48px rgba(10, 61, 110, 0.16);
                border: 1px solid rgba(10, 61, 110, 0.08);
            }}
            .login-banner-img {{
                width: 100%;
                height: 100%;
                min-height: 520px;
                object-fit: cover;
                display: block;
            }}
            .login-banner-overlay {{
                position: absolute;
                inset: 0;
                background: linear-gradient(135deg, rgba(10, 61, 110, 0.08) 0%, rgba(0, 123, 255, 0.06) 100%);
                pointer-events: none;
            }}
            .page-hero {{
                position: relative;
                border-radius: 22px;
                overflow: hidden;
                margin-bottom: 1.2rem;
                min-height: 150px;
                box-shadow: 0 16px 36px rgba(10, 61, 110, 0.1);
            }}
            .page-hero-bg {{
                position: absolute;
                inset: 0;
                background-size: cover;
                background-position: center 20%;
                filter: saturate(1.05);
            }}
            .page-hero-shade {{
                position: absolute;
                inset: 0;
                background: linear-gradient(90deg, rgba(10, 61, 110, 0.88) 0%, rgba(30, 107, 184, 0.72) 55%, rgba(0, 123, 255, 0.45) 100%);
            }}
            .page-hero-content {{
                position: relative;
                z-index: 1;
                padding: 1.5rem 1.75rem;
                color: #ffffff;
            }}
            .page-hero-title {{
                font-size: 1.75rem;
                font-weight: 800;
                margin-bottom: 0.35rem;
                letter-spacing: -0.02em;
            }}
            .page-hero-subtitle {{
                font-size: 0.98rem;
                line-height: 1.55;
                color: rgba(255, 255, 255, 0.9);
                max-width: 720px;
            }}
            .hero-title {{
                font-size: 2.2rem;
                font-weight: 800;
                color: {NAVY};
                margin-bottom: 0.35rem;
                letter-spacing: -0.02em;
            }}
            .hero-subtitle {{
                color: #334155;
                font-size: 1rem;
                line-height: 1.65;
            }}
            .section-title {{
                font-size: 1.15rem;
                font-weight: 700;
                color: {NAVY};
                margin-bottom: 0.2rem;
            }}
            .metric-strip {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin-top: 1rem;
            }}
            .metric-box {{
                background: linear-gradient(135deg, {NAVY}, {BLUE});
                color: white;
                border-radius: 18px;
                padding: 1rem;
            }}
            .metric-box strong {{
                display: block;
                font-size: 1.4rem;
                margin-bottom: 0.1rem;
            }}
            .chunk-title {{
                font-weight: 700;
                color: {NAVY};
                margin-bottom: 0.35rem;
            }}
            .chunk-meta {{
                color: #475569;
                font-size: 0.92rem;
                margin-bottom: 0.55rem;
            }}
            .auth-toggle {{
                color: {NAVY};
                font-size: 0.95rem;
                margin-top: 0.7rem;
                text-align: center;
            }}
            .auth-kicker {{
                color: {BLUE};
                font-size: 0.82rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 0.35rem;
            }}
            .score-row {{
                display: flex;
                align-items: center;
                gap: 0.6rem;
                margin: 0.25rem 0 0.4rem;
            }}
            .score-bar-wrap {{
                flex: 1;
                height: 10px;
                background: rgba(10, 61, 110, 0.08);
                border-radius: 999px;
                overflow: hidden;
            }}
            .score-bar-fill {{
                height: 100%;
                border-radius: 999px;
            }}
            .score-pill {{
                min-width: 3.4rem;
                text-align: right;
                font-weight: 700;
                font-size: 0.9rem;
                color: {NAVY};
            }}
            .citation-chip {{
                display: inline-block;
                background: rgba(0, 123, 255, 0.1);
                color: {BLUE};
                border: 1px solid rgba(30, 107, 184, 0.25);
                border-radius: 999px;
                padding: 0.15rem 0.7rem;
                margin: 0.15rem 0.2rem 0.15rem 0;
                font-size: 0.88rem;
                font-weight: 600;
            }}
            .clarify-banner {{
                background: rgba(234, 179, 8, 0.12);
                border: 1px solid rgba(234, 179, 8, 0.35);
                color: #7c5f00;
                border-radius: 12px;
                padding: 0.5rem 0.8rem;
                margin-bottom: 0.6rem;
                font-weight: 600;
            }}
            .step-row {{
                display: flex;
                align-items: flex-start;
                gap: 0.8rem;
                margin-top: 0.85rem;
            }}
            .step-num {{
                flex: 0 0 auto;
                width: 2.1rem;
                height: 2.1rem;
                border-radius: 999px;
                background: linear-gradient(135deg, {NAVY}, {SKY});
                color: #ffffff;
                font-weight: 700;
                font-size: 0.95rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .step-body strong {{
                display: block;
                color: {NAVY};
                margin-bottom: 0.1rem;
            }}
            .step-body span {{
                color: #475569;
                font-size: 0.92rem;
                line-height: 1.55;
            }}
            .feature-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.7rem;
                margin-top: 0.8rem;
            }}
            .feature-box {{
                background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border: 1px solid rgba(10, 61, 110, 0.1);
                border-radius: 14px;
                padding: 0.75rem 0.9rem;
                box-shadow: 0 4px 12px rgba(10, 61, 110, 0.05);
            }}
            .feature-box strong {{
                display: block;
                color: {NAVY};
                margin-bottom: 0.15rem;
                font-size: 0.95rem;
            }}
            .feature-box span {{
                color: #475569;
                font-size: 0.88rem;
                line-height: 1.5;
            }}
            .format-chip {{
                display: inline-block;
                background: rgba(0, 123, 255, 0.1);
                color: {BLUE};
                border: 1px solid rgba(30, 107, 184, 0.25);
                border-radius: 999px;
                padding: 0.2rem 0.85rem;
                margin: 0.2rem 0.3rem 0.2rem 0;
                font-size: 0.88rem;
                font-weight: 600;
            }}
            div[data-testid="stForm"] {{
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid rgba(10, 61, 110, 0.12);
                border-radius: 18px;
                padding: 1rem 1.1rem 0.4rem;
                box-shadow: 0 14px 32px rgba(10, 61, 110, 0.08);
            }}
            .stButton > button[kind="primary"],
            div[data-testid="stForm"] button[kind="primaryFormSubmit"] {{
                background: linear-gradient(135deg, {NAVY}, {SKY}) !important;
                color: #ffffff !important;
                border: none !important;
                font-weight: 700 !important;
                box-shadow: 0 10px 24px rgba(0, 123, 255, 0.25);
            }}
            .stButton > button[kind="primary"]:hover,
            div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {{
                filter: brightness(1.05);
                box-shadow: 0 14px 28px rgba(0, 123, 255, 0.32);
            }}
            [data-testid="stChatMessage"] {{
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid rgba(10, 61, 110, 0.08);
                border-radius: 16px;
            }}
            [data-testid="stMetric"] {{
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid rgba(10, 61, 110, 0.08);
                border-radius: 16px;
                padding: 0.75rem 1rem;
                box-shadow: 0 8px 20px rgba(10, 61, 110, 0.06);
            }}
            [data-testid="stPageLink"] {{
                display: flex;
                margin-bottom: 0.6rem;
            }}
            [data-testid="stPageLink"] a {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
                width: 100%;
                background: linear-gradient(135deg, #ffffff 0%, #f3f8ff 100%);
                color: {NAVY} !important;
                border: 1px solid rgba(10, 61, 110, 0.12);
                border-radius: 14px;
                padding: 0.8rem 1rem;
                box-shadow: 0 8px 18px rgba(10, 61, 110, 0.08);
                text-decoration: none !important;
                font-weight: 700;
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }}
            [data-testid="stPageLink"] a:hover {{
                transform: translateY(-2px);
                box-shadow: 0 12px 24px rgba(10, 61, 110, 0.14);
                color: {BLUE} !important;
                text-decoration: none !important;
            }}
            [data-testid="stSkeleton"],
            [data-testid="stCustomComponentV1"] {{
                display: none !important;
            }}
            {auth_css}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_auth_hero() -> None:
    uri = _banner_data_uri()
    st.markdown(
        f"""
        <div class="auth-hero-full">
            <div class="auth-hero-bg" style="background-image:url('{uri}');"></div>
            <div class="auth-hero-shade"></div>
            <div class="auth-hero-inner">
                <div class="auth-kicker" style="color:rgba(255,255,255,0.82);">Knowledge platform</div>
                <h1 class="auth-hero-title">Development of AI-Based Knowledge Retrieval Platform with Query Resolution System</h1>
                <p class="auth-hero-tagline">Ask. Understand. Resolve.</p>
                <p class="auth-hero-desc">
                    Upload your documents, ask in natural language, and get accurate grounded answers
                    with sources, confidence, and clarity.
                </p>
                <div class="auth-feature-row">
                    <span class="auth-feature-pill">Smart RAG retrieval</span>
                    <span class="auth-feature-pill">Multi-agent resolution</span>
                    <span class="auth-feature-pill">Source citations</span>
                    <span class="auth-feature-pill">Query analytics</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_auth_form_header(*, signup: bool) -> None:
    if signup:
        heading = "Create your account"
        subtitle = "Set up access to upload documents, chat with the agent, and review analytics."
    else:
        heading = "Welcome back"
        subtitle = "Sign in to open your knowledge workspace."
    st.markdown(
        f"""
        <div class="auth-form-header">
            <h2>{heading}</h2>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    uri = _banner_data_uri()
    st.markdown(
        f"""
        <div class="page-hero">
            <div class="page-hero-bg" style="background-image:url('{uri}');"></div>
            <div class="page-hero-shade"></div>
            <div class="page-hero-content">
                <div class="page-hero-title">{title}</div>
                <div class="page-hero-subtitle">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    ensure_session_state()
    pending_set = st.session_state.pop("_pending_set", None)
    if pending_set:
        store_auth_tokens(pending_set)
        set_tokens(
            str(pending_set.get("access_token", "")),
            str(pending_set.get("refresh_token", "")),
        )
    if st.session_state.pop("_pending_clear", False):
        clear_tokens()
    if not st.session_state.current_user:
        return
    get_access_token()
    with st.sidebar:
        name = st.session_state.current_user["name"]
        email = st.session_state.current_user["email"]
        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);
                        border-radius:16px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
                <div style="font-weight:700;color:#ffffff;font-size:0.95rem;">Signed in as {name}</div>
                <div style="color:rgba(255,255,255,0.78);font-size:0.85rem;margin-top:0.15rem;">{email}</div>
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
        st.page_link(home_page, label="Home")
    st.stop()


def render_about_header() -> None:
    uri = _banner_data_uri()
    st.markdown(
        f"""
        <div class="page-hero" style="min-height:220px;margin-bottom:1.4rem;">
            <div class="page-hero-bg" style="background-image:url('{uri}');"></div>
            <div class="page-hero-shade"></div>
            <div class="page-hero-content">
                <div class="auth-kicker">Ask. Understand. Resolve.</div>
                <div class="page-hero-title" style="font-size:2rem;">Development of AI-Based Knowledge Retrieval Platform with Query Resolution System</div>
                <div class="page-hero-subtitle">
                    Upload organizational documents, ask natural-language questions, and review grounded
                    answers with citations, confidence, source chunks, and retrieval scores.
                </div>
                <div class="metric-strip" style="margin-top:1.1rem;">
                    <div class="metric-box"><strong>Auth</strong>Signup and login with backend cookies</div>
                    <div class="metric-box"><strong>RAG</strong>PDF and DOCX ingestion into ChromaDB</div>
                    <div class="metric-box"><strong>Agent</strong>Transparent answers with source evidence</div>
                </div>
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
        return BLUE
    if score >= 0.5:
        return SKY
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


