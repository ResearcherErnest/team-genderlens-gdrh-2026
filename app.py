"""
GenderLens RW — Smart Gender Data Discovery Platform
Main entry point and landing page.
"""

import streamlit as st
from pathlib import Path

from src.pipeline.ingestion import load_all
from src.pipeline.transform import transform
from src.pipeline.quality import compute_quality_scores

# --- Page config ---
st.set_page_config(
    page_title="GenderLens RW",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Inject custom CSS ---
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


# --- Data loading (cached) ---
@st.cache_data(show_spinner="Loading and enriching data …")
def get_enriched_data():
    studies, resources, quality = load_all()
    df = transform(studies, resources, quality)
    df = compute_quality_scores(df)
    return df


df = get_enriched_data()


# --- Hero section ---
st.markdown(
    """
    <div style="text-align: center; padding: 2rem 0 1rem 0;">
        <div class="hero-title">GenderLens RW</div>
        <div class="hero-subtitle">
            Smart Gender Data Discovery Platform for Rwanda<br>
            <em>Find, trust, and use gender-related data for evidence-based advocacy</em>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# --- KPI metric cards ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Studies", len(df))

with col2:
    total_resources = df["resource_count_computed"].sum() if "resource_count_computed" in df.columns else 0
    st.metric("Total Resources", int(total_resources))

with col3:
    good_pct = (
        (df["quality_level"] == "good").sum() / len(df) * 100
        if len(df) > 0 else 0
    )
    st.metric("Good Quality", f"{good_pct:.0f}%")

with col4:
    microdata_count = df["has_microdata"].sum() if "has_microdata" in df.columns else 0
    st.metric("With Microdata", int(microdata_count))

st.markdown("---")

# --- Quick navigation ---
st.markdown("###Explore the Platform")

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    st.markdown(
        """
        <div class="glass-card" style="padding: 1.5rem; text-align: center;">
            <h3>Discovery</h3>
            <p style="color: #94A3B8; font-size: 0.9rem;">
                AI-powered semantic search across studies and abstracts
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav_col2:
    st.markdown(
        """
        <div class="glass-card" style="padding: 1.5rem; text-align: center;">
            <h3>Dashboard</h3>
            <p style="color: #94A3B8; font-size: 0.9rem;">
                Interactive analytics with year trends and breakdowns
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav_col3:
    st.markdown(
        """
        <div class="glass-card" style="padding: 1.5rem; text-align: center;">
            <h3>Data Quality</h3>
            <p style="color: #94A3B8; font-size: 0.9rem;">
                Quality observatory with traffic-light scoring
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with nav_col4:
    st.markdown(
        """
        <div class="glass-card" style="padding: 1.5rem; text-align: center;">
            <h3>Advocacy</h3>
            <p style="color: #94A3B8; font-size: 0.9rem;">
                Auto-generate policy briefs with citations
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# --- Data snapshot ---
st.markdown("###Data Snapshot")

with st.expander("View all studies", expanded=False):
    display_cols = [
        c for c in ["title", "year", "organization", "quality_level", "trust_score", "resource_count_computed"]
        if c in df.columns
    ]
    st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
    )

# --- Footer ---
st.markdown(
    """
    <div style="text-align: center; padding: 2rem 0; color: #64748B; font-size: 0.85rem;">
        <strong>GenderLens RW</strong> — GIZ Gender Responsive Budgeting Resource Discovery Challenge 2026<br>
        Data source: <a href="https://microdata.statistics.gov.rw" target="_blank" style="color: #7C3AED;">
        NISR Microdata Catalog</a>
    </div>
    """,
    unsafe_allow_html=True,
)
