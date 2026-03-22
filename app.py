"""
GenderLens RW — Smart Gender Data Discovery Platform
Main entry point and landing page.
"""

import re

import pandas as pd
import streamlit as st
from pathlib import Path

from src.pipeline.ingestion import load_all
from src.pipeline.transform import transform
from src.pipeline.quality import compute_quality_scores

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="GenderLens RW",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading and enriching data …")
def get_enriched_data() -> pd.DataFrame:
    studies, resources, quality = load_all()
    df = transform(studies, resources, quality)
    return compute_quality_scores(df)


df = get_enriched_data()


# ---------------------------------------------------------------------------
# Study-group helpers  (Data Snapshot section)
# ---------------------------------------------------------------------------
_SERIES_RENAMES: list[tuple[str, str]] = [
    (r"^agriculture\s+household",                "Agricultural Household Survey"),
    (r"^demographic\s+health\s+survey",           "Demographic and Health Survey"),
    (r"^comprehensive food security.*nutrition",   "Food Security & Vulnerability Survey"),
    (r"^comprehensive food security",              "Food Security & Vulnerability Survey (CFSVA)"),
]


def _series_name(title: str) -> str:
    """Strip the year suffix and normalise the survey-series name."""
    s = re.sub(r"\s*,?\s*\d{4}(?:[/–-]\d{2,4})?\s*$", "", str(title)).strip()
    low = s.lower()
    for pattern, replacement in _SERIES_RENAMES:
        if re.search(pattern, low):
            return replacement
    return s


def _frequency(years: list[int]) -> str:
    if len(years) < 2:
        return "Single edition"
    gaps = [years[i + 1] - years[i] for i in range(len(years) - 1)]
    avg = sum(gaps) / len(gaps)
    if avg <= 1.5:
        return "Annual"
    if avg <= 2.5:
        return "Biennial"
    if avg <= 4.5:
        return "Periodic (~3–4 yrs)"
    return "Ad-hoc"


