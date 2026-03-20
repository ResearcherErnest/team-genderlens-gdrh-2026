"""
📊 Dashboard — Interactive analytics dashboard.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from src.pipeline.ingestion import load_all
from src.pipeline.transform import transform
from src.pipeline.quality import compute_quality_scores

# --- Page config ---
st.set_page_config(page_title="Dashboard — GenderLens RW", page_icon="📊", layout="wide")

css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# --- Plotly theme ---
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#E2E8F0", "family": "Inter"},
        "xaxis": {"gridcolor": "rgba(148,163,184,0.1)"},
        "yaxis": {"gridcolor": "rgba(148,163,184,0.1)"},
    }
}
COLOR_SEQUENCE = ["#7C3AED", "#2563EB", "#10B981", "#F59E0B", "#EF4444", "#A78BFA"]


# --- Data ---
@st.cache_data(show_spinner="Loading data …")
def get_data():
    studies, resources, quality = load_all()
    df = transform(studies, resources, quality)
    df = compute_quality_scores(df)
    return df


df = get_data()

# --- Header ---
st.markdown("# 📊 Analytics Dashboard")
st.markdown("Interactive data exploration across studies, resources, and quality")
st.markdown("---")

# --- Row 1: Studies by Year + Resource Type Distribution ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📅 Studies by Year")
    if "year" in df.columns and df["year"].notna().any():
        year_counts = df.groupby("year").size().reset_index(name="count")
        fig = px.bar(
            year_counts,
            x="year",
            y="count",
            color_discrete_sequence=[COLOR_SEQUENCE[0]],
        )
        fig.update_layout(**PLOTLY_TEMPLATE["layout"], showlegend=False)
        fig.update_traces(
            marker=dict(
                cornerradius=6,
                line=dict(width=0),
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No year data available.")

with col2:
    st.markdown("### 📁 Resource Types")
    # Flatten resource_types lists
    all_types = []
    for types_list in df["resource_types"]:
        if isinstance(types_list, list):
            all_types.extend(types_list)

    if all_types:
        import pandas as pd
        type_counts = pd.Series(all_types).value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        fig = px.pie(
            type_counts,
            values="count",
            names="type",
            color_discrete_sequence=COLOR_SEQUENCE,
            hole=0.4,
        )
        fig.update_layout(**PLOTLY_TEMPLATE["layout"])
        fig.update_traces(textposition="inside", textinfo="label+percent")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No resource type data available.")

st.markdown("---")

# --- Row 2: Quality Distribution + Organization Breakdown ---
col3, col4 = st.columns(2)

with col3:
    st.markdown("### 🛡️ Quality Distribution")
    if "quality_level" in df.columns:
        quality_counts = df["quality_level"].value_counts().reset_index()
        quality_counts.columns = ["level", "count"]
        color_map = {
            "good": "#10B981",
            "warning": "#F59E0B",
            "critical": "#EF4444",
        }
        fig = px.bar(
            quality_counts,
            x="level",
            y="count",
            color="level",
            color_discrete_map=color_map,
        )
        fig.update_layout(**PLOTLY_TEMPLATE["layout"], showlegend=False)
        fig.update_traces(marker=dict(cornerradius=6))
        st.plotly_chart(fig, use_container_width=True)

with col4:
    st.markdown("### 🏛️ Organizations")
    if "organization" in df.columns:
        org_counts = df["organization"].value_counts().reset_index()
        org_counts.columns = ["organization", "count"]
        fig = px.bar(
            org_counts,
            x="count",
            y="organization",
            orientation="h",
            color_discrete_sequence=[COLOR_SEQUENCE[1]],
        )
        fig.update_layout(**PLOTLY_TEMPLATE["layout"], showlegend=False)
        fig.update_traces(marker=dict(cornerradius=6))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Row 3: Trust Score Distribution ---
st.markdown("### 📈 Trust Score Distribution")
if "trust_score" in df.columns:
    fig = px.histogram(
        df,
        x="trust_score",
        nbins=20,
        color_discrete_sequence=[COLOR_SEQUENCE[0]],
        labels={"trust_score": "Trust Score"},
    )
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], showlegend=False)
    fig.update_traces(marker=dict(cornerradius=4))
    st.plotly_chart(fig, use_container_width=True)

# --- Summary stats ---
st.markdown("### 📊 Summary Statistics")
stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

with stat_col1:
    avg_trust = df["trust_score"].mean() if "trust_score" in df.columns else 0
    st.metric("Avg Trust Score", f"{avg_trust:.2f}")

with stat_col2:
    avg_completeness = df["completeness_score"].mean() if "completeness_score" in df.columns else 0
    st.metric("Avg Completeness", f"{avg_completeness:.0%}")

with stat_col3:
    avg_freshness = df["freshness_score"].mean() if "freshness_score" in df.columns else 0
    st.metric("Avg Freshness", f"{avg_freshness:.0%}")

with stat_col4:
    total_resources = int(df["resource_count_computed"].sum()) if "resource_count_computed" in df.columns else 0
    st.metric("Total Resources", total_resources)
