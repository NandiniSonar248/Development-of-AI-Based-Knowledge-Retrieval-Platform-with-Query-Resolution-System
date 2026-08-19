from __future__ import annotations

import streamlit as st

import api_client
from api_client import FrontendAPIError
from cookie_manager import clear_tokens, get_tokens, set_tokens
from state import ensure_session_state, store_auth_tokens
from ui import apply_theme, render_about_header, render_auth_form_header, render_auth_hero, render_sidebar

st.set_page_config(
    page_title="Knowledge Query Platform",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.get("current_user") else "collapsed",
)


def _restore_browser_session() -> None:
    """Auto-restore a session from the stored refresh-token cookie."""
    tokens = get_tokens()
    if not tokens or tokens == st.session_state.get("_last_tokens"):
        return
    st.session_state["_last_tokens"] = tokens
    try:
        user, new_tokens = api_client.restore_session(tokens.get("refresh_token", ""))
        st.session_state.current_user = user
        if new_tokens:
            st.session_state["_pending_set"] = new_tokens
            store_auth_tokens(new_tokens)
        st.rerun()
    except FrontendAPIError:
        st.session_state["_pending_clear"] = True
        st.rerun()


def _render_auth_flow() -> None:
    render_auth_hero()

    _, form_col, _ = st.columns([0.2, 1.6, 0.2])
    with form_col:
        mode = st.session_state.auth_view
        render_auth_form_header(signup=mode == "signup")

        if mode == "signup":
            with st.form("signup_form", clear_on_submit=False):
                signup_name = st.text_input("Full name", placeholder="Your name")
                signup_email = st.text_input("Email", placeholder="you@company.com")
                signup_password = st.text_input("Password", type="password", placeholder="Create a password")
                signup_submitted = st.form_submit_button("Create account", use_container_width=True)

            if signup_submitted:
                try:
                    payload, tokens = api_client.signup(signup_name, signup_email, signup_password)
                    st.session_state.current_user = payload["user"]
                    st.session_state["_pending_set"] = tokens
                    store_auth_tokens(tokens)
                    st.success(payload["message"])
                    st.rerun()
                except FrontendAPIError as exc:
                    st.error(str(exc))

            st.markdown('<div class="auth-toggle">Already have an account?</div>', unsafe_allow_html=True)
            if st.button("Sign in instead", use_container_width=True):
                st.session_state.auth_view = "login"
                st.rerun()
        else:
            with st.form("login_form", clear_on_submit=False):
                login_email = st.text_input("Email", placeholder="you@company.com")
                login_password = st.text_input("Password", type="password", placeholder="Enter your password")
                login_submitted = st.form_submit_button("Sign in", use_container_width=True)

            if login_submitted:
                try:
                    payload, tokens = api_client.login(login_email, login_password)
                    st.session_state.current_user = payload["user"]
                    st.session_state["_pending_set"] = tokens
                    store_auth_tokens(tokens)
                    st.success(payload["message"])
                    st.rerun()
                except FrontendAPIError as exc:
                    st.error(str(exc))

            st.markdown('<div class="auth-toggle">Need a new account?</div>', unsafe_allow_html=True)
            if st.button("Create an account", use_container_width=True):
                st.session_state.auth_view = "signup"
                st.rerun()


