from __future__ import annotations

import streamlit as st

import api_client
from analytics_views import (
    apply_analytics_styles,
    build_insights,
    render_confidence_panel,
    render_gaps_panel,
    render_history_panel,
    render_insights_panel,
    render_metrics,
    render_top_topics_panel,
)
from api_client import FrontendAPIError
from state import ensure_session_state
from ui import apply_theme, render_page_header, render_sidebar, require_auth

ensure_session_state()
apply_theme()
apply_analytics_styles()
render_sidebar()
require_auth()

render_page_header(
    "Query Analytics",
    "Monitor query volume, confidence quality, recurring topics, and knowledge gaps.",
)

try:
    summary = api_client.get_analytics_summary()
except FrontendAPIError as exc:
    st.error(str(exc))
    st.stop()

try:
    recent = api_client.get_recent_queries(limit=50)
except FrontendAPIError as exc:
    st.warning(f"Could not load recent history: {exc}")
    recent = []

insights = build_insights(summary, recent)
total = insights["total"]
gap_threshold = float(summary["gap_threshold"])
top_questions = summary["top_questions"]
dist = summary["confidence_distribution"]
gaps = summary["knowledge_gaps"]

render_metrics(insights)
st.divider()
render_insights_panel(insights)
st.divider()

render_top_topics_panel(top_questions, total)
render_confidence_panel(dist, total)

st.divider()
render_gaps_panel(gaps, gap_threshold)
st.divider()
render_history_panel(recent)
