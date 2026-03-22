"""
Data Quality — Quality observatory page.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.pipeline.ingestion import load_all
from src.pipeline.quality import compute_quality_scores
from src.pipeline.transform import transform
from src.quality_badges import quality_badge_html, quality_emoji, trust_score_bar

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Data Quality — GenderLens RW",
    page_icon="🛡️",
    layout="wide",
)

css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

_QUALITY_COLOR = {"good": "#10b981", "warning": "#f59e0b", "critical": "#ef4444"}
_PLT_BG = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f1f5f9", family="Inter"),
    margin=dict(l=24, r=24, t=40, b=24),
    xaxis=dict(gridcolor="rgba(148,163,184,0.06)"),
    yaxis=dict(gridcolor="rgba(148,163,184,0.06)"),
)


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
st.markdown("# Data Quality Observatory")
st.caption("Monitor and understand data quality across all studies in the catalog")
st.markdown("---")

# ---------------------------------------------------------------------------
# Traffic-light overview cards
# ---------------------------------------------------------------------------
st.markdown('<h2 class="section-title">Quality Overview</h2>', unsafe_allow_html=True)

ov1, ov2, ov3 = st.columns(3, gap="large")
for col, level in zip([ov1, ov2, ov3], ["good", "warning", "critical"]):
    count = (df["quality_level"] == level).sum()
    pct   = count / max(len(df), 1) * 100
    color = _QUALITY_COLOR[level]
    with col:
        st.markdown(
            f"""
            <div class="glass-card" style="padding:1.5rem;text-align:center;">
                <div style="font-size:2.25rem;">{quality_emoji(level)}</div>
                <div style="font-size:1.85rem;font-weight:700;color:{color};">{count}</div>
                <div style="color:#94a3b8;font-size:0.85rem;">
                    {level.title()} &nbsp;({pct:.0f}%)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

# ---------------------------------------------------------------------------
# Missing field analysis  |  Completeness distribution
# ---------------------------------------------------------------------------
st.markdown('<h2 class="section-title">Missing Field Analysis</h2>', unsafe_allow_html=True)

mf_col, cs_col = st.columns(2, gap="large")

with mf_col:
    if "missing_field_count" in df.columns:
        fig = px.histogram(
            df, x="missing_field_count",
            color="quality_level",
            color_discrete_map=_QUALITY_COLOR,
            labels={"missing_field_count": "Missing Fields", "count": "Studies"},
            barmode="stack",
        )
        fig.update_layout(**_PLT_BG, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

with cs_col:
    if "completeness_score" in df.columns:
        fig = px.box(
            df, y="completeness_score",
            color="quality_level",
            color_discrete_map=_QUALITY_COLOR,
            labels={"completeness_score": "Completeness Score"},
        )
        fig.update_layout(**_PLT_BG)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Quality flag breakdown
# ---------------------------------------------------------------------------
st.markdown('<h2 class="section-title">Quality Flag Breakdown</h2>', unsafe_allow_html=True)

all_flags: list[str] = []
for flags_list in df.get("quality_flags_list", []):
    if isinstance(flags_list, list):
        all_flags.extend(flags_list)

if all_flags:
    _FLAG_LABELS = {
        "missing_study_type": "Missing Study Type",
        "missing_scope_notes": "Missing Scope Notes",
        "no_resources_found": "No Resources Found",
        "missing_abstract": "Missing Abstract",
        "missing_units_of_analysis": "Missing Units of Analysis",
        "missing_get_microdata_url": "Missing Microdata URL",
        "missing_data_access_type": "Missing Data Access Type",
    }
    all_flags = [_FLAG_LABELS.get(f, f.replace("_", " ").title()) for f in all_flags]
    flag_counts = pd.Series(all_flags).value_counts().reset_index()
    flag_counts.columns = ["flag", "count"]
    fig = px.bar(
        flag_counts, x="count", y="flag",
        orientation="h",
        color_discrete_sequence=["#f59e0b"],
        labels={"count": "Occurrences", "flag": ""},
    )
    fig.update_layout(**_PLT_BG, showlegend=False)
    fig.update_traces(marker=dict(cornerradius=6))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.success("✅ No quality flags detected — all studies have complete metadata!")

st.markdown("---")

# ---------------------------------------------------------------------------
# Per-study drill-down
# ---------------------------------------------------------------------------
st.markdown('<h2 class="section-title">Per-Study Quality Drill-Down</h2>', unsafe_allow_html=True)

selected_study = st.selectbox(
    "Select a study",
    df["title"].tolist(),
    key="quality_study_select",
)

if selected_study:
    row = df[df["title"] == selected_study].iloc[0]

    info_col, radar_col = st.columns([2, 1], gap="large")

    with info_col:
        st.markdown(f"#### {row['title']}")
        st.markdown(
            f"**Organisation**: {row.get('organization', 'N/A')} &nbsp;·&nbsp; "
            f"**Year**: {row.get('year', 'N/A')}",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"**Quality**: {quality_badge_html(row.get('quality_level', 'unknown'))}",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Trust Score**: {trust_score_bar(row.get('trust_score', 0))}")
        st.markdown(f"**Completeness**: {row.get('completeness_score', 0):.0%}")
        st.markdown(f"**Freshness**: {row.get('freshness_score', 0):.0%}")
        st.markdown(f"**Missing Fields**: {row.get('missing_field_count', 0)}")

        flags = row.get("quality_flags_list", [])
        if flags:
            st.markdown(f"**Quality Flags**: {', '.join(flags)}")
        else:
            st.markdown("**Quality Flags**: None ✅")

        url = row.get("url", "")
        if url:
            st.markdown(f"**Catalog**: [{url}]({url})")

    with radar_col:
        rc_norm = min(int(row.get("resource_count_computed", 0)), 20) / 20.0
        categories = ["Completeness", "Freshness", "Resources", "Trust"]
        values = [
            float(row.get("completeness_score", 0)),
            float(row.get("freshness_score", 0)),
            rc_norm,
            float(row.get("trust_score", 0)),
        ]

        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(59, 130, 246, 0.15)",
            line=dict(color="#3b82f6", width=2),
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    gridcolor="rgba(148,163,184,0.2)",
                    tickfont=dict(color="#94A3B8"),
                ),
                angularaxis=dict(gridcolor="rgba(148,163,184,0.2)"),
            ),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", family="Inter"),
            height=300,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
