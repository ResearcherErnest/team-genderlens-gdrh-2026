"""
Data Quality — Quality observatory page.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from src.pipeline.ingestion import load_all
from src.pipeline.transform import transform
from src.pipeline.quality import compute_quality_scores
from src.quality_badges import quality_emoji, quality_badge_html, trust_score_bar

# --- Page config ---
st.set_page_config(page_title="Data Quality — GenderLens RW", page_icon="🛡️", layout="wide")

css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

COLOR_MAP = {"good": "#10B981", "warning": "#F59E0B", "critical": "#EF4444"}
PLOTLY_BG = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#E2E8F0", "family": "Inter"},
}


@st.cache_data(show_spinner="Loading data …")
def get_data():
    studies, resources, quality = load_all()
    df = transform(studies, resources, quality)
    df = compute_quality_scores(df)
    return df


df = get_data()

# --- Header ---
st.markdown("# Data Quality Observatory")
st.markdown("Monitor and understand data quality across all studies")
st.markdown("---")

# --- Traffic-light overview ---
st.markdown("### Quality Overview")

col1, col2, col3 = st.columns(3)
for col, level in zip([col1, col2, col3], ["good", "warning", "critical"]):
    count = (df["quality_level"] == level).sum()
    pct = count / len(df) * 100 if len(df) > 0 else 0
    with col:
        st.markdown(
            f"""
            <div class="glass-card" style="padding: 1.5rem; text-align: center;">
                <div style="font-size: 2.5rem;">{quality_emoji(level)}</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: {COLOR_MAP.get(level, '#94A3B8')};">
                    {count}
                </div>
                <div style="color: #94A3B8; font-size: 0.9rem;">
                    {level.title()} ({pct:.0f}%)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

# --- Missing field analysis ---
st.markdown("### Missing Field Analysis")

col_a, col_b = st.columns(2)

with col_a:
    if "missing_field_count" in df.columns:
        fig = px.histogram(
            df,
            x="missing_field_count",
            color="quality_level",
            color_discrete_map=COLOR_MAP,
            labels={"missing_field_count": "Missing Fields"},
            barmode="stack",
        )
        fig.update_layout(**PLOTLY_BG, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.markdown("#### Completeness Scores")
    if "completeness_score" in df.columns:
        fig = px.box(
            df,
            y="completeness_score",
            color="quality_level",
            color_discrete_map=COLOR_MAP,
            labels={"completeness_score": "Completeness"},
        )
        fig.update_layout(**PLOTLY_BG)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Quality flag breakdown ---
st.markdown("### Quality Flag Breakdown")

all_flags = []
for flags_list in df["quality_flags_list"]:
    if isinstance(flags_list, list):
        all_flags.extend(flags_list)

if all_flags:
    flag_counts = pd.Series(all_flags).value_counts().reset_index()
    flag_counts.columns = ["flag", "count"]

    fig = px.bar(
        flag_counts,
        x="count",
        y="flag",
        orientation="h",
        color_discrete_sequence=["#F59E0B"],
    )
    fig.update_layout(**PLOTLY_BG, showlegend=False)
    fig.update_traces(marker=dict(cornerradius=6))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.success("No quality flags detected — all studies have complete metadata!")

st.markdown("---")

# --- Per-study drill-down ---
st.markdown("### Per-Study Quality Drill-Down")

selected_study = st.selectbox(
    "Select a study",
    df["title"].tolist(),
    key="quality_study_select",
)

if selected_study:
    row = df[df["title"] == selected_study].iloc[0]

    col_info, col_radar = st.columns([2, 1])

    with col_info:
        st.markdown(f"#### {row['title']}")
        st.markdown(
            f"**Organization**: {row.get('organization', 'N/A')} · "
            f"**Year**: {row.get('year', 'N/A')}",
        )
        st.markdown(f"**Quality**: {quality_badge_html(row['quality_level'])}", unsafe_allow_html=True)
        st.markdown(f"**Trust Score**: {trust_score_bar(row.get('trust_score', 0))}")
        st.markdown(f"**Completeness**: {row.get('completeness_score', 0):.0%}")
        st.markdown(f"**Freshness**: {row.get('freshness_score', 0):.0%}")
        st.markdown(f"**Missing Fields**: {row.get('missing_field_count', 0)}")

        flags = row.get("quality_flags_list", [])
        if flags:
            st.markdown(f"**Quality Flags**: {', '.join(flags)}")
        else:
            st.markdown("**Quality Flags**: None ✅")

    with col_radar:
        # Quality radar chart
        categories = ["Completeness", "Freshness", "Resources", "Trust"]
        rc = min(int(row.get("resource_count_computed", 0)), 20) / 20.0
        values = [
            row.get("completeness_score", 0),
            row.get("freshness_score", 0),
            rc,
            row.get("trust_score", 0),
        ]

        fig = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(124, 58, 237, 0.2)",
            line=dict(color="#7C3AED", width=2),
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(
                    visible=True, range=[0, 1],
                    gridcolor="rgba(148,163,184,0.2)",
                ),
                angularaxis=dict(gridcolor="rgba(148,163,184,0.2)"),
            ),
            showlegend=False,
            **PLOTLY_BG,
            height=300,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
