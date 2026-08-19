from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

_BIN_ORDER = ("high", "moderate", "low", "very_low")
_BIN_LABELS = {
    "high": "High (>=0.70)",
    "moderate": "Moderate (0.50-0.69)",
    "low": "Low (0.30-0.49)",
    "very_low": "Very low (<0.30)",
}
_BIN_METRIC_LABELS = {
    "high": "High",
    "moderate": "Moderate",
    "low": "Low",
    "very_low": "Very Low",
}
_BIN_MIDPOINTS = {
    "high": 0.85,
    "moderate": 0.6,
    "low": 0.4,
    "very_low": 0.15,
}


def apply_analytics_styles() -> None:
    st.markdown(
        """
<style>
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.92);
    border: 1px solid rgba(10,61,110,0.1);
    border-radius: 16px;
    padding: 0.75rem 1rem;
    box-shadow: 0 8px 20px rgba(10,61,110,0.06);
}
</style>
""",
        unsafe_allow_html=True,
    )


def _display_question(text: str, max_len: int = 80) -> str:
    cleaned = " ".join(str(text).split())
    if cleaned and cleaned == cleaned.lower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def _format_when(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %b %Y, %H:%M")
        except ValueError:
            return value
    return str(value)


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "High"
    if score >= 0.5:
        return "Moderate"
    if score >= 0.3:
        return "Low"
    return "Very low"


def build_insights(summary: dict[str, Any], recent: list[dict[str, Any]]) -> dict[str, Any]:
    total = int(summary["total_queries"])
    dist = summary["confidence_distribution"]
    gaps = summary["knowledge_gaps"]
    gap_threshold = float(summary["gap_threshold"])
    top_questions = summary["top_questions"]

    high = int(dist["high"])
    moderate = int(dist["moderate"])
    low = int(dist["low"])
    very_low = int(dist["very_low"])

    estimated_avg = 0.0
    if total:
        estimated_avg = sum(int(dist[k]) * _BIN_MIDPOINTS[k] for k in _BIN_MIDPOINTS) / total

    recent_avg = sum(float(r["confidence"]) for r in recent) / len(recent) if recent else 0.0
    gap_count = len(gaps)
    gap_rate = (gap_count / total * 100.0) if total else 0.0
    trusted_rate = ((high + moderate) / total * 100.0) if total else 0.0
    high_rate = (high / total * 100.0) if total else 0.0

    return {
        "total": total,
        "estimated_avg": estimated_avg,
        "recent_avg": recent_avg,
        "gap_count": gap_count,
        "gap_rate": gap_rate,
        "gap_threshold": gap_threshold,
        "trusted_rate": trusted_rate,
        "high_rate": high_rate,
        "unique_topics": len(top_questions),
        "top_topic": top_questions[0] if top_questions else None,
        "high": high,
        "moderate": moderate,
        "low": low,
        "very_low": very_low,
    }


def render_metrics(insights: dict[str, Any]) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total queries", insights["total"])
    c2.metric("Avg confidence", f"{insights['estimated_avg']:.0%}")
    c3.metric("Knowledge gaps", insights["gap_count"])
    c4.metric("Trusted answers", f"{insights['trusted_rate']:.0f}%")


def render_insights_panel(insights: dict[str, Any]) -> None:
    if insights["total"] == 0:
        st.info("No queries yet. Use **Knowledge Assistant** to ask questions — analytics update after each answer.")
        return

    lines = [
        f"**{insights['total']}** queries across **{insights['unique_topics']}** recurring topics.",
        f"Average confidence **{insights['estimated_avg']:.0%}** · **{insights['trusted_rate']:.0f}%** moderate or high.",
    ]
    if insights["gap_count"]:
        lines.append(
            f"**{insights['gap_count']}** knowledge gaps ({insights['gap_rate']:.0f}%) below "
            f"threshold **{insights['gap_threshold']:.2f}**."
        )
    else:
        lines.append("No knowledge gaps at the current threshold.")
    if insights["top_topic"]:
        topic = _display_question(str(insights["top_topic"]["question"]))
        lines.append(f'Most asked: **"{topic}"** ({int(insights["top_topic"]["count"])}×).')

    st.markdown("**Key insights**")
    for line in lines:
        st.markdown(f"- {line}")


_MIN_TOP_QUESTION_COUNT = 5


def render_top_topics_panel(top_questions: list[dict[str, Any]], total: int) -> None:
    st.subheader("Top questions")
    st.caption("Shown when the same question is asked more than 5 times.")

    frequent = [item for item in top_questions if int(item["count"]) > _MIN_TOP_QUESTION_COUNT]
    if not frequent:
        st.info("No questions have been repeated more than 5 times yet.")
        return

    max_count = max(int(item["count"]) for item in frequent)
    for item in frequent:
        q = _display_question(str(item["question"]))
        count = int(item["count"])
        share = (count / total * 100.0) if total else 0.0
        st.markdown(f"**{q}**")
        st.caption(f"{count} times · {share:.0f}% of queries")
        st.progress(min(count / max_count, 1.0))
        st.markdown("")


def render_confidence_panel(dist: dict[str, int], total: int) -> None:
    st.subheader("Confidence mix")
    if not total:
        st.caption("No data yet.")
        return

    rows = [
        {"Band": _BIN_LABELS[key], "Queries": int(dist[key])}
        for key in _BIN_ORDER
    ]
    df = pd.DataFrame(rows).set_index("Band")
    st.bar_chart(df, color="#1e6bb8", height=220)

    cols = st.columns(4)
    for col, key in zip(cols, _BIN_ORDER):
        count = int(dist[key])
        pct = count / total * 100.0 if total else 0.0
        col.metric(_BIN_METRIC_LABELS[key], count, f"{pct:.0f}%")



def render_gaps_panel(gaps: list[dict[str, Any]], gap_threshold: float) -> None:
    st.subheader("Knowledge gaps")
    st.caption(f"Queries with confidence below {gap_threshold:.2f}.")

    if not gaps:
        st.success("No knowledge gaps detected.")
        return

    for gap in gaps[:12]:
        score = float(gap["confidence"])
        label = _confidence_label(score)
        when = _format_when(gap.get("created_at", ""))
        with st.expander(f"{gap['question'][:70]} — {label} ({score:.2f})"):
            st.caption(when)
            st.progress(min(max(score, 0.0), 1.0))
            st.write(gap["answer"])


def render_history_panel(recent: list[dict[str, Any]]) -> None:
    st.subheader("Recent history")
    if not recent:
        st.caption("No history yet.")
        return

    rows = [
        {
            "When": _format_when(r.get("created_at", "")),
            "Question": r["question"],
            "Confidence": float(r["confidence"]),
            "Band": _confidence_label(float(r["confidence"])),
            "Answer": (r["answer"][:200] + "…") if len(r["answer"]) > 200 else r["answer"],
        }
        for r in recent
    ]
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Confidence": st.column_config.ProgressColumn(
                "Confidence",
                format="%.2f",
                min_value=0.0,
                max_value=1.0,
            ),
            "Question": st.column_config.TextColumn("Question", width="medium"),
            "Answer": st.column_config.TextColumn("Answer", width="large"),
        },
    )