def home_page() -> None:
    ensure_session_state()

    if not st.session_state.current_user:
        apply_theme(auth_page=True)
        render_sidebar()
        _restore_browser_session()
        _render_auth_flow()
        return

    apply_theme()
    render_sidebar()
    render_about_header()
    st.markdown("")
    intro_col, actions_col = st.columns([1.25, 0.75], gap="large")

    with intro_col:
            st.markdown(
                """
                <div class="glass-card" style="margin-bottom:1.1rem;">
                    <div class="section-title">About This Project</div>
                    <div class="hero-subtitle">
                        <p><strong>Development of AI-Based Knowledge Retrieval Platform with Query Resolution System</strong> is a domain-agnostic conversational knowledge platform designed to make information retrieval faster, simpler, and more reliable. Organizations and teams often store important information across policies, manuals, FAQs, process guides, and technical documents, making it difficult for users to quickly find the right information through traditional keyword-based searches.</p>
                        <p>The system allows users to <strong>upload their own knowledge base</strong> in formats such as PDF, DOCX, TXT, and FAQ CSV files. The uploaded documents are automatically processed through a <strong>Retrieval-Augmented Generation (RAG) pipeline</strong>, where relevant information is indexed and retrieved when a user asks a question.</p>
                        <p>A <strong>multi-agent resolution layer</strong> works on top of the RAG pipeline. The Query Understanding Agent identifies the user's intent and query type, the Retrieval Agent finds relevant information, the Response Generation Agent produces a grounded answer, and the Clarification Agent asks follow-up questions when the query is incomplete or ambiguous. Conversation memory maintains context across multiple turns.</p>
                        <p>To improve <strong>transparency and trust</strong>, every response can display the relevant source chunks, citations, and confidence information used to generate the answer. The platform also includes query analytics and knowledge-gap detection to identify unanswered or low-confidence queries and highlight areas where the knowledge base may need additional information.</p>
                        <p>The same platform can be applied to different domains—for example, <strong>HR policies, college handbooks, organizational guidelines, or technical documentation</strong>—without changing the core query-resolution architecture.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="glass-card" style="margin-bottom:1.1rem;">
                    <div class="section-title">How the platform works</div>
                    <div class="step-row">
                        <div class="step-num">1</div>
                        <div class="step-body">
                            <strong>Upload your knowledge base</strong>
                            <span>Drop in PDF, DOCX, TXT, or FAQ CSV files; the system ingests and indexes them automatically.</span>
                        </div>
                    </div>
                    <div class="step-row">
                        <div class="step-num">2</div>
                        <div class="step-body">
                            <strong>Ask in natural language</strong>
                            <span>No keywords or filters needed — ask questions the way you would ask a colleague.</span>
                        </div>
                    </div>
                    <div class="step-row">
                        <div class="step-num">3</div>
                        <div class="step-body">
                            <strong>Agents resolve your query</strong>
                            <span>A multi-agent layer understands intent, retrieves evidence, generates grounded answers, and asks for clarification when needed.</span>
                        </div>
                    </div>
                    <div class="step-row">
                        <div class="step-num">4</div>
                        <div class="step-body">
                            <strong>Review evidence and confidence</strong>
                            <span>Every answer shows source chunks, citations, and a confidence score so you can verify it before acting.</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="glass-card" style="margin-bottom:1.1rem;">
                    <div class="section-title">The multi-agent resolution layer</div>
                    <div class="feature-grid">
                        <div class="feature-box">
                            <strong>Query Understanding Agent</strong>
                            <span>Identifies the user's intent and query type before retrieval begins.</span>
                        </div>
                        <div class="feature-box">
                            <strong>Retrieval Agent</strong>
                            <span>Finds the most relevant passages across all indexed documents.</span>
                        </div>
                        <div class="feature-box">
                            <strong>Response Generation Agent</strong>
                            <span>Produces grounded answers strictly from the retrieved evidence.</span>
                        </div>
                        <div class="feature-box">
                            <strong>Clarification Agent</strong>
                            <span>Asks follow-up questions when a query is incomplete or ambiguous.</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="glass-card" style="margin-bottom:1.1rem;">
                    <div class="section-title">Key capabilities</div>
                    <div class="feature-grid">
                        <div class="feature-box">
                            <strong>RAG pipeline</strong>
                            <span>Retrieval-augmented generation over your own uploaded documents.</span>
                        </div>
                        <div class="feature-box">
                            <strong>Conversation memory</strong>
                            <span>Context is maintained across multiple turns in each thread.</span>
                        </div>
                        <div class="feature-box">
                            <strong>Transparency</strong>
                            <span>Citations, source chunks, and confidence on every answer.</span>
                        </div>
                        <div class="feature-box">
                            <strong>Analytics & gap detection</strong>
                            <span>Track query history and spot knowledge gaps in your base.</span>
                        </div>
                        <div class="feature-box">
                            <strong>Secure access</strong>
                            <span>Cookie-based JWT authentication with per-user data isolation.</span>
                        </div>
                        <div class="feature-box">
                            <strong>Domain agnostic</strong>
                            <span>HR policies, handbooks, guidelines, or technical documentation.</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with actions_col:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="section-title">Open Workspace</div>
                    <div class="hero-subtitle" style="margin-bottom:1.2rem;">
                        Jump straight into document ingestion, the chat workspace, or query analytics.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
            st.page_link(
                "pages/2_Upload_Documents.py",
                label="Upload Documents",
                icon=":material/upload_file:",
                use_container_width=True,
            )
            st.page_link(
                "pages/3_Chat_With_Agent.py",
                label="Chat With Agent",
                icon=":material/forum:",
                use_container_width=True,
            )
            st.page_link(
                "pages/4_Query_Analytics.py",
                label="Query Analytics",
                icon=":material/analytics:",
                use_container_width=True,
            )
            st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class="glass-card">
                    <div class="section-title">Supported formats</div>
                    <div>
                        <span class="format-chip">PDF</span>
                        <span class="format-chip">DOCX</span>
                        <span class="format-chip">TXT</span>
                        <span class="format-chip">FAQ CSV</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


pages = [
    st.Page(home_page, title="Home", icon=":material/home:", url_path="home", default=True),
    st.Page(
        "pages/2_Upload_Documents.py",
        title="Knowledge Base",
        icon=":material/library_books:",
        url_path="knowledge-base",
    ),
    st.Page(
        "pages/3_Chat_With_Agent.py",
        title="Knowledge Assistant",
        icon=":material/forum:",
        url_path="knowledge-assistant",
    ),
    st.Page(
        "pages/4_Query_Analytics.py",
        title="Query Analytics",
        icon=":material/analytics:",
        url_path="query-analytics",
    ),
]

st.session_state["home_page"] = pages[0]

authed = bool(st.session_state.get("current_user"))
st.navigation(pages, position="sidebar" if authed else "hidden").run()