def build_study_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Group studies by survey series for the Data Snapshot table."""
    tmp = df.copy()
    tmp["_series"] = tmp["title"].apply(_series_name)
    org_col = "org_short" if "org_short" in tmp.columns else "organization"
    rows = []
    for series, grp in tmp.groupby("_series", sort=True):
        years = sorted(grp["year"].dropna().astype(int).unique().tolist())
        orgs = list(dict.fromkeys(grp[org_col].dropna().tolist()))
        res_col = "resource_count_computed"
        total_res = int(grp[res_col].sum()) if res_col in grp.columns else 0
        rows.append({
            "Survey Series":   series,
            "Frequency":       _frequency(years),
            "Years Conducted": " · ".join(map(str, years)),
            "Organization(s)": " / ".join(orgs[:2]) + ("…" if len(orgs) > 2 else ""),
            "Total Resources": total_res,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="gl-hero">
        <div class="gl-hero-badge">Open-source · Evidence-driven</div>
        <div class="gl-hero-title">
            GenderLens <span class="gl-accent-text">RW</span>
        </div>
        <p class="gl-hero-tagline">
            Rwanda&#39;s smart platform for discovering, trusting, and using
            gender-disaggregated microdata for evidence-based advocacy.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# PROBLEM & SOLUTION
# ---------------------------------------------------------------------------
st.markdown("---")
prob_col, sol_col = st.columns(2, gap="large")

with prob_col:
    st.markdown(
        """
        <div class="info-card problem-card">
            <h3>The Problem</h3>
            <p>
                Rwanda&#39;s gender-disaggregated datasets are <strong>fragmented across
                dozens of surveys</strong>, with <strong>inconsistent metadata quality</strong>
                and no unified discovery interface — making it hard for advocates,
                policymakers, and researchers to find and trust the data they need.
            </p>
            <ul>
                <li>No single place to search across all gender surveys</li>
                <li>Metadata completeness and freshness vary widely</li>
                <li>Difficult to assess data reliability at a glance</li>
                <li>Policy briefs require slow, manual citation work</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with sol_col:
    st.markdown(
        """
        <div class="info-card solution-card">
            <h3>The Solution</h3>
            <p>
                <strong>GenderLens RW</strong> provides a unified, AI-powered discovery
                layer on top of NISR&#39;s microdata catalog — enabling fast, trusted,
                evidence-based gender-data decisions.
            </p>
            <ul>
                <li><strong>Smart search</strong> across all studies and abstracts</li>
                <li><strong>Quality scoring</strong> with traffic-light indicators</li>
                <li><strong>Analytics dashboard</strong> with year trends and breakdowns</li>
                <li><strong>Advocacy toolkit</strong> with AI-generated policy briefs</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# KEY METRICS
# ---------------------------------------------------------------------------
st.markdown('<h2 class="section-title">Platform at a Glance</h2>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Studies", len(df))
with m2:
    total_res = int(df["resource_count_computed"].sum()) if "resource_count_computed" in df.columns else 0
    st.metric("Total Resources", total_res)
with m3:
    good_pct = (df["quality_level"] == "good").sum() / max(len(df), 1) * 100
    st.metric("Good Quality", f"{good_pct:.0f}%")
with m4:
    micro = int(df["has_microdata"].sum()) if "has_microdata" in df.columns else 0
    st.metric("With Microdata", micro)

# ---------------------------------------------------------------------------
# NISR GENDER DATA LAB
# ---------------------------------------------------------------------------
st.markdown('<h2 class="section-title">NISR Gender Data Lab</h2>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="nisr-ack-card">
        <p>
            GenderLens RW is built on data curated and published by the
            <strong>National Institute of Statistics of Rwanda (NISR)</strong>
            through its <strong>Gender Data Lab</strong> — Rwanda&#39;s authoritative
            source for gender-disaggregated statistics and interactive visualisation.
        </p>
        <p>
            The live Gender Data Lab dashboard is embedded below.
            Visit <a href="https://genderlab.statistics.gov.rw" target="_blank">
            genderlab.statistics.gov.rw</a> for the full platform.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <a href="https://genderlab.statistics.gov.rw/Visualisation/" target="_blank"
       style="text-decoration:none;">
        <div class="glass-card" style="
            padding: 2rem 1.75rem;
            text-align: center;
            cursor: pointer;
        ">
            <div style="font-size:1.15rem; font-weight:700; color:#f1f5f9; margin-bottom:0.5rem;">
                NISR Gender Data Lab &mdash; Live Dashboard
            </div>
            <div style="color:#94a3b8; font-size:0.9rem; margin-bottom:1.25rem; line-height:1.6;">
                Interactive visualisations of Rwanda&#39;s gender-disaggregated statistics,<br>
                published and maintained by the National Institute of Statistics of Rwanda.
            </div>
            <span class="stat-pill" style="padding:0.4rem 1.2rem; font-size:0.85rem;">
                Open Gender Data Lab &rarr;
            </span>
            <div style="margin-top:0.75rem; color:#64748b; font-size:0.75rem;">
                genderlab.statistics.gov.rw &middot; opens in a new tab
            </div>
        </div>
    </a>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KEY FEATURES
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown('<h2 class="section-title">Key Features</h2>', unsafe_allow_html=True)

feat_cols = st.columns(4, gap="medium")
_FEATURES = [
    {
        "title": "Smart Discovery",
        "desc": (
            "AI-powered TF-IDF semantic search across study titles and abstracts. "
            "Filter by year, organisation, quality level, and microdata availability."
        ),
        "page": "pages/Discovery.py",
        "label": "Open Discovery →",
    },
    {
        "title": "Analytics Dashboard",
        "desc": (
            "Interactive charts: study trends by year, resource-type distribution, "
            "quality breakdown, and organisation profiles."
        ),
        "page": "pages/Dashboard.py",
        "label": "Open Dashboard →",
    },
    {
        "title": "Data Quality",
        "desc": (
            "Traffic-light quality observatory: completeness, freshness, and resource "
            "scoring for every dataset in the catalog."
        ),
        "page": "pages/Data_Quality.py",
        "label": "Open Data Quality →",
    },
    {
        "title": "Advocacy Toolkit",
        "desc": (
            "Generate AI-assisted policy briefs with gender distributions, export data, "
            "and view full data provenance — all in one workflow."
        ),
        "page": "pages/Advocacy_Toolkit.py",
        "label": "Open Toolkit →",
    },
]

for col, feat in zip(feat_cols, _FEATURES):
    with col:
        st.markdown(
            f"""
            <div class="feature-card">
                <h4>{feat['title']}</h4>
                <p>{feat['desc']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link(feat["page"], label=feat["label"])

# ---------------------------------------------------------------------------
# DATA SNAPSHOT
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown('<h2 class="section-title">Data Snapshot</h2>', unsafe_allow_html=True)
st.caption(
    "Survey programmes in the NISR microdata catalog, grouped by series. "
    "Each row represents a recurring survey with one or more editions."
)

study_groups = build_study_groups(df)
st.dataframe(
    study_groups,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Survey Series":   st.column_config.TextColumn("Survey Series",   width="large"),
        "Frequency":       st.column_config.TextColumn("Frequency",       width="medium"),
        "Years Conducted": st.column_config.TextColumn("Years Conducted", width="medium"),
        "Organization(s)": st.column_config.TextColumn("Organization(s)", width="medium"),
        "Total Resources": st.column_config.NumberColumn("Resources",     format="%d"),
    },
)

with st.expander("Show all individual studies"):
    display_cols = [
        c for c in ["title", "year", "organization", "quality_level", "trust_score", "resource_count_computed"]
        if c in df.columns
    ]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div class="gl-footer">
        <strong>GenderLens RW</strong> &mdash;
        GIZ Gender Responsive Budgeting &amp; Resource Discovery Challenge 2026<br>
        Data source:
        <a href="https://microdata.statistics.gov.rw" target="_blank">NISR Microdata Catalog</a>
        &nbsp;&middot;&nbsp;
        <a href="https://genderlab.statistics.gov.rw" target="_blank">NISR Gender Data Lab</a>
        &nbsp;&middot;&nbsp;
        <a href="https://www.statistics.gov.rw" target="_blank">statistics.gov.rw</a>
    </div>
    """,
    unsafe_allow_html=True,
)
