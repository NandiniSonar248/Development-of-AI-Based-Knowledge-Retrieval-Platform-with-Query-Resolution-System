from __future__ import annotations

import pandas as pd
import streamlit as st

import api_client
from api_client import FrontendAPIError
from state import ensure_session_state
from ui import apply_theme, render_sidebar, require_auth

ensure_session_state()
apply_theme()
render_sidebar()
require_auth()

st.title("📊 Query Analytics & Knowledge Gap Detection")
st.caption("Your query history, common topics, confidence trends, and knowledge gaps.")

try:
    summary = api_client.get_analytics_summary()
except FrontendAPIError as exc:
    st.error(str(exc))
    st.stop()

total = int(summary["total_queries"])
gap_threshold = float(summary["gap_threshold"])
top_questions = summary["top_questions"]
dist = summary["confidence_distribution"]
gaps = summary["knowledge_gaps"]

metric_col, gap_col = st.columns([1, 1])
with metric_col:
    st.metric("Total queries", total)
with gap_col:
    st.metric("Knowledge gaps (conf < %.2f)" % gap_threshold, len(gaps))

st.divider()

st.subheader("Most common queries / topics")
if top_questions:
    freq_df = pd.DataFrame(
        [{"Question": item["question"], "Count": int(item["count"])} for item in top_questions]
    ).set_index("Question")
    st.bar_chart(freq_df, color="#0f766e", horizontal=True, height=240)
    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
    for item in top_questions:
        q = item["question"]
        n = int(item["count"])
        pct = (n / total * 100) if total else 0.0
        st.markdown(
            f"""
            <div class="chunk-card" style="margin-bottom:0.9rem;">
                <div class="chunk-title">{q}</div>
                <div class="score-row">
                    <div class="score-bar-wrap">
                        <div class="score-bar-fill" style="width:{pct:.1f}%;background:#0f766e;"></div>
                    </div>
                    <div class="score-pill" style="color:#0f766e;">{n}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No queries recorded yet.")

st.divider()

st.subheader("Confidence distribution")
if total:
    labels = ["High (>=0.70)", "Moderate (0.50-0.69)", "Low (0.30-0.49)", "Very low (<0.30)"]
    values = [dist["high"], dist["moderate"], dist["low"], dist["very_low"]]
    colors = ["#0f766e", "#0891b2", "#d97706", "#dc2626"]

    pcts = [value / total * 100 for value in values]
    gradient_parts: list[str] = []
    start = 0.0
    for pct, color in zip(pcts, colors):
        end = start + pct
        gradient_parts.append(f"{color} {start:.1f}% {end:.1f}%")
        start = end
    gradient = "conic-gradient(" + ", ".join(gradient_parts) + ")"

    legend = "".join(
        (
            '<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;">'
            f'<span style="width:12px;height:12px;border-radius:3px;background:{color};flex:0 0 auto;"></span>'
            f'<span style="color:#334155;font-size:0.92rem;">{label}</span>'
            f'<span style="color:#0f172a;font-weight:700;font-size:0.92rem;margin-left:auto;">{value} ({pct:.0f}%)</span>'
            "</div>"
        )
        for label, value, pct, color in zip(labels, values, pcts, colors)
    )

    st.markdown(
        f"""
        <div class="glass-card" style="display:flex;align-items:center;gap:2rem;flex-wrap:wrap;">
            <div style="position:relative;width:170px;height:170px;border-radius:50%;background:{gradient};flex:0 0 auto;">
                <div style="position:absolute;top:25%;left:25%;width:50%;height:50%;border-radius:50%;background:rgba(255,255,255,0.88);"></div>
                <div style="position:absolute;top:0;left:0;right:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                    <span style="font-weight:700;font-size:1.5rem;color:#0f172a;">{total}</span>
                    <span style="font-size:0.78rem;color:#64748b;">queries</span>
                </div>
            </div>
            <div style="min-width:220px;flex:1;">{legend}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

    bins_df = pd.DataFrame({"Count": values}, index=[label.split(" ")[0] for label in labels])
    st.bar_chart(bins_df, color="#0891b2", height=240)
else:
    st.info("No confidence data yet.")

st.divider()

st.subheader("Knowledge gaps")
st.caption("Queries with confidence below the gap threshold — consider adding source documents for these topics.")
if gaps:
    for g in gaps:
        score = float(g["confidence"])
        st.markdown(
            f"""
            <div class="chunk-card" style="margin-bottom:0.9rem;">
                <div class="chunk-title">{g['question']}</div>
                <div class="chunk-meta">Confidence: {score:.2f} | {g['created_at']}</div>
                <div style="color:#334155;line-height:1.5;">{g['answer']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.success("No knowledge gaps detected.")

st.divider()

st.subheader("Recent query history")
try:
    recent = api_client.get_recent_queries(limit=50)
except FrontendAPIError as exc:
    st.error(str(exc))
    recent = []

if recent:
    rows = [
        {
            "Question": r["question"],
            "Confidence": float(r["confidence"]),
            "Answer": r["answer"],
            "When": r["created_at"],
        }
        for r in recent
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.info("No recent queries yet.")