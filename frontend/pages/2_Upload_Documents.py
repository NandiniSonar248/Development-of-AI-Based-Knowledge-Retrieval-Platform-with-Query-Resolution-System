from __future__ import annotations

import streamlit as st

import api_client
from api_client import FrontendAPIError
from state import ensure_session_state
from ui import apply_theme, render_page_header, render_sidebar, require_auth

ensure_session_state()
apply_theme()
render_sidebar()
require_auth()

render_page_header(
    "Knowledge Base",
    "Upload PDF or DOCX files, index them for retrieval, and manage your organization's document library.",
)

st.markdown(
    """
    <div class="glass-card">
        <div class="section-title">Knowledge Base Upload</div>
        <div class="hero-subtitle">
            Send files to the backend, let ingestion index them, and keep track of what is already
            available for retrieval.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Choose files",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)

upload_col, clear_col, refresh_col = st.columns(3)

with upload_col:
    if st.button("Upload and index", use_container_width=True, disabled=not uploaded_files):
        files = [
            (
                file.name,
                file.getvalue(),
                file.type or "application/octet-stream",
            )
            for file in uploaded_files
        ]
        progress = st.progress(0.0, text="Preparing files…")
        try:
            progress.progress(0.2, text="Saving and indexing…")
            result = api_client.upload_documents(files)
            progress.progress(1.0, text="Done")
            st.success(result["message"])
        except FrontendAPIError as exc:
            progress.empty()
            st.error(str(exc))

with clear_col:
    if st.button("Clear knowledge base", use_container_width=True):
        try:
            result = api_client.clear_documents()
            st.success(result["message"])
        except FrontendAPIError as exc:
            st.error(str(exc))

with refresh_col:
    refresh_documents = st.button("Refresh list", use_container_width=True)

if refresh_documents or True:
    try:
        documents = api_client.list_documents()
        st.subheader("Indexed documents")
        if documents:
            for index, name in enumerate(documents, start=1):
                st.markdown(
                    f"""
                    <div class="chunk-card" style="margin-bottom:0.9rem;">
                        <div class="chunk-title">{index}. {name}</div>
                        <div class="chunk-meta">Ready for retrieval and citation</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No documents indexed yet.")
    except FrontendAPIError as exc:
        st.error(str(exc))