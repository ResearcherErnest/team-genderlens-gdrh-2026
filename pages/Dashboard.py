"""
Dashboard — Interactive analytics dashboard.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.pipeline.ingestion import load_all
from src.pipeline.quality import compute_quality_scores
from src.pipeline.transform import transform

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard — GenderLens RW",
    page_icon="📊",
    layout="wide",
)

css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Plotly theme — matches NISR colour palette
# ---------------------------------------------------------------------------
_PLT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E2E8F0", family="Inter"),
    xaxis=dict(gridcolor="rgba(148,163,184,0.08)"),
    yaxis=dict(gridcolor="rgba(148,163,184,0.08)"),
    margin=dict(l=24, r=24, t=40, b=24),
)
_COLORS = ["#1268B3", "#3498DB", "#00843D", "#D4A017", "#EF4444", "#64A7E5"]
_QUALITY_COLOR = {"good": "#00843D", "warning": "#D4A017", "critical": "#EF4444"}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data …")
def get_data() -> pd.DataFrame:
    studies, resources, quality = load_all()
    df = transform(studies, resources, quality)
    return compute_quality_scores(df)


df = get_data()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# 📊 Analytics Dashboard")
st.caption("Interactive data exploration across studies, resources, quality scores, and organisations")
st.markdown("---")

# ---------------------------------------------------------------------------
# Summary KPIs
# ---------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Total Studies", len(df))
with k2:
    avg_trust = df["trust_score"].mean() if "trust_score" in df.columns else 0
    st.metric("Avg Trust Score", f"{avg_trust:.0%}")
with k3:
    avg_comp = df["completeness_score"].mean() if "completeness_score" in df.columns else 0
    st.metric("Avg Completeness", f"{avg_comp:.0%}")
with k4:
    total_res = int(df["resource_count_computed"].sum()) if "resource_count_computed" in df.columns else 0
    st.metric("Total Resources", total_res)

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 1 — Studies by Year  |  Resource Types
# ---------------------------------------------------------------------------
col_a, col_b = st.columns(2, gap="large")

with col_a:
    st.markdown("### Studies by Year")
    if "year" in df.columns and df["year"].notna().any():
        year_counts = df.groupby("year").size().reset_index(name="count")
        fig = px.bar(
            year_counts, x="year", y="count",
            color_discrete_sequence=[_COLORS[0]],
            labels={"year": "Year", "count": "Studies"},
        )
        fig.update_layout(**_PLT_LAYOUT, showlegend=False)
        fig.update_traces(marker=dict(cornerradius=6, line=dict(width=0)))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No year data available.")

with col_b:
    st.markdown("### Resource Types")
    all_types: list[str] = []
    for types_list in df.get("resource_types", []):
        if isinstance(types_list, list):
            all_types.extend(types_list)

    if all_types:
        type_counts = pd.Series(all_types).value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        fig = px.pie(
            type_counts, values="count", names="type",
            color_discrete_sequence=_COLORS, hole=0.42,
        )
        fig.update_layout(**_PLT_LAYOUT)
        fig.update_traces(textposition="inside", textinfo="label+percent")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No resource-type data available.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 2 — Quality Distribution  |  Top Organisations
# ---------------------------------------------------------------------------
col_c, col_d = st.columns(2, gap="large")

with col_c:
    st.markdown("### Quality Distribution")
    if "quality_level" in df.columns:
        qc = df["quality_level"].value_counts().reset_index()
        qc.columns = ["level", "count"]
        fig = px.bar(
            qc, x="level", y="count",
            color="level", color_discrete_map=_QUALITY_COLOR,
            labels={"level": "Quality Level", "count": "Studies"},
        )
        fig.update_layout(**_PLT_LAYOUT, showlegend=False)
        fig.update_traces(marker=dict(cornerradius=6))
        st.plotly_chart(fig, use_container_width=True)

with col_d:
    st.markdown("### Top Organisations")
    if "organization" in df.columns:
        org_col = "org_short" if "org_short" in df.columns else "organization"
        org_counts = df[org_col].value_counts().head(10).reset_index()
        org_counts.columns = ["organisation", "count"]
        fig = px.bar(
            org_counts, x="count", y="organisation",
            orientation="h",
            color_discrete_sequence=[_COLORS[1]],
            labels={"count": "Studies", "organisation": ""},
        )
        fig.update_layout(**_PLT_LAYOUT, showlegend=False)
        fig.update_traces(marker=dict(cornerradius=6))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 3 — Trust Score Distribution
# ---------------------------------------------------------------------------
st.markdown("### Trust Score Distribution")
if "trust_score" in df.columns:
    fig = px.histogram(
        df, x="trust_score", nbins=20,
        color_discrete_sequence=[_COLORS[0]],
        labels={"trust_score": "Trust Score"},
    )
    fig.update_layout(**_PLT_LAYOUT, showlegend=False)
    fig.update_traces(marker=dict(cornerradius=4))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Row 4 — Quality radar per year
# ---------------------------------------------------------------------------
st.markdown("### Completeness vs Freshness vs Resources")

if all(c in df.columns for c in ["completeness_score", "freshness_score", "resource_count_computed"]):
    fig = px.scatter(
        df,
        x="completeness_score",
        y="freshness_score",
        size=df["resource_count_computed"].clip(upper=20).fillna(1),
        color="quality_level",
        color_discrete_map=_QUALITY_COLOR,
        hover_name="title",
        hover_data={"completeness_score": ":.0%", "freshness_score": ":.0%"},
        labels={
            "completeness_score": "Completeness",
            "freshness_score": "Freshness",
            "quality_level": "Quality",
        },
    )
    fig.update_layout(**_PLT_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
